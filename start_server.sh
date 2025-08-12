#!/bin/bash

# ESP32 WebRTC AI Assistant Server - Startup Script
# This script sets up and runs the server with proper environment checks

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}🚀 ESP32 WebRTC AI Assistant Server${NC}"
echo -e "${BLUE}=====================================${NC}"

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if Python is installed
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        print_status "Python 3 found: $PYTHON_VERSION"
        
        # Check if version is 3.10 or higher
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
            print_status "Python version is compatible (3.10+)"
        else
            print_error "Python 3.10+ is required. Current version: $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python 3 is not installed"
        exit 1
    fi
}

# Check if virtual environment exists
check_virtual_env() {
    if [ -d "venv" ]; then
        print_status "Virtual environment found"
        source venv/bin/activate
        print_status "Virtual environment activated"
    else
        print_warning "Virtual environment not found"
        read -p "Create virtual environment? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            python3 -m venv venv
            source venv/bin/activate
            print_status "Virtual environment created and activated"
        else
            print_info "Continuing without virtual environment"
        fi
    fi
}

# Install dependencies
install_dependencies() {
    print_info "Checking dependencies..."
    
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_status "Dependencies installed"
    else
        print_warning "requirements.txt not found, installing basic dependencies"
        pip install fastapi uvicorn python-dotenv loguru pydantic
        pip install "pipecat-ai[runner,webrtc,openai,deepgram,cartesia,silero]"
    fi
}

# Check environment variables
check_environment() {
    print_info "Checking environment configuration..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            print_warning ".env file not found"
            read -p "Copy from .env.example? (y/n): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                cp .env.example .env
                print_status ".env file created from template"
                print_warning "Please edit .env file with your API keys before continuing"
                read -p "Press Enter to continue after editing .env file..."
            fi
        else
            print_error ".env file not found and no .env.example template available"
            exit 1
        fi
    fi
    
    # Source environment variables
    if [ -f ".env" ]; then
        export $(grep -v '^#' .env | xargs)
        print_status "Environment variables loaded"
    fi
    
    # Check required API keys
    required_vars=("OPENAI_API_KEY" "DEEPGRAM_API_KEY" "CARTESIA_API_KEY")
    missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -eq 0 ]; then
        print_status "All required API keys found"
    else
        print_warning "Missing API keys: ${missing_vars[*]}"
        print_warning "Server may not function properly without these keys"
        read -p "Continue anyway? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Run tests
run_tests() {
    if [ -f "test_server.py" ]; then
        print_info "Running server tests..."
        read -p "Run tests before starting server? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # Start server in background for testing
            python esp32_webrtc_server.py --port 8001 &
            SERVER_PID=$!
            
            # Wait for server to start
            sleep 3
            
            # Run tests
            if python test_server.py; then
                print_status "All tests passed"
            else
                print_warning "Some tests failed"
            fi
            
            # Stop test server
            kill $SERVER_PID 2>/dev/null || true
            sleep 1
        fi
    fi
}

# Parse command line arguments
parse_args() {
    HOST="0.0.0.0"
    PORT="8000"
    LOG_LEVEL="info"
    RELOAD=false
    SKIP_CHECKS=false
    RUN_TESTS=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --host)
                HOST="$2"
                shift 2
                ;;
            --port)
                PORT="$2"
                shift 2
                ;;
            --log-level)
                LOG_LEVEL="$2"
                shift 2
                ;;
            --reload)
                RELOAD=true
                shift
                ;;
            --skip-checks)
                SKIP_CHECKS=true
                shift
                ;;
            --test)
                RUN_TESTS=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --host HOST        Server host (default: 0.0.0.0)"
                echo "  --port PORT        Server port (default: 8000)"
                echo "  --log-level LEVEL  Log level: debug, info, warning, error (default: info)"
                echo "  --reload           Enable auto-reload for development"
                echo "  --skip-checks      Skip environment and dependency checks"
                echo "  --test             Run tests before starting server"
                echo "  --help             Show this help message"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
}

# Main startup sequence
main() {
    parse_args "$@"
    
    print_info "Starting ESP32 WebRTC AI Assistant Server..."
    print_info "Host: $HOST, Port: $PORT, Log Level: $LOG_LEVEL"
    
    if [ "$SKIP_CHECKS" = false ]; then
        check_python
        check_virtual_env
        install_dependencies
        check_environment
        
        if [ "$RUN_TESTS" = true ]; then
            run_tests
        fi
    fi
    
    # Build server command
    SERVER_CMD="python esp32_webrtc_server.py --host $HOST --port $PORT --log-level $LOG_LEVEL"
    
    if [ "$RELOAD" = true ]; then
        SERVER_CMD="$SERVER_CMD --reload"
        print_info "Development mode: Auto-reload enabled"
    fi
    
    print_status "All checks completed successfully!"
    echo ""
    print_info "Starting server..."
    print_info "API Documentation: http://$HOST:$PORT/docs"
    print_info "Health Check: http://$HOST:$PORT/health"
    print_info "Web Test Client: file://$(pwd)/web_test_client.html"
    echo ""
    print_info "Press Ctrl+C to stop the server"
    echo ""
    
    # Trap Ctrl+C and cleanup
    trap 'echo -e "\n${YELLOW}🛑 Shutting down server...${NC}"; exit 0' INT
    
    # Run the server
    exec $SERVER_CMD
}

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
