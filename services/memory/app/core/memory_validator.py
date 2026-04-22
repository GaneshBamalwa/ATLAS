import time
from typing import List, Dict, Any

class MemoryValidator:
    def validate_facts(self, facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        valid_memories = []
        for fact in facts:
            confidence = fact.get("confidence", 0)
            
            # 1. Reject low confidence (or store as inactive, but rules say reject < 0.6 to not influence, but earlier we said reject < 0.75, let's allow all but we filter active)
            
            # 2. Strict type filtering
            fact_type = fact.get("type", "")
            if fact_type not in ["preference", "entity", "instruction", "stable_fact"]:
                continue
            
            # 3. Assign importance score based on type
            importance = 0.5
            prefix = "FACT"
            if fact_type == "preference":
                importance = 0.95
                prefix = "STYLE_PREFERENCE"
            elif fact_type == "instruction":
                importance = 0.90
                prefix = "ACTIVE_RULE"
            elif fact_type == "entity":
                importance = 0.80
                prefix = "USER_ROLE"
            elif fact_type == "stable_fact":
                importance = 0.85
                prefix = "SYSTEM_FACT"
                
            key = str(fact.get("key", "unknown")).upper()
            value = str(fact.get("value", ""))
            
            normalized_rule = f"{prefix}: {key} = {value}"
            
            valid_memories.append({
                "memory_type": fact_type,
                "key": key.lower(),
                "value": value,
                "normalized_rule": normalized_rule,
                "confidence": float(confidence),
                "importance_score": float(importance),
                "recency_timestamp": float(time.time()),
                "text": normalized_rule,  # For vector search embedding targeting the rule itself
                "active": True if confidence >= 0.6 else False
            })
            
        return valid_memories

memory_validator = MemoryValidator()

