#!/usr/bin/env python3
"""
Bill Generator Server Startup Script
Starts the FastAPI server with proper configuration
"""
import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def main():
    """Start the FastAPI server"""
    try:
        import uvicorn
        
        print("Starting Bill Generator API Server...")
        print(f"Project root: {PROJECT_ROOT}")
        print(f"Server will be available at: http://localhost:8000")
        print(f"API docs will be available at: http://localhost:8000/docs")
        print(f"Health check: http://localhost:8000/health")
        print()
        
        # Start the server
        uvicorn.run(
            "backend.app:app",  # Use import string for reload to work
            host="0.0.0.0",
            port=8000,
            reload=True,
            reload_dirs=[str(PROJECT_ROOT / "backend"), str(PROJECT_ROOT / "engine")],
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()