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
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure engine is importable
ENGINE_DIR = Path(__file__).parent.parent / "engine"
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from routes.bills import router as bills_router
from models import HealthResponse

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # tighten in Phase 8
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bills_router)


@app.get("/healthz", response_model=HealthResponse, tags=["health"])
async def health():
    """Health check — verifies engine is importable."""
    try:
        from calculation.bill_processor import process_bill  # noqa
        engine_status = "ok"
    except Exception as e:
        engine_status = f"error: {e}"
    return HealthResponse(status="ok", engine=engine_status)


@app.on_event("startup")
async def startup():
    logger.info("Bill Generator API starting up")
    logger.info(f"Engine path: {ENGINE_DIR}")
