"""
services/orchestrator/tools/executor.py - Modular tool execution engine
Coordinates client calls to local and cloud MCP service gateways.
"""

import time
import logging
from typing import Any, Dict, Optional

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from shared.config import global_config as settings
from .schemas import ToolCall, ToolResponse
from .registry import registry, ToolDefinition

logger = logging.getLogger(__name__)

RETRYABLE_HTTPX_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.ReadError,
    httpx.RemoteProtocolError,
)

def _build_url(tool_def: ToolDefinition, arguments: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
    """Builds full workspace tool URLs and replaces path parameters"""
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
    retry=retry_if_exception_type(RETRYABLE_HTTPX_EXCEPTIONS),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
async def _http_call(
    method: str,
    url: str,
    params: Optional[Dict] = None,
    json_body: Optional[Dict] = None,
    headers: Optional[Dict] = None,
    timeout: float = None,
) -> Dict[str, Any]:
    """Handles the async HTTP call with Tenacity connection retries"""
    call_timeout = timeout if timeout is not None else settings.mcp_call_timeout
    async with httpx.AsyncClient(timeout=call_timeout) as client:
        resp = await client.request(
            method=method,
            url=url,
            params=params,
            json=json_body,
            headers=headers,
        )
        resp.raise_for_status()
        return resp.json()


async def execute_tool(
    tool_call: ToolCall,
    gmail_user_id: Optional[str] = None,
    drive_user_id: Optional[str] = None,
    calendar_user_id: Optional[str] = None
) -> ToolResponse:
    """Dispatches a validated ToolCall schema against MCP endpoints"""
    tool_def = registry.get(tool_call.tool)
    if not tool_def:
        logger.error(f"[EXECUTOR] Unknown tool: {tool_call.tool}")
        return ToolResponse(
            tool=tool_call.tool,
            success=False,
            error=f"Tool '{tool_call.tool}' not found in registry.",
        )

    # Scopes matching for user identification headers
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
        target_user_id = gmail_user_id or drive_user_id or calendar_user_id
        service_name = "service"

    if tool_def.requires_user_id and not target_user_id:
        logger.warning(f"[EXECUTOR] Tool '{tool_call.tool}' requires {service_name} credentials.")
        return ToolResponse(
            tool=tool_call.tool,
            success=False,
            error=f"This action requires {service_name} authentication. Please connect your account first via the {service_name} tab.",
        )

    url, remaining_args = _build_url(tool_def, tool_call.arguments)
    headers = _make_headers(target_user_id)
    method = tool_def.http_method.upper()

    logger.info(f"[EXECUTOR] Dispatching {method} {url} with args {remaining_args}")
    start = time.perf_counter()

    try:
        # Optimized timeouts: email tasks are time-sensitive
        call_timeout = 15.0 if "email" in tool_call.tool.lower() or "send" in tool_call.tool.lower() else settings.mcp_call_timeout
        data = await _http_call(method, url, params=remaining_args, headers=headers, timeout=call_timeout)

        # Intercept embedded error blocks
        if isinstance(data, dict) and "error" in data:
            elapsed_ms = (time.perf_counter() - start) * 1000
            err_obj = data.get("error") or {}
            error_msg = err_obj.get("message") if isinstance(err_obj, dict) else str(err_obj)
            error_msg = error_msg or "Tool execution failed."

            lowered = error_msg.lower()
            if "not authenticated" in lowered or "status code 401" in lowered or "401" in lowered:
                error_msg = f"{service_name} is not authenticated. Please connect it first and then try again."

            logger.error(f"[EXECUTOR] Tool '{tool_call.tool}' failed: {error_msg}")
            return ToolResponse(
                tool=tool_call.tool,
                success=False,
                error=error_msg,
                data=data,
                execution_time_ms=elapsed_ms,
            )

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

        logger.error(f"[EXECUTOR] Gateway HTTP {status} from MCP: {detail}")
        if status == 401:
            return ToolResponse(
                tool=tool_call.tool,
                success=False,
                error="Gmail session expired. Please reconnect your account via Web Console.",
                execution_time_ms=elapsed_ms,
            )
        return ToolResponse(
            tool=tool_call.tool,
            success=False,
            error=f"MCP Gateway error status {status}: {detail}",
            execution_time_ms=elapsed_ms,
        )

    except httpx.TimeoutException:
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.error(f"[EXECUTOR] Timeout fetching '{tool_call.tool}' after {elapsed_ms:.1f}ms")
        return ToolResponse(
            tool=tool_call.tool,
            success=False,
            error="The requested workspace service timed out. Please retry.",
            execution_time_ms=elapsed_ms,
        )

    except httpx.ReadError as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.warning(f"[EXECUTOR] Read error fetching '{tool_call.tool}' after {elapsed_ms:.1f}ms: {e}")
        return ToolResponse(
            tool=tool_call.tool,
            success=False,
            error="The downstream service closed the connection while responding. Please retry.",
            execution_time_ms=elapsed_ms,
        )

    except httpx.RemoteProtocolError as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.warning(f"[EXECUTOR] Protocol error fetching '{tool_call.tool}' after {elapsed_ms:.1f}ms: {e}")
        return ToolResponse(
            tool=tool_call.tool,
            success=False,
            error="The downstream service interrupted the response. Please retry.",
            execution_time_ms=elapsed_ms,
        )

    except Exception as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.exception(f"[EXECUTOR] Unhandled execution error on tool '{tool_call.tool}': {e}")
        return ToolResponse(
            tool=tool_call.tool,
            success=False,
            error=f"Runtime error: {str(e)}",
            execution_time_ms=elapsed_ms,
        )


def format_tool_result_as_text(tool_response: ToolResponse) -> str:
    """Translates tool output JSON payloads into stylized Markdown summaries for client feeds"""
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
        if isinstance(data, dict) and data.get("error"):
            err = data.get("error")
            msg = err.get("message") if isinstance(err, dict) else str(err)
            if msg and ("not authenticated" in msg.lower() or "401" in msg.lower()):
                return "⚠️ Gmail is not authenticated. Please connect Gmail first, then resend the email."
            return f"❌ Failed to send email: {msg or 'Unknown error'}"
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

    if tool == "clear_calendar_schedule":
        del_count = data.get("deleted_count", 0)
        failed = data.get("failed_count", 0)
        if del_count == 0 and failed == 0:
            return "✅ **Schedule Cleared**\nNo events were found to delete for this date."
        msg = f"🗑️ **Schedule Cleared**\nSuccessfully removed {del_count} event(s)."
        if failed > 0:
            msg += f"\n⚠️ Failed to delete {failed} event(s)."
        return msg

    return f"✅ Tool `{tool}` completed:\n```json\n{json.dumps(data, indent=2)[:800]}\n```"
