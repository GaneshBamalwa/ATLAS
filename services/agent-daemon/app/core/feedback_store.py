import time
from typing import Dict, List, Any

class FeedbackStore:
    def __init__(self):
        # user_id -> list of feedback entries
        self.history: Dict[str, List[Dict[str, Any]]] = {}

    def log_feedback(self, user_id: str, suggestion_type: str, status: str, context_hash: str):
        """status: accepted | dismissed | ignored"""
        if user_id not in self.history:
            self.history[user_id] = []
            
        self.history[user_id].append({
            "user_id": user_id,
            "suggestion_type": suggestion_type,
            "timestamp": time.time(),
            "status": status,
            "context_hash": context_hash
        })
        
        # Keep last 100 entries per user
        self.history[user_id] = self.history[user_id][-100:]

    def get_history(self, user_id: str) -> List[Dict[str, Any]]:
        return self.history.get(user_id, [])

feedback_store = FeedbackStore()
