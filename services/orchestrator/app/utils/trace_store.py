import redis
import json
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class TraceStore:
    def __init__(self):
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = int(os.getenv("REDIS_PORT", 6379))
        try:
            self.r = redis.Redis(
                host=self.host,
                port=self.port,
                decode_responses=True
            )
        except Exception as e:
            logger.error(f"Failed to connect to Redis for TraceStore: {e}")
            self.r = None

    def save_trace(self, user_id: str, session_id: str, trace_id: str, trace_data: dict):
        if not self.r: return
        key = f"trace:{user_id}:{session_id}:{trace_id}"
        try:
            self.r.set(key, json.dumps(trace_data), ex=3600) # 1 hour TTL
        except Exception as e:
            logger.error(f"Error saving trace: {e}")

    def get_session_traces(self, user_id: str, session_id: str):
        if not self.r: return []
        pattern = f"trace:{user_id}:{session_id}:*"
        try:
            keys = self.r.keys(pattern)
            if not keys: return []
            traces = self.r.mget(keys)
            return [json.loads(t) for t in traces if t]
        except Exception as e:
            logger.error(f"Error getting session traces: {e}")
            return []

trace_store = TraceStore()
