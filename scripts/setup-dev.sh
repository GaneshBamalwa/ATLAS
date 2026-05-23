#!/bin/bash

# ============================================================================
# ATLAS Development Environment Setup Script (cloud-first)
# Initializes Docker and services for local development (no Ollama)
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

log_header() {
    echo -e "\n${BLUE}════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}════════════════════════════════════════════${NC}\n"
}

log_info() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 not installed"
        return 1
    fi
    log_info "$1 is installed"
    return 0
}

# ============================================================================
# MAIN SETUP
# ============================================================================

main() {
    log_header "ATLAS Development Environment Setup"

    # Check prerequisites
    log_header "Checking Prerequisites"
    
    local all_ok=true
    check_command docker || all_ok=false
    check_command docker-compose || all_ok=false
    # local Ollama is not required for cloud-first setup
    check_command python || all_ok=false
    
    if [ "$all_ok" = false ]; then
        log_error "Please install missing dependencies"
        log_info "Docker: https://docs.docker.com/get-docker/"
        log_info "Ollama: https://ollama.ai"
        log_info "Python: https://www.python.org/downloads/"
        exit 1
    fi

    # Check Python version
    PYTHON_VERSION=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    if [ $(echo "$PYTHON_VERSION < 3.10" | bc) -eq 1 ]; then
        log_error "Python 3.10+ required (found $PYTHON_VERSION)"
        exit 1
    fi
    log_info "Python $PYTHON_VERSION"

    # Create virtual environment
    log_header "Setting Up Python Environment"
    if [ ! -d ".venv" ]; then
        log_info "Creating virtual environment..."
        python -m venv .venv
        log_info "Virtual environment created"
    else
        log_info "Using existing virtual environment"
    fi

    # Activate venv and install dependencies
    log_info "Activating virtual environment..."
    source .venv/bin/activate
    
    log_info "Upgrading pip, setuptools, wheel..."
    pip install --quiet --upgrade pip setuptools wheel
    
    log_info "Installing ATLAS dependencies..."
    pip install --quiet -e .
    pip install --quiet -e ".[dev]"
    log_info "Dependencies installed"

    # No local model pulling required for cloud-first deployment

    # Setup environment file
    log_header "Environment Configuration"
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            log_info "Copying .env.example to .env"
            cp .env.example .env
            log_warning "Please update .env with your API keys:"
            log_warning "  - LLM_ROUTING_API_KEY (Groq API key)"
            log_warning "  - GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET"
        fi
    else
        log_info "Using existing .env file"
    fi

    # Setup Docker
    log_header "Docker Configuration"
    
    log_info "Creating Docker network..."
    docker network create atlas-network 2>/dev/null || log_info "Network already exists"
    
    log_info "Building Docker images..."
    docker-compose build --quiet
    log_info "Docker images built"

    # Start services
    log_header "Starting Services"
    
    log_info "Starting Docker containers..."
    docker-compose up -d
    
    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:11434/api/tags > /dev/null 2>&1 && \
           curl -s http://localhost:6379 > /dev/null 2>&1; then
            break
        fi
        attempt=$((attempt + 1))
        echo -n "."
        sleep 1
    done
    echo ""
    
    if [ $attempt -eq $max_attempts ]; then
        log_warning "Services may still be starting up"
    else
        log_info "Services are healthy"
    fi

    # Display summary
    log_header "Setup Complete!"
    
    echo -e "${GREEN}ATLAS is ready for development!${NC}\n"
    
    echo "📍 Service URLs:"
    echo "   Note: Ollama local inference is not used in this setup"
    echo "   Redis               : localhost:6379"
    echo "   Google MCP          : http://localhost:8000"
    echo "   Memory Service      : http://localhost:8002"
    echo "   Orchestrator        : http://localhost:9000"
    echo "   Sentinel Daemon     : http://localhost:9001"
    echo "   Web Console         : http://localhost:3000"
    echo ""
    
    echo "🚀 Next Steps:"
    echo "   1. Update .env with your API keys (if not already done)"
    echo "   2. Run: make dev        # or docker-compose up to restart services"
    echo "   3. Open http://localhost:3000 in your browser"
    echo ""
    
    echo "📖 Documentation:"
    echo "   make help           # Show all available commands"
    echo "   cat README.md       # Read project documentation"
    echo "   docker-compose logs -f  # Follow service logs"
    echo ""
}

# ============================================================================
# CLEANUP & HELP
# ============================================================================

cleanup() {
    log_header "Cleaning Up"
    log_info "Stopped"
}

show_help() {
    cat << EOF
ATLAS Development Environment Setup Script

Usage: $0 [OPTIONS]

Options:
    -h, --help      Show this help message
    -c, --clean     Clean all services and data before setup

Examples:
    $0              # Full setup
    $0 --clean      # Clean setup (removes all data)

EOF
}

# ============================================================================
# ENTRY POINT
# ============================================================================

trap cleanup EXIT

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -c|--clean)
            log_header "Cleaning Previous Setup"
            log_info "Stopping containers..."
            docker-compose down -v 2>/dev/null || true
            log_info "Previous setup cleaned"
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Run setup
main
