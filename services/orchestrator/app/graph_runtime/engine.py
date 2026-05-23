import uuid
from typing import Dict, Any

from app.graph_runtime.state import GraphState
from app.graph_runtime.nodes.planner_node import plan_next_step
from app.graph_runtime.nodes.executor_node import execute_tool_node
from app.graph_runtime.nodes.formatter_node import finalize_response


# Try to use langgraph when available for a richer graph runtime. If it's not
# installed, fall back to a small deterministic loop that sequentially calls
# the planner, executor and formatter nodes to produce a compatible result.
try:
    from langgraph.graph import StateGraph, END

    def should_execute_tool(state: GraphState) -> str:
        """Conditional edge routing based on planner decision."""
        if state.get("requires_tool") and not state.get("fatal_error"):
            return "executor"
        return "formatter"

    def build_execution_graph():
        workflow = StateGraph(GraphState)

        # 1. Add Vertices
        workflow.add_node("planner", plan_next_step)
        workflow.add_node("executor", execute_tool_node)
        workflow.add_node("formatter", finalize_response)

        workflow.set_entry_point("planner")

        # 2. Add Conditional Routing (Edges)
        workflow.add_conditional_edges(
            "planner",
            should_execute_tool,
            {
                "executor": "executor",
                "formatter": "formatter"
            }
        )

        # 3. Complete Loop cycle
        workflow.add_edge("executor", "planner")
        workflow.add_edge("formatter", END)

        return workflow.compile()

    async def run_workflow(message: str, history: list = None, context: dict = None, execution_id: str = None):
        """
        Main entry point for running the LangGraph orchestration using langgraph.
        """
        app = build_execution_graph()

        initial_state: GraphState = {
            "execution_id": execution_id or f"exe_{uuid.uuid4().hex[:8]}",
            "user_message": message,
            "history": history or [],
            "user_context": context or {},
            "loop_count": 0,
            "current_message": message,
            "current_history": history or [],
            "executed_actions": [],
            "orchestrator_errors": [],
            "requires_tool": False,
            "fatal_error": False
        }

        final_output = await app.ainvoke(initial_state)

        response = final_output.get("final_human_response") or final_output.get("final_orchestrator_result") or "Task completed."

        return {"response": response, "final_state": final_output}

except Exception:
    # Fallback implementation when langgraph is not installed. This runs the
    # planner/executor/formatter nodes sequentially until a formatter result is
    # produced or a fatal error occurs.
    async def run_workflow(message: str, history: list = None, context: dict = None, execution_id: str = None):
        state: GraphState = {
            "execution_id": execution_id or f"exe_{uuid.uuid4().hex[:8]}",
            "user_message": message,
            "history": history or [],
            "user_context": context or {},
            "loop_count": 0,
            "current_message": message,
            "current_history": history or [],
            "executed_actions": [],
            "orchestrator_errors": [],
            "requires_tool": False,
            "fatal_error": False
        }

        MAX_LOOPS = 12
        try:
            while True:
                # Planner step
                planner_updates: Dict[str, Any] = await plan_next_step(state)
                # Merge updates into state
                state.update(planner_updates or {})
                state["loop_count"] = state.get("loop_count", 0) + 1

                if state.get("fatal_error"):
                    break

                if state.get("requires_tool"):
                    # Executor step
                    exec_updates: Dict[str, Any] = await execute_tool_node(state)
                    # Merge executor outputs
                    # Append executed actions if present
                    if exec_updates.get("executed_actions"):
                        state.setdefault("executed_actions", [])
                        state["executed_actions"] = exec_updates.get("executed_actions")
                    # Merge other fields
                    for k, v in exec_updates.items():
                        if k != "executed_actions":
                            state[k] = v

                    # Safety: prevent infinite loops
                    if state.get("loop_count", 0) > MAX_LOOPS:
                        state["fatal_error"] = True
                        state.setdefault("orchestrator_errors", []).append("Max LangGraph fallback loops exceeded")
                        break
                    # Continue loop to planner
                    continue

                # If no tool required, finalize
                formatter_result = await finalize_response(state)
                final_text = formatter_result.get("final_human_response")
                return {"response": final_text, "final_state": state}

        except Exception as e:
            state.setdefault("orchestrator_errors", []).append(str(e))
            # Try to produce a formatter message with the error
            try:
                formatter_result = await finalize_response(state)
                final_text = formatter_result.get("final_human_response")
            except Exception:
                final_text = f"Internal LangGraph fallback failure: {str(e)}"
            return {"response": final_text, "final_state": state}
