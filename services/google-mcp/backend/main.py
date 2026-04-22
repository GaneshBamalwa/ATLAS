import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from backend.mcp_tools import (
    list_unread_emails_tool,
    read_email_tool,
    send_email_tool,
    download_attachments_tool,
    search_emails_tool,
    get_labels_tool,
    get_threads_tool,
    get_user_profile_tool,
    search_drive_tool,
    read_drive_file_tool,
    upload_drive_file_tool,
    move_drive_file_to_trash_tool,
    get_drive_share_link_tool,
    list_calendar_events_tool,
    add_calendar_event_tool,
    delete_calendar_event_tool
)
from backend.gmail_auth import auth_router
from backend.llm_chains import draft_new_email

load_dotenv(override=True)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up Gmail MCP Backend with User Auth...")
    yield
    logger.info("Shutting down...")

app = FastAPI(title="Gmail MCP Server", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["auth"])

def get_current_user(x_user_id: str = Header(None)):
    logger.info(f"[BACKEND] Incoming request with X-User-Id: {x_user_id}")
    if not x_user_id:
        raise HTTPException(status_code=401, detail="X-User-Id header missing")
    return x_user_id

@app.get("/api/emails/unread")
def api_list_unread_emails(limit: int = 10, user_id: str = Depends(get_current_user)):
    return list_unread_emails_tool(user_id, max_results=limit)

@app.get("/api/emails/{message_id}")
def api_read_email(message_id: str, summarize: bool = False, user_id: str = Depends(get_current_user)):
    return read_email_tool(user_id, message_id, summarize=summarize)

@app.post("/api/emails/send")
def api_send_email(to: str, subject: str, body: str, user_id: str = Depends(get_current_user)):
    return send_email_tool(user_id, to, subject, body)

@app.post("/api/emails/draft")
def api_draft_email(topic: str, user_id: str = Depends(get_current_user)):
    return {"draft": draft_new_email(topic)}

@app.post("/api/emails/{message_id}/download-attachments")
def api_download_attachments(message_id: str, user_id: str = Depends(get_current_user)):
    return download_attachments_tool(user_id, message_id)

@app.get("/api/search")
def api_search_emails(query: str, user_id: str = Depends(get_current_user)):
    return search_emails_tool(user_id, query)

@app.get("/api/labels")
def api_get_labels(user_id: str = Depends(get_current_user)):
    return get_labels_tool(user_id)

@app.get("/api/threads")
def api_get_threads(limit: int = 10, user_id: str = Depends(get_current_user)):
    return get_threads_tool(user_id, limit)

@app.get("/api/profile")
def api_get_profile(user_id: str = Depends(get_current_user)):
    return get_user_profile_tool(user_id)

@app.get("/api/drive/search")
def api_search_drive(query: str, limit: int = 5, user_id: str = Depends(get_current_user)):
    return search_drive_tool(user_id, query, limit)

@app.get("/api/drive/files/{file_id}")
def api_read_drive_file(file_id: str, user_id: str = Depends(get_current_user)):
    return read_drive_file_tool(user_id, file_id)

@app.post("/api/drive/upload")
def api_upload_drive_file(file_path: str, file_name: str, mime_type: str = "application/octet-stream", user_id: str = Depends(get_current_user)):
    return upload_drive_file_tool(user_id, file_path, file_name, mime_type)

@app.post("/api/drive/files/{file_id}/trash")
def api_trash_drive_file(file_id: str, user_id: str = Depends(get_current_user)):
    return move_drive_file_to_trash_tool(user_id, file_id)

@app.post("/api/drive/files/{file_id}/share")
def api_get_drive_share_link(file_id: str, make_public: bool = False, user_id: str = Depends(get_current_user)):
    return get_drive_share_link_tool(user_id, file_id, make_public)

@app.get("/api/calendar/events")
def api_list_calendar_events(date: str = None, days: int = 1, user_id: str = Depends(get_current_user)):
    return list_calendar_events_tool(user_id, date, days)

@app.post("/api/calendar/events")
def api_add_calendar_event(summary: str, date: str, start_time: str, duration: int = 60, description: str = "", user_id: str = Depends(get_current_user)):
    return add_calendar_event_tool(user_id, summary, date, start_time, duration, description)

@app.delete("/api/calendar/events/{event_id}")
def api_delete_calendar_event(event_id: str, user_id: str = Depends(get_current_user)):
    return delete_calendar_event_tool(user_id, event_id)

@app.get("/health")
def health_check():
    return {"status": "ok"}

# Mount frontend so you don't need a separate server
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)
