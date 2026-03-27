"""ARQ worker settings — async job queue backed by Redis.
Falls back gracefully if Redis is unavailable (jobs run in-process via BackgroundTasks).
"""
from app.core.config import settings


class WorkerSettings:
    """ARQ WorkerSettings — run with: uv run python -m arq app.jobs.worker.WorkerSettings"""
    redis_settings_from_url = settings.redis_url
    functions = []  # bill generation runs via FastAPI BackgroundTasks for now
    max_jobs = 10
    job_timeout = 300  # 5 min
