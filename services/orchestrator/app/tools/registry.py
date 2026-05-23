"""
services/orchestrator/tools/registry.py - Master Tool Registry
Stores definitions of all Google Workspace and plugin-based tools.
"""

from __future__ import annotations
import os
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

@dataclass
class ToolDefinition:
    name: str
    description: str
    input_schema: Dict[str, Any]          # JSON-schema format
    endpoint: str                          # Backend relative path
    http_method: str = "GET"
    requires_user_id: bool = True          # True requires X-User-Id header mapping
    tags: List[str] = field(default_factory=list)
    path_param: Optional[str] = None       # Substitutes path variables e.g. /emails/{message_id}


# ─── Gmail MCP Tool Definitions ───────────────────────────────────────────────
GMAIL_TOOLS: List[ToolDefinition] = [
    ToolDefinition(
        name="list_unread_emails",
        description=(
            "List unread emails from the user's Gmail inbox. "
            "Use when the user asks to check, show, fetch, or list their emails or inbox. "
            "Returns a list of message IDs."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of emails to return (default 5)",
                    "default": 5,
                }
            },
            "required": [],
        },
        endpoint="/emails/unread",
        http_method="GET",
        tags=["gmail", "inbox", "read"],
    ),
    ToolDefinition(
        name="read_email",
        description=(
            "Read a specific email by its message ID. "
            "Use when the user wants to open, read, or summarize a specific email. "
            "Requires a message_id argument."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "message_id": {
                    "type": "string",
                    "description": "The Gmail message ID to read",
                },
                "summarize": {
                    "type": "boolean",
                    "description": "Whether to include an AI-generated summary",
                    "default": True,
                },
            },
            "required": ["message_id"],
        },
        endpoint="/emails/{message_id}",
        http_method="GET",
        path_param="message_id",
        tags=["gmail", "read"],
    ),
    ToolDefinition(
        name="send_email",
        description=(
            "Send an email via the user's Gmail account. "
            "IMPORTANT: If the user provides a general intent like 'Email John about the meeting', "
            "you MUST infer a professional 'subject' and draft a polite 'body' based on the context. "
            "If they give a specific topic, use it to generate the content. "
            "Requires 'to', 'subject', and 'body' arguments."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient email address"},
                "subject": {"type": "string", "description": "Professional subject line (infer from context if not given)"},
                "body": {"type": "string", "description": "Full email content (draft politely based on user intent if not provided verbatim)"},
            },
            "required": ["to", "subject", "body"],
        },
        endpoint="/emails/send",
        http_method="POST",
        tags=["gmail", "send", "compose"],
    ),
    ToolDefinition(
        name="search_emails",
        description=(
            "Search Gmail emails using natural language. "
            "Use when the user wants to find or search for specific emails, "
            "e.g. 'emails from John', 'emails about invoices last week'."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language search query",
                }
            },
            "required": ["query"],
        },
        endpoint="/search",
        http_method="GET",
        tags=["gmail", "search"],
    ),
    ToolDefinition(
        name="get_labels",
        description=(
            "Fetch all Gmail labels/folders for the user. "
            "Use when the user asks about their Gmail labels, folders, or categories."
        ),
        input_schema={"type": "object", "properties": {}, "required": []},
        endpoint="/labels",
        http_method="GET",
        tags=["gmail", "labels"],
    ),
    ToolDefinition(
        name="get_threads",
        description=(
            "Fetch recent Gmail email threads/conversations. "
            "Use when the user asks about threads, conversations, or recent activity."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of threads to return",
                    "default": 5,
                }
            },
            "required": [],
        },
        endpoint="/threads",
        http_method="GET",
        tags=["gmail", "threads"],
    ),
    ToolDefinition(
        name="get_profile",
        description=(
            "Get the authenticated user's Gmail profile (email address, message count). "
            "Use when the user asks who they are logged in as, or their account info."
        ),
        input_schema={"type": "object", "properties": {}, "required": []},
        endpoint="/profile",
        http_method="GET",
        tags=["gmail", "profile"],
    ),
]


# ─── Drive MCP Tool Definitions ───────────────────────────────────────────────
DRIVE_TOOLS: List[ToolDefinition] = [
    ToolDefinition(
        name="search_drive",
        description=(
            "Search for files or documents in Google Drive by name or keywords. "
            "Use when the user asks to 'find', 'fetch', 'get', or 'search' for a file, resume, doc, etc."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Filename or search keywords"},
                "limit": {"type": "integer", "description": "Max results (default 5)", "default": 5},
            },
            "required": ["query"],
        },
        endpoint="/drive/search",
        http_method="GET",
        tags=["drive", "search"],
    ),
    ToolDefinition(
        name="read_drive_file",
        description=(
            "Read the actual content of a specific Google Drive file. "
            "Use when the user wants to 'summarize', 'read', or 'mail' the content of a file found via search_drive."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "file_id": {"type": "string", "description": "The unique Drive file ID"},
            },
            "required": ["file_id"],
        },
        endpoint="/drive/files/{file_id}",
        http_method="GET",
        path_param="file_id",
        tags=["drive", "read"],
    ),
    ToolDefinition(
        name="trash_drive_file",
        description="Move a specific file to the Google Drive trash.",
        input_schema={
            "type": "object",
            "properties": {
                "file_id": {"type": "string", "description": "The Drive file ID to trash"},
            },
            "required": ["file_id"],
        },
        endpoint="/drive/files/{file_id}/trash",
        http_method="POST",
        path_param="file_id",
        tags=["drive", "delete", "trash"],
    ),
    ToolDefinition(
        name="get_drive_share_link",
        description=(
            "Get a shareable web link for a Google Drive file. "
            "Use when the user wants to share a file, get a link, or make a file public."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "file_id": {"type": "string", "description": "The Drive file ID to share"},
                "make_public": {
                    "type": "boolean", 
                    "description": "Whether to make the file accessible to anyone with the link (reader role)",
                    "default": False
                },
            },
            "required": ["file_id"],
        },
        endpoint="/drive/files/{file_id}/share",
        http_method="POST",
        path_param="file_id",
        tags=["drive", "share", "link"],
    ),
]


# ─── Calendar MCP Tool Definitions ────────────────────────────────────────────
CALENDAR_TOOLS: List[ToolDefinition] = [
    ToolDefinition(
        name="list_calendar_events",
        description=(
            "List events from the user's Google Calendar. "
            "Use when the user asks 'what's on my calendar', 'check my schedule', or 'show my events'. "
            "You can specify a 'date' (YYYY-MM-DD) or a number of 'days' to look ahead."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "Specific date to check (YYYY-MM-DD)"},
                "days": {"type": "integer", "description": "Number of days to check from the date (default 1)", "default": 1},
            },
            "required": [],
        },
        endpoint="/calendar/events",
        http_method="GET",
        tags=["calendar", "schedule", "events"],
    ),
    ToolDefinition(
        name="add_calendar_event",
        description=(
            "Add a new event to the user's Google Calendar. "
            "Requires 'summary', 'date' (YYYY-MM-DD), and 'start_time' (HH:MM). "
            "IMPORTANT: This tool automatically checks for conflicts and will return AI-suggested alternatives if they exist."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "Brief title of the event"},
                "date": {"type": "string", "description": "Date of the event (YYYY-MM-DD)"},
                "start_time": {"type": "string", "description": "Start time in 24h format (HH:MM)"},
                "duration": {"type": "integer", "description": "Duration in minutes (default 60)", "default": 60},
                "description": {"type": "string", "description": "Optional detailed description"},
            },
            "required": ["summary", "date", "start_time"],
        },
        endpoint="/calendar/events",
        http_method="POST",
        tags=["calendar", "schedule", "add"],
    ),
    ToolDefinition(
        name="delete_calendar_event",
        description="Delete a specific Google Calendar event by its ID.",
        input_schema={
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "description": "The unique event ID to delete"},
            },
            "required": ["event_id"],
        },
        endpoint="/calendar/events/{event_id}",
        http_method="DELETE",
        path_param="event_id",
        tags=["calendar", "delete"],
    ),
    ToolDefinition(
        name="clear_calendar_schedule",
        description=(
            "Delete all Google Calendar events for a specific date or clear the entire schedule for a day. "
            "Use this ONLY when the user explicitly asks to 'clear my schedule', 'cancel all meetings', or 'delete all events' for a given date. "
            "You can optionally provide a time range (e.g. 14:00 to 16:00) if the user asks to clear a specific block."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "Specific date to clear schedule for (YYYY-MM-DD)"},
                "start_time": {"type": "string", "description": "Optional start time in 24h format (HH:MM)"},
                "end_time": {"type": "string", "description": "Optional end time in 24h format (HH:MM)"},
            },
            "required": ["date"],
        },
        endpoint="/calendar/clear",
        http_method="POST",
        tags=["calendar", "clear", "delete", "schedule"],
    ),
]


class ToolRegistry:
    """Modulized Central Tool Registry. Decoupled and extensible."""

    def __init__(self) -> None:
        self._tools: Dict[str, ToolDefinition] = {}

    def register(self, tools: List[ToolDefinition]) -> None:
        for t in tools:
            self._tools[t.name] = t

    def get(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def all_tools(self) -> List[ToolDefinition]:
        return list(self._tools.values())

    def get_all_tools(self) -> List[ToolDefinition]:
        return self.all_tools()

    def register_plugin_tool(self, plugin_manifest: dict) -> None:
        """Register a single tool from a plugin manifest dict."""
        try:
            required_fields = ["name", "description", "input_schema", "endpoint"]
            missing = [f for f in required_fields if f not in plugin_manifest]
            if missing:
                logger.error(f"[TOOL REGISTRY] Plugin tool manifest lacks required fields: {missing}")
                return
                
            requires_user_id = plugin_manifest.get("requires_user_id", True)
            if "auth_type" in plugin_manifest and plugin_manifest["auth_type"] == "none":
                requires_user_id = False
                
            tool_def = ToolDefinition(
                name=plugin_manifest["name"],
                description=plugin_manifest["description"],
                input_schema=plugin_manifest["input_schema"],
                endpoint=plugin_manifest["endpoint"],
                http_method=plugin_manifest.get("http_method", "GET"),
                requires_user_id=requires_user_id,
                tags=plugin_manifest.get("tags", []),
                path_param=plugin_manifest.get("path_param")
            )
            
            if tool_def.name in self._tools:
                logger.warning(f"[TOOL REGISTRY] Duplicate tool name ignored: {tool_def.name}")
                return
                
            self._tools[tool_def.name] = tool_def
            logger.info(f"[TOOL REGISTRY] Registered plugin tool successfully: {tool_def.name}")
        except Exception as e:
            logger.error(f"[TOOL REGISTRY] Failed to register plugin tool: {e}")

    def load_plugins_from_directory(self, path: str) -> None:
        """Loads additional capabilities dynamically from plugins directory"""
        try:
            from app.plugins.loader import load_plugins_from_directory
            plugins = load_plugins_from_directory(path)
            for t in plugins:
                if t.name in self._tools:
                    continue
                # Wrap plugin in our standard dataclass
                self._tools[t.name] = ToolDefinition(
                    name=t.name,
                    description=t.description,
                    input_schema=t.input_schema,
                    endpoint=t.endpoint,
                    http_method=t.http_method,
                    requires_user_id=t.requires_user_id,
                    tags=t.tags,
                    path_param=t.path_param
                )
        except Exception as e:
            logger.debug(f"Plugins loader details: {e}")

    def tool_descriptions_for_prompt(self) -> str:
        """Helper to build text summaries of available capability endpoints for LLMs"""
        lines = []
        for t in self.get_all_tools():
            props = t.input_schema.get("properties", {})
            required = t.input_schema.get("required", [])
            args_desc = ", ".join(
                f"{k}{'*' if k in required else ''}: {v.get('description', '')}"
                for k, v in props.items()
            )
            lines.append(f"- {t.name}: {t.description}")
            if args_desc:
                lines.append(f"  Arguments: {args_desc}  (* = required)")
        return "\n".join(lines)


# Singleton instance initialization
registry = ToolRegistry()
registry.register(GMAIL_TOOLS)
registry.register(DRIVE_TOOLS)
registry.register(CALENDAR_TOOLS)

# Pre-load custom plugins on start
PLUGINS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugins")
if os.path.exists(PLUGINS_DIR):
    registry.load_plugins_from_directory(PLUGINS_DIR)
