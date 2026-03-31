"""
Bill Generator Backend — Phase 4
Thin FastAPI wrapper over engine/.

Endpoints:
  GET  /healthz
  POST /bills/upload          → parse Excel, return structured data
  POST /bills/generate        → enqueue generation job
  GET  /bills/jobs/{id}       → poll job status
  GET  /bills/jobs/{id}/download?format=zip|pdf|html

Run:
  uvicorn backend.app:app --reload --port 8000
  OR from backend/ folder:
  uvicorn app:app --reload --port 8000
"""
import logging
import sys
import os
from pathlib import Path

import redis.asyncio as aioredis
from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure engine is importable
ENGINE_DIR = Path(__file__).parent.parent / "engine"
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from backend.database import create_db_and_tables
from backend.routes.bills import router as bills_router
from backend.routes.auth import router as auth_router
from backend.models import HealthResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Bill Generator API",
    description="PWD Contractor Bill Generation — Phase 4 Backend",
    version="1.0.0",
)

# 2. CORS and Global Middleware - Hardened for Production
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bills_router)
app.include_router(auth_router)


# --- Standardized Health Checkpoints (Audit Fix) ---
@app.get("/health", tags=["System"])
@app.get("/healthz", tags=["System"])
async def health_check():
    """System health check (standardized for /health and /healthz compatibility)."""
    try:
        from engine.calculation.bill_processor import process_unified_bill  # noqa
        engine_status = "ok"
    except Exception as e:
        engine_status = f"error: {e}"
        
    redis_status = "unknown"
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = aioredis.from_url(redis_url, socket_timeout=1)
        if await r.ping():
            redis_status = "connected"
        else:
            redis_status = "failed"
        await r.aclose()
    except Exception:
        redis_status = "failed"
        
    return HealthResponse(
        status="ok", 
        redis=redis_status,
        worker="unknown",  # MVP static value until ARQ worker is integrated
        engine=engine_status
    )


@app.on_event("startup")
async def startup():
    create_db_and_tables()
    logger.info("Bill Generator API starting up")
    logger.info(f"Engine path: {ENGINE_DIR}")
    
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        app.state.redis_pool = await create_pool(RedisSettings.from_dsn(redis_url))
        logger.info("Connected to Redis successfully")
    except Exception as e:
        logger.warning(f"Failed to connect to Redis: {e}. Background jobs will be unavailable.")
        app.state.redis_pool = None

@app.on_event("shutdown")
async def shutdown():
    if getattr(app.state, "redis_pool", None) is not None:
        app.state.redis_pool.close()
        await app.state.redis_pool.wait_closed()