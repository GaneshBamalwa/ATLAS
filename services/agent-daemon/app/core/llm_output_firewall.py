from typing import Dict, Any, List
import logging
import time
from app.core.feedback_store import feedback_store

logger = logging.getLogger(__name__)

class LLMOutputFirewall:
    def validate(
        self,
        user_id: str,
        suggestions: List[Dict[str, Any]],
        confidence: float,
        suppressed_types: List[str],
        passive_downgrade_types: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """FINAL AUTHORITY: Enforce deterministic rules post-LLM."""
        
        approved = []
        blocked = []
        downgraded = []
        
        if confidence < 0.7:
            logger.warning("Firewall BLOCKED all suggestions: Confidence too low.")
            return {"approved_suggestions": [], "blocked_suggestions": suggestions, "downgraded_suggestions": []}
            
        history = feedback_store.get_history(user_id)
        now = time.time()
        recent_hashes = set()
        for entry in history:
            if now - entry.get("timestamp", 0) < 3600:
                recent_hashes.add(entry.get("context_hash"))
            
        for sug in suggestions:
            s_type = sug.get("type", "alert")
            s_hash = f"{s_type}:{sug.get('recommended_action')}"
            
            if s_hash in recent_hashes:
                logger.info(f"Firewall BLOCKED '{s_type}': Duplicate exists in last 60 minutes.")
                blocked.append(sug)
                continue
            
            if s_type in suppressed_types:
                logger.info(f"Firewall BLOCKED '{s_type}': In suppressed types.")
                blocked.append(sug)
                continue
                
            if s_type in passive_downgrade_types:
                sug["priority"] = "low"
                logger.info(f"Firewall DOWNGRADED '{s_type}': Predicted passive downgrade.")
                downgraded.append(sug)
                approved.append(sug)
                continue
                
            approved.append(sug)
            
        return {
            "approved_suggestions": approved,
            "blocked_suggestions": blocked,
            "downgraded_suggestions": downgraded
        }

llm_output_firewall = LLMOutputFirewall()
