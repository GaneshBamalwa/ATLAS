from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class TraceNode(BaseModel):
    id: str
    name: str = "Unknown Node"
    type: str  # "llm_planner", "mcp_tool", "formatter", "condition"
    status: str  # "pending", "running", "success", "failed"
    inputs: Dict[str, Any]
    outputs: Optional[Dict[str, Any]] = None
    meta: Dict[str, Any] = Field(default_factory=dict)
    outputs: Optional[Dict[str, Any]] = None
    latency_ms: float = 0.0
    error: Optional[str] = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

class TraceEdge(BaseModel):
    source: str
    target: str
    condition: Optional[str] = None

class ExecutionTrace(BaseModel):
    execution_id: str
    status: str
    nodes: List[TraceNode] = []
    edges: List[TraceEdge] = []
    total_latency_ms: float = 0.0
