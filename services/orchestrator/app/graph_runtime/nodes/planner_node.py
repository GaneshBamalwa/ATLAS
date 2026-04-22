import uuid
import time
from typing import Dict, Any
from app.graph_runtime.state import GraphState
from app.router import route_query
from app.core.tracker import emit_trace_event
from app.middleware.instrumentation import instrument_node

@instrument_node(node_type="llm_planner", node_name="Intent Planner")
async def plan_next_step(state: GraphState) -> Dict[str, Any]:
    execution_id = state["execution_id"]
    loop_count = state.get("loop_count", 0) + 1
    
    current_message = state.get("current_message", state["user_message"])
    current_history = state.get("current_history", state.get("history", [])[-10:])
    user_context = state.get("user_context", {})
    
    # 10 loop max for complex chaining
    if loop_count > 10:
         return {"fatal_error": True, "orchestrator_errors": ["Max reasoning loops exceeded"]}

    try:
        # We pass the full history so the LLM knows what has already happened.
        decision = await route_query(current_message, history=current_history, context=user_context)
        
        state["_temp_meta"] = {
             "model_name": "meta-llama/llama-3.3-70b-instruct",
             "tokens_used": len(current_message) * 2
        }
        
        updates = {
            "loop_count": loop_count,
            "requires_tool": decision.requires_tool,
            "current_history": current_history,
            "current_message": current_message,
        }
        
        if decision.requires_tool:
            # --- STRICT LOOP PREVENTION ---
            tool_call = decision.tool_call
            for action in state.get("executed_actions", []):
                if action["tool_name"] == tool_call.tool and action["input"] == tool_call.arguments:
                    # We have already executed this exact tool call. Break the loop.
                    updates["requires_tool"] = False
                    updates["final_orchestrator_result"] = "I have already executed the necessary actions to fulfill this request. Here is the summary based on the results so far."
                    return updates
            
            updates["current_tool_call"] = tool_call
            updates["system_intent"] = f"using_{tool_call.tool}"
        else:
            updates["final_orchestrator_result"] = decision.response or "Process complete."
            
        return updates

        
    except Exception as e:
        error_msg = str(e)
        
        # Context window retry logic
        if "context_length_exceeded" in error_msg and loop_count == 1:
             return {"current_history": current_history[-2:], "loop_count": 0}
             
        return {
            "fatal_error": True, 
            "requires_tool": False,
            "orchestrator_errors": state.get("orchestrator_errors", []) + [error_msg]
        }
