"""
router.py - LLM-powered intent router.

Uses httpx directly to call the OpenRouter API.
"""

from __future__ import annotations
import httpx
import json
import re
import datetime
from typing import Optional, Any, List

from app.config import get_settings
from app.schemas import RouterDecision, ToolCall
from app.tool_registry import registry
from app.utils.logger import logger, log_execution_time

settings = get_settings()

SYSTEM_PROMPT_TEMPLATE = """You are the reasoning engine of an AI orchestration system.

Your responsibilities:
1. Understand user intent
2. Execute tool calls when necessary
3. Chain tools if needed
4. SYNTHESIZE a helpful final human response once tools are finished.

CRITICAL RULES:
1. ALWAYS use the unique 'id' returned from search results (search_drive, search_emails) when calling follow-up tools (get_drive_share_link, read_email). NEVER use 'name' or 'subject' as an ID.
2. DO NOT verify success by running another tool if the previous tool's output already confirms it.
3. If you have gathered the requested information, DO NOT use any more tools. Set 'requires_tool' to false and put the summary in 'final_result' IMMEDIATELY.
4. NEVER repeat a tool call with the same arguments.
5. Provide a warm, human-friendly summary in 'final_result'.
6. Always output valid JSON.

OUTPUT FORMAT (JSON only):
{{
  "intent": "<intent>",
  "requires_tool": true | false,
  "actions": [
    {{
      "step": 1,
      "tool_name": "<tool name>",
      "input": {{ ... }}
    }}
  ],
  "final_result": "<User-facing summary of results if tools are done, or follow-up question>",
  "confidence": 0.0 - 1.0
}}
"""

def _build_system_prompt(context: dict = None) -> str:
    now = datetime.datetime.now()
    sys_context = f"Current Time: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
    if context:
        sys_context += f"User Email: {context.get('email', 'N/A')}\n"
    
    memory = "None"
    if context and context.get("relevant_past_memories"):
        memory = "\n".join([str(m) for m in context.get("relevant_past_memories")])

    return f"{SYSTEM_PROMPT_TEMPLATE}\n\n### CONTEXT\n{sys_context}\n\n### TOOLS\n{registry.tool_descriptions_for_prompt()}\n\n### MEMORY\n{memory}"

def _extract_json(text: str) -> Optional[dict]:
    bare = re.search(r"(\{.*\})", text, re.DOTALL)
    if bare:
        try:
            return json.loads(bare.group(1))
        except:
            pass
    return None

@log_execution_time
async def route_query(user_message: str, history: list[dict[str, str]] = None, context: dict = None) -> RouterDecision:
    logger.info(f"[ROUTER] Routing: '{user_message[:100]}'")

    messages = [{"role": "system", "content": _build_system_prompt(context)}]
    if history:
        messages.extend(history[-10:])
    messages.append({"role": "user", "content": user_message})

    from dotenv import dotenv_values
    env = dotenv_values(".env")
    api_key = env.get("OPENROUTER_API_KEY", "").strip() or env.get("GROQ_API_KEY", "").strip()
    base_url = env.get("LLM_BASE_URL", settings.llm_base_url).strip()
    model = env.get("LLM_MODEL", settings.llm_model).strip()

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,
        "response_format": {"type": "json_object"}
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{base_url}/chat/completions", json=payload, headers={"Authorization": f"Bearer {api_key}"})
            if resp.status_code != 200:
                raise Exception(f"API Error {resp.status_code}")

            raw = resp.json()["choices"][0]["message"]["content"]
            parsed = _extract_json(raw)
            if not parsed:
                return RouterDecision(requires_tool=False, response=raw)

            requires_tool = parsed.get("requires_tool", False)
            actions = parsed.get("actions", [])
            final_res = parsed.get("final_result", "")

            # HEURISTIC: If model provided actions, it MUST require a tool, regardless of what it said.
            if actions:
                requires_tool = True

            if requires_tool and actions:
                tool = actions[0].get("tool_name")
                args = actions[0].get("input", {})
                if registry.get(tool):
                    logger.info(f"[ROUTER] Valid tool call: {tool}")
                    return RouterDecision(requires_tool=True, tool_call=ToolCall(tool=tool, arguments=args))
                else:
                    logger.warning(f"[ROUTER] Unknown tool: {tool}")

            return RouterDecision(requires_tool=False, response=final_res or raw)
    except Exception as e:
        logger.error(f"[ROUTER] Failed: {e}")
        return RouterDecision(requires_tool=False, response="Sorry, I encountered a technical routing error.")

async def extract_facts(user_message: str, response: str) -> List[Dict[str, Any]]:
    return []
