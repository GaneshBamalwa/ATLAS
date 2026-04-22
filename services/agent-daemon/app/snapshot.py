import time
import httpx
import logging
from typing import Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

async def build_context_snapshot(user_id: str) -> Dict[str, Any]:
    """Deterministically aggregate user state without an LLM."""
    snapshot = {
        "timestamp": str(time.time()),
        "unread_emails": 0,
        "important_senders": [],
        "urgent_keywords_detected": [],
        "upcoming_meetings": [],
        "system_signals": {
            "email_pressure": "low",
            "calendar_pressure": "low"
        }
    }
    
    headers = {"X-User-Id": user_id}
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 1. Check Emails
            resp = await client.get(
                f"{settings.gmail_mcp_base_url}/api/emails/unread?limit=25",
                headers=headers
            )
            
            if resp.status_code == 200:
                data = resp.json()
                # data is typically the result from list_unread_emails_tool (a list of dicts or {"success": true, "data": [...]})
                # Check structure
                if isinstance(data, dict) and data.get("success"):
                    messages = data.get("data", [])
                elif isinstance(data, list):
                    messages = data
                else:
                    messages = data.get("messages", [])
                    
                snapshot["unread_emails"] = len(messages)
                if snapshot["unread_emails"] > 5:
                    snapshot["system_signals"]["email_pressure"] = "medium"
                if snapshot["unread_emails"] > 15:
                    snapshot["system_signals"]["email_pressure"] = "high"
                        
            # 2. Check Calendar
            cal_resp = await client.get(
                f"{settings.gmail_mcp_base_url}/api/calendar/events?days=1",
                headers=headers
            )
            if cal_resp.status_code == 200:
                cal_data = cal_resp.json()
                if isinstance(cal_data, dict) and cal_data.get("success"):
                    events = cal_data.get("data", [])
                elif isinstance(cal_data, list):
                    events = cal_data
                else:
                    events = cal_data.get("events", [])
                    
                for e in events:
                    title = e.get("summary", "Upcoming meeting")
                    snapshot["upcoming_meetings"].append({
                        "title": title,
                        "time_until_minutes": 30 # Simple placeholder unless we parse time
                    })
                    
                if len(events) >= 2:
                    snapshot["system_signals"]["calendar_pressure"] = "high"
                    
    except Exception as e:
        logger.error(f"Snapshot builder failed for {user_id}: {e}")

    return snapshot
