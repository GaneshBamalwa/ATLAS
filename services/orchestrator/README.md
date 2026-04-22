# 🧠 Central NLP Orchestrator

A modular, enterprise-grade orchestration service that understands natural language queries, routes them to the correct MCP tool (Gmail, and future services), and returns structured results to the frontend.

---

## 🏗️ Architecture

```
User Message
    │
    ▼
POST /chat (port 9000)
    │
    ▼
┌─────────────┐
│  LLM Router │  ← Groq / OpenAI-compatible
└─────────────┘
    │ tool needed?
    ├── YES → ┌──────────────┐
    │          │   Executor   │ ─── httpx (retry + timeout)
    │          └──────────────┘
    │               │
    │               ▼
    │         Gmail MCP (port 8000)
    │               │
    └── NO  → direct LLM response
    │
    ▼
ChatResponse (text + trace)
```

---

## 🚀 Quick Start

### 1. Install dependencies

```bash
cd central-orchestrator
python -m venv venv
# Windows
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure `.env`

```env
GROQ_API_KEY=your_groq_api_key_here
GMAIL_MCP_BASE_URL=http://localhost:8000
```

### 3. Run

```bash
uvicorn app.main:app --reload --port 9000
```

---

## 📡 API

### `POST /chat`

```json
{
  "message": "Check my unread emails",
  "user_id": "gmail_oauth_user_id"
}
```

**Response:**

```json
{
  "response": "📬 Found 3 unread emails...",
  "tool_used": "list_unread_emails",
  "tool_result": { ... },
  "response_type": "tool_result",
  "trace": {
    "steps": [...],
    "total_time_ms": 812.3,
    "status": "success"
  }
}
```

### `GET /health`

Returns service health status and registered tools count.

### `GET /tools`

Returns a JSON list of all registered MCP tools.

---

## ➕ Adding New MCP Services

1. Open `app/tool_registry.py`
2. Define a new `List[ToolDefinition]` for your service
3. Call `registry.register(YOUR_TOOLS)` at the bottom
4. Done — the router picks them up automatically

---

## 📁 Project Structure

```
central-orchestrator/
├── app/
│   ├── main.py           # FastAPI app + /chat endpoint
│   ├── router.py         # LLM intent routing
│   ├── executor.py       # MCP HTTP execution engine
│   ├── tool_registry.py  # All available tools
│   ├── schemas.py        # Pydantic models
│   ├── config.py         # Settings from .env
│   └── utils/
│       └── logger.py     # Structured logging
├── requirements.txt
├── .env
└── README.md
```
