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
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure engine is importable
ENGINE_DIR = Path(__file__).parent.parent / "engine"
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from backend.routes.bills import router as bills_router
from backend.routes.auth import router as auth_router
from backend.models import HealthResponse
from backend.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(application: FastAPI):
    """Modern replacement for deprecated @app.on_event startup/shutdown."""
    # Startup
    logger.info("Bill Generator API starting up")
    
    logger.info("Bill Generator API starting up")
    logger.info(f"Engine path: {ENGINE_DIR}")
    
    # Try to connect to Redis, but don't fail if it's not available
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        # Test connection first
        import redis.asyncio as aioredis
        test_redis = aioredis.from_url(redis_url, socket_timeout=2)
        await test_redis.ping()
        await test_redis.aclose()
        
        # If test succeeds, create the pool
        application.state.redis_pool = await create_pool(RedisSettings.from_dsn(redis_url))
        logger.info("✅ Redis connection established")
    except Exception as e:
        logger.warning(f"⚠️ Redis connection failed: {e}")
        logger.warning("Background job processing will not be available")
        application.state.redis_pool = None
    
    yield
    
    # Shutdown
    if hasattr(application.state, "redis_pool") and application.state.redis_pool:
        try:
            await application.state.redis_pool.aclose()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.warning(f"Error closing Redis connection: {e}")

app = FastAPI(
    title="Bill Generator API",
    description="PWD Contractor Bill Generation — Phase 4 Backend",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — driven by settings, not hardcoded
_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origins_list,  # explicit list, never "*" with credentials
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
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


# Remove deprecated @app.on_event handlers - replaced with lifespan
