"""
services/orchestrator/formatter.py - Provider-agnostic Response Formatter
Synthesizes structured tool results into elegant, polished markdown.
"""

import json
import logging
import re
from typing import Optional

from shared.config import global_config as settings
from app.utils.logger import log_execution_time
from app.llm.provider import LLMProvider, LLMFactory

logger = logging.getLogger(__name__)

GROQ_SYSTEM_PROMPT = """You are a professional AI response generator.

Your task is to synthesize a final human-readable response based on the structured data provided. The 'final_result' field contains the core answer from the reasoning engine.

RULES:
- Use 'final_result' as your primary source of truth.
- Use 'actions' strictly to fill in any missing specific details (e.g., exact names, IDs, or links) that 'final_result' may have omitted.
- Do NOT invent information. Do NOT hallucinate.
- NEVER mention tools, internal systems, JSON, or the reasoning engine.
- Produce a natural, polished, and direct response to the user.
- Use markdown formatting (bolding, lists) to make it highly readable.

Return ONLY the final response string. Do not include introductory filler.
"""


def _format_send_email_summary(orchestrator_output: dict) -> Optional[str]:
    """Format email send response as markdown."""
    actions = orchestrator_output.get("actions", []) or []
    email_action = next(
        (
            action
            for action in reversed(actions)
            if action.get("tool_name") == "send_email"
        ),
        None,
    )

    if not email_action:
        return None

    email_input = email_action.get("input", {}) or {}
    email_output = email_action.get("output", {}) or {}
    status = email_action.get("status")

    recipient = email_input.get("to", "Unknown recipient")
    subject = email_input.get("subject", "No subject")
    body = (email_input.get("body", "") or "").strip()

    if status == "success":
        message_id = email_output.get("messageId", "N/A")
        markdown_parts = [
            "# Email Sent Successfully",
            "",
            "The email was sent successfully with the details below:",
            "",
            f"**To:** {recipient}",
            f"**Subject:** {subject}",
            f"**Message ID:** `{message_id}`",
        ]
        if body:
            markdown_parts.append("")
            markdown_parts.append("## Body Preview")
            markdown_parts.append("")
            for line in body.split('\n'):
                markdown_parts.append(f"> {line}")
    else:
        error_msg = email_output.get("error", {}).get("message") if isinstance(email_output.get("error"), dict) else email_output.get("error")
        error_msg = error_msg or email_action.get("error") or "Unknown send error."
        markdown_parts = [
            "# ❌ Email Sending Failed",
            "",
            "The email could not be sent. Please review the details below:",
            "",
            f"**To:** {recipient}",
            f"**Subject:** {subject}",
            f"**Error Details:** `{error_msg}`",
        ]

    result = "\n".join(markdown_parts)
    return result


def _normalize_markdown_output(content: str) -> str:
    """Cleans up escaping artifacts, line endings, and lists spacing in markdown"""
    if not content:
        return ""

    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    normalized = normalized.replace("\\n", "\n")
    
    # Remove unnecessary markdown escaping
    normalized = normalized.replace(r"\\*", "*")
    normalized = normalized.replace(r"\*", "*")
    normalized = normalized.replace(r"\_", "_")
    normalized = normalized.replace(r"\-", "-")
    normalized = normalized.replace(r'\\"', '"')

    # Ensure common heading-to-content glue is split into paragraphs.
    normalized = re.sub(
        r"^(#{1,6}\s+[^\n]+?)\s+(?=(?:To\s+|Use\s+|Follow\s+|Example\b|\d+\.\s|[-*]\s))",
        r"\1\n\n",
        normalized,
        flags=re.MULTILINE,
    )

    # Start numbered/bulleted lists on a new line after sentence-like text.
    normalized = re.sub(r"([.:])\s+(?=(?:\d+\.\s|[-*]\s))", r"\1\n\n", normalized)

    # Keep one blank line between sections.
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    
    return normalized.strip()


@log_execution_time
async def format_response(orchestrator_output: dict, llm: Optional[LLMProvider] = None) -> str:
    """Passes the orchestrator's structured JSON output to LLM for natural language formatting."""
    send_email_summary = _format_send_email_summary(orchestrator_output)
    if send_email_summary:
        return send_email_summary

    # For pure no-tool answers, preserve and normalize the direct response.
    if not orchestrator_output.get("requires_tools") and orchestrator_output.get("final_result"):
        return _normalize_markdown_output(str(orchestrator_output.get("final_result", "")))

    if llm is None:
        # Load local Ollama or cloud Groq dynamically from unified configuration
        provider = settings.llm.formatting_provider
        if provider == "ollama":
            config = {
                "model": settings.llm.formatting_model,
                "base_url": settings.llm.formatting_base_url,
                "timeout": 60
            }
        else:
            config = {
                "model": settings.llm.routing_model,
                "api_key": settings.llm.routing_api_key or settings.llm_api_key,
                "timeout": 20
            }
        llm = LLMFactory.create(provider, config)

    prompt = f"{GROQ_SYSTEM_PROMPT}\n\nSTRUCTURED DATA:\n{json.dumps(orchestrator_output, indent=2)}\n\nFINAL RESPONSE:"

    try:
        content = await llm.generate(
            prompt=prompt,
            temperature=0.3,
            max_tokens=1000
        )
        return _normalize_markdown_output(content)
        
    except Exception as e:
        logger.error(f"[FORMATTER] Synthesis generation failed: {e}")
        return _normalize_markdown_output(
            str(orchestrator_output.get("final_result", "I completed the tasks but failed to format the response."))
        )
