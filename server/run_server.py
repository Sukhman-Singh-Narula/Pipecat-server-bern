#!/usr/bin/env python3

"""
Run the enhanced Pipecat server with FastAPI
"""

import uvicorn
import argparse
from config.settings import get_settings

def main():
    parser = argparse.ArgumentParser(description="Enhanced Pipecat Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=7860, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--log-level", default="info", help="Log level")
    
    args = parser.parse_args()
    
    print(f"🚀 Starting Enhanced Pipecat Server...")
    print(f"   Host: {args.host}")
    print(f"   Port: {args.port}")
    print(f"   Log Level: {args.log_level}")
    print(f"   Reload: {args.reload}")
    
    # Run the server
    uvicorn.run(
        "bot:app",
        host=args.host,
        port=args.port,
        log_level=args.log_level,
        reload=args.reload,
        access_log=True
    )

if __name__ == "__main__":
    main()
