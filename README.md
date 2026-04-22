# ATLAS: Unified AI Orchestration Platform 🚀

ATLAS is a state-of-the-art AI orchestration ecosystem designed to bridge natural language reasoning with real-world tool execution. It features a modular microservice architecture that integrates multiple Google services (Gmail, Drive, Calendar) through a unified MCP (Model Context Protocol) interface.

## 🌟 Key Features

- **Central Orchestrator**: High-intelligence "brain" that routes queries, executes multi-step tool chains, and synthesizes human-friendly responses.
- **Unified Google MCP**: A specialized bridge for Gmail, Drive, and Calendar with OAuth2 security.
- **Proactive Intelligence Daemon**: A background service that monitors events and initiates proactive suggestions.
- **Dynamic Execution Tracing**: A beautiful frontend dashboard to visualize AI reasoning steps and tool payloads.
- **Memory & Learning**: Persistent memory layer that extracts facts and user preferences over time.

## 🏗️ Architecture

The system is built on a distributed microservice architecture:

- **Apps**:
  - `web-console`: React-based premium dashboard.
- **Services**:
  - `orchestrator`: The core reasoning engine (FastAPI).
  - `google-mcp`: The Google API bridge (FastAPI).
  - `agent-daemon`: Proactive monitoring service.
  - `memory`: Context and fact storage.

For a deeper dive, see [Architecture Documentation](./architecture.md).

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose
- Google Cloud Console Credentials (`credentials.json`)
- Python 3.10+
- Node.js & pnpm

### Quick Start

1. **Setup Environment**:
   Run the setup script to sync configuration across services.
   ```powershell
   ./setup_atlas.ps1
   ```

2. **Launch with Docker**:
   ```bash
   docker-compose up --build
   ```

3. **Access the Console**:
   Open `http://localhost:5173` to interact with the ATLAS Console.

## 📚 Documentation

- [Architecture](./architecture.md) - High-level system design.
- [Features](./features.md) - Detailed breakdown of system capabilities.
- [Startup Guide](./startup.md) - Detailed installation and running instructions.
- [Detailed Technical Specs](./details.md) - API endpoints and implementation notes.

## 🛠️ Tech Stack

- **Frontend**: React, Vite, Tailwind CSS, Lucide Icons, Shadcn UI.
- **Backend**: FastAPI, LangChain/LangGraph, Groq (Llama 3), OpenAI.
- **Infrastructure**: Docker, Redis (Memory), Google OAuth 2.0.

---

Built with ❤️ by the ATLAS Team.
