from typing import Dict, Any
from app.graph_runtime.state import GraphState
from app.formatter import format_response
from app.middleware.instrumentation import instrument_node

@instrument_node(node_type="formatter", node_name="Response Synthesis")
async def finalize_response(state: GraphState) -> Dict[str, Any]:
    # Construct strictly what the Formatter model expects
    payload = {
        "intent": state.get("system_intent", "general_query"),
        "requires_tools": len(state.get("executed_actions", [])) > 0,
        "actions": state.get("executed_actions", []),
        "final_result": state.get("final_orchestrator_result", "Process complete."),
        "confidence": 0.85 if not state.get("orchestrator_errors") else 0.4,
        "errors": state.get("orchestrator_errors", [])
    }
    
    try:
        if state.get("fatal_error"):
            # If router crashed or max loops hit, just return technical failure
            errors = state.get("orchestrator_errors", [])
            err_msg = errors[-1] if errors else "Unknown logic error."
            final_text = f"**Technical Failure:** `{err_msg}`"
        else:
            final_text = await format_response(payload)
            
        return {"final_human_response": final_text}
    except Exception as e:
        return {"final_human_response": "An internal error occurred while formatting your response."}
