# ATLAS Project Architecture: Unified Google Workspace AI Orchestrator

This document provides a comprehensive deep-dive into the architecture, data flow, operational logic, and technological stack of the **ATLAS** AI Orchestration platform.

---

## 🏗️ System Overview

The **ATLAS** project is structured as a robust, modern, three-tier microservice architecture designed to provide an intelligent, unified natural language interface for various tools, starting with Google Workspace (Gmail, Drive, Calendar). 

The system handles everything from intent recognition to independent execution and verification, all wrapped in a visually stunning interface.

### 1. **Core Components**

*   **ATLAS Web Console (`apps/web-console`)**:
    *   **Tech Stack:** React 18, Vite, Typecript, plain CSS with some Tailwind for utilities.
    *   **Role:** The user-facing client. Shows a highly polished, glassmorphic UI representing the "ATLAS" design language.
    *   **Features:** Chat input, real-time message streaming, detailed execution tracing (showing users exactly what the AI is thinking and doing), and an independent settings panel for managing OAuth sessions.
*   **ATLAS Central Orchestrator (`services/orchestrator`)**:
    *   **Tech Stack:** FastAPI, Python 3.12+, Groq / OpenRouter.
    *   **Role:** The "Brain". This service acts as the central router and ReAct reasoning engine. It does not perform operations directly; instead, it determines user intent, decides which tools to invoke, and chains operations together autonomously.
*   **Unified Google MCP Service (`services/google-mcp`)**:
    *   **Tech Stack:** FastAPI, Google Client API, OAuth2.
    *   **Role:** The "Muscle". Provides a unified Model Context Protocol (MCP) compatible layer for Google services. Contains specialized tools for Gmail, Drive, and Calendar, executing them directly against Google's APIs.
*   **ATLAS Memory Service (`services/memory` & Redis)**:
    *   **Tech Stack:** FastAPI, ChromaDB, Redis.
    *   **Role:** Handles long-term semantic memory, storing facts and preferences about the user locally to provide contextual personalization over time.

---

## 🧠 The Orchestrator Logic (ReAct Loop)

The central piece of this architecture is the LLM-driven **Reasoning & Acting (ReAct)** loop inside the Orchestrator. 

When a user submits a query:

1.  **Context Assembly:** The Orchestrator gathers system prompts, current datetime (for resolving relative dates like "tomorrow"), conversation history, and user authentication state.
2.  **Intent Detection (LLM):** The router feeds the context to the LLM to decide: *Can I answer this directly, or do I need a tool?*
3.  **Autonomous Chaining:**
    *   If a tool is needed, the Orchestrator initiates an HTTP request to the respective service (e.g., Google MCP).
    *   Upon receiving the result, the Orchestrator *feeds the result back into the LLM*.
    *   The LLM reasoning continues: *Do I have enough information now? Do I need another tool?* (e.g., "I found the invoice on Drive, now I must email it via Gmail").
4.  **Final Synthesis:** Once no more tools are required, the LLM constructs a final, human-readable response, which is streamed to the UI alongside the full "trace" of its actions.

---

## 🛠️ Tool Registry & Service Boundaries

The Orchestrator dynamically registers tools exposed by the MCP services via its `tool_registry.py`.

### **1. Gmail Intelligence**
*   **Semantic Search**: Converts natural language into Gmail Query Language (GQL).
*   **Batch Intelligence**: Retrieves and categorizes multiple emails efficiently.
*   **Resolute Drafting**: Generates professional subjects/bodies and dispatches emails.

### **2. Google Drive Protocol**
*   **Search & Retrieval**: Locates files by name, type, or internal content.
*   **Cross-Service Chaining**: Seamlessly reads a document in Drive and extracts context for answering questions or drafting emails.

### **3. Calendar Timeline**
*   **Event Scheduling & Checking**: Lists and adds events.
*   **Conflict Awareness**: Employs AI conflict resolution logic. Before an event is booked, the system checks for overlaps. If a conflict occurs, the LLM proposes alternate slots.
*   **Post-Verification Mechanism**: Automatically verifies additions by listing the day's events *after* adding or modifying an event to ensure absolute accuracy.

---

## 🔐 Security & Authentication

*   **Independent Service Scopes**: Rather than clumping all Google permissions together, Gmail, Drive, and Calendar operate on distinct OAuth endpoints and token scopes.
*   **Decoupled State**: Tokens are persisted separately in the `google-mcp/tokens` directory. Users can opt-in to specific services without needing to grant all permissions.
*   **ID Forwarding**: The Frontend maintains an authentication session. Whenever it makes a request to the Orchestrator, it passes an `X-User-Id` header, which the Orchestrator forwards to the MCP service to load the correct individual OAuth payload.

---

## 📡 Networking & Ports map

The ecosystem operates seamlessly both individually and within Docker Compose.

| Component | Port | Network Role / Accessibility |
| :--- | :--- | :--- |
| **ATLAS Web Console (Vite)** | `3000` | Exposes the application to the User. |
| **ATLAS Orchestrator** | `9000` | Accepts Web Console API requests. |
| **Google MCP** | `8000` | Internal API, accessed only by Orchestrator. |
| **Memory Server** | `8002` | Internal API, providing ChromaDB access. |
| **Redis** | `6379` | State persistence. |

---

## 📋 Data Flow Example: "Review my resume in Drive and email John if it's ready"

1.  **Frontend (Port 3000):** Sends `{"message": "...", "user_id": "oauth_user"}`.
2.  **Orchestrator (Port 9000):** Starts execution trace. LLM determines it needs to read Drive first.
3.  **Orchestrator -> Google MCP:** Calls `search_drive_files({"query": "resume"....})`.
4.  **Google MCP (Port 8000):** Fetches from Google API via OAuth. Returns document content.
5.  **Orchestrator Reasoning Loop:** LLM analyzes the text. Determines if it looks "ready" based on internal reasoning.
6.  **Orchestrator -> Google MCP:** If ready, calls `draft_and_send_email({"to": "John", "body": "Resume attached details..."})`.
7.  **Final Wrap-up:** LLM outputs: "I reviewed your resume (it looked finished) and dispatched an email to John." Frontend visualizes the two sequential steps in the UI Execution Trace.

---

## ✨ ATLAS Features Checklist

- **Multi-Service AI Reasoning:** Autonomous problem solving that chains multiple tools (e.g. read an email, check calendar, reply or set an event).
- **Dynamic Execution Trace:** Real-time visibility into the LLM's thought process and operations in the UI.
- **Microservice Architecture:** Complete separation of concerns: Frontend, Brain (Orchestrator), and Muscle (Google MCP).
- **Independent OAuth Connectors:** Granular scopes so users only grant permissions to the services they want to use.
- **Conflict Management (Calendar):** AI-powered conflict resolution for scheduling events.
- **Intelligent Summarization (Gmail/Drive):** Capable of reading large amounts of text to provide brief, accurate summaries.
- **Full Docker Support:** One command (`docker-compose up`) brings up the entire ecosystem.

---

## 🧰 Full ATLAS Tool Registry

The following tools are actively registered and available for the Orchestrator's LLM to use:

### 📧 Gmail Tools
1. **`list_unread_emails`**: List recently unread emails by ID.
2. **`read_email`**: Read a specific email by ID and optionally summarize it.
3. **`send_email`**: Compose and send a professional email. The LLM infers the tone and subject automatically.
4. **`search_emails`**: Natural language search for past emails.
5. **`get_labels`**: Fetch all Gmail folders/labels.
6. **`get_threads`**: Retrieve recent email threads and conversations.
7. **`get_profile`**: Get info on the authenticated user.

### 📁 Google Drive Tools
1. **`search_drive`**: Search for files or documents by name or keyword.
2. **`read_drive_file`**: Read the textual content of a file.
3. **`trash_drive_file`**: Move a specific file to the Drive trash bin.
4. **`get_drive_share_link`**: Generate a shareable link and optional public access rights.

### 📅 Google Calendar Tools
1. **`list_calendar_events`**: List events for a specific date or upcoming block of days.
2. **`add_calendar_event`**: Add an event. Checks for conflicts and suggests alternative time slots if a collision occurs.
3. **`delete_calendar_event`**: Remove a specific calendar event.
