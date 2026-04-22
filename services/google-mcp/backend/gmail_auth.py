import os
import json
import logging
from typing import Optional
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import google.auth.transport.requests

logger = logging.getLogger(__name__)

# Independent Scopes
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.modify", "https://www.googleapis.com/auth/userinfo.email"]
DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/userinfo.email"]
CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar", "https://www.googleapis.com/auth/userinfo.email"]

# Set 'OAUTHLIB_INSECURE_TRANSPORT' temporarily in dev; remove in prod
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

TOKEN_DIR = os.getenv("TOKEN_DIR", os.path.join(os.getcwd(), "tokens"))
os.makedirs(TOKEN_DIR, exist_ok=True)

auth_router = APIRouter()
auth_flow_store = {} # state -> (flow, service_type)

def get_client_secrets_file():
    return os.getenv("GOOGLE_CLIENT_SECRETS_JSON", "credentials.json")

def get_token_path(user_id: str, service: str):
    return os.path.join(TOKEN_DIR, f"{service}_{user_id}_token.json")

def get_flow(service: str, state=None):
    client_secrets_file = get_client_secrets_file()
    if not os.path.exists(client_secrets_file):
        raise HTTPException(status_code=500, detail="credentials.json not found")
        
    if service == "gmail":
        scopes = GMAIL_SCOPES
    elif service == "drive":
        scopes = DRIVE_SCOPES
    else:
        scopes = CALENDAR_SCOPES
        
    flow = Flow.from_client_secrets_file(
        client_secrets_file,
        scopes=scopes,
        state=state
    )
    # The redirect URI must still match what's in Google Console
    flow.redirect_uri = os.getenv("REDIRECT_URI", "http://localhost:8000/auth/callback")
    return flow

@auth_router.get("/login/{service}")
def login(service: str):
    """Initiates the Google OAuth 2.0 flow for a specific service."""
    if service not in ["gmail", "drive", "calendar"]:
        raise HTTPException(status_code=400, detail="Invalid service type")
        
    flow = get_flow(service)
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    auth_flow_store[state] = (flow, service)
    return RedirectResponse(authorization_url)

@auth_router.get("/callback")
def auth_callback(request: Request, state: str = None, code: str = None):
    """Unified callback for both services."""
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code missing")
        
    stored = auth_flow_store.get(state)
    if not stored:
        raise HTTPException(status_code=400, detail="Invalid state or session expired")
        
    flow, service = stored
    
    try:
        flow.fetch_token(authorization_response=str(request.url))
    except Exception as e:
        logger.error(f"Error fetching token: {e}")
        raise HTTPException(status_code=400, detail=f"OAuth Token Error: {str(e)}")
        
    del auth_flow_store[state]
    
    credentials = flow.credentials
    try:
        # Fetch profile info using the appropriate API
        if service == "gmail":
            srv = build('gmail', 'v1', credentials=credentials)
            profile = srv.users().getProfile(userId='me').execute()
            user_id = profile['emailAddress']
        elif service == "drive":
            srv = build('drive', 'v3', credentials=credentials)
            profile = srv.about().get(fields="user").execute()
            user_id = profile['user']['emailAddress']
        else:
            # Calendar uses userinfo.email via profile api
            srv = build('oauth2', 'v2', credentials=credentials)
            profile = srv.userinfo().get().execute()
            user_id = profile['email']
    except Exception as e:
        logger.error(f"Failed to fetch profile for {service}: {e}")
        user_id = "default_user"

    token_path = get_token_path(user_id, service)
    with open(token_path, "w") as token_file:
        token_file.write(credentials.to_json())
        
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    # Tell frontend which service was connected
    return RedirectResponse(f"{frontend_url}/?user_id={user_id}&service={service}")

def get_user_credentials(user_id: str, service: str):
    token_path = get_token_path(user_id, service)
    if not os.path.exists(token_path):
        return None
        
    if service == "gmail":
        scopes = GMAIL_SCOPES
    elif service == "drive":
        scopes = DRIVE_SCOPES
    else:
        scopes = CALENDAR_SCOPES

    try:
        creds = Credentials.from_authorized_user_file(token_path, scopes)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(google.auth.transport.requests.Request())
            with open(token_path, "w") as token_file:
                token_file.write(creds.to_json())
        return creds
    except Exception as e:
        logger.error(f"Error loading {service} credentials for {user_id}: {e}")
        return None

def get_gmail_service(user_id: str):
    creds = get_user_credentials(user_id, "gmail")
    if not creds:
        raise HTTPException(status_code=401, detail="Gmail not authenticated.")
    return build('gmail', 'v1', credentials=creds, cache_discovery=False)

def get_drive_service(user_id: str):
    creds = get_user_credentials(user_id, "drive")
    if not creds:
        raise HTTPException(status_code=401, detail="Google Drive not authenticated.")
    return build('drive', 'v3', credentials=creds, cache_discovery=False)

def get_calendar_service(user_id: str):
    creds = get_user_credentials(user_id, "calendar")
    if not creds:
        raise HTTPException(status_code=401, detail="Google Calendar not authenticated.")
    return build("calendar", "v3", credentials=creds, cache_discovery=False)
