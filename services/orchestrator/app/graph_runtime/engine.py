import uuid
from langgraph.graph import StateGraph, END
from app.graph_runtime.state import GraphState
from app.graph_runtime.nodes.planner_node import plan_next_step
from app.graph_runtime.nodes.executor_node import execute_tool_node
from app.graph_runtime.nodes.formatter_node import finalize_response

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
    Main entry point for running the LangGraph orchestration.
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
    
    # Determine the final human response
    # The formatter node should put it in final_human_response or final_orchestrator_result
    response = final_output.get("final_human_response") or final_output.get("final_orchestrator_result") or "Task completed."
    
    return {
        "response": response,
        "final_state": final_output
    }
