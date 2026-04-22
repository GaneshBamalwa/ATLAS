# How to Start ATLAS Orchestration Project

You can start **ATLAS** using either **Docker Compose** (recommended for running everything at once) or by running the services **individually**.

## Option 1: Docker Compose (All-in-One)

This is the easiest way to start the entire ATLAS stack (Orchestrator, Google MCP, Memory, Redis, and Web Console).

From the root project directory (`G:\MCPs\fresh`), run:

```bash
docker-compose up --build
```

## Option 2: Run Services Individually

If you prefer to run the services individually for development/debugging, you will need separate terminal windows for each service.

**Note:** Ensure you activate your python virtual environment (`venv\Scripts\activate`) for the python services.

### 1. ATLAS Central Orchestrator
```bash
cd services/orchestrator
uvicorn app.main:app --reload --port 9000
```
*(Currently running on port 9000)*

### 2. Google MCP Service
```bash
cd services/google-mcp
uvicorn backend.main:app --reload --port 8000
```

### 3. ATLAS Web Console (Frontend)
Make sure you are in `apps/web-console`, not in any of the services folders!

```bash
cd apps/web-console
pnpm install   # If dependencies are not installed yet
pnpm run dev
```

### 4. Memory Service (Required)
The memory/RAG component stores context and behavioral tracking data:
```bash
cd services/memory
uvicorn app.main:app --reload --port 8002
```
*(Note: Requires a running Redis instance as defined in docker-compose)*

### 5. Proactive Intelligence Daemon (PID)
The autonomous background agent daemon tracks context and pushes suggestions via WebSocket:
```bash
cd services/agent-daemon
uvicorn app.main:app --reload --port 9001
```

---

## 🌐 External API Dependencies

ATLAS relies on the following external services to function. When the services are running, they will make internet-bound API calls to these providers:

### 1. LLM / AI Providers (Orchestrator & Agent Daemon)
The `central-orchestrator` and `agent-daemon` services communicate with external AI inference providers to power reasoning loops and proactive decision making.
- **Who it calls:** **Groq** (`api.groq.com`) or **OpenRouter** (`openrouter.ai`) depending on your `.env` configuration.
- **What it sends:** System prompts, conversation history (minus actual PII from unconnected services), and tool action results to get the next step or final answer.

### 2. Google Workspace APIs (Google MCP)
The `google-mcp` service talks directly to Google's backend. All operations here are strictly scoped to the user who authenticates via the Frontend console.
- **Who it calls:** **Google Cloud / Workspace APIs** (`googleapis.com` / `oauth2.googleapis.com`).
- **What it calls:**
  - **Gmail API:** For reading unread counts, extracting email threads, and sending outgoing emails on behalf of the user.
  - **Drive API:** For searching documents, reading file content, generating share links, and trashing files.
  - **Calendar API:** For listing temporal events, identifying scheduling conflicts, and inserting new appointments. 
- **Authentication:** These requests use OAuth2 Bearer Tokens acquired when the user connects their Google account via the web console.
