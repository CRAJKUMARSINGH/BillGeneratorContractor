"""Bills API router — upload, generate, job status, download"""
import asyncio
import io
import logging
import uuid
import zipfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.config import settings
from app.engine.models import (
    BillItem, DocumentInfo, ExtraItem, GenerateOptions, JobStatus, UnifiedDocument,
)
from app.engine.parsers.excel import parse_excel
from app.engine.calculator.engine import calculate
from app.engine.renderer.html import render_html
from app.engine.renderer.pdf import render_pdf

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory job store (MVP — swap for Redis/ARQ in Phase 7)
JOBS: dict = {}


# ── Request / Response models ─────────────────────────────────────────────

class BillData(BaseModel):
    fileId: str
    fileName: str
    titleData: dict
    billItems: list[BillItem]
    extraItems: list[ExtraItem]
    totalAmount: float
    hasExtraItems: bool
    sheets: list[str]


class GenerateRequest(BaseModel):
    fileId: str
    titleData: dict
    billItems: list[BillItem]
    extraItems: list[ExtraItem]
    options: GenerateOptions = Field(default_factory=GenerateOptions)


# ── Upload ────────────────────────────────────────────────────────────────

@router.post("/upload", response_model=BillData)
async def upload_excel(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(400, "No file provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in {".xlsx", ".xls", ".xlsm"}:
        raise HTTPException(400, f"Unsupported file type: {ext}")

    content = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(413, f"File too large. Max {settings.max_upload_mb}MB.")

    file_id = str(uuid.uuid4())
    save_path = settings.upload_dir / f"{file_id}{ext}"
    save_path.write_bytes(content)
    logger.info(f"Saved {file.filename} → {save_path} ({len(content)} bytes)")

    try:
        doc: UnifiedDocument = await asyncio.get_event_loop().run_in_executor(
            None, parse_excel, save_path, file_id, file.filename
        )
    except Exception as e:
        logger.exception("Excel parse failed")
        save_path.unlink(missing_ok=True)
        raise HTTPException(500, f"Failed to parse Excel: {e}")

    return BillData(
        fileId=doc.fileId,
        fileName=doc.fileName,
        titleData=doc.titleData,
        billItems=doc.billItems,
        extraItems=doc.extraItems,
        totalAmount=doc.totalAmount,
        hasExtraItems=doc.hasExtraItems,
        sheets=doc.sheets,
    )


# ── Generate ──────────────────────────────────────────────────────────────

@router.post("/generate", response_model=JobStatus)
async def generate_bill(req: GenerateRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    out_dir = settings.output_dir / job_id
    JOBS[job_id] = {
        "jobId": job_id, "status": "pending", "progress": 0,
        "message": "Queued", "documents": [], "error": None,
        "output_dir": str(out_dir),
    }
    background_tasks.add_task(_run_generation, job_id, req)
    return JobStatus(jobId=job_id, status="pending", message="Generation queued")


async def _run_generation(job_id: str, req: GenerateRequest):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _generate_sync, job_id, req)


def _generate_sync(job_id: str, req: GenerateRequest):
    job = JOBS[job_id]
    job.update({"status": "processing", "progress": 5, "message": "Preparing data..."})
    out_dir = Path(job["output_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        doc = UnifiedDocument(
            fileId=req.fileId, fileName="",
            titleData=req.titleData,
            billItems=req.billItems,
            extraItems=req.extraItems,
        )
        doc.recompute_totals()
        template_data = calculate(doc)

        job.update({"progress": 15, "message": "Rendering HTML..."})
        html_files = render_html(template_data, out_dir)
        docs = [DocumentInfo(name=f.name, format="html", size=f.stat().st_size) for f in html_files]

        job["progress"] = 50
        if req.options.generatePdf:
            job["message"] = "Generating PDFs..."
            pdf_files = render_pdf(html_files, out_dir)
            docs += [DocumentInfo(name=f.name, format="pdf", size=f.stat().st_size) for f in pdf_files]

        job.update({"progress": 85, "message": "Creating ZIP..."})
        _create_zip(out_dir)

        job.update({
            "status": "complete", "progress": 100,
            "message": "Done", "documents": [d.model_dump() for d in docs],
        })
        logger.info(f"Job {job_id} complete — {len(docs)} docs")

    except Exception as e:
        logger.exception(f"Job {job_id} failed")
        job.update({"status": "error", "error": str(e), "message": "Generation failed"})


def _create_zip(out_dir: Path) -> Path:
    zip_path = out_dir / "bill_documents.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in out_dir.glob("*"):
            if f.suffix in {".html", ".pdf"} and f.name != "bill_documents.zip":
                zf.write(f, f.name)
    return zip_path


# ── Job status ────────────────────────────────────────────────────────────

@router.get("/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return JobStatus(**{k: v for k, v in job.items() if k != "output_dir"})


# ── Download ──────────────────────────────────────────────────────────────

@router.get("/jobs/{job_id}/download")
async def download(job_id: str, format: str = "zip"):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if job["status"] != "complete":
        raise HTTPException(400, f"Job not complete (status: {job['status']})")

    out_dir = Path(job["output_dir"])

    if format == "zip":
        zip_path = out_dir / "bill_documents.zip"
        if not zip_path.exists():
            zip_path = _create_zip(out_dir)
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
