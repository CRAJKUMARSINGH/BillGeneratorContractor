#!/usr/bin/env python3
"""
Bill Generator Worker Startup Script
Starts the ARQ worker for background job processing
"""
import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def main():
    """Start the ARQ worker"""
    try:
        from backend.worker import main as worker_main
        
        print("Starting Bill Generator Worker...")
        print(f"Project root: {PROJECT_ROOT}")
        print(f"Redis URL: {os.getenv('REDIS_URL', 'redis://localhost:6379/0')}")
        print(f"Concurrency: {os.getenv('WORKER_CONCURRENCY', '4')}")
        print()
        
        # Start the worker
        import asyncio
        asyncio.run(worker_main())
        
    except KeyboardInterrupt:
        print("\n👋 Worker stopped by user")
    except Exception as e:
        print(f"Failed to start worker: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()