from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class MemoryStoreRequest(BaseModel):
    text: str
    metadata: Optional[Dict[str, Any]] = None

class MemoryBatchStoreRequest(BaseModel):
    facts: List[Dict[str, Any]]

class MemorySearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 5

class MemoryResponse(BaseModel):
    status: str
    message: Optional[str] = None
    data: Optional[Any] = None
