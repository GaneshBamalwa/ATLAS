"""
schemas.py - Pydantic models for all request/response types.
"""

from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, model_validator
from datetime import datetime, timezone


# ─── Inbound ──────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: Optional[str] = Field(None, min_length=1, max_length=4000, description="User's natural language query")
    query: Optional[str] = Field(None, min_length=1, max_length=4000, description="Alias for message")
    history: List[Dict[str, str]] = Field(default_factory=list, description="Previous conversation rounds")
    user_id: Optional[str] = Field(None, description="Legacy session user ID")
    gmail_user_id: Optional[str] = Field(None, description="Individual Gmail account ID")
    drive_user_id: Optional[str] = Field(None, description="Individual Drive account ID")
    calendar_user_id: Optional[str] = Field(None, description="Individual Calendar account ID")
    session_id: Optional[str] = Field(None, description="Optional session identifier for tracing")
    engine: Optional[str] = Field("standard", description="Orchestration engine (standard or langgraph)")

    @model_validator(mode="before")
    @classmethod
    def normalize_query(cls, values):
        if isinstance(values, dict):
            message = values.get("message")
            query = values.get("query")
            if not message and query:
                values["message"] = query
        return values


# ─── Tool Layer ───────────────────────────────────────────────────────────────

class ToolCall(BaseModel):
    tool: str = Field(..., description="Name of the MCP tool to invoke")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Arguments to pass to the tool")


class ToolResponse(BaseModel):
    tool: str
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0


# ─── Execution Trace ─────────────────────────────────────────────────────────

class TraceStep(BaseModel):
    id: str
    title: str
    description: str
    status: Literal["pending", "running", "completed", "success", "failed", "error"] = "pending"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    details: Optional[str] = None


class ExecutionTrace(BaseModel):
    steps: List[TraceStep] = Field(default_factory=list)
    total_time_ms: float = 0.0
    status: Literal["running", "success", "completed", "error", "failed", "partial"] = "running"


# ─── Outbound ─────────────────────────────────────────────────────────────────

class DAGNodeMetadata(BaseModel):
    created_by: str = "planner"
    estimated_cost: float = 0.0
    priority: int = 1

class DAGNode(BaseModel):
    id: str
    label: str
    tool: str
    input: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    metadata: DAGNodeMetadata = Field(default_factory=DAGNodeMetadata)

class DAGNodeResult(BaseModel):
    node_id: str
    label: str
    tool: str
    status: str
    start_time: float
    end_time: float
    duration_ms: float
    input: Dict[str, Any] = Field(default_factory=dict)
    output: Any = None
    error: Optional[str] = None

class ExecutionGraph(BaseModel):
    nodes: List[DAGNode] = Field(default_factory=list)
    edges: List[List[str]] = Field(default_factory=list)
    node_results: List[DAGNodeResult] = Field(default_factory=list)

class PipelineNode(BaseModel):
    id: str
    label: str
    status: str  # "success", "error", "pending"
    duration: float = 0.0
    error: Optional[str] = None

class PipelineEdge(BaseModel):
    source: str
    target: str
    type: str = "sequence"

class PipelineData(BaseModel):
    nodes: List[PipelineNode] = Field(default_factory=list)
    edges: List[PipelineEdge] = Field(default_factory=list)
    execution_time_ms: float = 0.0

class ChatResponse(BaseModel):
    response: str = Field(..., description="Human-readable response text")
    tool_used: Optional[str] = None
    tool_result: Optional[Any] = None
    response_type: Literal["text", "success", "tool_result", "error", "failed"] = "text"
    trace: ExecutionTrace = Field(default_factory=ExecutionTrace)
    session_id: Optional[str] = None
    mode: str = "legacy"
    execution_graph: Optional[ExecutionGraph] = None
    pipeline: Optional[PipelineData] = None


# ─── Router internal ─────────────────────────────────────────────────────────

class RouterDecision(BaseModel):
    """LLM routing decision — either a tool call or a direct text response."""
    requires_tool: bool
    tool_call: Optional[ToolCall] = None
    response: Optional[str] = None
