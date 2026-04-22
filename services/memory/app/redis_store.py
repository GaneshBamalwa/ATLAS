import redis
import json
from app.config import settings

class RedisStore:
    def __init__(self):
        self.r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True
        )

    def set_context(self, user_id: str, history: list, ttl: int = 3600):
        key = f"context:{user_id}"
        self.r.set(key, json.dumps(history), ex=ttl)

    def get_context(self, user_id: str):
        key = f"context:{user_id}"
        data = self.r.get(key)
        return json.loads(data) if data else []

    def clear_context(self, user_id: str):
        key = f"context:{user_id}"
        self.r.delete(key)

redis_store = RedisStore()
