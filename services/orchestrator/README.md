# ATLAS Central Orchestrator

The Central Orchestrator is a modular, high-performance service responsible for natural language understanding, task planning, and distributed tool execution. It serves as the primary intelligence layer of the ATLAS ecosystem.

---

## Architecture and Data Flow

The Orchestrator utilizes a ReAct-based reasoning loop to process user intent and coordinate with specialized MCP services.

```text
User Request
    |
    v
POST /chat (Port 9000)
    |
    v
+----------------+
|   LLM Router   |  <-- Groq / OpenAI / Anthropic
+----------------+
    |
    | Tool Intervention Required?
    |
    +--- YES ---> +----------------+
    |             | Task Executor  | ---> HTTP/JSON Interface
    |             +----------------+
    |                    |
    |                    v
    |           Google MCP Service (Port 8000)
    |                    |
    +--- NO ----> Direct Synthesis
    |
    v
ChatResponse (Response + Execution Trace)
```

---

## Getting Started

### 1. Dependency Installation
Initialize a virtual environment and install the required service dependencies:

```bash
cd services/orchestrator
python -m venv venv
# Windows
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Configuration
Configure the `.env` file with the necessary API keys and service endpoints:

```env
GROQ_API_KEY=your_api_key
GMAIL_MCP_BASE_URL=http://localhost:8000
```

### 3. Service Execution
Launch the FastAPI application using Uvicorn:

```bash
uvicorn app.main:app --reload --port 9000
```

---

## API Reference

### POST `/chat`
Submits a natural language query for orchestration.

**Payload**:
```json
{
  "message": "Retrieve unread emails and summarize them.",
  "user_id": "authorized_user_id"
}
```

**Response**:
```json
{
  "response": "Summarized content of 3 unread emails...",
  "response_type": "success",
  "trace": {
    "steps": [...],
    "total_time_ms": 1240.5,
    "status": "success"
  }
}
```

### GET `/health`
Returns the operational status of the service and the count of registered tool capabilities.

### GET `/tools`
Retrieves a structured list of all active tool definitions within the registry.

---

## Extensibility

To integrate additional MCP services or custom tools:

1.  Navigate to `app/tool_registry.py`.
2.  Define a new `List[ToolDefinition]` following the established schema.
3.  Register the tools using the `registry.register()` method.
4.  The routing engine will automatically incorporate the new capabilities into its planning logic.

---

## Directory Structure

```text
services/orchestrator/
├── app/
│   ├── main.py           # Application entry point and API routes
│   ├── router.py         # LLM-based intent routing and planning
│   ├── executor.py       # Distributed task execution engine
│   ├── tool_registry.py  # Source of truth for system capabilities
│   ├── schemas.py        # Pydantic data models
│   ├── config.py         # Configuration management
│   └── utils/
│       └── logger.py     # Structured logging utilities
├── requirements.txt
└── .env
```
