"""
shared/types.py - Standard Type Definitions & Pydantic Schemas
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

class UserProfile(BaseModel):
    """Authenticated user info"""
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None


class ExecutionContext(BaseModel):
    """Main execution session boundary context"""
    session_id: str = Field(default_factory=lambda: "default-session")
    gmail_user_id: Optional[str] = None
    drive_user_id: Optional[str] = None
    calendar_user_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ToolCall(BaseModel):
    """Tool invocation format"""
    tool: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    """Consolidated Tool response format"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
