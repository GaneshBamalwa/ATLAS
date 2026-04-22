# ATLAS Architecture Overview

This document provides a technical deep-dive into the architecture of ATLAS, the Unified Model Context Protocol (MCP) and Central Orchestration ecosystem.

---

## System Design Philosophy

ATLAS is architected as a modular, distributed microservice environment. It follows a hub-and-spoke model where a high-intelligence central orchestrator manages specialized worker services. This separation of concerns ensures that the reasoning engine remains decoupled from the specific implementation details of external integrations.

---

## Component Breakdown

### 1. Central Orchestrator
**Port:** 9000  
**Location:** `services/orchestrator`  

The Orchestrator is the primary intelligence layer. It is responsible for session management, reasoning, and the execution lifecycle.

- **Routing Engine (`router.py`)**: Utilizes high-parameter LLMs to decompose natural language queries into discrete intent units. It determines if a request requires external tool intervention or can be resolved with existing context.
- **Task Executor (`executor.py`)**: Manages the execution of tool calls. It handles HTTP communication with MCP servers, implements retry logic, and manages timeouts and state forwarding.
- **Capability Registry (`tool_registry.py`)**: Acts as the system's source of truth for all available actions. It defines tool signatures, required parameters, and downstream endpoint mapping.
- **Response Formatter (`formatter.py`)**: A synthesis layer that transforms raw tool outputs and JSON payloads into polished, human-centric responses using LLM-based post-processing.
- **Memory Integration**: Synchronizes with the Memory Service via asynchronous channels to retrieve historical context and persist newly extracted facts.

### 2. Google MCP Service
**Port:** 8000  
**Location:** `services/google-mcp`  

A protocol-compliant bridge between the Orchestrator and Google Cloud Platform. It abstracts the complexity of Google Workspace APIs into a unified set of tools.

- **Gmail Integration**: Provides capabilities for inbox monitoring, thread analysis, and automated communication.
- **Drive Integration**: Facilitates semantic search across file systems, document retrieval, and permission management.
- **Calendar Integration**: Manages scheduling, conflict detection, and event lifecycle.
- **Authentication Gateway**: Implements OAuth 2.0 flows to ensure secure, user-scoped data access.

### 3. Agent Daemon
**Location:** `services/agent-daemon`  

The Agent Daemon provides proactive capabilities to the system. Unlike the reactive nature of the Orchestrator, the Daemon monitors background triggers and initiates interactions based on predefined conditions or identified user needs.

### 4. Memory Service
**Port:** 9100  
**Location:** `services/memory`  

A high-performance storage layer for persistent context. It utilizes both relational and vector storage to manage user preferences, factual history, and semantic embeddings for context-aware retrieval.

### 5. Web Console
**Location:** `apps/web-console`  

A premium React-based interface for interaction and observability. It features a real-time chat environment and an execution trace visualizer for auditing the AI's internal reasoning paths.

---

## Interaction Lifecycle

1.  **Ingestion**: The user submits a natural language request through the Web Console.
2.  **Contextual Enrichment**: The Orchestrator queries the Memory Service for relevant historical data and user preferences.
3.  **Strategic Planning**: The reasoning engine decomposes the request into an execution plan (e.g., "Search Drive for X" then "Email Y").
4.  **Distributed Execution**:
    - The Orchestrator invokes the Google MCP Service.
    - The MCP Service executes the requested operation via Google APIs.
    - Results are returned to the Orchestrator.
5.  **Fact Extraction**: The Orchestrator identifies new information from the interaction and asynchronously updates the Memory Service.
6.  **Synthesis**: The Formatter combines execution results into a final response.
7.  **Delivery**: The response is rendered to the user via the Web Console.

---

## Implementation Specifications

| Layer | Standard / Technology |
| :--- | :--- |
| **Communication Protocol** | RESTful HTTP / JSON |
| **Authentication** | OAuth 2.0 / Bearer Tokens |
| **Persistence** | Redis / ChromaDB / SQLite |
| **Inference Engines** | Groq, OpenAI, Anthropic |
| **Frontend Framework** | React / TypeScript / Vite |

---

## Directory Mapping

- `services/orchestrator/app/`: Core orchestration and routing logic.
- `services/google-mcp/backend/`: MCP tool implementations and Google API bindings.
- `services/agent-daemon/app/`: Proactive monitoring and notification logic.
- `services/memory/app/`: Semantic storage and fact extraction modules.
- `apps/web-console/`: User interface and observability dashboard.
