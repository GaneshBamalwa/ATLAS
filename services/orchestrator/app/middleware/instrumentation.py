import time
import functools
from app.core.tracker import emit_trace_event

def instrument_node(node_type: str, node_name: str):
    """
    Decorator that intercepts a LangGraph Node execution, 
    records inputs, calculates latency, handles failures/simulations, 
    and emits structured telemetry to the distributed tracker.
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(state: dict, *args, **kwargs):
            execution_id = state.get("execution_id", "unknown_exe")
            
            # Dynamic Name resolution (e.g. for Tool Execution)
            display_name = node_name
            if node_type == "mcp_tool" and "current_tool_call" in state:
                # e.g. "Execute search_emails"
                t_call = state["current_tool_call"]
                tool_name = getattr(t_call, "tool", str(t_call))
                display_name = f"Execute {tool_name}"

            # Use deterministic state node ID if available or fallback
            base_node_id = f"{node_type}_{display_name.lower().replace(' ', '_')}"
            loop_count = state.get("loop_count", 0)
            
            node_id = f"{base_node_id}_{loop_count}" if "planner" in node_type else f"{base_node_id}_{time.time_ns()}"
            
            # 1. Pre-execution telemetry
            safe_inputs = {k: v for k, v in state.items() if k not in ["current_history", "history", "user_context"]}
            emit_trace_event(
                execution_id, 
                node_id, 
                "running", 
                node_type=node_type,
                name=display_name,
                inputs=safe_inputs
            )
            
            start_time = time.perf_counter()
            
            try:
                # ─── INJECT SIMULATED FAILURES ───
                forced_failures = state.get("simulated_failures", {})
                if node_id in forced_failures or node_name in forced_failures:
                    raise RuntimeError(f"Simulated Runtime Fault: {forced_failures.get(node_id, 'Forced Interruption')}")
                
                # 2. Execute Business Logic
                result = await func(state, *args, **kwargs)
                
                latency = (time.perf_counter() - start_time) * 1000
                
                # Extract meta from state if the node attached any
                meta = state.pop("_temp_meta", {})
                
                emit_trace_event(
                    execution_id, 
                    node_id, 
                    "success", 
                    name=display_name,
                    outputs=result, 
                    meta=meta,
                    latency=latency
                )
                
                return result
                
            except Exception as e:
                latency = (time.perf_counter() - start_time) * 1000
                emit_trace_event(
                    execution_id, 
                    node_id, 
                    "failed", 
                    error=str(e), 
                    latency=latency
                )
                raise
                
        return wrapper
    return decorator
