import httpx
import logging
from typing import List, Dict, Any, Optional
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

async def get_relevant_memories(user_id: str, query: str, limit: int = 20) -> List[str]:
    """Retrieve relevant long-term memories with strict budget control."""
    if not user_id:
        return []
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{settings.memory_service_url}/memory/search",
                headers={"X-User-Id": user_id},
                json={"query": query, "limit": limit}
            )
            if resp.status_code == 200:
                data = resp.json()
                if data["status"] == "success":
                    memories = []
                    # We roughly estimate 1 token = 4 characters. Budget = 1200 tokens ~ 4800 characters
                    max_chars = 4800 
                    current_chars = 0
                    
                    for m in data["data"]:
                        confidence = m.get("confidence", 0.5)
                        if confidence < 0.6: 
                            continue # Safety drop low confidence
                            
                        rule = m.get("normalized_rule", m.get("text", ""))
                        formatted = f"- {rule} (confidence: {confidence})"
                        
                        if m.get("metadata", {}).get("conflict_group"):
                            formatted += " [CONFLICT_FLAG: CHECK CONFIDENCE]"
                            
                        if current_chars + len(formatted) > max_chars:
                            break # Exceeded budget, drop remaining (assumes already sorted descending)
                            
                        memories.append(formatted)
                        current_chars += len(formatted)
                        
                    return memories
    except Exception as e:
        logger.warning(f"Memory retrieval failed: {e}")
    
    return []

async def store_memory(user_id: str, text: str, metadata: Dict[str, Any] = None):
    pass # Deprecated by store_memory_batch, kept for compatibility if needed.

async def store_memory_batch(user_id: str, facts: List[Dict[str, Any]]):
    """Store an array of extracted facts to the memory service."""
    if not user_id or not facts:
        return
        
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"{settings.memory_service_url}/memory/store_batch",
                headers={"X-User-Id": user_id},
                json={"facts": facts}
            )
    except Exception as e:
        logger.warning(f"Memory batch storage failed: {e}")

async def async_memory_writerTask(user_id: str, user_message: str, human_response: str):
    """Background task to extract and store facts."""
    try:
        from app.router import extract_facts
        facts = await extract_facts(user_message, human_response)
        if facts:
            await store_memory_batch(user_id, facts)
    except Exception as e:
        logger.warning(f"Async Memory Writer failed: {e}")
