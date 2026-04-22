import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.notification import notifier
from app.scheduler import scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Proactive Intelligence Daemon (PID)...")
    await scheduler.start()
    yield
    logger.info("Shutting down PID...")
    await scheduler.stop()


app = FastAPI(title="Proactive Intelligence Daemon", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws/notifications/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await notifier.connect(websocket)
    
    if user_id not in scheduler.active_users:
        scheduler.active_users.append(user_id)
        
    logger.info(f"Client connected: {user_id}")
    try:
        from app.core.feedback_store import feedback_store
        import json
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
            else:
                try:
                    payload = json.loads(data)
                    if "feedback" in payload:
                        fb = payload["feedback"]
                        feedback_store.log_feedback(
                            user_id=user_id,
                            suggestion_type=fb.get("suggestion_type", ""),
                            status=fb.get("status", "ignored"),
                            context_hash=fb.get("context_hash", "")
                        )
                        logger.info(f"Logged feedback for {user_id}: {fb.get('status')}")
                except Exception:
                    pass
    except WebSocketDisconnect:
        notifier.disconnect(websocket)
        logger.info(f"Client disconnected: {user_id}")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "agent-daemon"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.daemon_host, port=settings.daemon_port, reload=True)
