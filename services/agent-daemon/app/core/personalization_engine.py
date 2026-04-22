from typing import Dict, Any, List
from app.core.feedback_store import feedback_store

class PersonalizationEngine:
    def evaluate(self, user_id: str) -> Dict[str, Any]:
        """Analyze feedback history and build preference weights."""
        history = feedback_store.get_history(user_id)
        
        # Base weights
        weights = {
            "email_summary": 1.0,
            "meeting_preparation": 1.0,
            "alert": 1.0,
            "reminder": 1.0
        }
        
        # Calculate adjustments
        for entry in history:
            s_type = entry.get("suggestion_type")
            status = entry.get("status")
            
            if s_type not in weights:
                weights[s_type] = 1.0
                
            if status == "accepted":
                weights[s_type] += 0.2
            elif status == "dismissed":
                weights[s_type] -= 0.3
            elif status == "ignored":
                weights[s_type] -= 0.1
                
        # Clamp constraints and determine suppression
        suppressed = []
        for k, v in weights.items():
            clamped = max(0.1, min(2.0, v))
            weights[k] = round(clamped, 2)
            
            if weights[k] < 0.3:
                suppressed.append(k)
                
        return {
            "user_preferences": weights,
            "suppressed_suggestion_types": suppressed
        }

personalization_engine = PersonalizationEngine()
