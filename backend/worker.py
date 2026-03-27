import asyncio
import os
import sys
from pathlib import Path
import logging

from arq import Worker
from arq.connections import RedisSettings
from routes.bills import _generate_documents
from models import GenerateRequest

logger = logging.getLogger("worker")

async def generate_bill_task(ctx, job_id: str, req_dump: dict):
    logger.info(f"Worker picked up job_id: {job_id}")
    req = GenerateRequest(**req_dump)
    try:
        _generate_documents(job_id, req)
        logger.info(f"Worker finished job_id: {job_id}")
    except Exception as e:
        logger.error(f"Worker failed on job_id {job_id}: {e}")
        raise e

class WorkerSettings:
    functions = [generate_bill_task]
    redis_settings = RedisSettings.from_dsn(os.getenv("REDIS_URL", "redis://redis:6379/0"))
    max_jobs = int(os.getenv("WORKER_CONCURRENCY", "4"))

    async def on_startup(ctx):
        logger.info("ARQ Worker started cleanly.")

if __name__ == "__main__":
    async def main():
        worker = Worker(
            functions=[generate_bill_task],
            redis_settings=WorkerSettings.redis_settings,
            max_jobs=WorkerSettings.max_jobs,
            on_startup=WorkerSettings.on_startup,
        )
        await worker.async_run()
    asyncio.run(main())
