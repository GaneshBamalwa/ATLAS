"""
services/orchestrator/tools/schemas.py - Modular tool layer schemas
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class ToolCall(BaseModel):
    """Represents a request to execute a single MCP tool"""
    tool: str = Field(..., description="Name of the MCP tool to invoke")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Arguments to pass to the tool")


class ToolResponse(BaseModel):
    """Encapsulates the status and data returned by a tool execution"""
    tool: str
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
