import time
import json
from typing import Any, Tuple

# In-memory dictionary: key -> (timestamp, data)
_CACHE = {}

def get_cache_key(tool_name: str, arguments: dict, user_id: str) -> str:
    """Generate a deterministic key for the tool call."""
    arg_str = json.dumps(arguments, sort_keys=True)
    return f"{user_id}:{tool_name}:{arg_str}"

def get_cached_result(key: str, max_age: int = 60) -> Any:
    """Return cached data if it exists and is not expired."""
    if key in _CACHE:
        timestamp, data = _CACHE[key]
        if time.time() - timestamp < max_age:
            return data
        else:
            del _CACHE[key]
    return None

def set_cached_result(key: str, data: Any) -> None:
    """Store data in cache with current timestamp."""
    _CACHE[key] = (time.time(), data)
