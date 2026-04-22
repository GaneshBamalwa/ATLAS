import json
import httpx
import logging
from typing import Dict, Any, List
from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Decision Engine for a Proactive Intelligence Daemon.
Your ONLY job is to evaluate a context snapshot and determine if the user requires proactive notifications.

RULES:
- Return ONLY valid JSON.
- Never output free text.
- Do NOT hallucinate actions.
- Do NOT re-suggest items in the Last 20 Decisions.
- Propose suggestions freely based on context. You DO NOT need to suppress or enforce rules; external systems will handle enforcement. 
- You MUST rely on the behavioral memory trends if adjusting your suggestions.

You will be given:
1. Snapshot Priorities: Critical, High, Medium events.
2. User Personalization Weights.
3. Suppressed Suggestion Types.
4. Behavioral Memory Summary.
5. Last 20 Decisions.

OUTPUT FORMAT:
{
  "should_notify": true|false,
  "suggestions": [
    {
      "type": "email_summary | meeting_preparation | alert | reminder",
      "priority": "low | medium | high",
      "reason": "<short explanation>",
      "recommended_action": "<what you think the user should do>"
    }
  ],
  "confidence": <float 0.0-1.0>
}
"""

async def evaluate_snapshot(
    snapshot: Dict[str, Any],
    personalization_profile: Dict[str, Any] = None,
    behavioral_memory: Dict[str, Any] = None,
    last_decisions: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    api_key = settings.openrouter_api_key or settings.groq_api_key
    
    stateful_payload = {
        "priority_snapshot": snapshot,
        "personalization": personalization_profile or {},
        "behavioral_memory": behavioral_memory or {},
        "last_decisions": last_decisions or []
    }
    
    payload = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(stateful_payload)}
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"}
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{settings.llm_base_url}/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            )
            if resp.status_code == 200:
                data = resp.json()
                raw = data["choices"][0]["message"]["content"]
                
                try:
                    parsed = json.loads(raw)
                    return parsed
                except Exception:
                    logger.error("Decision engine returned malformed JSON.")
    except Exception as e:
        logger.error(f"Decision engine failure: {e}")
        
    return {"should_notify": False, "suggestions": [], "confidence": 0.0}
