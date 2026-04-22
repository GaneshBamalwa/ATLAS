# 🏗️ ATLAS System Architecture: AI Orchestration Platform

This document outlines the architecture and implementation details of **ATLAS**, the Unified MCP & Central Orchestrator ecosystem.

---

## 🛰️ High-Level Component Overview

The ATLAS system is designed as a modular, distributed microservice architecture where a central "brain" (Orchestrator) manages various "specialized workers" (MCP Servers).

### 1. 🧠 ATLAS Central Orchestrator
**Port:** `9000`  
**Location:** `services/orchestrator`  
The core intelligence layer that manages the conversation flow and tool execution.

*   **Router (`router.py`)**: Uses LLMs (Groq/OpenAI) to parse natural language and determine if a "Tool Call" is required or if a direct response is sufficient.
*   **Executor (`executor.py`)**: The "hands" of the system. It carries out HTTP requests to the registered MCP servers, handling retries, timeouts, and user ID forwarding.
*   **Tool Registry (`tool_registry.py`)**: The source of truth for all system capabilities. It defines every tool (Gmail, Drive, Calendar), its required arguments, and its endpoint.
*   **Formatter (`formatter.py`)**: A post-processing layer that takes raw JSON data from tools and uses an LLM to synthesize a polished, human-friendly response.
*   **Memory Integration**: Interacts with a standalone **Memory Service** (Port 9100) to retrieve relevant past context and store newly extracted facts using an asynchronous back-channel (`async_memory_writerTask`).

### 2. 🔌 Unified Google MCP Service
**Port:** `8000`  
**Location:** `services/google-mcp`  
A specialized server that acts as a bridge between the Orchestrator and the Google Cloud Platform.

*   **Gmail Module**:
    *   `list_unread_emails`: Fetches latest unread messages.
    *   `read_email`: Retrieves content and can optionally auto-summarize.
    *   `send_email`: Composes and sends professional emails.
    *   `search_emails`: Advanced natural language search across the inbox.
*   **Google Drive Module**:
    *   `search_drive`: Finds files by name or content.
    *   `read_drive_file`: Fetches content for summarization or attachment.
    *   `get_drive_share_link`: Manages file permissions and sharing.
*   **Google Calendar Module**:
    *   `list_calendar_events`: Checks daily/weekly schedules.
    *   `add_calendar_event`: Schedules new meetings with automated conflict detection.
    *   `delete_calendar_event`: Removes scheduled items.
*   **Authentication Hub**: Implements a robust OAuth2 flow to manage user tokens securely.

### 3. 🧠 ATLAS Proactive Agent Daemon
**Location:** `services/agent-daemon`  
A background service that enables the system to be *proactive* rather than just *reactive*. It monitors for specific triggers (e.g., upcoming meetings, unread urgent emails) and can initiate interactions via the Central Orchestrator.

### 4. 🗄️ Memory Service
**Port:** `9100`  
**Location:** `services/memory`  
A high-performance storage layer for user preferences, facts, and interaction history. It uses vector embeddings (likely) for semantic retrieval.

### 5. 🖥️ ATLAS Web Console (Frontend)
**Location:** `apps/web-console`  
A premium, dark-themed React dashboard where users interact with the assistant. It features:
*   Real-time chat interface.
*   **Execution Trace Visualizer**: Shows the "thinking process" of the orchestrator (which tools were called and why).
*   Account management for connecting Google services.

---

## 🔄 Interaction Workflow (Sequence)

1.  **Ingestion**: User asks: *"Find the project proposal on my Drive and email it to John with a summary."*
2.  **Context Enrichment**: The **Orchestrator** queries the **Memory Service** for any known context about "John" or "project proposal".
3.  **Reasoning**: The **Orchestrator** identifies two steps:
    *   Step A: Use `search_drive` to find the file.
    *   Step B: Use `send_email` with the retrieved content.
4.  **Execution Loop**:
    *   Orchestrator calls **Google MCP** (`GET /api/drive/search`).
    *   MCP returns file ID and content.
    *   Orchestrator calls **Google MCP** (`POST /api/emails/send`).
5.  **Learning**: After the interaction, the **Orchestrator** asynchronously sends extracted facts (e.g., "John is a project stakeholder") to the **Memory Service**.
6.  **Formatting**: The raw success/failure data is sent to the **Formatter LLM**.
7.  **Delivery**: The user receives: *"I've found your 'Project_Alpha_Proposal.pdf' on Drive and sent a summarized version to John as requested. ✅"*

---

## 🛠️ Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Backend Framework** | FastAPI (Python 3.10+) |
| **Orchestration Logic** | ReAct / Tool-use Prompting |
| **LLM Providers** | Groq (Llama 3), OpenAI (GPT-4o) |
| **Communication** | RESTful HTTP / JSON |
| **Authentication** | Google OAuth 2.0 |
| **Caching** | In-memory with TTL for tool results |
| **Logging** | Structured JSON logging for trace analysis |

---

## 📂 Directory Map

*   `services/orchestrator/app/`: Core logic for routing and execution.
*   `services/google-mcp/backend/`: Tool implementations and Google API integration.
*   `services/google-mcp/frontend/`: (Optional) Specialized auth or management UI for the MCP server.
*   `apps/web-console/`: The main user-facing application.
