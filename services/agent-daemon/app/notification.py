import asyncio
import json
import logging
import uuid
import time
from typing import Dict, List, Any
from fastapi import WebSocket
from app.core.feedback_store import feedback_store

logger = logging.getLogger(__name__)

class NotificationEngine:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.notification_history: Dict[str, Dict[str, float]] = {}
        self.last_push_time: Dict[str, float] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def push_suggestions(self, user_id: str, suggestions: List[Dict[str, Any]]):
        """Deduplicate, filter via feedback, and push to websockets"""
        if not suggestions:
            return

        now = time.time()
        
        # 1. Feedback awareness: Has user dismissed or ignored this recently?
        feedback = feedback_store.get_history(user_id)
        recently_dismissed = set()
        for f in feedback:
            if f.get("status") in ["dismissed", "ignored"] and (now - f.get("timestamp", 0) < 3600):
                # Suppress for 1 hour
                recently_dismissed.add(f.get("context_hash"))
        
        # 2. Rate Limiting: Max 1 batch per 10 mins (600s)
        last_push = self.last_push_time.get(user_id, 0)
        if now - last_push < 600:
            logger.info(f"Rate limited notifications for {user_id}. Try again later.")
            return

        # 3. Deduplication
        if user_id not in self.notification_history:
            self.notification_history[user_id] = {}
            
        history = self.notification_history[user_id]
        
        keys_to_delete = [k for k, v in history.items() if now - v > 3600]
        for k in keys_to_delete:
            del history[k]

        valid_notifications = []
        for sug in suggestions:
            dedup_key = f"{sug.get('type')}:{sug.get('recommended_action')}"
            
            # Semantic feedback check
            if dedup_key in recently_dismissed:
                logger.info(f"Suppressing {dedup_key} due to recent dismissal.")
                continue
                
            if dedup_key in history:
                continue # Already sent recently
                
            history[dedup_key] = now
            valid_notifications.append({
                "id": str(uuid.uuid4()),
                "type": sug.get("type", "alert"),
                "message": sug.get("reason", "Proactive alert generated"),
                "priority": sug.get("priority", "low"),
                "timestamp": str(now),
                "context_hash": dedup_key # Using dedup_key for feedback context parsing
            })

        if not valid_notifications:
            return

        # 4. Push
        self.last_push_time[user_id] = now
        logger.info(f"Pushing {len(valid_notifications)} proactive alerts for {user_id}")
        
        for conn in self.active_connections:
            try:
                await conn.send_text(json.dumps({"user_id": user_id, "notifications": valid_notifications}))
            except Exception as e:
                logger.error(f"WS send error: {e}")

notifier = NotificationEngine()
