from typing import Dict, Any
from app.core.feedback_store import feedback_store

class RejectionPredictor:
    def predict(self, suggestion_type: str, user_id: str, personalization: Dict[str, Any]) -> Dict[str, Any]:
        """Predict rejection probability based on feedback history and weights."""
        history = feedback_store.get_history(user_id)
        
        # Base probability is neutral
        rejection_prob = 0.5
        
        weights = personalization.get("user_preferences", {})
        weight = weights.get(suggestion_type, 1.0)
        
        # Heavy penalty if weight is super low
        if weight < 0.5:
            rejection_prob += 0.3
        elif weight > 1.2:
            rejection_prob -= 0.3
            
        # Analyze very recent specific interactions
        recent_dismiss_streak = 0
        for entry in reversed(history[-10:]):
            if entry.get("suggestion_type") == suggestion_type:
                if entry.get("status") in ["dismissed", "ignored"]:
                    recent_dismiss_streak += 1
                elif entry.get("status") == "accepted":
                    break # Streak broken
                    
        if recent_dismiss_streak >= 3:
            rejection_prob += 0.25
        elif recent_dismiss_streak == 2:
            rejection_prob += 0.15
            
        # Clamp
        rejection_prob = max(0.0, min(1.0, rejection_prob))
        
        should_suppress = rejection_prob > 0.65
        passive_downgrade = 0.5 <= rejection_prob <= 0.65
        
        return {
            "rejection_probability": round(rejection_prob, 2),
            "should_suppress": should_suppress,
            "passive_downgrade": passive_downgrade
        }
        
rejection_predictor = RejectionPredictor()
