import base64
import os
import logging
import html
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

# Base directory setup for downloads
DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "downloads")

def decode_base64_url(data: str) -> str:
    """Decode base64url encoded string safely."""
    if not data:
        return ""
    try:
        # data might already be padded or have a valid length
        padding = 4 - (len(data) % 4)
        if padding < 4:
            data += '=' * padding
        return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
    except Exception as e:
        logger.error(f"Error decoding base64url: {e}")
        return ""

def _normalize_email_body(message_text: str) -> str:
    """Normalize body text to preserve intended spacing and line breaks."""
    if not message_text:
        return ""

    normalized = message_text.replace("\r\n", "\n").replace("\r", "\n")

    # Handle tool payloads that include escaped line breaks/tabs as literal text.
    normalized = normalized.replace("\\n", "\n").replace("\\t", "\t")

    # Strip trailing spaces per line and collapse excessive blank lines.
    normalized = "\n".join(line.rstrip() for line in normalized.split("\n"))
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def _format_flat_email_body(message_text: str) -> str:
    """Turn a single-paragraph draft into a more readable email layout."""
    if not message_text:
        return ""

    if "\n" in message_text:
        return message_text

    text = re.sub(r"\s+", " ", message_text).strip()
    if not text:
        return ""

    signoff_match = re.search(
        r"\b(best regards|kind regards|regards|sincerely|thanks|thank you)\b[,:-]?",
        text,
        flags=re.IGNORECASE,
    )

    body_text = text
    signoff_text = ""
    if signoff_match:
        body_text = text[:signoff_match.start()].strip()
        signoff_text = text[signoff_match.start():].strip()

    paragraphs: list[str] = []

    greeting_match = re.match(r"^(dear|hello|hi)\b[^,]*,\s*(.+)$", body_text, flags=re.IGNORECASE)
    if greeting_match:
        greeting_end = body_text.find(",")
        if greeting_end != -1:
            greeting = body_text[: greeting_end + 1].strip()
            remainder = body_text[greeting_end + 1 :].strip()
            if greeting:
                paragraphs.append(greeting)
            body_text = remainder

    sentence_parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", body_text) if body_text else []
    sentence_parts = [part.strip() for part in sentence_parts if part.strip()]

    if sentence_parts:
        paragraphs.extend(sentence_parts)
    elif body_text:
        paragraphs.append(body_text)

    if signoff_text:
        signoff_line, _, signature_name = signoff_text.partition(",")
        signoff_line = signoff_line.strip()
        signature_name = signature_name.strip()

        if signature_name and signature_name.lower() in {"[your name]", "your name", "name", "[name]"}:
            signature_name = ""

        if paragraphs:
            paragraphs.append("")
        paragraphs.append(signoff_line)
        if signature_name:
            paragraphs.append(signature_name)

    formatted = "\n\n".join(part for part in paragraphs if part != "")
    return formatted.strip() if formatted else text


def _plain_to_minimal_html(message_text: str) -> str:
    """Render plain/markdown-like text into minimal safe HTML."""

    def apply_inline_markdown(value: str) -> str:
        escaped = html.escape(value)

        # Basic inline markdown support
        escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
        escaped = re.sub(r"\*(.+?)\*", r"<em>\1</em>", escaped)
        escaped = re.sub(r"`(.+?)`", r"<code>\1</code>", escaped)
        escaped = re.sub(
            r"\[(.+?)\]\((https?://[^\s)]+)\)",
            r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>',
            escaped,
        )
        return escaped

    lines = message_text.split("\n")
    rendered: list[str] = []
    paragraph_lines: list[str] = []
    in_ul = False
    in_ol = False

    def flush_paragraph() -> None:
        nonlocal paragraph_lines
        if paragraph_lines:
            rendered.append(f"<p>{'<br>'.join(paragraph_lines)}</p>")
            paragraph_lines = []

    def close_lists() -> None:
        nonlocal in_ul, in_ol
        if in_ul:
            rendered.append("</ul>")
            in_ul = False
        if in_ol:
            rendered.append("</ol>")
            in_ol = False

    for raw_line in lines:
        line = raw_line.strip()

        if not line:
            flush_paragraph()
            close_lists()
            continue

        heading_match = re.match(r"^(#{1,3})\s+(.+)$", line)
        if heading_match:
            flush_paragraph()
            close_lists()
            level = len(heading_match.group(1))
            content = apply_inline_markdown(heading_match.group(2))
            rendered.append(f"<h{level}>{content}</h{level}>")
            continue

        unordered_match = re.match(r"^[-*]\s+(.+)$", line)
        if unordered_match:
            flush_paragraph()
            if in_ol:
                rendered.append("</ol>")
                in_ol = False
            if not in_ul:
                rendered.append("<ul>")
                in_ul = True
            rendered.append(f"<li>{apply_inline_markdown(unordered_match.group(1))}</li>")
            continue

        ordered_match = re.match(r"^\d+\.\s+(.+)$", line)
        if ordered_match:
            flush_paragraph()
            if in_ul:
                rendered.append("</ul>")
                in_ul = False
            if not in_ol:
                rendered.append("<ol>")
                in_ol = True
            rendered.append(f"<li>{apply_inline_markdown(ordered_match.group(1))}</li>")
            continue

        close_lists()
        paragraph_lines.append(apply_inline_markdown(line))

    flush_paragraph()
    close_lists()

    return "\n".join(rendered) if rendered else "<p></p>"

def create_raw_email(sender: str, to: str, subject: str, message_text: str, sender_name: str | None = None) -> dict:
    """Create a raw email for sending using MIME standards."""
    normalized_body = _normalize_email_body(message_text)
    formatted_body = _format_flat_email_body(normalized_body)

    if sender_name:
        signature_markers = ["best regards", "kind regards", "regards", "sincerely", "thanks", "thank you"]
        body_lines = formatted_body.split("\n")
        for index, line in enumerate(body_lines):
            if line.strip().lower() in signature_markers:
                has_signature_name = index + 1 < len(body_lines) and body_lines[index + 1].strip()
                if not has_signature_name:
                    body_lines.insert(index + 1, sender_name)
                break
        formatted_body = "\n".join(body_lines)

    message = MIMEMultipart("alternative")
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject

    plain_part = MIMEText(formatted_body, "plain", "utf-8")
    html_part = MIMEText(_plain_to_minimal_html(formatted_body), "html", "utf-8")
    message.attach(plain_part)
    message.attach(html_part)

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    return {"raw": encoded_message}

def save_attachment(filename: str, data: bytes) -> str:
    """Save an attachment to the downloads folder."""
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
    
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(data)
    return filepath
