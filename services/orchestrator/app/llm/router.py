"""
services/orchestrator/llm/router.py - Provider-agnostic Intent Router and Modes Classifier
"""

import json
import re
import logging
from typing import Optional, List, Dict, Any

from shared.config import global_config as settings
from app.schemas import RouterDecision, ToolCall
from app.tool_registry import registry
from app.utils.logger import log_execution_time

from .prompts import (
    TOOL_HINT_PATTERNS,
    DIRECT_ANSWER_SYSTEM_PROMPT,
    build_system_prompt,
    build_context_block
)
from .provider import LLMProvider, LLMFactory

logger = logging.getLogger(__name__)

# Fallback initializer helper
def _get_default_llm_clients() -> tuple[LLMProvider, LLMProvider]:
    """Helper to initialize clients when they are not passed in explicitly"""
    routing_provider = settings.llm.routing_provider
    routing_config = {
        "model": settings.llm.routing_model,
        "api_key": settings.llm.routing_api_key or settings.llm_api_key,
        "timeout": 15
    }
    
    formatting_provider = settings.llm.formatting_provider
    formatting_config = {
        "model": settings.llm.formatting_model,
        "base_url": settings.llm.formatting_base_url,
        "timeout": 60
    }
    
    routing_client = LLMFactory.create(routing_provider, routing_config)
    formatting_client = LLMFactory.create(formatting_provider, formatting_config)
    return routing_client, formatting_client


def looks_tool_related(user_message: str) -> bool:
    """Uses fast regex patterns to check if a query likely requires workspace tools"""
    normalized = user_message.strip()
    if not normalized:
        return False
    return any(pattern.search(normalized) for pattern in TOOL_HINT_PATTERNS)


def extract_json(text: str) -> Optional[dict]:
    """Extracts JSON substrings safely"""
    if not text:
        return None
    bare = re.search(r"(\{.*\})", text, re.DOTALL)
    if bare:
        try:
            return json.loads(bare.group(1))
        except Exception:
            pass
    return None


async def generate_direct_answer(
    user_message: str,
    history: Optional[List[Dict[str, str]]] = None,
    context: Optional[Dict[str, Any]] = None,
    llm: Optional[LLMProvider] = None
) -> str:
    """Answers user queries directly using LLM without tools"""
    if llm is None:
        llm, _ = _get_default_llm_clients()
        
    prompt = f"{DIRECT_ANSWER_SYSTEM_PROMPT}\n\n{build_context_block(context)}\n\n"
    if history:
        prompt += "### DISCUSSION HISTORY\n"
        for h in history[-6:]:
            prompt += f"{h['role'].upper()}: {h['content']}\n"
    prompt += f"USER: {user_message}\nASSISTANT:"
    
    try:
        # We use standard fast model for direct answering
        response = await llm.generate(
            prompt=prompt,
            temperature=0.3,
            max_tokens=600
        )
        return response
    except Exception as e:
        logger.error(f"Failed to generate direct response: {e}")
        raise


@log_execution_time
async def route_query(
    user_message: str,
    history: Optional[List[Dict[str, str]]] = None,
    context: Optional[Dict[str, Any]] = None,
    routing_llm: Optional[LLMProvider] = None,
    formatting_llm: Optional[LLMProvider] = None
) -> RouterDecision:
    """Main routing entry point. Analyzes queries and decides whether tools are required"""
    logger.info(f"[ROUTER] Analyzing query: '{user_message[:100]}'")
    
    if routing_llm is None or formatting_llm is None:
        def_routing, def_formatting = _get_default_llm_clients()
        routing_llm = routing_llm or def_routing
        formatting_llm = formatting_llm or def_formatting
        
    # Step 1: Direct fast routing heuristic
    if not looks_tool_related(user_message):
        try:
            direct_response = await generate_direct_answer(
                user_message, history=history, context=context, llm=routing_llm
            )
            return RouterDecision(requires_tool=False, response=direct_response)
        except Exception as e:
            logger.error(f"[ROUTER] Direct response generation failed: {e}")
            
    # Step 2: System-prompt intent classification
    system_prompt = build_system_prompt(context)
    prompt = f"{system_prompt}\n\n"
    if history:
        prompt += "### CONVERSATION HISTORY\n"
        for h in history[-6:]:
            prompt += f"{h['role'].upper()}: {h['content']}\n"
    prompt += f"USER: {user_message}\n\nCompile strict routing JSON payload following output instructions:"
    
    try:
        raw_response = await routing_llm.generate(
            prompt=prompt,
            temperature=0.1,
            max_tokens=800
        )
        
        parsed = extract_json(raw_response)
        if not parsed:
            # Fallback if LLM outputs plain text directly
            return RouterDecision(requires_tool=False, response=raw_response or "Sorry, I couldn't understand that.")
            
        requires_tool = parsed.get("requires_tool", False)
        actions = parsed.get("actions", [])
        final_res = parsed.get("final_result", "")
        
        # Guard rails: if actions are explicitly mapped, we must execute them
        if actions:
            requires_tool = True
            
        if requires_tool and actions:
            tool = actions[0].get("tool_name")
            args = actions[0].get("input", {})
            if registry.get(tool):
                logger.info(f"[ROUTER] Router dispatched tool: {tool}")
                return RouterDecision(requires_tool=True, tool_call=ToolCall(tool=tool, arguments=args))
            else:
                logger.warning(f"[ROUTER] Unknown tool call blocked: {tool}")
                
        return RouterDecision(requires_tool=False, response=final_res or raw_response)
        
    except Exception as e:
        logger.error(f"[ROUTER] Error routing query: {e}")
        return RouterDecision(requires_tool=False, response="Sorry, I encountered a technical routing issue.")


async def extract_facts(user_message: str, response: str) -> List[Dict[str, Any]]:
    """Legacy compatibility extractor hook"""
    return []


async def decide_execution_mode(user_message: str, llm: Optional[LLMProvider] = None) -> str:
    """Decides dynamically between parallel DAG execution and loop-based ReAct orchestration"""
    if llm is None:
        llm, _ = _get_default_llm_clients()
        
    system_prompt = """Classify the user's query into one of two orchestration modes:
- "dag": For explicit multi-step tasks, tool-heavy workflows, or requests that require independent/parallel execution of clearly defined subtasks (e.g. "search my drive for X and email Y").
- "react": For ambiguous requests, conversational reasoning, complex step-by-step conditional logic where the next step depends entirely on the previous step's output.

Return a JSON with a single key "mode" set to "dag" or "react". Default to "dag" if unsure."""

    prompt = f"{system_prompt}\n\nUSER QUERY: {user_message}\nCLASSIFICATION JSON:"
    
    try:
        raw_response = await llm.generate(
            prompt=prompt,
            temperature=0.0,
            max_tokens=100
        )
        parsed = extract_json(raw_response)
        if not parsed:
            parsed = json.loads(raw_response)
        return parsed.get("mode", "dag").lower()
    except Exception as e:
        logger.error(f"[ROUTER] Execution mode classification failed: {e}")
        return "dag"
