from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel


class ToolName(str, Enum):
    SEARCH_DRIVE = "search_drive"
    READ_DRIVE_FILE = "read_drive_file"
    TRASH_DRIVE_FILE = "trash_drive_file"
    GET_DRIVE_SHARE_LINK = "get_drive_share_link"
    LIST_UNREAD_EMAILS = "list_unread_emails"
    READ_EMAIL = "read_email"
    SEND_EMAIL = "send_email"
    SEARCH_EMAILS = "search_emails"
    GET_LABELS = "get_labels"
    GET_THREADS = "get_threads"
    GET_PROFILE = "get_profile"
    LIST_CALENDAR_EVENTS = "list_calendar_events"
    ADD_CALENDAR_EVENT = "add_calendar_event"
    DELETE_CALENDAR_EVENT = "delete_calendar_event"


class ToolCall(BaseModel):
    name: str
    params: Dict[str, Any] = {}


class OrchestratorRequest(BaseModel):
    tools: List[ToolCall] = []
    reasoning: str = ""


TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "list_unread_emails": {"description": "List unread emails from Gmail", "params": ["limit"]},
    "read_email": {"description": "Read a Gmail message by message_id", "params": ["message_id", "summarize"]},
    "send_email": {"description": "Send email via Gmail", "params": ["to", "subject", "body"]},
    "search_emails": {"description": "Search Gmail emails", "params": ["query"]},
    "get_labels": {"description": "Get Gmail labels", "params": []},
    "get_threads": {"description": "Get recent Gmail threads", "params": ["limit"]},
    "get_profile": {"description": "Get Gmail profile", "params": []},
    "search_drive": {"description": "Search for files in Google Drive", "params": ["query", "limit"]},
    "read_drive_file": {"description": "Read file content from Google Drive", "params": ["file_id"]},
    "trash_drive_file": {"description": "Move a Drive file to trash", "params": ["file_id"]},
    "get_drive_share_link": {"description": "Get a shareable Drive link", "params": ["file_id", "make_public"]},
    "list_calendar_events": {"description": "List calendar events", "params": ["date", "days"]},
    "add_calendar_event": {"description": "Create a calendar event", "params": ["summary", "date", "start_time", "duration", "description"]},
    "delete_calendar_event": {"description": "Delete a calendar event", "params": ["event_id"]},
}
