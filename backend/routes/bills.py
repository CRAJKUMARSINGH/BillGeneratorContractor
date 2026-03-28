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

router = APIRouter()
logger = logging.getLogger(__name__)

from backend.models import (
    BillItem, DocumentInfo, ExtraItem, GenerateRequest,
    JobStatus, ParsedBillData, User, BillRecord, TemplateRequest
)
from backend.dependencies import get_current_user
from backend.database import engine
from sqlmodel import Session, select

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
    try:
        sync_redis = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        key = f"job:{job_id}"
        data = sync_redis.get(key)
        if data:
            job_data = json.loads(data)
            job_data.update(kwargs)
            sync_redis.set(key, json.dumps(job_data), ex=86400)
        else:
            sync_redis.set(key, json.dumps(kwargs), ex=86400)
    except Exception as e:
        logger.warning(f"Failed to update Redis job {job_id}: {e}")

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
    safe_name = _sanitize_filename(file.filename, {".xlsx", ".xls", ".xlsm"})
    save_path = UPLOAD_DIR / f"{file_id}_{safe_name}"
    save_path.write_bytes(content)
    logger.info(f"Saved upload {file.filename} → {save_path}")

    try:
        data = await asyncio.get_event_loop().run_in_executor(
            None, _parse_excel, save_path, file_id, file.filename
        )
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
    safe_name = _sanitize_filename(file.filename, {".png", ".jpg", ".jpeg", ".pdf"})
    save_path = UPLOAD_DIR / f"{file_id}_{safe_name}"
    save_path.write_bytes(content)
    logger.info(f"Saved image upload {file.filename} → {save_path}")

    try:
        import sys
        root_dir = Path(__file__).parent.parent.parent
        if str(root_dir) not in sys.path:
            sys.path.insert(0, str(root_dir))
        
        from ingestion.ocr_extractor import extract_table_from_image
        from ingestion.normalizer import normalize_to_unified_model

        raw_data = await asyncio.get_event_loop().run_in_executor(None, extract_table_from_image, str(save_path))
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
    This fulfills Option B of the Human-in-the-Loop OCR Refinement strategy.
    """
    import sys
    root_dir = Path(__file__).parent.parent.parent
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))
        
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


def _parse_excel(path: Path, file_id: str, filename: str) -> ParsedBillData:
    """
    Parse Excel using the Unified Ingestion Engine (excel_parser -> normalizer)
    and Calculate using the Unified Calculation Engine (bill_processor).
    """
    import sys
    from pathlib import Path
    root_dir = Path(__file__).parent.parent.parent
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))

    from ingestion.excel_parser import parse_excel_to_raw
    from ingestion.normalizer import normalize_to_unified_model
    from engine.calculation.bill_processor import process_unified_bill

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
            quantity=row.qty_to_date,
            rate=row.rate,
            amount=row.amount
        ))

    return ParsedBillData(
        fileId=file_id,
        fileName=filename,
        titleData=unified_doc.raw_metadata,
        billItems=bill_items,
        extraItems=[], # Handled within billItems or separately depending on frontend logic
        totalAmount=unified_doc.total_amount,
        hasExtraItems=bool(unified_doc.raw_metadata.get('has_extra_items', False)),
        sheets=unified_doc.raw_metadata.get('raw_sheet_names', ["Sheet1"])
    )


# ── Generate ──────────────────────────────────────────────────────────────────

@router.post("/generate-template")
async def generate_template(req: TemplateRequest):
    """Takes a natural language prompt, runs it against the AI layer, and returns a JSON schema representation."""
    import sys
    root_dir = Path(__file__).parent.parent.parent
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))
    
    from ingestion.template_generator import generate_template_schema
    
    try:
        schema = await asyncio.get_event_loop().run_in_executor(None, generate_template_schema, req.prompt)
        return schema
    except Exception as e:
        logger.exception("Template generation failed")
        raise HTTPException(500, f"AI generation failed: {e}")

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
    redis_client = aioredis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    await redis_client.set(f"job:{job_id}", json.dumps(initial_job_state), ex=86400)
    await redis_client.aclose()
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
    """
    Synchronous generation — transforms GenerateRequest (UI edits) into 
    UnifiedDocumentModel and runs the unified calculation/rendering pipeline.
    """
    import sys
    from pathlib import Path
    root_dir = Path(__file__).parent.parent.parent
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))

    from ingestion.models import UnifiedDocumentModel, DocumentRow
    from engine.calculation.bill_processor import process_unified_bill
    from engine.rendering.html_renderer_enterprise import (
        EnterpriseHTMLRenderer, RenderConfig, DocumentType
    )
    from engine.rendering.pdf_generator import PDFGenerator

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

    try:
        update_redis_job(job_id, status="processing", progress=10, message="Syncing document model...")
        update_db_status("processing", "Syncing document model...")

        # 1. Map GenerateRequest -> UnifiedDocumentModel
        # This keeps UI data consistent with the engine's internal schema
        doc_rows = []
        for item in req.billItems:
            doc_rows.append(DocumentRow(
                serial_no=item.itemNo,
                description=item.description,
                unit=item.unit,
                qty_since_last_bill=item.quantitySince,
                qty_to_date=item.quantityUpto,
                rate=item.rate,
                amount=item.amount
            ))
            
        for ei in req.extraItems:
            doc_rows.append(DocumentRow(
                serial_no=ei.itemNo,
                description=ei.description,
                unit=ei.unit,
                qty_since_last_bill=ei.quantity,
                qty_to_date=ei.quantity,
                rate=ei.rate,
                amount=ei.amount,
                remarks=ei.bsr or ei.remark or "Extra Item"
            ))

        # Inject UI options into metadata for the processor
        metadata = req.titleData.copy()
        metadata['tender_premium_percentage'] = opts.premiumPercent
        metadata['last_bill_deduction'] = opts.previousBillAmount
        metadata['has_extra_items'] = len(req.extraItems) > 0

        unified_doc = UnifiedDocumentModel(
            document_id=job_id,
            source_type="ui_edit",
            raw_metadata=metadata,
            rows=doc_rows,
            total_amount=sum(r.amount for r in doc_rows)
        )

        update_redis_job(job_id, progress=30, message="Running unified calculation engine...")

        # 2. Run Unified Calculation
        calculated_data = process_unified_bill(unified_doc)
        payable = calculated_data['totals']['payable']
        
        update_db_status("processing", "Calculation complete", payable)

        update_redis_job(job_id, progress=50, message="Rendering high-fidelity templates...")

        # 3. Render HTML using v2 templates
        # We explicitly use v2 for the unified consolidated app
        config = RenderConfig(
            template_dir=root_dir / "engine" / "templates" / "v2",
            output_dir=out_dir,
            enable_security_checks=True,
            pdf_ready=True,
        )
        renderer = EnterpriseHTMLRenderer(config)

        doc_types = [
            DocumentType.FIRST_PAGE,
            DocumentType.NOTE_SHEET,
            DocumentType.DEVIATION_STATEMENT,
            DocumentType.EXTRA_ITEMS,
            DocumentType.CERTIFICATES,
            DocumentType.LAST_PAGE,
        ]

        html_paths = []
        for i, doc_type in enumerate(doc_types):
            # Pass correct sub-data context based on document type
            if doc_type == DocumentType.DEVIATION_STATEMENT:
                template_context = {"data": calculated_data["deviation"], "metadata": calculated_data["metadata"]}
            elif doc_type == DocumentType.EXTRA_ITEMS:
                template_context = {"data": calculated_data["extra_items"], "metadata": calculated_data["metadata"]}
            else:
                template_context = {"data": calculated_data, "metadata": calculated_data["metadata"]}

            result = renderer.render(doc_type, template_context, f"{doc_type.value}.html")
            if result.success:
                html_paths.append(result.output_path)
            update_redis_job(job_id, progress=50 + int(20 * (i + 1) / len(doc_types)))

        docs = [DocumentInfo(name=p.name, format="html", size=p.stat().st_size) for p in html_paths]

        # ── Generate PDFs ─────────────────────────────────────────────────────
        if opts.generatePdf and html_paths:
            update_redis_job(job_id, progress=72, message="Generating PDFs...")
            pdf_gen = PDFGenerator(orientation="portrait")
            for html_path in html_paths:
                pdf_path = out_dir / (html_path.stem + ".pdf")
                html_content = html_path.read_text(encoding="utf-8")
                try:
                    engine_used = pdf_gen.generate_with_fallback(
                        html_content, str(pdf_path)
                    )
                    docs.append(DocumentInfo(
                        name=pdf_path.name, format="pdf",
                        size=pdf_path.stat().st_size
                    ))
                    logger.info(f"PDF [{engine_used}] → {pdf_path.name}")
                except Exception as e:
                    logger.warning(f"PDF failed for {html_path.name}: {e}")

        # ── ZIP ───────────────────────────────────────────────────────────────
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
        update_db_status("complete", "Generation complete")
        log_job_event(job_id, "job completed", f"{len(docs)} documents generated")

    except Exception as e:
        update_db_status("error", f"Generation failed: {e}")
        log_job_event(job_id, "job failed", str(e))
        update_redis_job(job_id, status="error", error=str(e), message="Generation failed")


# ── Job Status & Download ─────────────────────────────────────────────────────

@router.get("/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    redis_client = aioredis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    data = await redis_client.get(f"job:{job_id}")
    await redis_client.aclose()
    
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
async def download_result(job_id: str, format: str = "zip"):
    redis_client = aioredis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    data = await redis_client.get(f"job:{job_id}")
    await redis_client.aclose()
    
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
