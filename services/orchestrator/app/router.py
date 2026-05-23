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

TOOL_HINT_PATTERNS = [
    re.compile(r"\b(email|mail|gmail|inbox|message|send\s+email|reply\s+to\s+email)\b", re.IGNORECASE),
    re.compile(r"\b(calendar|meeting|event|schedule|appointment|invite)\b", re.IGNORECASE),
    re.compile(r"\b(drive|file|document|folder|share\s+link|upload|download|search\s+drive)\b", re.IGNORECASE),
    re.compile(r"\b(open|read|find|search|send|draft|delete|trash|move|share)\b", re.IGNORECASE),
]


DIRECT_ANSWER_SYSTEM_PROMPT = """You are a helpful assistant.

Answer the user's message directly in natural language.
Do not mention tools, JSON, routing, orchestration, or internal systems.
Use concise markdown formatting when helpful.
If you use headings, place heading text on its own line.
If you use lists, put each item on its own line and keep a blank line before the list.
Do not collapse multiple sections into a single line.
"""

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


def _build_context_block(context: dict = None) -> str:
    now = datetime.datetime.now()
    sys_context = f"Current Time: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
    if context:
        sys_context += f"User Email: {context.get('email', 'N/A')}\n"

    memory = "None"
    if context and context.get("relevant_past_memories"):
        memory = "\n".join([str(m) for m in context.get("relevant_past_memories")])

    return f"### CONTEXT\n{sys_context}\n### MEMORY\n{memory}"

def _extract_json(text: str) -> Optional[dict]:
    if not text:
        return None
    bare = re.search(r"(\{.*\})", text, re.DOTALL)
    if bare:
        try:
            return json.loads(bare.group(1))
        except:
            pass
    return None


def _looks_tool_related(user_message: str) -> bool:
    normalized = user_message.strip()
    if not normalized:
        return False

    return any(pattern.search(normalized) for pattern in TOOL_HINT_PATTERNS)


async def _generate_direct_answer(user_message: str, history: list[dict[str, str]] = None, context: dict = None) -> str:
    messages = [{"role": "system", "content": DIRECT_ANSWER_SYSTEM_PROMPT + "\n\n" + _build_context_block(context)}]
    if history:
        # Limit to last 3 messages for speed
        messages.extend(history[-6:])
    messages.append({"role": "user", "content": user_message})

    from dotenv import dotenv_values
    env = dotenv_values(".env")
    api_key = env.get("GROQ_API_KEY", "").strip() or env.get("OPENROUTER_API_KEY", "").strip()
    
    # Use faster model for direct answers
    model = "llama-3.1-8b-instant"
    base_url = "https://api.groq.com/openai/v1"
    
    # Fallback if Groq key not available
    if not env.get("GROQ_API_KEY"):
        model = env.get("LLM_MODEL", settings.llm_model)
        base_url = env.get("LLM_BASE_URL", settings.llm_base_url)

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 500,  # Limit output for speed
    }

    async with httpx.AsyncClient(timeout=15.0) as client:  # Reduced from 60s to 15s
        resp = await client.post(
            f"{base_url}/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {api_key}"},
        )
        if resp.status_code != 200:
            raise Exception(f"API Error {resp.status_code}")

        data = resp.json()
        content = data["choices"][0]["message"].get("content") or ""
        return content.strip()

@log_execution_time
async def route_query(user_message: str, history: list[dict[str, str]] = None, context: dict = None) -> RouterDecision:
    logger.info(f"[ROUTER] Routing: '{user_message[:100]}'")

    if not _looks_tool_related(user_message):
        try:
            direct_response = await _generate_direct_answer(user_message, history=history, context=context)
            return RouterDecision(requires_tool=False, response=direct_response)
        except Exception as e:
            logger.error(f"[ROUTER] Direct-answer fallback failed: {e}")

    messages = [{"role": "system", "content": _build_system_prompt(context)}]
    if history:
        # Limit to last 6 messages (3 exchanges) for speed
        messages.extend(history[-6:])
    messages.append({"role": "user", "content": user_message})

    from dotenv import dotenv_values
    env = dotenv_values(".env")
    api_key = env.get("OPENROUTER_API_KEY", "").strip() or env.get("GROQ_API_KEY", "").strip()
    
    # Use Groq's faster model for routing decisions
    model = "llama-3.1-8b-instant"
    base_url = "https://api.groq.com/openai/v1"
    
    # Fallback to configured model if Groq not available
    if not env.get("GROQ_API_KEY"):
        model = env.get("LLM_MODEL", settings.llm_model)
        base_url = env.get("LLM_BASE_URL", settings.llm_base_url)

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
        "max_tokens": 800,  # Limit output for speed
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:  # Reduced from 60s to 15s
            resp = await client.post(f"{base_url}/chat/completions", json=payload, headers={"Authorization": f"Bearer {api_key}"})
            if resp.status_code != 200:
                raise Exception(f"API Error {resp.status_code}")

            raw = resp.json()["choices"][0]["message"].get("content") or ""
            parsed = _extract_json(raw)
            if not parsed:
                return RouterDecision(requires_tool=False, response=raw or "Sorry, I couldn't understand that.")

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

async def decide_execution_mode(user_message: str) -> str:
    """Decides whether to use 'dag' or 'react' execution mode based on query complexity."""
    from dotenv import dotenv_values
    env = dotenv_values(".env")
    api_key = env.get("OPENROUTER_API_KEY", "").strip() or env.get("GROQ_API_KEY", "").strip()
    
    # Fast model
    model = "llama-3.1-8b-instant"
    base_url = "https://api.groq.com/openai/v1"
    if not env.get("GROQ_API_KEY"):
        model = env.get("LLM_MODEL", settings.llm_model)
        base_url = env.get("LLM_BASE_URL", settings.llm_base_url)

    system_prompt = """Classify the user's query into one of two orchestration modes:
- "dag": For explicit multi-step tasks, tool-heavy workflows, or requests that require independent/parallel execution of clearly defined subtasks (e.g. "search my drive for X and email Y").
- "react": For ambiguous requests, conversational reasoning, complex step-by-step conditional logic where the next step depends entirely on the previous step's output.

Return a JSON with a single key "mode" set to "dag" or "react". Default to "dag" if unsure."""

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.0,
        "response_format": {"type": "json_object"},
        "max_tokens": 100,
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(f"{base_url}/chat/completions", json=payload, headers={"Authorization": f"Bearer {api_key}"})
            if resp.status_code != 200:
                return "dag"
            raw = resp.json()["choices"][0]["message"]["content"]
            parsed = _extract_json(raw)
            if not parsed:
                parsed = json.loads(raw)
            return parsed.get("mode", "dag").lower()
    except Exception as e:
        logger.error(f"[ROUTER] Mode classification failed, defaulting to dag: {e}")
        return "dag"
