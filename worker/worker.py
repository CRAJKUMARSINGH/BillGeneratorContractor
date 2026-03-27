import asyncio
from typing import Dict, Any

async def parse_task(ctx: Dict[str, Any], file_path: str) -> Dict[str, Any]:
    """
    Simulate parsing a document asynchronously.
    In reality, this would call the ingestion library.
    """
    # Wait for IO-bound work like file reading
    await asyncio.sleep(1)
    return {"status": "parsed", "file": file_path}

async def render_task(ctx: Dict[str, Any], document_data: Dict[str, Any]) -> bytes:
    """
    Simulate rendering a document into a PDF asynchronously.
    """
    # Wait for CPU-bound rendering
    await asyncio.sleep(2)
    return b"%PDF-1.4\n%..."

class WorkerSettings:
    """
    The ARQ worker entry point settings.
    You can run this worker using `arq worker.worker.WorkerSettings`
    """
    functions = [parse_task, render_task]
    
    async def on_startup(ctx: Dict[str, Any]) -> None:
        print("Worker starting up...")
        
    async def on_shutdown(ctx: Dict[str, Any]) -> None:
        print("Worker shutting down...")
