"""
Bill routes — upload, generate, job status, download.
Thin wrapper: all domain logic lives in engine/.
"""
import asyncio
import io
import logging
import uuid
import zipfile
import time
from datetime import datetime
from collections import defaultdict
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Request
from fastapi.responses import StreamingResponse
import redis.asyncio as aioredis
import redis
import os
import json

from models import (
    BillItem, DocumentInfo, ExtraItem, GenerateRequest,
    JobStatus, ParsedBillData, User, BillRecord, TemplateRequest,
    PreviewRequest, PreviewResponse
)
from utils.preview_annotator import annotate_preview_html
from dependencies import get_current_user
from engine.rendering.html_renderer_enterprise import EnterpriseHTMLRenderer, DocumentType, RenderConfig
from database import engine
from sqlmodel import Session, select

logger = logging.getLogger(__name__)
from services.bill_service import BillService

router = APIRouter(prefix="/bills", tags=["bills"])

UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
OUTPUT_DIR = Path(__file__).parent.parent / "outputs"
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Helper for synchronous workers modifying job progress in Redis
def update_redis_job(job_id: str, **kwargs):
    sync_redis = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"))
    key = f"job:{job_id}"
    data = sync_redis.get(key)
    if data:
        job_data = json.loads(data)
        job_data.update(kwargs)
        sync_redis.set(key, json.dumps(job_data), ex=86400)
    else:
        sync_redis.set(key, json.dumps(kwargs), ex=86400)

# Simple in-memory rate limiter for job creation
RATE_LIMIT_STORE = defaultdict(list)
RATE_LIMIT_MAX_REQUESTS = 10  # max 10 requests
RATE_LIMIT_WINDOW_SEC = 60    # per minute

def is_rate_limited(ip: str) -> bool:
    now = time.time()
    RATE_LIMIT_STORE[ip] = [t for t in RATE_LIMIT_STORE[ip] if now - t < RATE_LIMIT_WINDOW_SEC]
    if len(RATE_LIMIT_STORE[ip]) >= RATE_LIMIT_MAX_REQUESTS:
        return True
    RATE_LIMIT_STORE[ip].append(now)
    return False

def log_job_event(job_id: str, stage: str, message: str):
    timestamp = datetime.now().isoformat()
    # Exact format required: timestamp | job_id | stage | message
    logger.info(f"{timestamp} | {job_id} | {stage} | {message}")


# ── Upload & Parse ────────────────────────────────────────────────────────────

@router.post("/upload", response_model=ParsedBillData)
async def upload_excel(file: UploadFile = File(...)):
    """Upload Excel file, parse it, return structured data for editing."""
    if not file.filename:
        raise HTTPException(400, "No file provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in {".xlsx", ".xls", ".xlsm"}:
        raise HTTPException(400, f"Unsupported file type: {ext}")

    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(413, "File too large. Max 20 MB.")

    file_id = str(uuid.uuid4())
    save_path = UPLOAD_DIR / f"{file_id}{ext}"
    save_path.write_bytes(content)
    logger.info(f"Saved upload {file.filename} → {save_path}")

    try:
        from services.ingestion_service import IngestionService
        data = await IngestionService.process_file(save_path, file_id, file.filename)
        
        # Phase 12: Integrate Anomaly Detector
        from ingestion.anomaly_detector import extract_features, detect_anomalies
        rows_for_features = [{"rate": item.rate, "quantity": item.quantity, "amount": item.amount} for item in data.billItems]
        features = extract_features(rows_for_features)
        data.anomaly_warnings = detect_anomalies(features)
        
        return data
    except Exception as e:
        save_path.unlink(missing_ok=True)
        logger.exception("Excel parse failed")
        raise HTTPException(500, f"Failed to parse Excel: {e}")

@router.post("/upload-image", response_model=ParsedBillData)
async def upload_image(file: UploadFile = File(...)):
    """Upload an image (scanned handwritten bill), run OCR, return structured data."""
    if not file.filename:
        raise HTTPException(400, "No file provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in {".png", ".jpg", ".jpeg", ".pdf"}:
        raise HTTPException(400, f"Unsupported image type: {ext}")

    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(413, "File too large. Max 20 MB.")

    file_id = str(uuid.uuid4())
    save_path = UPLOAD_DIR / f"{file_id}{ext}"
    save_path.write_bytes(content)
    logger.info(f"Saved image upload {file.filename} → {save_path}")

    try:
        from services.ingestion_service import IngestionService
        data = await IngestionService.process_file(save_path, file_id, file.filename)
        
        # Phase 12: Integrate Anomaly Detector for OCR
        from ingestion.anomaly_detector import extract_features, detect_anomalies
        rows_for_features = [{"rate": item.rate, "quantity": item.quantity, "amount": item.amount} for item in data.billItems]
        features = extract_features(rows_for_features)
        data.anomaly_warnings = detect_anomalies(features)

        return data

    except Exception as e:
        logger.exception("OCR parse failed")
        save_path.unlink(missing_ok=True)
        raise HTTPException(500, f"Failed to run OCR on image: {e}")


@router.post("/export-excel")
async def export_excel(data: ParsedBillData):
    """
    Accepts ParsedBillData (e.g., from OCR or UI) and returns a streaming Excel (.xlsx) file
    using the Reverse Excel Exporter utility. 
    This fulfills Option B of the Human-in-the-Loop OCR Refinement strategy.
    """
    from ingestion.excel_exporter import generate_excel_from_data
    
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



# legacy _parse_excel removed, replaced by services.ingestion_service.IngestionService

# legacy _parse_excel removed, replaced by services.ingestion_service.IngestionService


# ── Generate ──────────────────────────────────────────────────────────────────

@router.post("/generate-template")
async def generate_template(req: TemplateRequest):
    """Takes a natural language prompt, runs it against the AI layer, and returns a JSON schema representation."""
    from ingestion.template_generator import generate_template_schema
    
    try:
        schema = await asyncio.get_event_loop().run_in_executor(None, generate_template_schema, req.prompt)
        return schema
    except Exception as e:
        logger.exception("Template generation failed")
        raise HTTPException(500, f"AI generation failed: {e}")

@router.post("/preview", response_model=PreviewResponse)
def preview_document(req: PreviewRequest, current_user: User = Depends(get_current_user)):
    """Synchronously render a single document type to HTML for browser preview."""
    # Validate document_type against the enum
    try:
        doc_type = DocumentType(req.document_type)
    except ValueError:
        valid = [dt.value for dt in DocumentType]
        raise HTTPException(
            status_code=422,
            detail=f"Invalid document_type '{req.document_type}'. Must be one of: {valid}"
        )

    # Build template_data using the unified service logic
    from services.bill_service import BillService
    template_data = BillService.prepare_template_data(req.model_dump())

    config = RenderConfig(
        pdf_ready=True,
        template_dir=Path("engine/templates") / req.options.templateVersion,
        output_dir=Path("backend/outputs/preview"),
        enable_security_checks=True,
    )
    renderer = EnterpriseHTMLRenderer(config)

    result = renderer.render(doc_type, template_data)

    if not result.success:
        raise HTTPException(status_code=500, detail=f"Render failed: {result.errors}")

    annotated_html = annotate_preview_html(result.html_content, req.document_type)
    return PreviewResponse(document_type=req.document_type, html=annotated_html)


@router.post("/generate", response_model=JobStatus)
async def generate_bill(req: GenerateRequest, request: Request, current_user: User = Depends(get_current_user)):
    """Enqueue bill document generation via ARQ. Returns job_id immediately."""
    client_ip = request.client.host if request.client else "unknown"
    if is_rate_limited(client_ip):
        raise HTTPException(status_code=429, detail="Too many job creation requests. Please try again later.")

    job_id = str(uuid.uuid4())
    out_dir = OUTPUT_DIR / job_id
    out_dir.mkdir(parents=True, exist_ok=True)

    initial_job_state = {
        "jobId": job_id,
        "status": "pending",
        "progress": 0,
        "message": "Queued",
        "documents": [],
        "error": None,
        "output_dir": str(out_dir),
    }

    # Initialize job in Redis
    await request.app.state.redis_client.set(f"job:{job_id}", json.dumps(initial_job_state), ex=86400)
    
    with Session(engine) as session:
        bill_record = BillRecord(
            job_id=job_id,
            user_id=current_user.id,
            status="pending",
            message="Generation queued",
            total_amount=0.0
        )
        session.add(bill_record)
        session.commit()

    await request.app.state.redis_pool.enqueue_job("generate_bill_task", job_id, req.model_dump())
    log_job_event(job_id, "request received", f"Generate req received from {current_user.username}")
    log_job_event(job_id, "job enqueued", "Job pushed to ARQ worker queue")
    return JobStatus(**initial_job_state)


def _generate_documents(job_id: str, req: GenerateRequest):
    """Synchronous generation — calls engine directly."""
    from engine.calculation.bill_processor import process_bill
    from engine.model.document import BillDocument
    from engine.rendering.html_renderer_enterprise import (
        EnterpriseHTMLRenderer, RenderConfig, DocumentType
    )
    from engine.rendering.pdf_generator import PDFGenerator
    import pandas as pd

    out_dir = OUTPUT_DIR / job_id
    opts = req.options

    def update_db_status(status_str, message_str, amount=None):
        with Session(engine) as session:
            record = session.exec(select(BillRecord).where(BillRecord.job_id == job_id)).first()
            if record:
                record.status = status_str
                record.message = message_str
                if amount is not None:
                    record.total_amount = amount
                session.add(record)
                session.commit()

    async def _redis_progress_cb(jid: str, progress: int, message: str):
        update_redis_job(jid, progress=progress, message=message)

    try:
        update_redis_job(job_id, status="processing", progress=10, message="Service-layer orchestration started...")
        update_db_status("processing", "Service-layer orchestration started...")

        # Orchestrate via BillService (async API; run from sync worker context)
        docs, data_hash = asyncio.run(
            BillService.process_generation(job_id, req.model_dump(), _redis_progress_cb)
        )

        # ZIP ───────────────────────────────────────────────────────────────
        out_dir = OUTPUT_DIR / job_id
        update_redis_job(job_id, progress=92, message="Creating ZIP archive...")
        zip_path = out_dir / "bill_documents.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in out_dir.glob("*"):
                if f.suffix in {".html", ".pdf", ".docx"}:
                    zf.write(f, f.name)

        update_redis_job(
            job_id,
            status="complete", progress=100,
            message="Generation complete",
            documents=[d.model_dump() for d in docs],
        )
        
        # Save to DB with hash
        with Session(engine) as session:
            record = session.exec(select(BillRecord).where(BillRecord.job_id == job_id)).first()
            if record:
                record.status = "complete"
                record.message = "Generation complete"
                record.data_hash = data_hash
                session.add(record)
                session.commit()

        log_job_event(job_id, "job completed", f"{len(docs)} documents generated with hash {data_hash[:8]}")

    except Exception as e:
        update_db_status("error", f"Generation failed: {e}")
        log_job_event(job_id, "job failed", str(e))
        update_redis_job(job_id, status="error", error=str(e), message="Generation failed")


# ── Job Status & Download ─────────────────────────────────────────────────────

@router.get("/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str, request: Request, current_user: User = Depends(get_current_user)):
    # Verify ownership in DB first
    with Session(engine) as session:
        record = session.exec(
            select(BillRecord).where(BillRecord.job_id == job_id)
        ).first()
        if not record:
            raise HTTPException(404, "Job record not found")
        if record.user_id != current_user.id:
            raise HTTPException(403, "Access denied: You do not own this job")

    data = await request.app.state.redis_client.get(f"job:{job_id}")
    
    if not data:
        raise HTTPException(404, "Job not found in queue")
    
    job = json.loads(data)
    return JobStatus(**{k: v for k, v in job.items() if k != "output_dir"})

@router.get("/history")
async def get_history(current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        records = session.exec(select(BillRecord).where(BillRecord.user_id == current_user.id).order_by(BillRecord.created_at.desc())).all()
        return records


@router.get("/jobs/{job_id}/download")
async def download_result(job_id: str, request: Request, format: str = "zip", current_user: User = Depends(get_current_user)):
    # Verify ownership in DB
    with Session(engine) as session:
        record = session.exec(
            select(BillRecord).where(BillRecord.job_id == job_id)
        ).first()
        if not record:
            raise HTTPException(404, "Job record not found")
        if record.user_id != current_user.id:
            raise HTTPException(403, "Access denied: You do not own this job")

    data = await request.app.state.redis_client.get(f"job:{job_id}")
    
    if not data:
        raise HTTPException(404, "Job not found")
        
    job = json.loads(data)
    if job.get("status") != "complete":
        raise HTTPException(400, f"Job not complete (status: {job.get('status')})")

    out_dir = Path(job["output_dir"])

    if format == "zip":
        zip_path = out_dir / "bill_documents.zip"
        if not zip_path.exists():
            raise HTTPException(404, "ZIP not found")
        return StreamingResponse(
            io.BytesIO(zip_path.read_bytes()),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=bill_{job_id[:8]}.zip"},
        )

    if format == "pdf":
        pdfs = list(out_dir.glob("*.pdf"))
        if not pdfs:
            raise HTTPException(404, "No PDFs found")
        if len(pdfs) == 1:
            return StreamingResponse(
                io.BytesIO(pdfs[0].read_bytes()),
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={pdfs[0].name}"},
            )
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in pdfs:
                zf.write(p, p.name)
        buf.seek(0)
        return StreamingResponse(buf, media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=bills_pdf_{job_id[:8]}.zip"})

    if format == "html":
        htmls = list(out_dir.glob("*.html"))
        if not htmls:
            raise HTTPException(404, "No HTML files found")
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for h in htmls:
                zf.write(h, h.name)
        buf.seek(0)
        return StreamingResponse(buf, media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=bills_html_{job_id[:8]}.zip"})

    raise HTTPException(400, f"Unknown format: {format}")
