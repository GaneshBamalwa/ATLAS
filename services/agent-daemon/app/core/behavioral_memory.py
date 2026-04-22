from typing import Dict, Any, List
import time
from app.core.feedback_store import feedback_store

class BehavioralMemory:
    def evaluate(self, user_id: str) -> Dict[str, Any]:
        """Track 30-90 day trends, compute stable preferences and detect drift."""
        history = feedback_store.get_history(user_id) # Using the extended list if available
        
        now = time.time()
        thirty_days = 30 * 86400
        
        acceptance_counts = {}
        total_counts = {}
        recent_acceptance = {}
        recent_total = {}
        
        for entry in history:
            s_type = entry.get("suggestion_type")
            status = entry.get("status")
            timestamp = entry.get("timestamp", 0)
            
            if s_type not in total_counts:
                total_counts[s_type] = 0
                acceptance_counts[s_type] = 0
                recent_total[s_type] = 0
                recent_acceptance[s_type] = 0
                
            total_counts[s_type] += 1
            if status == "accepted":
                acceptance_counts[s_type] += 1
                
            # Recent means last 14 days
            if now - timestamp < 14 * 86400:
                recent_total[s_type] += 1
                if status == "accepted":
                    recent_acceptance[s_type] += 1

        stable_preferences = {}
        drift_signals = []
        
        for s_type, total in total_counts.items():
            overall_rate = acceptance_counts[s_type] / total if total > 0 else 0
            stable_preferences[s_type] = round(overall_rate, 2)
            
            if recent_total[s_type] >= 3:
                recent_rate = recent_acceptance[s_type] / recent_total[s_type]
                
                # Drift detection
                if recent_rate < overall_rate - 0.3:
                    drift_signals.append(f"User stopped accepting '{s_type}' alerts recently (last 14 days)")
                elif recent_rate > overall_rate + 0.3:
                    drift_signals.append(f"User started accepting '{s_type}' alerts more over last 14 days")
                    
        return {
            "stable_preferences": stable_preferences,
            "drift_signals": drift_signals
        }

behavioral_memory = BehavioralMemory()
