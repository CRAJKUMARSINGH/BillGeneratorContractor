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

try:
    import redis.asyncio as aioredis
    from arq import create_pool
    from arq.connections import RedisSettings
except ImportError:
    # MOCK for restricted environments
    aioredis = None
    create_pool = None
    RedisSettings = None

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlmodel import Session, select

from database import create_db_and_tables, engine
from routes.bills import router as bills_router
from routes.auth import router as auth_router
from models import HealthResponse, User
from auth_utils import get_password_hash

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

# Security: Restrict origins in production
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bills_router)
app.include_router(auth_router)


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health():
    """Health check — verifies engine and infrastructure."""
    try:
        from engine.calculation.bill_processor import process_bill  # noqa
        engine_status = "ok"
    except Exception as e:
        engine_status = f"error: {e}"
        
    redis_status = "unknown"
    try:
        if hasattr(app.state, "redis_client"):
            if await app.state.redis_client.ping():
                redis_status = "connected"
            else:
                redis_status = "failed"
        else:
            redis_status = "not_initialized"
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
    # Secret Validation
    if not os.getenv("SECRET_KEY") and os.getenv("NODE_ENV") == "production":
        logger.error("CRITICAL: SECRET_KEY not set in production!")
        sys.exit(1)

    create_db_and_tables()
    with Session(engine) as session:
        if not session.exec(select(User).where(User.username == "guest")).first():
            session.add(
                User(
                    username="guest",
                    hashed_password=get_password_hash("noop"),
                    role="operator",
                )
            )
            session.commit()
            logger.info("Created shared guest user for open access")
    logger.info("Bill Generator API starting up")
    
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    if not redis_url:
        logger.error("CRITICAL: REDIS_URL not set!")
        sys.exit(1)

    if aioredis:
        try:
            app.state.redis_client = aioredis.from_url(redis_url, decode_responses=True)
        except Exception as e:
            logger.warning("Redis async client unavailable: %s", e)
    if create_pool and RedisSettings:
        try:
            app.state.redis_pool = await create_pool(RedisSettings.from_dsn(redis_url))
        except Exception as e:
            logger.warning("Redis ARQ pool unavailable (jobs may fail): %s", e)
    else:
        logger.warning("Worker/Redis infrastructure mocked (Dependencies missing)")

@app.on_event("shutdown")
async def shutdown():
    if hasattr(app.state, "redis_client") and app.state.redis_client:
        await app.state.redis_client.aclose()
    if hasattr(app.state, "redis_pool") and app.state.redis_pool:
        await app.state.redis_pool.close()
        # await app.state.redis_pool.wait_closed()
