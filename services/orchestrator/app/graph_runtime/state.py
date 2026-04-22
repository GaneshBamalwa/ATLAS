from typing import TypedDict, List, Dict, Any, Optional
from app.schemas import ToolCall

class GraphState(TypedDict, total=False):
    execution_id: str
    user_message: str
    history: List[Dict[str, str]]
    user_context: Dict[str, Any]
    
    # Internal router state
    loop_count: int
    system_intent: str
    current_message: str
    current_history: List[Dict[str, str]]
    
    # Routing decision
    requires_tool: bool
    current_tool_call: Optional[ToolCall]
    final_orchestrator_result: Optional[str]
    fatal_error: bool
    
    # Accumulators for Formatter
    executed_actions: List[Dict[str, Any]]
    orchestrator_errors: List[str]
    
    # Final Output
    final_human_response: Optional[str]
