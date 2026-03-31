"""
Bill routes — upload, generate, job status, download.
Thin wrapper: all domain logic lives in engine/.
"""
import asyncio
import io
import logging
import uuid
import zipfile
import json
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Request
from fastapi.responses import StreamingResponse
import redis.asyncio as aioredis
import redis
import os

# Module-level path setup (NOT per-request)
import sys as _sys
_ROOT_DIR = Path(__file__).parent.parent.parent
if str(_ROOT_DIR) not in _sys.path:
    _sys.path.insert(0, str(_ROOT_DIR))
if str(_ROOT_DIR / "engine") not in _sys.path:
    _sys.path.insert(0, str(_ROOT_DIR / "engine"))

# Module-level imports (previously loaded per-request)
from ingestion.ocr_extractor import extract_table_from_image
from ingestion.normalizer import normalize_to_unified_model
from ingestion.excel_exporter import generate_excel_from_data
from ingestion.template_generator import generate_template_schema
from ingestion.excel_parser import parse_excel_to_raw
from engine.calculation.bill_processor import process_unified_bill

router = APIRouter(prefix="/bills", tags=["bills"])
logger = logging.getLogger(__name__)

from backend.models import (
    BillItem, DocumentInfo, ExtraItem, GenerateRequest,
    JobStatus, ParsedBillData, User, BillRecord, TemplateRequest
)
from backend.dependencies import get_current_user
from backend.database import engine
from backend.config import get_settings
from sqlmodel import Session, select

_settings = get_settings()
_UPLOAD_LIMIT = _settings.upload_limit_bytes

# Shared Redis connection pool (NOT new connection per call)
_REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
_sync_redis_pool = redis.ConnectionPool.from_url(_REDIS_URL)

# Magic numbers documented
BILL_HEADER_ROW_COUNT = 19  # process_bill() reads ws_wo.iloc[:19, :7] as header
RATE_LIMIT_MAX_REQUESTS = 10  # max requests per window
RATE_LIMIT_WINDOW_SEC = 60    # 60-second sliding window
MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20 MB

import re

# Only allow safe filename characters — prevents path traversal
_SAFE_NAME_RE = re.compile(r"^[\w\-. ]+$")

def _sanitize_filename(filename: str, allowed_exts: set) -> str:
    """
    Return a safe filename. Falls back to a UUID name if the original
    contains suspicious characters or a disallowed extension.
    """
    ext = Path(filename).suffix.lower()
    if ext not in allowed_exts:
        ext = ".bin"
    stem = Path(filename).stem
    if not stem or not _SAFE_NAME_RE.match(stem) or ".." in filename:
        return f"{uuid.uuid4()}{ext}"
    return f"{stem[:50]}{ext}"   # cap length

UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
OUTPUT_DIR = Path(__file__).parent.parent / "outputs"
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Helper for synchronous workers modifying job progress in Redis
def update_redis_job(job_id: str, **kwargs):
    """
    Atomically update specific fields of a job's Redis state.
    Uses optimistic locking (WATCH/MULTI/EXEC) to prevent race conditions
    when multiple threads update the same job simultaneously.
    """
    r = redis.Redis(connection_pool=_sync_redis_pool)
    key = f"job:{job_id}"
    with r.pipeline() as pipe:
        for _ in range(3):  # max 3 retries on concurrent modification
            try:
                pipe.watch(key)
                raw = pipe.get(key)
                job_data = json.loads(raw) if raw else {}
                job_data.update(kwargs)
                pipe.multi()
                pipe.set(key, json.dumps(job_data), ex=86400)
                pipe.execute()
                return
            except redis.WatchError:
                continue
    logger.warning("Could not update Redis job %s after retries", job_id)


def _reconstruct_output_dir(job_id: str) -> Path:
    """
    Safely reconstruct output path from a trusted job_id.
    NEVER trust output_dir values from Redis/user-controlled data.
    """
    out_dir = (OUTPUT_DIR / job_id).resolve()
    if not str(out_dir).startswith(str(OUTPUT_DIR.resolve())):
        raise ValueError(f"Suspicious job_id resolved outside OUTPUT_DIR: {job_id}")
    return out_dir


# Redis-backed rate limiting (works across multiple processes)
async def is_rate_limited_redis(ip: str) -> bool:
    """Redis-backed rate limiter that works across multiple processes. Robust to connection failures."""
    try:
        async with aioredis.from_url(_REDIS_URL, socket_timeout=1) as rc:
            rl_key = f"ratelimit:{ip}"
            count = await rc.incr(rl_key)
            if count == 1:
                await rc.expire(rl_key, RATE_LIMIT_WINDOW_SEC)
            return count > RATE_LIMIT_MAX_REQUESTS
    except Exception as e:
        # Fallback to no rate limit if Redis is down
        logger.warning(f"Redis rate limiter failed: {e}. Skipping rate check.")
        return False

def log_job_event(job_id: str, stage: str, message: str):
    """Structured job event log (ISO timestamp | job_id | stage | message)."""
    # Use logger's built-in timestamp rather than manual datetime formatting
    logger.info("%s | %s | %s", job_id, stage, message)


# ── Upload & Parse ────────────────────────────────────────────────────────────

@router.post("/upload", response_model=ParsedBillData)
async def upload_excel(request: Request, file: UploadFile = File(...)) -> ParsedBillData:
    """Upload an Excel file, parse it, and return structured data for frontend editing."""
    # ── [HIGH-6] Redis Rate Limiter ──
    if await is_rate_limited_redis(request.client.host if request.client else "127.0.0.1"):
        raise HTTPException(status_code=429, detail="Too many requests. Please wait 60 seconds.")

    if not file.filename:
        raise HTTPException(400, "No file provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in {".xlsx", ".xls", ".xlsm"}:
        raise HTTPException(400, f"Unsupported file type: {ext}. Allowed: xlsx, xls, xlsm")

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "File too large. Maximum allowed: 20 MB.")

    file_id = str(uuid.uuid4())
    save_path = UPLOAD_DIR / f"{file_id}{ext}"
    save_path.write_bytes(content)
    logger.info("Saved upload '%s' → %s", file.filename, save_path)

    try:
        loop = asyncio.get_running_loop()  # 3.10+ safe replacement for get_event_loop()
        data = await loop.run_in_executor(
            None, _parse_excel, save_path, file_id, file.filename
        )
        return data
    except Exception:
        logger.exception("Excel parse failed for file_id=%s", file_id)
        raise HTTPException(500, "Failed to parse Excel. Ensure the file matches the expected template.")
    finally:
        save_path.unlink(missing_ok=True)  # Always clean up uploaded file

@router.post("/upload-image", response_model=ParsedBillData)
async def upload_image(file: UploadFile = File(...)):
    """Upload an image (scanned handwritten bill), run OCR, return structured data."""
    if not file.filename:
        raise HTTPException(400, "No file provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in {".png", ".jpg", ".jpeg", ".pdf"}:
        raise HTTPException(400, f"Unsupported image type: {ext}")

    content = await file.read()
    if len(content) > _UPLOAD_LIMIT:
        raise HTTPException(413, f"File too large. Max {_settings.upload_limit_mb} MB.")

    file_id = str(uuid.uuid4())
    safe_name = _sanitize_filename(file.filename, {".png", ".jpg", ".jpeg", ".pdf"})
    save_path = UPLOAD_DIR / f"{file_id}_{safe_name}"
    save_path.write_bytes(content)
    logger.info(f"Saved image upload {file.filename} → {save_path}")

    try:
        raw_data = await asyncio.get_running_loop().run_in_executor(None, extract_table_from_image, str(save_path))
        unified = normalize_to_unified_model(raw_data, source_type="ocr")

        # Map UnifiedDocumentModel -> ParsedBillData
        bill_items = []
        for i, row in enumerate(unified.rows):
            bill_items.append(BillItem(
                itemNo=str(i+1),
                description=row.description,
                unit=row.unit,
                quantitySince=row.quantity,
                quantityUpto=row.quantity,
                quantity=row.quantity,
                rate=row.rate,
                amount=row.amount
            ))

        return ParsedBillData(
            fileId=file_id,
            fileName=file.filename,
            titleData=unified.raw_metadata,
            billItems=bill_items,
            extraItems=[],
            totalAmount=unified.total_amount,
            hasExtraItems=False,
            sheets=["OCR Output"]
        )

    except Exception as e:
        logger.exception("OCR parse failed")
        save_path.unlink(missing_ok=True)
        raise HTTPException(500, f"Failed to run OCR on image: {e}")


@router.post("/export-excel")
async def export_excel(data: ParsedBillData):
    """
    Accepts ParsedBillData (e.g., from OCR or UI) and returns a streaming Excel (.xlsx) file
    using the Reverse Excel Exporter utility. 
    """
    try:
        # Convert Pydantic model to dict for the exporter
        parsed_dict = data.dict(by_alias=True) if hasattr(data, "dict") else data.model_dump(by_alias=True)
        excel_io = generate_excel_from_data(parsed_dict)
        
        headers = {
            'Content-Disposition': 'attachment; filename="exported_bill_data.xlsx"'
        }
        return StreamingResponse(
            excel_io, 
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
            headers=headers
        )
    except Exception as e:
        logger.exception("Excel export failed")
        raise HTTPException(500, f"Failed to generate Excel: {e}")


def _parse_excel(path: Path, file_id: str, filename: str) -> ParsedBillData:
    """
    Parse Excel using the Unified Ingestion Engine (excel_parser -> normalizer)
    and Calculate using the Unified Calculation Engine (bill_processor).
    """
    # 1. Parse & Normalize
    raw_data = parse_excel_to_raw(str(path))
    if raw_data.get("error"):
        raise RuntimeError(f"Excel parse failed: {raw_data['error']}")
    
    unified_doc = normalize_to_unified_model(raw_data)
    
    # 2. Process / Calculate
    calculated = process_unified_bill(unified_doc)
    
    # 3. Map to API response model (ParsedBillData)
    # Note: ParsedBillData is used by the frontend to show the editable table.
    bill_items = []
    for row in unified_doc.rows:
        bill_items.append(BillItem(
            itemNo=str(row.serial_no),
            description=row.description,
            unit=row.unit,
            quantitySince=row.qty_since_last_bill,
            quantityUpto=row.qty_to_date,
            quantity=row.qty_to_date, # Fallback for simple bills
            rate=row.rate,
            amount=row.amount
        ))
    
    extra_items = []
    # Similar mapping for extra items if needed, currently using primary rows
    
    return ParsedBillData(
        fileId=file_id,
        fileName=filename,
        titleData=raw_data.get("metadata", {}),
        billItems=bill_items,
        extraItems=extra_items,
        totalAmount=unified_doc.total_amount,
        hasExtraItems=len(extra_items) > 0,
        sheets=list(raw_data.get("sheets", [])),
        anomaly_warnings=unified_doc.anomaly_warnings
    )


# ── Generate ──────────────────────────────────────────────────────────────────

@router.post("/generate-template")
async def generate_template(req: TemplateRequest):
    """Takes a natural language prompt, runs it against the AI layer, and returns a JSON schema representation."""
    try:
        schema = await asyncio.get_running_loop().run_in_executor(None, generate_template_schema, req.prompt)
        return schema
    except Exception as e:
        logger.exception("Template generation failed")
        raise HTTPException(500, f"AI generation failed: {e}")

@router.post("/generate", response_model=JobStatus)
async def generate_bill(
    req: GenerateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> JobStatus:
    """Enqueue bill document generation via ARQ. Returns job_id immediately."""
    client_ip = request.client.host if request.client else "unknown"

    # Redis-backed rate limiting (works across multiple processes)
    if await is_rate_limited_redis(client_ip):
        raise HTTPException(429, "Too many requests. Please try again later.")

    job_id = str(uuid.uuid4())
    out_dir = _reconstruct_output_dir(job_id)
    out_dir.mkdir(parents=True, exist_ok=True)

    initial_state = {
        "jobId": job_id, "status": "pending", "progress": 0,
        "message": "Queued", "documents": [], "error": None,
        # Note: output_dir is NOT stored in Redis to prevent path traversal
    }

    # Store job state and DB record atomically
    async with aioredis.from_url(_REDIS_URL) as rc:
        await rc.set(f"job:{job_id}", json.dumps(initial_state), ex=86400)

    # Extract work_name from titleData if available (for better history visibility)
    work_name = req.titleData.get("Name of Work") or req.titleData.get("work_name")

    with Session(engine) as session:
        session.add(BillRecord(
            job_id=job_id, user_id=current_user.id,
            status="pending", message="Generation queued", 
            work_name=work_name, total_amount=0.0,
        ))
        session.commit()

    # Enqueue job if Redis is available, otherwise process synchronously
    if hasattr(request.app.state, "redis_pool") and request.app.state.redis_pool:
        await request.app.state.redis_pool.enqueue_job(
            "generate_bill_task", job_id, req.model_dump()
        )
        log_job_event(job_id, "enqueued", f"Request from user '{current_user.username}'")
    else:
        # Fallback: process synchronously if Redis is not available
        logger.warning(f"Redis not available, processing job {job_id} synchronously")
        try:
            from backend.services.bill_generation_service import generate_documents
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, generate_documents, job_id, req, OUTPUT_DIR)
            log_job_event(job_id, "completed", f"Processed synchronously for user '{current_user.username}'")
        except Exception as e:
            logger.error(f"Synchronous processing failed for job {job_id}: {e}")
            update_redis_job(job_id, status="error", error=str(e))
    
    return JobStatus(**initial_state)


# ── Job Status & Download ─────────────────────────────────────────────────────

@router.get("/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    try:
        redis_client = aioredis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), socket_timeout=1)
        data = await redis_client.get(f"job:{job_id}")
        await redis_client.aclose()
        if data:
            job = json.loads(data)
            return JobStatus(**{k: v for k, v in job.items() if k != "output_dir"})
    except Exception:
        pass
    
    # Fallback to DB if Redis is down or job not found there
    with Session(engine) as session:
        record = session.exec(select(BillRecord).where(BillRecord.job_id == job_id)).first()
        if not record:
            raise HTTPException(404, "Job not found")
        return JobStatus(
            jobId=record.job_id,
            status=record.status,
            message=record.message,
            progress=100 if record.status == "complete" else 0,
            documents=[],
            error=None
        )

@router.get("/history")
async def get_history(current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        records = session.exec(select(BillRecord).where(BillRecord.user_id == current_user.id).order_by(BillRecord.created_at.desc())).all()
        return records


@router.get("/jobs/{job_id}/download")
async def download_result(
    job_id: str,
    format: Literal["zip", "pdf", "html"] = "zip",
    current_user: User = Depends(get_current_user),  # REQUIRED: auth gate
) -> StreamingResponse:
    """Download generated documents. Requires authentication and job ownership."""
    async with aioredis.from_url(_REDIS_URL) as rc:
        data = await rc.get(f"job:{job_id}")
    if not data:
        raise HTTPException(404, "Job not found.")

    job = json.loads(data)
    if job.get("status") != "complete":
        raise HTTPException(400, f"Job not complete (status: {job.get("status")}).")

    # Verify ownership via DB (do not trust Redis for authorization)
    with Session(engine) as session:
        record = session.exec(
            select(BillRecord).where(
                BillRecord.job_id == job_id,
                BillRecord.user_id == current_user.id,
            )
        ).first()
        if not record:
            raise HTTPException(403, "You do not have access to this job.")

    # Reconstruct path from trusted job_id — never from Redis-stored data
    out_dir = _reconstruct_output_dir(job_id)

    if format == "zip":
        zip_path = out_dir / "bill_documents.zip"
        if not zip_path.exists():
            raise HTTPException(404, "ZIP archive not found. Job may have failed silently.")
        return StreamingResponse(
            io.BytesIO(zip_path.read_bytes()),
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="bill_{job_id[:8]}.zip"'},
        )

    if format == "pdf":
        pdfs = sorted(out_dir.glob("*.pdf"))
        if not pdfs:
            raise HTTPException(404, "No PDF files found for this job.")
        if len(pdfs) == 1:
            return StreamingResponse(
                io.BytesIO(pdfs[0].read_bytes()),
                media_type="application/pdf",
                headers={"Content-Disposition": f'attachment; filename="{pdfs[0].name}"'},
            )
        # Multiple PDFs → bundle in ZIP
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in pdfs:
                zf.write(p, p.name)
        buf.seek(0)
        return StreamingResponse(
            buf, media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="bills_pdf_{job_id[:8]}.zip"'},
        )

    # format == "html" (guaranteed by Literal type)
    htmls = sorted(out_dir.glob("*.html"))
    if not htmls:
        raise HTTPException(404, "No HTML files found for this job.")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for h in htmls:
            zf.write(h, h.name)
    buf.seek(0)
    return StreamingResponse(
        buf, media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="bills_html_{job_id[:8]}.zip"'},
    )

    raise HTTPException(400, f"Unknown format: {format}")
