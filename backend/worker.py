import asyncio
import os
import sys
from pathlib import Path
import logging

# Ensure engine is importable
PROJECT_ROOT = Path(__file__).parent.parent
ENGINE_DIR = PROJECT_ROOT / "engine"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from arq import Worker
from arq.connections import RedisSettings
from backend.services.bill_generation_service import generate_documents
from backend.models import GenerateRequest
from backend.routes.bills import OUTPUT_DIR

logger = logging.getLogger("worker")

async def generate_bill_task(ctx, job_id: str, req_dump: dict):
    """
    ARQ task handler. Runs the CPU-bound generation in a thread pool
    so we don't block the event loop for potentially minutes.
    """
    logger.info("Worker picked up job_id=%s", job_id)
    req = GenerateRequest(**req_dump)
    loop = asyncio.get_running_loop()
    try:
        # run_in_executor: prevents sync PDF generation from blocking event loop
        # This is critical for not starving other concurrent jobs
        await loop.run_in_executor(
            None, 
            generate_documents, 
            job_id, 
            req,
            OUTPUT_DIR
        )
        logger.info("Worker completed job_id=%s", job_id)
    except Exception as exc:
        logger.exception("Worker failed on job_id=%s: %s", job_id, exc)
        raise  # Re-raise so ARQ marks job as failed

class WorkerSettings:
    functions = [generate_bill_task]
    redis_settings = RedisSettings.from_dsn(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    max_jobs = int(os.getenv("WORKER_CONCURRENCY", "4"))

    async def on_startup(ctx):
        logger.info("ARQ Worker started cleanly.")

async def main():
    """Run the ARQ worker."""
    worker = Worker(
        functions=[generate_bill_task],
        redis_settings=WorkerSettings.redis_settings,
        max_jobs=WorkerSettings.max_jobs,
        on_startup=WorkerSettings.on_startup,
    )
    await worker.async_run()

if __name__ == "__main__":
    asyncio.run(main())
