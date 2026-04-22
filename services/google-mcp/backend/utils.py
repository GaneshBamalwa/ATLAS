import base64
import os
import logging

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

from email.mime.text import MIMEText

def create_raw_email(sender: str, to: str, subject: str, message_text: str) -> dict:
    """Create a raw email for sending using MIME standards."""
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
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
