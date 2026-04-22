import logging
import base64
import concurrent.futures
from tenacity import retry, stop_after_attempt, wait_exponential
from backend.gmail_auth import get_gmail_service, get_drive_service, get_calendar_service
from googleapiclient.http import MediaFileUpload
from backend.utils import decode_base64_url, create_raw_email, save_attachment
from backend.llm_chains import (
    summarize_email, 
    generate_search_query, 
    generate_subject_line,
    enrich_email,
    batch_summarize_emails,
    suggest_alternate_slots
)
import datetime as dt
from datetime import datetime
from backend.config import settings
import functools

logger = logging.getLogger(__name__)

def formatted_error(msg: str, err_type: str = "InternalError", retryable: bool = False):
    return {"error": {"message": msg, "type": err_type, "retryable": retryable}}

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def resilient_gmail_call(func, *args, **kwargs):
    return func(*args, **kwargs)

def list_unread_emails_tool(user_id: str, max_results: int = 10):
    try:
        service = get_gmail_service(user_id)
        request = service.users().messages().list(userId='me', labelIds=['UNREAD', 'INBOX'], maxResults=max_results)
        results = resilient_gmail_call(request.execute)
        messages = results.get('messages', [])
        
        if not messages:
            return {"status": "success", "count": 0, "unread_inbox_list": []}
            
        # 1. Fetch raw details for all messages in parallel (Batch metadata/body fetch)
        raw_emails = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=settings.MAX_WORKERS) as executor:
            # We call read_email_tool with metadata_only=True for lightning fast list views
            futures = [executor.submit(read_email_tool, user_id, m['id'], summarize=False, service=service, skip_subject_gen=True, bypass_intelligence=True, metadata_only=True) for m in messages]
            for future in concurrent.futures.as_completed(futures):
                try:
                    res = future.result()
                    # Even if there's an error dict return, we extract at least what we can
                    if isinstance(res, dict) and "error" in res:
                        # Fallback for individual error: at least show the ID if we can't fetch detail
                        raw_emails.append({"id": "Unknown", "subject": "Error loading detail", "from": "Unknown"})
                    else:
                        raw_emails.append(res)
                except Exception as e:
                    logger.error(f"Failed to fetch raw email: {e}")

        # 2. Batch process intelligence (optional phase)
        intelligence_map = {}
        if settings.ENABLE_EMAIL_INTELLIGENCE and raw_emails:
            try:
                intelligence_map = batch_summarize_emails(raw_emails)
            except Exception as e:
                logger.warning(f"Batch AI intelligence failed: {e}")

        # 3. Final re-assembly
        full_emails = []
        for i, email in enumerate(raw_emails):
            # Sort emails into a list we can return
            intel = intelligence_map.get(f"email_{i}", {})
            
            # Use original keys for backward compatibility + new fields for enhancement
            mailbox_entry = {
                "id": email.get("id"),
                "subject": email.get("subject", "No Subject"),
                "from": email.get("from"),
                "summary": intel.get("summary", ""),
                "classification": intel.get("classification", ""),
                "intent": intel.get("intent", ""),
                
                # Keep these for high-visibility if needed, but primary keys are above
                "MAIL_SUBJECT": email.get("subject", "No Subject"),
                "MESSAGE_ID": email.get("id")
            }
            full_emails.append(mailbox_entry)
                    
        return {
            "status": "success",
            "count": len(full_emails),
            "emails": full_emails, # Keep original key name
            "unread_inbox_list": full_emails # New key name
        }
    except Exception as e:
        logger.error(f"Error listing unread emails: {e}")
        return formatted_error(str(e), "GmailAPIError", True)

@functools.lru_cache(maxsize=100)
def _cached_read_email(user_id: str, message_id: str, summarize: bool, include_thread: bool = False, service=None, generate_missing_subject: bool = True, bypass_intelligence: bool = False, metadata_only: bool = False):
    if not service:
        service = get_gmail_service(user_id)
        
    # Metadata-only fetch for performance
    fmt = 'metadata' if metadata_only else 'full'
    request = service.users().messages().get(userId='me', id=message_id, format=fmt)
    msg = resilient_gmail_call(request.execute)
    
    payload = msg.get('payload', {})
    headers = payload.get('headers', [])
    thread_id = msg.get('threadId')
    
    raw_subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '').strip()
    sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown Sender')
    
    def get_body(payload_part):
        if payload_part.get('mimeType') == 'text/plain':
            return decode_base64_url(payload_part.get('body', {}).get('data', ''))
        if 'parts' in payload_part:
            for part in payload_part['parts']:
                body_text = get_body(part)
                if body_text: return body_text
        if payload_part.get('mimeType') == 'text/html':
            return decode_base64_url(payload_part.get('body', {}).get('data', ''))
        return ""

    body = get_body(payload)
    
    # Subject Augmentation - DISABLE AI GENERATION DURING BATCH LISTING
    subject = raw_subject
    if not subject or subject.lower() == "no subject":
        if generate_missing_subject and body:
            subject = generate_subject_line(body)
        else:
            subject = "No Subject"

    result = {"id": message_id, "subject": subject, "from": sender, "body": body}
    
    if summarize and body and not bypass_intelligence:
        result['summary'] = summarize_email(body)
        
    if settings.ENABLE_EMAIL_INTELLIGENCE and body and not bypass_intelligence:
        # Fallback to single enrichment if batching isn't used
        enrichment = enrich_email(body, subject, sender)
        result.update(enrichment)
        
    if include_thread and thread_id:
        try:
            thread_req = service.users().threads().get(userId='me', id=thread_id)
            thread_data = resilient_gmail_call(thread_req.execute)
            thread_msgs = thread_data.get('messages', [])
            result['thread'] = {
                "id": thread_id,
                "message_count": len(thread_msgs),
                "summary": "Thread contains " + str(len(thread_msgs)) + " messages."
            }
        except Exception:
            pass
            
    return result

def read_email_tool(user_id: str, message_id: str, summarize: bool = False, include_thread: bool = False, service=None, skip_subject_gen: bool = False, bypass_intelligence: bool = False, metadata_only: bool = False):
    try:
        # Pass metadata_only down the chain
        return _cached_read_email(user_id, message_id, summarize, include_thread, service, not skip_subject_gen, bypass_intelligence, metadata_only)
    except Exception as e:
        logger.error(f"Error reading email: {e}")
        return formatted_error(str(e), "GmailAPIError", True)

def send_email_tool(user_id: str, to: str, subject: str, body: str):
    try:
        service = get_gmail_service(user_id)
        raw_msg = create_raw_email("me", to, subject, body)
        request = service.users().messages().send(userId='me', body=raw_msg)
        sent_message = resilient_gmail_call(request.execute)
        return {"status": "success", "messageId": sent_message['id']}
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return formatted_error(str(e), "SendError", False)

def download_attachments_tool(user_id: str, message_id: str):
    try:
        service = get_gmail_service(user_id)
        request = service.users().messages().get(userId='me', id=message_id)
        msg = resilient_gmail_call(request.execute)
        parts = msg.get('payload', {}).get('parts', [])
        
        downloaded = []
        for part in parts:
            if part.get('filename') and part.get('body', {}).get('attachmentId'):
                att_id = part['body']['attachmentId']
                att_req = service.users().messages().attachments().get(userId='me', messageId=message_id, id=att_id)
                attachment = resilient_gmail_call(att_req.execute)
                data = base64.urlsafe_b64decode(attachment['data'])
                filepath = save_attachment(part['filename'], data)
                
                # Attachment metadata enrichment
                size_kb = len(data) / 1024
                downloaded.append({
                    "filepath": filepath,
                    "filename": part['filename'],
                    "type": part.get('mimeType', 'unknown'),
                    "size_kb": round(size_kb, 2)
                })
                
        return {"downloaded_files": downloaded}
    except Exception as e:
        logger.error(f"Error downloading attachments: {e}")
        return formatted_error(str(e), "AttachmentError", True)

def search_emails_tool(user_id: str, query: str):
    try:
        service = get_gmail_service(user_id)
        gmail_query = generate_search_query(query) if settings.ENABLE_SEMANTIC_SEARCH else query
        request = service.users().messages().list(userId='me', q=gmail_query, maxResults=10)
        results = resilient_gmail_call(request.execute)
        messages = results.get('messages', [])
        
        full_emails = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=settings.MAX_WORKERS) as executor:
            future_to_msg = {executor.submit(read_email_tool, user_id, m['id'], summarize=True): m for m in messages}
            for future in concurrent.futures.as_completed(future_to_msg):
                m = future_to_msg[future]
                try:
                    full_email = future.result()
                    if "error" not in full_email:
                        full_emails.append(full_email)
                    else:
                        full_emails.append(m)
                except Exception:
                    full_emails.append(m)
                
        return {"query_used": gmail_query, "emails": full_emails}
    except Exception as e:
        logger.error(f"Error searching emails: {e}")
        return formatted_error(str(e), "SearchError", True)

def get_labels_tool(user_id: str):
    try:
        service = get_gmail_service(user_id)
        request = service.users().labels().list(userId='me')
        results = resilient_gmail_call(request.execute)
        return {"labels": results.get('labels', [])}
    except Exception as e:
        logger.error(f"Error getting labels: {e}")
        return formatted_error(str(e), "GmailAPIError", True)

def get_threads_tool(user_id: str, limit: int = 10):
    try:
        service = get_gmail_service(user_id)
        request = service.users().threads().list(userId='me', maxResults=limit)
        results = resilient_gmail_call(request.execute)
        return {"threads": results.get('threads', [])}
    except Exception as e:
        logger.error(f"Error getting threads: {e}")
        return formatted_error(str(e), "GmailAPIError", True)

def get_user_profile_tool(user_id: str):
    try:
        service = get_gmail_service(user_id)
        request = service.users().getProfile(userId='me')
        profile = resilient_gmail_call(request.execute)
        return profile
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        return formatted_error(str(e), "GmailAPIError", True)


# --------------------------------------------------
# GOOGLE DRIVE TOOLS
# --------------------------------------------------

def search_drive_tool(user_id: str, query: str, limit: int = 5):
    """Search Google Drive using a name or content query."""
    try:
        service = get_drive_service(user_id)
        # We'll use a simple name contains query for robust matching
        drive_query = f"name contains '{query}' and trashed = false"
        results = resilient_gmail_call(
            service.files().list(
                q=drive_query,
                pageSize=limit,
                fields="files(id, name, mimeType, webViewLink)"
            ).execute
        )
        return {
            "status": "success",
            "query": drive_query,
            "files": results.get("files", [])
        }
    except Exception as e:
        logger.error(f"Error searching drive: {e}")
        return formatted_error(str(e), "DriveAPIError", True)

def read_drive_file_tool(user_id: str, file_id: str):
    """Read file content (text/docs/exports) from Google Drive."""
    try:
        service = get_drive_service(user_id)
        file_meta = service.files().get(fileId=file_id, fields="name, mimeType").execute()
        
        mime_type = file_meta.get("mimeType", "")
        if "google-apps.document" in mime_type:
            # Export Google Docs as plain text
            raw = service.files().export(fileId=file_id, mimeType="text/plain").execute()
        else:
            # Direct media download
            raw = service.files().get_media(fileId=file_id).execute()

        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError:
            # Fallback for binary: base64
            content = base64.b64encode(raw).decode("utf-8")

        return {
            "status": "success",
            "file_name": file_meta["name"],
            "mime_type": mime_type,
            "content": content
        }
    except Exception as e:
        logger.error(f"Error reading drive file: {e}")
        return formatted_error(str(e), "DriveAPIError", True)

def upload_drive_file_tool(user_id: str, file_path: str, file_name: str, mime_type: str = "application/octet-stream"):
    """Upload a local file to Google Drive."""
    try:
        service = get_drive_service(user_id)
        media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
        file = service.files().create(
            body={"name": file_name},
            media_body=media,
            fields="id"
        ).execute()
        return {"status": "success", "file_id": file["id"]}
    except Exception as e:
        logger.error(f"Error uploading to drive: {e}")
        return formatted_error(str(e), "DriveAPIError", False)

def move_drive_file_to_trash_tool(user_id: str, file_id: str):
    """Trash a file in Google Drive."""
    try:
        service = get_drive_service(user_id)
        service.files().update(fileId=file_id, body={"trashed": True}).execute()
        return {"status": "success", "file_id": file_id, "action": "trashed"}
    except Exception as e:
        logger.error(f"Error trashing drive file: {e}")
        return formatted_error(str(e), "DriveAPIError", True)

def get_drive_share_link_tool(user_id: str, file_id: str, make_public: bool = False):
    """Retrieve the shareable web link for a Google Drive file, optionally making it public."""
    try:
        service = get_drive_service(user_id)
        
        if make_public:
            # Set permission to anyone with the link can view
            service.permissions().create(
                fileId=file_id,
                body={'type': 'anyone', 'role': 'reader'}
            ).execute()
        
        # Fetch the webViewLink
        file_meta = service.files().get(
            fileId=file_id,
            fields="name, webViewLink, permissions"
        ).execute()
        
        return {
            "status": "success",
            "file_name": file_meta.get("name"),
            "share_link": file_meta.get("webViewLink"),
            "is_public": any(p.get('type') == 'anyone' for p in file_meta.get('permissions', []))
        }
    except Exception as e:
        logger.error(f"Error getting share link for file {file_id}: {e}")
        return formatted_error(
            f"Failed to get share link for '{file_id}'. Error: {str(e)}. "
            "IMPORTANT: If you used a filename as file_id, please call search_drive first and use the 'id' field from the results.",
            "DriveAPIError",
            True
        )

# --------------------------------------------------
# GOOGLE CALENDAR TOOLS
# --------------------------------------------------

def list_calendar_events_tool(user_id: str, date_str: str = None, days_ahead: int = 1):
    """List Google Calendar events for a specific date or upcoming period."""
    try:
        service = get_calendar_service(user_id)
        
        # Use provided date or default to today
        if date_str:
            start_dt = datetime.fromisoformat(date_str).replace(hour=0, minute=0, second=0)
        else:
            start_dt = datetime.now().replace(hour=0, minute=0, second=0)
            
        end_dt = start_dt + dt.timedelta(days=days_ahead)
        
        # IST offset handling correctly
        time_min = start_dt.isoformat() + "Z" if "Z" in start_dt.isoformat() else start_dt.isoformat() + "+05:30"
        time_max = end_dt.isoformat() + "Z" if "Z" in end_dt.isoformat() else end_dt.isoformat() + "+05:30"

        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime',
            timeZone='Asia/Kolkata'
        ).execute()

        events = events_result.get('items', [])
        summaries = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            summaries.append({
                "id": event.get('id'),
                "summary": event.get('summary', 'No Title'),
                "start": start,
                "end": end,
                "description": event.get('description', ''),
                "location": event.get('location', '')
            })

        return {"status": "success", "count": len(summaries), "events": summaries}
    except Exception as e:
        logger.error(f"Error listing calendar events: {e}")
        return formatted_error(str(e), "CalendarAPIError", True)

def add_calendar_event_tool(user_id: str, summary: str, date: str, start_time: str, duration_minutes: int = 60, description: str = ""):
    """Add a new event to Google Calendar with conflict detection."""
    try:
        service = get_calendar_service(user_id)
        
        # Parse start and end times
        start_dt = datetime.fromisoformat(f"{date}T{start_time}")
        end_dt = start_dt + dt.timedelta(minutes=duration_minutes)
        
        time_min = start_dt.isoformat() + "+05:30"
        time_max = end_dt.isoformat() + "+05:30"

        # Check for conflicts
        conflicts_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            timeZone='Asia/Kolkata'
        ).execute()
        
        conflicts = conflicts_result.get('items', [])
        
        if conflicts:
            conflict_data = []
            for c in conflicts:
                conflict_data.append({
                    "summary": c.get("summary", "Unknown"),
                    "start": c['start'].get('dateTime')
                })
            
            suggestions = suggest_alternate_slots(summary, conflict_data)
            
            return {
                "status": "conflict",
                "message": f"This '{summary}' event conflicts with existing appointments.",
                "conflicts": conflict_data,
                "ai_suggestions": suggestions
            }

        # Create event
        event_body = {
            'summary': summary,
            'description': description,
            'start': {'dateTime': start_dt.isoformat(), 'timeZone': 'Asia/Kolkata'},
            'end': {'dateTime': end_dt.isoformat(), 'timeZone': 'Asia/Kolkata'}
        }

        created = service.events().insert(calendarId='primary', body=event_body).execute()
        return {"status": "created", "event_id": created.get('id'), "link": created.get('htmlLink')}
        
    except Exception as e:
        logger.error(f"Error adding calendar event: {e}")
        return formatted_error(str(e), "CalendarAPIError", True)

def delete_calendar_event_tool(user_id: str, event_id: str):
    """Delete a specific Google Calendar event by its ID."""
    try:
        service = get_calendar_service(user_id)
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        return {"status": "success", "event_id": event_id, "action": "deleted"}
    except Exception as e:
        logger.error(f"Error deleting calendar event: {e}")
        return formatted_error(str(e), "CalendarAPIError", True)
