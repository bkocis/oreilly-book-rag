#!/bin/bash

# O'Reilly RAG Quiz Application Startup Script
# This script starts all required services for the application

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
VENV_PATH="$HOME/venv/oreilly-rag"
BACKEND_PORT=8000
FRONTEND_PORT=5173
QDRANT_PORT=6333
QDRANT_CONTAINER_NAME="qdrant-oreilly"

# Function to print colored output
print_step() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${PURPLE}======================================${NC}"
    echo -e "${PURPLE}  O'Reilly RAG Quiz Application${NC}"
    echo -e "${PURPLE}======================================${NC}"
    echo
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
port_in_use() {
    lsof -i :$1 >/dev/null 2>&1
}

# Function to check if docker container is running
container_running() {
    docker ps --format "table {{.Names}}" | grep -q "^$1$"
}

# Function to start Qdrant vector database
start_qdrant() {
    print_step "Checking Qdrant vector database..."
    
    if ! command_exists docker; then
        print_error "Docker is not installed. Please install Docker to run Qdrant."
        exit 1
    fi
    
    if container_running "$QDRANT_CONTAINER_NAME"; then
        print_success "Qdrant container is already running"
    else
        print_step "Starting Qdrant container..."
        if docker ps -a --format "table {{.Names}}" | grep -q "^$QDRANT_CONTAINER_NAME$"; then
            # Container exists but is stopped
            docker start "$QDRANT_CONTAINER_NAME" >/dev/null 2>&1
        else
            # Container doesn't exist, create it
            docker run -d \
                --name "$QDRANT_CONTAINER_NAME" \
                -p ${QDRANT_PORT}:6333 \
                -p 6334:6334 \
                qdrant/qdrant >/dev/null 2>&1
        fi
        
        # Wait for Qdrant to be ready
        print_step "Waiting for Qdrant to be ready..."
        for i in {1..30}; do
            if curl -s http://localhost:${QDRANT_PORT}/collections >/dev/null 2>&1; then
                break
            fi
            sleep 1
        done
        
        if curl -s http://localhost:${QDRANT_PORT}/collections >/dev/null 2>&1; then
            print_success "Qdrant is ready on port ${QDRANT_PORT}"
        else
            print_error "Qdrant failed to start"
            exit 1
        fi
    fi
}

# Function to start backend
start_backend() {
    print_step "Starting backend API..."
    
    # Check if virtual environment exists
    if [ ! -d "$VENV_PATH" ]; then
        print_error "Virtual environment not found at $VENV_PATH"
        print_error "Please create the virtual environment first:"
        print_error "python -m venv $VENV_PATH"
        exit 1
    fi
    
    # Check if backend is already running
    if port_in_use $BACKEND_PORT; then
        print_warning "Port $BACKEND_PORT is already in use. Backend might already be running."
        print_step "Checking if it's our backend..."
        if curl -s http://localhost:${BACKEND_PORT}/health | grep -q "healthy"; then
            print_success "Backend is already running and healthy"
            return 0
        else
            print_error "Port $BACKEND_PORT is occupied by another service"
            exit 1
        fi
    fi
    
    # Start backend in background
    cd backend
    source "$VENV_PATH/bin/activate"
    
    print_step "Installing/updating Python dependencies..."
    pip install -r requirements.txt >/dev/null 2>&1
    
    print_step "Starting FastAPI backend on port $BACKEND_PORT..."
    python -m app.main > ../logs/backend.log 2>&1 &
    BACKEND_PID=$!
    
    # Wait for backend to be ready
    print_step "Waiting for backend to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:${BACKEND_PORT}/health >/dev/null 2>&1; then
            break
        fi
        sleep 1
    done
    
    if curl -s http://localhost:${BACKEND_PORT}/health | grep -q "healthy"; then
        print_success "Backend is ready on port $BACKEND_PORT"
        echo $BACKEND_PID > ../logs/backend.pid
    else
        print_error "Backend failed to start"
        exit 1
    fi
    
    cd ..
}

# Function to start frontend
start_frontend() {
    print_step "Starting frontend application..."
    
    if ! command_exists npm; then
        print_error "npm is not installed. Please install Node.js and npm."
        exit 1
    fi
    
    # Check if frontend is already running
    if port_in_use $FRONTEND_PORT; then
        print_warning "Port $FRONTEND_PORT is already in use. Frontend might already be running."
        return 0
    fi
    
    cd frontend
    
    print_step "Installing/updating Node.js dependencies..."
    npm install >/dev/null 2>&1
    
    print_step "Starting Vite development server on port $FRONTEND_PORT..."
    npm run dev > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    
    # Wait for frontend to be ready
    print_step "Waiting for frontend to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:${FRONTEND_PORT} >/dev/null 2>&1; then
            break
        fi
        sleep 1
    done
    
    if curl -s http://localhost:${FRONTEND_PORT} >/dev/null 2>&1; then
        print_success "Frontend is ready on port $FRONTEND_PORT"
        echo $FRONTEND_PID > ../logs/frontend.pid
    else
        print_error "Frontend failed to start"
        exit 1
    fi
    
    cd ..
}

# Function to show running services
show_services() {
    echo
    print_header
    print_success "🎉 O'Reilly RAG Quiz Application is now running!"
    echo
    echo -e "${CYAN}📱 Frontend (React):${NC}"
    echo -e "   🌐 Web App: ${GREEN}http://localhost:${FRONTEND_PORT}${NC}"
    echo
    echo -e "${CYAN}🔧 Backend (FastAPI):${NC}"
    echo -e "   🌐 API Health: ${GREEN}http://localhost:${BACKEND_PORT}/health${NC}"
    echo -e "   📚 API Docs: ${GREEN}http://localhost:${BACKEND_PORT}/docs${NC}"
    echo -e "   📋 API Endpoints: ${GREEN}http://localhost:${BACKEND_PORT}/api/v1/documents${NC}"
    echo
    echo -e "${CYAN}🗄️ Vector Database (Qdrant):${NC}"
    echo -e "   🌐 Qdrant UI: ${GREEN}http://localhost:${QDRANT_PORT}/dashboard${NC}"
    echo -e "   🔍 Collections: ${GREEN}http://localhost:${QDRANT_PORT}/collections${NC}"
    echo
    echo -e "${YELLOW}📋 Available API Endpoints:${NC}"
    echo -e "   POST /api/v1/documents/upload - Upload PDF documents"
    echo -e "   GET  /api/v1/documents/list - List all documents"
    echo -e "   GET  /api/v1/documents/processing-status/{task_id} - Check processing status"
    echo -e "   POST /api/v1/documents/extract-topics - Extract topics from text"
    echo
    echo -e "${CYAN}📂 Log Files:${NC}"
    echo -e "   Backend: ${GREEN}logs/backend.log${NC}"
    echo -e "   Frontend: ${GREEN}logs/frontend.log${NC}"
    echo
    echo -e "${YELLOW}🛑 To stop the application:${NC}"
    echo -e "   Run: ${GREEN}./stop.sh${NC}"
    echo -e "   Or press Ctrl+C to stop this script"
    echo
}

# Function to create logs directory
setup_logs() {
    mkdir -p logs
    touch logs/backend.log logs/frontend.log
}

# Function to cleanup on exit
cleanup() {
    echo
    print_step "Cleaning up..."
    
    # Kill background processes
    if [ -f logs/backend.pid ]; then
        BACKEND_PID=$(cat logs/backend.pid)
        if kill -0 $BACKEND_PID 2>/dev/null; then
            kill $BACKEND_PID 2>/dev/null
            print_step "Backend process stopped"
        fi
        rm -f logs/backend.pid
    fi
    
    if [ -f logs/frontend.pid ]; then
        FRONTEND_PID=$(cat logs/frontend.pid)
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            kill $FRONTEND_PID 2>/dev/null
            print_step "Frontend process stopped"
        fi
        rm -f logs/frontend.pid
    fi
    
    print_success "Cleanup complete"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Main execution
main() {
    print_header
    print_step "Starting O'Reilly RAG Quiz Application..."
    echo
    
    # Setup
    setup_logs
    
    # Start services
    start_qdrant
    start_backend
    start_frontend
    
    # Show status
    show_services
    
    # Keep script running
    print_step "Application is running. Press Ctrl+C to stop."
    while true; do
        sleep 1
    done
}

# Run main function
main "$@" 