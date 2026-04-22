"""
executor.py - MCP Tool Execution Engine.

Receives a ToolCall decision from the router and:
1. Looks up the tool definition in the registry.
2. Builds the correct HTTP request (GET params / POST body / path params).
3. Calls the MCP backend via httpx with retry + timeout.
4. Returns a structured ToolResponse.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from app.config import get_settings
from app.schemas import ToolCall, ToolResponse
from app.tool_registry import registry, ToolDefinition
from app.utils.logger import logger, log_execution_time

import logging

settings = get_settings()


def _build_url(tool_def: ToolDefinition, arguments: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
    """
    Build the final URL and leftover arguments (for query params / body).
    Handles path-param substitution e.g. /emails/{message_id}.
    """
    endpoint = tool_def.endpoint
    remaining_args = dict(arguments)

    if tool_def.path_param and tool_def.path_param in remaining_args:
        path_value = remaining_args.pop(tool_def.path_param)
        endpoint = endpoint.replace(f"{{{tool_def.path_param}}}", str(path_value))

    url = f"{settings.gmail_api_base}{endpoint}"
    return url, remaining_args


def _make_headers(user_id: Optional[str]) -> Dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if user_id:
        headers["X-User-Id"] = user_id
    return headers


@retry(
    stop=stop_after_attempt(settings.max_retries),
    wait=wait_exponential(multiplier=settings.retry_backoff, min=1, max=10),
    retry=retry_if_exception_type(httpx.ConnectError),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
async def _http_call(
    method: str,
    url: str,
    params: Optional[Dict] = None,
    json_body: Optional[Dict] = None,
    headers: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Async HTTP call with retry on network errors."""
    async with httpx.AsyncClient(timeout=settings.mcp_call_timeout) as client:
        resp = await client.request(
            method=method,
            url=url,
            params=params,
            json=json_body,
            headers=headers,
        )
        resp.raise_for_status()
        return resp.json()


@log_execution_time
async def execute_tool(tool_call: ToolCall, gmail_user_id: Optional[str] = None, drive_user_id: Optional[str] = None, calendar_user_id: Optional[str] = None) -> ToolResponse:
    """
    Execute an MCP tool call.

    Args:
        tool_call:         The ToolCall from the router.
        gmail_user_id:     Gmail account ID.
        drive_user_id:     Drive account ID.
        calendar_user_id:  Calendar account ID.

    Returns:
        ToolResponse with success/failure and raw data.
    """
    tool_def = registry.get(tool_call.tool)
    if not tool_def:
        logger.error(f"[EXECUTOR] Unknown tool: {tool_call.tool}")
        return ToolResponse(
            tool=tool_call.tool,
            success=False,
            error=f"Tool '{tool_call.tool}' not found in registry.",
        )

    # Determine which user_id to use based on tags
    target_user_id = None
    if "gmail" in tool_def.tags:
        target_user_id = gmail_user_id
        service_name = "Gmail"
    elif "drive" in tool_def.tags:
        target_user_id = drive_user_id
        service_name = "Google Drive"
    elif "calendar" in tool_def.tags:
        target_user_id = calendar_user_id
        service_name = "Google Calendar"
    else:
        # Fallback to whatever we have
        target_user_id = gmail_user_id or drive_user_id or calendar_user_id
        service_name = "service"

    if tool_def.requires_user_id and not target_user_id:
        logger.warning(f"[EXECUTOR] Tool '{tool_call.tool}' requires {service_name} auth but none provided.")
        return ToolResponse(
            tool=tool_call.tool,
            success=False,
            error=f"This action requires {service_name} authentication. Please connect your account first via the {service_name} tab.",
        )

    url, remaining_args = _build_url(tool_def, tool_call.arguments)
    headers = _make_headers(target_user_id)
    method = tool_def.http_method.upper()

    logger.info(f"[EXECUTOR] Calling {method} {url} | args={remaining_args}")
    start = time.perf_counter()

    try:
        # Both GET and POST in this Gmail MCP implementation use query parameters
        # based on the error loc: ['query', 'to'] etc.
        data = await _http_call(method, url, params=remaining_args, headers=headers)

        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(f"[EXECUTOR] Tool '{tool_call.tool}' succeeded in {elapsed_ms:.1f}ms")

        return ToolResponse(
            tool=tool_call.tool,
            success=True,
            data=data,
            execution_time_ms=elapsed_ms,
        )

    except httpx.HTTPStatusError as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        status = e.response.status_code
        detail = ""
        try:
            detail = e.response.json().get("detail", str(e))
        except Exception:
            detail = str(e)

        logger.error(f"[EXECUTOR] HTTP {status} from MCP: {detail}")

        if status == 401:
            return ToolResponse(
                tool=tool_call.tool,
                success=False,
                error="Gmail session expired or not authenticated. Please reconnect via the Gmail tab.",
                execution_time_ms=elapsed_ms,
            )
        return ToolResponse(
            tool=tool_call.tool,
            success=False,
            error=f"MCP returned HTTP {status}: {detail}",
            execution_time_ms=elapsed_ms,
        )

    except httpx.TimeoutException:
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.error(f"[EXECUTOR] Timeout calling '{tool_call.tool}' after {elapsed_ms:.1f}ms")
        return ToolResponse(
            tool=tool_call.tool,
            success=False,
            error="The Gmail service timed out. Please try again.",
            execution_time_ms=elapsed_ms,
        )

    except Exception as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.exception(f"[EXECUTOR] Unexpected error for tool '{tool_call.tool}': {e}")
        return ToolResponse(
            tool=tool_call.tool,
            success=False,
            error=f"Unexpected error: {str(e)}",
            execution_time_ms=elapsed_ms,
        )


def format_tool_result_as_text(tool_response: ToolResponse) -> str:
    """Convert a ToolResponse into a human-readable summary for the chat."""
    if not tool_response.success:
        return f"⚠️ {tool_response.error}"

    data = tool_response.data
    tool = tool_response.tool

    if tool == "list_unread_emails":
        emails = data.get("emails", [])
        if not emails:
            return "✅ Your inbox is clear! No unread emails were found."
        count = len(emails)
        ids = "\n".join(f"  • **{e.get('subject', 'No Subject')}** (ID: `{e['id']}`)" for e in emails[:10])
        return f"📬 I found **{count}** unread email(s) for you:\n\n{ids}\n\n_Tip: Mention an ID or subject if you want me to read one._"

    if tool == "read_email":
        subject = data.get("subject", "No Subject")
        sender = data.get("from", "Unknown")
        body = data.get("body", "")[:600]
        summary = data.get("summary", "")
        result = f"### 📧 {subject}\n**From:** {sender}\n\n---\n"
        if summary:
            result += f"**AI Summary:**\n{summary}\n\n"
        if body:
            result += f"**Message Preview:**\n{body}..."
        return result

    if tool == "send_email":
        if data.get("status") == "success":
            return f"✅ Email sent successfully! Message ID: `{data.get('messageId', 'N/A')}`"
        return f"❌ Failed to send email: {data.get('error', 'Unknown error')}"

    if tool == "search_emails":
        emails = data.get("emails", [])
        query_used = data.get("query_used", "")
        if not emails:
            return f"🔍 No emails found matching the query: *\"{query_used}\"*"
        count = len(emails)
        ids = "\n".join(f"  • **{e.get('subject', 'No Subject')}** (from {e.get('from', 'Unknown')}) (ID: `{e['id']}`)" for e in emails[:10])
        return f"🔍 **Search Results** for *\"{query_used}\"*\nI found **{count}** matching results:\n\n{ids}"

    if tool == "get_labels":
        labels = data.get("labels", [])
        names = ", ".join(f"`{l['name']}`" for l in labels[:20])
        return f"🏷️ Gmail Labels: {names}"

    if tool == "get_threads":
        threads = data.get("threads", [])
        count = len(threads)
        ids = "\n".join(f"  • Thread ID: `{t['id']}`" for t in threads[:5])
        return f"💬 **Threads Found:**\nI recovered **{count}** recent conversation threads:\n\n{ids}"

    if tool == "get_profile":
        email = data.get("emailAddress", "Unknown")
        total = data.get("messagesTotal", "N/A")
        threads = data.get("threadsTotal", "N/A")
        return (
            f"👤 **Connection Status**\n"
            f"- **Account:** {email}\n"
            f"- **Total Messages:** {total:,}\n"
            f"- **Total Threads:** {threads:,}\n\n"
            f"You are successfully authenticated and ready to interact with your Gmail MCP tools."
        )

    if tool == "get_drive_share_link":
        link = data.get("share_link", "N/A")
        name = data.get("file_name", "the file")
        public = data.get("is_public", False)
        status = "🌎 Public" if public else "🔒 Private/Restricted"
        return f"🔗 **Share Link Generated**\n- **File:** {name}\n- **Link:** {link}\n- **Access:** {status}"

    if tool == "list_calendar_events":
        events = data.get("events", [])
        if not events:
            return "📅 Your schedule is clear! No events were found for the requested period."
        count = len(events)
        items = "\n".join(f"  • **{e['summary']}** ({e['start'].split('T')[1][:5] if 'T' in e['start'] else e['start']}) [ID: `{e['id'][:6]}...`]" for e in events[:10])
        return f"🗓️ **Calendar Schedule**\nI found **{count}** event(s):\n\n{items}"

    if tool == "add_calendar_event":
        status = data.get("status")
        if status == "created":
            return f"✅ **Event Created!**\n- **ID:** `{data.get('event_id')}`\n- [View in Google Calendar]({data.get('link')})"
        if status == "conflict":
            conflicts = "\n".join([f"- {c['summary']} at {c['start']}" for c in data.get("conflicts", [])])
            return f"⚠️ **Scheduling Conflict!**\nIt looks like you're busy:\n{conflicts}\n\n**Suggestions:**\n{data.get('ai_suggestions')}"
        return f"❌ Failed to add event: {data.get('error', 'Unknown error')}"

    if tool == "delete_calendar_event":
        return f"🗑️ **Event Deleted**\nSuccessfully removed event ID: `{data.get('event_id')}`"

    # Fallback
    import json
    return f"✅ Tool `{tool}` completed:\n```json\n{json.dumps(data, indent=2)[:800]}\n```"
