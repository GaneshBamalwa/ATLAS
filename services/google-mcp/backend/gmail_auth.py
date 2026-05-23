import os
import json
import logging
import time
from typing import Optional
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import google.auth.transport.requests

logger = logging.getLogger(__name__)

# Independent Scopes
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.modify", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"]
DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"]
CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"]

# Set 'OAUTHLIB_INSECURE_TRANSPORT' temporarily in dev; remove in prod
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

TOKEN_DIR = os.getenv("TOKEN_DIR", os.path.join(os.getcwd(), "tokens"))
os.makedirs(TOKEN_DIR, exist_ok=True)

auth_router = APIRouter()
auth_flow_store = {} # state -> (flow, service_type)


def _validate_service(service: str) -> str:
    if service not in ["gmail", "drive", "calendar"]:
        raise HTTPException(status_code=400, detail="Invalid service type")
    return service

def get_client_secrets_file():
    return os.getenv("GOOGLE_CLIENT_SECRETS_JSON", "credentials.json")

def get_token_path(user_id: str, service: str):
    return os.path.join(TOKEN_DIR, f"{service}_{user_id}_token.json")


def get_profile_path(user_id: str, service: str):
    return os.path.join(TOKEN_DIR, f"{service}_{user_id}_profile.json")

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
    # The redirect URI must still match what's in Google Console.
    # Support both GOOGLE_REDIRECT_URI and legacy REDIRECT_URI env names.
    flow.redirect_uri = os.getenv("GOOGLE_REDIRECT_URI") or os.getenv("REDIRECT_URI") or "http://localhost:8000/auth/callback"
    return flow

@auth_router.get("/login/{service}")
def login(service: str):
    """Initiates the Google OAuth 2.0 flow for a specific service."""
    _validate_service(service)
        
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
        userinfo = build('oauth2', 'v2', credentials=credentials)
        profile = userinfo.userinfo().get().execute()
        profile_json = profile or {}
        user_id = profile_json.get('email') or profile_json.get('emailAddress')
        display_name = profile_json.get('name') or profile_json.get('given_name') or ''
        logger.info(f"OAuth profile fetched: {profile_json}")
        if not user_id:
            # Try fallbacks and log clearly when email is missing
            id_token_email = None
            try:
                id_token_email = credentials.id_token.get('email') if getattr(credentials, 'id_token', None) else None
            except Exception:
                id_token_email = None
            user_id = id_token_email
            if user_id:
                logger.warning(f"Email found in id_token fallback: {user_id}")
            else:
                logger.warning("OAuth profile did not contain an email; assigning placeholder 'unknown_user'.")
                user_id = f"unknown_user_{int(time.time())}"
    except Exception as e:
        logger.error(f"Failed to fetch profile for {service}: {e}")
        user_id = f"unknown_user_{int(time.time())}"
        display_name = ""

    token_path = get_token_path(user_id, service)
    with open(token_path, "w") as token_file:
        token_file.write(credentials.to_json())

    profile_path = get_profile_path(user_id, service)
    with open(profile_path, "w") as profile_file:
        json.dump(
            {
                "user_id": user_id,
                "service": service,
                "email": user_id,
                "name": display_name,
            },
            profile_file,
        )
        
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")
    redirect_target = f"{frontend_url}/integrations?user_id={user_id}&service={service}"
    logger.info(f"OAuth callback successful — redirecting to frontend: {redirect_target}")
    # Tell frontend which service was connected
    return RedirectResponse(redirect_target)


@auth_router.get("/status/{service}/{user_id}")
def auth_status(service: str, user_id: str):
    """Return whether a specific Google service is authenticated for the user."""
    _validate_service(service)
    token_path = get_token_path(user_id, service)
    authenticated = os.path.exists(token_path)
    return {
        "status": "success",
        "service": service,
        "user_id": user_id,
        "authenticated": authenticated,
    }


@auth_router.post("/logout/{service}/{user_id}")
def logout(service: str, user_id: str):
    """Disconnect a specific Google service by deleting its stored token."""
    _validate_service(service)
    token_path = get_token_path(user_id, service)
    profile_path = get_profile_path(user_id, service)
    removed_any = False

    if os.path.exists(token_path):
        os.remove(token_path)
        removed_any = True
    if os.path.exists(profile_path):
        os.remove(profile_path)
        removed_any = True

    if removed_any:
        return {
            "status": "success",
            "service": service,
            "user_id": user_id,
            "disconnected": True,
        }

    return {
        "status": "success",
        "service": service,
        "user_id": user_id,
        "disconnected": False,
        "message": "No token found for this service/user.",
    }


def get_user_profile_metadata(user_id: str, service: str = "gmail"):
    profile_path = get_profile_path(user_id, service)
    if not os.path.exists(profile_path):
        return {}

    try:
        with open(profile_path, "r") as profile_file:
            return json.load(profile_file)
    except Exception as e:
        logger.error(f"Error loading profile metadata for {service} {user_id}: {e}")
        return {}

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
