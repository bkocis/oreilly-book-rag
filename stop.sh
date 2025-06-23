#!/bin/bash

# O'Reilly RAG Quiz Application Stop Script
# This script stops all services started by run.sh

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
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
    echo -e "${PURPLE}  Stopping O'Reilly RAG Quiz App${NC}"
    echo -e "${PURPLE}======================================${NC}"
    echo
}

# Function to stop backend
stop_backend() {
    print_step "Stopping backend API..."
    
    if [ -f logs/backend.pid ]; then
        BACKEND_PID=$(cat logs/backend.pid)
        if kill -0 $BACKEND_PID 2>/dev/null; then
            kill $BACKEND_PID 2>/dev/null
            sleep 2
            if kill -0 $BACKEND_PID 2>/dev/null; then
                kill -9 $BACKEND_PID 2>/dev/null
            fi
            print_success "Backend stopped"
        else
            print_warning "Backend process not found"
        fi
        rm -f logs/backend.pid
    else
        # Try to kill any python process running app.main
        pkill -f "python -m app.main" 2>/dev/null || true
        print_step "Backend process cleaned up"
    fi
}

# Function to stop frontend
stop_frontend() {
    print_step "Stopping frontend application..."
    
    if [ -f logs/frontend.pid ]; then
        FRONTEND_PID=$(cat logs/frontend.pid)
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            kill $FRONTEND_PID 2>/dev/null
            sleep 2
            if kill -0 $FRONTEND_PID 2>/dev/null; then
                kill -9 $FRONTEND_PID 2>/dev/null
            fi
            print_success "Frontend stopped"
        else
            print_warning "Frontend process not found"
        fi
        rm -f logs/frontend.pid
    else
        # Try to kill any npm dev process
        pkill -f "npm run dev" 2>/dev/null || true
        pkill -f "vite" 2>/dev/null || true
        print_step "Frontend process cleaned up"
    fi
}

# Function to stop Qdrant (optional)
stop_qdrant() {
    if [ "$1" = "--with-qdrant" ]; then
        print_step "Stopping Qdrant container..."
        if docker ps --format "table {{.Names}}" | grep -q "^$QDRANT_CONTAINER_NAME$"; then
            docker stop "$QDRANT_CONTAINER_NAME" >/dev/null 2>&1
            print_success "Qdrant container stopped"
        else
            print_step "Qdrant container not running"
        fi
    else
        print_step "Leaving Qdrant running (use --with-qdrant to stop it too)"
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  --with-qdrant    Also stop the Qdrant container"
    echo "  --help           Show this help message"
    echo
}

# Main execution
main() {
    # Parse arguments
    STOP_QDRANT=false
    for arg in "$@"; do
        case $arg in
            --with-qdrant)
                STOP_QDRANT=true
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $arg"
                show_usage
                exit 1
                ;;
        esac
    done

    print_header
    print_step "Stopping O'Reilly RAG Quiz Application..."
    echo
    
    # Stop services
    stop_backend
    stop_frontend
    
    if [ "$STOP_QDRANT" = true ]; then
        stop_qdrant --with-qdrant
    else
        stop_qdrant
    fi
    
    echo
    print_success "🛑 O'Reilly RAG Quiz Application stopped!"
    echo
    print_step "To restart the application, run: ${GREEN}./run.sh${NC}"
    
    if [ "$STOP_QDRANT" != true ]; then
        print_step "Qdrant is still running. To stop it: ${GREEN}./stop.sh --with-qdrant${NC}"
    fi
    
    echo
}

# Run main function
main "$@" 