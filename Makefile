.PHONY: help setup dev test lint format clean docker-up docker-down docker-logs pull-model

# Default target
help:
	@echo "ATLAS Development Commands"
	@echo "======================================"
	@echo "setup              - Setup development environment (first-time setup)"
	@echo "dev                - Start all services in Docker"
	@echo "dev-local          - Start services locally (requires manual service setup)"
	@echo "test               - Run all tests"
	@echo "test-service S=    - Run tests for specific service (e.g., make test-service S=orchestrator)"
	@echo "lint               - Run linting (black, flake8, mypy)"
	@echo "format             - Format code with black and isort"
	@echo "docker-up          - Start all Docker services"
	@echo "docker-down        - Stop all Docker services"
	@echo "docker-logs        - Follow Docker logs"
	@echo "docker-build       - Rebuild Docker images"
	@echo "pull-model         - Pull Qwen 3.5 model for Ollama"
	@echo "clean              - Clean build artifacts and cache"
	@echo "install-deps       - Install development dependencies"
	@echo "venv               - Create Python virtual environment"
	@echo ""

# ============================================================================
# SETUP TARGETS
# ============================================================================

setup: check-requirements venv install-deps pull-model docker-setup
	@echo "✅ Setup complete! Run 'make dev' to start services."


check-requirements:
	@command -v docker >/dev/null 2>&1 || (echo "❌ Docker not installed" && exit 1)
	@command -v docker-compose >/dev/null 2>&1 || (echo "❌ Docker Compose not installed" && exit 1)
	@command -v python >/dev/null 2>&1 || (echo "❌ Python not installed" && exit 1)
	@echo "✅ All requirements present"

venv:
	@if [ ! -d ".venv" ]; then \
		echo "📦 Creating Python virtual environment..."; \
		python -m venv .venv; \
		echo "✅ Virtual environment created"; \
	else \
		echo "✅ Virtual environment already exists"; \
	fi

install-deps: venv
	@echo "📦 Installing Python dependencies..."
	@. .venv/bin/activate && pip install --upgrade pip setuptools wheel
	@. .venv/bin/activate && pip install -e .
	@. .venv/bin/activate && pip install -e ".[dev]"
	@echo "✅ Dependencies installed"

docker-setup:
	@echo "🐳 Creating Docker networks..."
	@docker network create atlas-network 2>/dev/null || true
	@echo "✅ Docker setup complete"



# ============================================================================
# DEVELOPMENT TARGETS
# ============================================================================

dev: docker-build docker-up
	@echo "⏳ Waiting for services to be healthy..."
	@sleep 10
	@echo ""
	@echo "✅ Services started!"
	@echo "📍 Web Console: http://localhost:3000"
	@echo "📍 Orchestrator: http://localhost:9000"
	@echo "📍 Google MCP: http://localhost:8000"
	@echo "📍 Memory: http://localhost:8002"
	@echo "📍 Sentinel: http://localhost:9001"
	@echo "📍 Ollama: http://localhost:11434"
	@echo ""
	@echo "Run 'make docker-logs' to follow logs"

dev-local:
	@echo "Starting services locally (not in Docker)..."
	@echo "⚠️  Make sure Ollama is running: ollama serve"
	@echo ""
	@echo "In separate terminals, run:"
	@echo "  cd services/orchestrator && uvicorn app.main:app --reload --port 9000"
	@echo "  cd services/memory && uvicorn app.main:app --reload --port 8002"
	@echo "  cd services/google-mcp && uvicorn backend.main:app --reload --port 8000"
	@echo "  cd services/sentinel && uvicorn app.main:app --reload --port 9001"
	@echo "  cd apps/web-console && pnpm install && pnpm run dev"

# ============================================================================
# TESTING TARGETS
# ============================================================================

test:
	@echo "🧪 Running all tests..."
	@. .venv/bin/activate && python -m pytest tests/ -v --cov=services --cov=shared
	@echo "✅ Tests completed"

test-service:
	@if [ -z "$(S)" ]; then \
		echo "❌ Please specify service: make test-service S=orchestrator"; \
		exit 1; \
	fi
	@echo "🧪 Testing service: $(S)"
	@. .venv/bin/activate && python -m pytest services/$(S)/tests/ -v
	@echo "✅ Service tests completed"

test-integration:
	@echo "🧪 Running integration tests..."
	@. .venv/bin/activate && python -m pytest tests/integration/ -v -s
	@echo "✅ Integration tests completed"

# ============================================================================
# CODE QUALITY TARGETS
# ============================================================================

lint:
	@echo "🔍 Running linters..."
	@. .venv/bin/activate && black --check services/ shared/ --line-length 100
	@. .venv/bin/activate && flake8 services/ shared/ --max-line-length 100
	@. .venv/bin/activate && mypy services/ shared/ --ignore-missing-imports
	@echo "✅ Linting complete"

format:
	@echo "✨ Formatting code..."
	@. .venv/bin/activate && black services/ shared/ --line-length 100
	@. .venv/bin/activate && isort services/ shared/ --profile black
	@echo "✅ Code formatted"

# ============================================================================
# DOCKER TARGETS
# ============================================================================

docker-build:
	@echo "🐳 Building Docker images..."
	docker-compose build
	@echo "✅ Images built"

docker-up:
	@echo "🚀 Starting Docker containers..."
	docker-compose up -d
	@echo "✅ Containers started"

docker-down:
	@echo "🛑 Stopping Docker containers..."
	docker-compose down
	@echo "✅ Containers stopped"

docker-logs:
	docker-compose logs -f

docker-ps:
	docker-compose ps

docker-clean:
	@echo "🧹 Cleaning Docker resources..."
	docker-compose down --volumes
	docker system prune -f
	@echo "✅ Docker cleaned"

# ============================================================================
# CLEANUP TARGETS
# ============================================================================

clean:
	@echo "🧹 Cleaning build artifacts..."
	@find services shared apps -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find services shared apps -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	@find services shared apps -type d -name ".egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find services shared apps -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf .coverage htmlcov/ build/ dist/ 2>/dev/null || true
	@echo "✅ Cleanup complete"

clean-venv:
	@echo "🧹 Removing virtual environment..."
	@rm -rf .venv
	@echo "✅ Virtual environment removed"

# ============================================================================
# UTILITY TARGETS
# ============================================================================

health-check:
	@echo "🏥 Checking service health..."
	@curl -s http://localhost:9000/health | jq . || echo "❌ Orchestrator unhealthy"
	@curl -s http://localhost:8002/health | jq . || echo "❌ Memory unhealthy"
	@curl -s http://localhost:8000/health | jq . || echo "❌ Google MCP unhealthy"


logs-orchestrator:
	docker-compose logs -f orchestrator

logs-memory:
	docker-compose logs -f memory

logs-google-mcp:
	docker-compose logs -f google-mcp

logs-sentinel:
	docker-compose logs -f sentinel

# ============================================================================
# DATABASE TARGETS
# ============================================================================

db-reset:
	@echo "🔄 Resetting database state..."
	docker-compose down -v
	@echo "✅ Database reset"

# ============================================================================
# DOCUMENTATION
# ============================================================================

docs:
	@echo "📖 ATLAS Documentation"
	@echo "======================================"
	@echo "README.md           - Project overview"
	@echo "architecture.md     - System architecture"
	@echo "details.md          - Technical specifications"
	@echo "features.md         - Feature registry"
	@echo "startup.md          - Deployment guide"
	@echo ""
	@echo "Quick Start:"
	@echo "  1. make setup       # First-time setup"
	@echo "  2. make dev         # Start all services"
	@echo "  3. Open http://localhost:3000"
