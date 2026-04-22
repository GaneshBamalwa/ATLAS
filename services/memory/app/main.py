from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import MemoryStoreRequest, MemorySearchRequest, MemoryResponse, MemoryBatchStoreRequest
from app.vector_store import vector_store
from app.redis_store import redis_store
from app.core.memory_validator import memory_validator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Memory Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_user_id(x_user_id: str = Header(None)):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="X-User-Id header missing")
    return x_user_id

@app.post("/memory/store", response_model=MemoryResponse)
async def store_memory(req: MemoryStoreRequest, user_id: str = Depends(get_user_id)):
    try:
        doc_id = await vector_store.store(user_id, req.text, req.metadata)
        return MemoryResponse(status="success", data={"id": doc_id})
    except Exception as e:
        logger.error(f"Store error: {e}")
        return MemoryResponse(status="error", message=str(e))

@app.post("/memory/store_batch", response_model=MemoryResponse)
async def store_batch_memory(req: MemoryBatchStoreRequest, user_id: str = Depends(get_user_id)):
    try:
        valid_facts = memory_validator.validate_facts(req.facts)
        stored_ids = []
        for fact in valid_facts:
            # text is generated in the validator as key: value
            doc_id = await vector_store.store(user_id, fact["text"], fact)
            stored_ids.append(doc_id)
        return MemoryResponse(status="success", data={"stored_count": len(stored_ids), "ids": stored_ids})
    except Exception as e:
        logger.error(f"Batch Store error: {e}")
        return MemoryResponse(status="error", message=str(e))

@app.post("/memory/search", response_model=MemoryResponse)
async def search_memory(req: MemorySearchRequest, user_id: str = Depends(get_user_id)):
    try:
        memories = await vector_store.search(user_id, req.query, req.limit)
        return MemoryResponse(status="success", data=memories)
    except Exception as e:
        logger.error(f"Search error: {e}")
        return MemoryResponse(status="error", message=str(e))

@app.delete("/memory/clear", response_model=MemoryResponse)
async def clear_memory(user_id: str = Depends(get_user_id)):
    try:
        await vector_store.clear(user_id)
        redis_store.clear_context(user_id)
        return MemoryResponse(status="success", message="All memory cleared for user")
    except Exception as e:
        return MemoryResponse(status="error", message=str(e))

@app.get("/memory/stats", response_model=MemoryResponse)
async def get_stats(user_id: str = Depends(get_user_id)):
    try:
        stats = vector_store.get_stats(user_id)
        return MemoryResponse(status="success", data=stats)
    except Exception as e:
        return MemoryResponse(status="error", message=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
