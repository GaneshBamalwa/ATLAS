# ATLAS Deployment and Startup Guide

This document provides comprehensive instructions for deploying and initializing the ATLAS Orchestration ecosystem. The platform supports both containerized deployment via Docker and manual service execution for local development.

---

## Deployment Option 1: Docker Compose (Recommended)

Docker Compose is the preferred method for production-like environments, ensuring all microservices (Orchestrator, Google MCP, Memory, Redis, and Web Console) are initialized with correct networking and environment configurations.

Execute the following command from the root directory:

```bash
docker-compose up --build
```

Access the integrated Web Console at: `http://localhost:5173`

---

## Deployment Option 2: Local Service Execution

For development and debugging, services can be executed independently. Ensure all dependencies are installed and the appropriate virtual environments are activated.

### 1. Central Orchestrator
The core reasoning engine manages tool-use and interaction flows.
```bash
cd services/orchestrator
uvicorn app.main:app --reload --port 9000
```

### 2. Google MCP Service
The protocol bridge for Google Workspace integrations.
```bash
cd services/google-mcp
uvicorn backend.main:app --reload --port 8000
```

### 3. Memory Service
Provides semantic storage and factual persistence. Requires a running Redis instance.
```bash
cd services/memory
uvicorn app.main:app --reload --port 8002
```

### 4. Agent Daemon
Manages proactive notifications and background monitoring via WebSockets.
```bash
cd services/agent-daemon
uvicorn app.main:app --reload --port 9001
```

### 5. Web Console (Frontend)
The primary interface for user interaction and system observability.
```bash
cd apps/web-console
pnpm install
pnpm run dev
```

---

## External Infrastructure Dependencies

ATLAS utilizes external service providers for high-performance inference and data access.

### 1. AI Inference Providers
The Orchestrator and Agent Daemon utilize external LLM APIs for reasoning and planning.
- **Providers**: Groq (`api.groq.com`), OpenAI (`api.openai.com`), or OpenRouter (`openrouter.ai`).
- **Data Exchange**: System instructions, sanitized conversation history, and tool schemas are transmitted to generate next-step actions.

### 2. Google Workspace Ecosystem
The Google MCP Service communicates directly with Google Cloud endpoints to perform user-authorized operations.
- **Endpoint**: `googleapis.com` / `oauth2.googleapis.com`
- **Scope of Operations**:
    - **Gmail**: Message retrieval, thread summarization, and outbound drafting.
    - **Drive**: Semantic file search, content extraction, and permission management.
    - **Calendar**: Event lifecycle management and conflict detection.
- **Authorization**: All requests are scoped to the specific user via OAuth 2.0 Bearer Tokens.

---

## Technical Prerequisites

To ensure successful deployment, the following environment specifications must be met:

| Requirement | Specification |
| :--- | :--- |
| **Operating System** | Linux, macOS, or Windows with WSL2 / PowerShell |
| **Containerization** | Docker 20.10+ and Docker Compose v2 |
| **Runtime Environments** | Python 3.10+ and Node.js 18+ |
| **Package Managers** | pip, pnpm |
| **Credentials** | Valid Google Cloud `credentials.json` in the appropriate service path |
