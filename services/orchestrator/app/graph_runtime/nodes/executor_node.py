import time
import uuid
import re
from typing import Dict, Any
from app.graph_runtime.state import GraphState
from app.executor import execute_tool
from app.schemas import ToolCall
from app.utils.logger import logger
from app.middleware.instrumentation import instrument_node

@instrument_node(node_type="mcp_tool", node_name="Tool Execution")
async def execute_tool_node(state: GraphState) -> Dict[str, Any]:
    tool_call = state["current_tool_call"]
    mutative_tools = {"send_email", "add_calendar_event", "delete_calendar_event", "trash_drive_file"}
    
    # ── Universal Skip & Replay Logic ─────────────────────────────────────────
    # If this tool was already successful in this session, REPLAY the result 
    # instead of re-executing.
    # ──────────────────────────────────────────────────────────────────────────
    executed_actions = state.get("executed_actions", [])
    for action in executed_actions:
        # Check for matching executions
        is_exact_match = (action["tool_name"] == tool_call.tool and action["input"] == tool_call.arguments)
        is_mutative_match = (tool_call.tool in mutative_tools and action["tool_name"] == tool_call.tool)
        
        if is_exact_match or is_mutative_match:
            if action["status"] == "success":
                logger.info(f"[REPLAY] Fast-forwarding {tool_call.tool} using cached result.")
                
                # Prepare result for the LLM turn
                essential_data = action["output"]
                if isinstance(essential_data, dict) and "content" in essential_data:
                    essential_data = {k: v for k, v in essential_data.items() if k != "content"}
                    essential_data["_info"] = "Result replayed from memory."
                    
                current_history = state.get("current_history", []) + [
                    {"role": "user", "content": f"Result of {tool_call.tool} (replayed): {essential_data}"}
                ]
                
                original_request = state.get("user_message", "Satisfy user intent")
                
                # Stronger directive to prevent loops
                next_msg = f"CONTEXT: I have already replayed the result for '{tool_call.tool}'. " \
                           f"THE GOAL IS: '{original_request}'. " \
                           f"MOVE TO THE NEXT STEP. DO NOT RE-EXECUTE '{tool_call.tool}'."

                return {
                    "current_history": current_history,
                    "current_message": next_msg,
                }
            else:
                # Repeated failure detection
                logger.warning(f"[LOOP] Repeated failure for {tool_call.tool}. Adding warning to history.")
                current_history = state.get("current_history", []) + [
                    {"role": "user", "content": f"WARNING: I previously attempted '{tool_call.tool}' with these arguments and it FAILED: {action.get('output', 'Error')}. " \
                                               f"Do NOT retry the exact same call. Check if you should use an ID instead of a name, or if arguments are missing."}
                ]
                # Allow it to continue to normal execution logic which will likely return the same error 
                # but with the history warning now present.

    # ── Normal Execution ──────────────────────────────────────────────────────
    try:
        user_context = state.get("user_context", {})
        response = await execute_tool(
            tool_call, 
            gmail_user_id=user_context.get("gmail_user_id"),
            drive_user_id=user_context.get("drive_user_id"),
            calendar_user_id=user_context.get("calendar_user_id")
        )
        
        status = "success" if response.success else "failed"
        action_log = {
            "step": state.get("loop_count", 1),
            "tool_name": tool_call.tool,
            "input": tool_call.arguments,
            "output": response.data,
            "status": status
        }
        
        # Format output for LLM
        essential_data = response.data
        if isinstance(essential_data, dict) and "content" in essential_data:
            essential_data = {k: v for k, v in essential_data.items() if k != "content"}
            essential_data["_info"] = "Content truncated."
            
        current_history = state.get("current_history", []) + [
            {"role": "user", "content": f"Output from {tool_call.tool}: {essential_data}"}
        ]
        
        original_request = state.get("user_message", "Satisfy user intent")
        next_message = f"CONTEXT: I just executed '{tool_call.tool}' successfully. " \
                       f"THE GOAL IS: '{original_request}'. " \
                       f"BASED ON THE TOOL OUTPUT IN HISTORY, WHAT IS THE NEXT STEP? " \
                       f"DO NOT RE-EXECUTE '{tool_call.tool}' UNLESS ABSOLUTELY NECESSARY WITH DIFFERENT ARGS."
        
        return {
            "executed_actions": executed_actions + [action_log],
            "orchestrator_errors": state.get("orchestrator_errors", []) + ([response.error] if not response.success else []),
            "current_history": current_history,
            "current_message": next_message,
        }
    except Exception as e:
        logger.error(f"[EXECUTOR] Critical error: {e}")
        return {"orchestrator_errors": state.get("orchestrator_errors", []) + [str(e)], "fatal_error": True}
