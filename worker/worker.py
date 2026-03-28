"""
DEPRECATED — This stub worker module has been removed.

The real ARQ worker lives in backend/worker.py.

To run the worker:
    cd backend
    arq worker.WorkerSettings
OR using the docker-compose service:
    docker-compose up worker

DO NOT use this directory for worker logic.
"""
raise ImportError(
    "worker/worker.py is deprecated. "
    "The real worker is backend/worker.py — run `arq worker.WorkerSettings` from backend/."
)
