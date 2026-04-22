# ATLAS Technical Specifications

This document provides a comprehensive technical deep-dive into the architecture, operational logic, data flow, and security protocols of the ATLAS AI Orchestration platform.

---

## System Architecture

ATLAS is implemented as a modern, three-tier microservice architecture designed to provide an intelligent natural language interface for multi-system automation.

### 1. ATLAS Web Console
- **Location**: `apps/web-console`
- **Role**: Primary user interface and observability dashboard.
- **Specifications**: React 18, Vite, TypeScript, and a bespoke glassmorphic design system.
- **Key Features**: Real-time message streaming, live execution tracing, and session-based state management.

### 2. ATLAS Central Orchestrator
- **Location**: `services/orchestrator`
- **Role**: Central reasoning engine and task coordinator.
- **Specifications**: FastAPI, Python 3.12+, LLM-driven ReAct loop.
- **Key Features**: Intent recognition, autonomous task chaining, and response synthesis.

### 3. Unified Google MCP Service
- **Location**: `services/google-mcp`
- **Role**: Protocol-compliant bridge for Google Workspace integration.
- **Specifications**: FastAPI, Google API Client Library, OAuth 2.0.
- **Key Features**: Standardized tool interface for Gmail, Drive, and Calendar operations.

### 4. ATLAS Memory Service
- **Location**: `services/memory`
- **Role**: Semantic storage and historical context management.
- **Specifications**: FastAPI, ChromaDB, Redis.
- **Key Features**: Fact extraction, vector-based retrieval, and personalization.

---

## Orchestration Logic: The ReAct Loop

The system operates on a Recursive Reasoning and Acting (ReAct) paradigm, enabling the orchestrator to solve complex, multi-step problems through iterative cycles.

1.  **Context Aggregation**: The Orchestrator gathers the user query, temporal metadata, conversation history, and user-scoped authentication state.
2.  **Intent Decomposition**: The reasoning engine evaluates the input to determine if the query requires external data or tool execution.
3.  **Autonomous Chaining**:
    - If tool intervention is required, the Orchestrator dispatches a request to the appropriate MCP endpoint.
    - The execution result is integrated back into the model's context.
    - The loop repeats until the reasoning engine determines that sufficient information has been gathered to resolve the user's intent.
4.  **Polished Synthesis**: A final processing layer transforms the aggregated data into a professional, human-readable response.

---

## Service Capabilities and Boundaries

The platform exposes specialized toolsets through its unified registry, ensuring clear boundaries between intent and execution.

### Gmail Intelligence
- **Semantic Analysis**: Converts natural language into Gmail Query Language (GQL) for precise message filtering.
- **Automated Communication**: Manages the drafting and dispatching of professional emails with optimized tone and content.

### Google Drive Protocol
- **Content Retrieval**: Facilitates file discovery by metadata and internal text analysis.
- **Cross-Service Data Flow**: Enables the extraction of context from Drive documents for downstream use in other integrations.

### Calendar and Scheduling
- **Intelligent Scheduling**: Validates availability and manages the event lifecycle.
- **Conflict Resolution**: Employs automated reasoning to identify scheduling collisions and propose alternative time windows.
- **State Verification**: Performs immediate post-action checks to ensure calendar integrity.

---

## Security and Authorization

ATLAS implements a rigorous security model to protect user data and ensure authorized access.

- **Granular Scopes**: Gmail, Drive, and Calendar operate with independent OAuth 2.0 scopes, allowing users to grant minimum necessary permissions.
- **User-Scoped Persistence**: Authentication tokens are stored in isolated, user-specific payloads within the service infrastructure.
- **Header-Based Authorization**: The Frontend transmits user identification via `X-User-Id` headers. The Orchestrator forwards this identifier to MCP services to load the corresponding OAuth credentials for each request.

---

## System Networking and Port Mapping

| Component | Port | Accessibility |
| :--- | :--- | :--- |
| **Web Console** | 5173 | Publicly accessible (User Interface) |
| **Central Orchestrator** | 9000 | Accessible by Web Console |
| **Google MCP Service** | 8000 | Accessible by Orchestrator |
| **Memory Service** | 8002 | Accessible by Orchestrator |
| **Agent Daemon** | 9001 | Accessible by Web Console (WebSocket) |
| **Redis** | 6379 | Internal State Persistence |

---

## Data Flow Lifecycle: Example Interaction

**User Query**: "Review the project proposal in my Drive and email a summary to John."

1.  **Ingestion**: Web Console transmits the query to the Orchestrator.
2.  **Initial Plan**: Orchestrator determines it must first locate and read the file from Drive.
3.  **Tool Execution (Step 1)**: Orchestrator calls `search_drive` via the Google MCP Service.
4.  **Reasoning**: Orchestrator analyzes the retrieved document content to extract key highlights.
5.  **Tool Execution (Step 2)**: Orchestrator calls `send_email` via the Google MCP Service with the generated summary.
6.  **Finalization**: Orchestrator confirms both steps were successful and delivers a consolidated confirmation to the user.
7.  **Trace Visualization**: The Web Console renders each reasoning step and tool call in the execution trace for user audit.
