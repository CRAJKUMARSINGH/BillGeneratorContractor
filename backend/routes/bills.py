"""
Bill routes — upload, generate, job status, download.
Thin wrapper: all domain logic lives in engine/.
"""
import asyncio
import io
import logging
import uuid
import zipfile
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from models import (
    BillItem, DocumentInfo, ExtraItem, GenerateRequest,
    JobStatus, ParsedBillData,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/bills", tags=["bills"])

UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
OUTPUT_DIR = Path(__file__).parent.parent / "outputs"
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# In-memory job store (MVP — replace with Redis in Phase 6)
JOBS: dict = {}


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
        data = await asyncio.get_event_loop().run_in_executor(
            None, _parse_excel, save_path, file_id, file.filename
        )
        return data
    except Exception as e:
        save_path.unlink(missing_ok=True)
        logger.exception("Excel parse failed")
        raise HTTPException(500, f"Failed to parse Excel: {e}")


def _parse_excel(path: Path, file_id: str, filename: str) -> ParsedBillData:
    """Parse using engine's EnterpriseExcelProcessor + bill_processor."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "engine"))

    from calculation.excel_processor_enterprise import EnterpriseExcelProcessor
    from calculation.bill_processor import process_bill
    import pandas as pd

    processor = EnterpriseExcelProcessor(sanitize_strings=True, validate_schemas=False)
    result = processor.process_file(
        path,
        sheet_names=["Work Order", "Bill Quantity", "Extra Items"]
    )
    if not result.success:
        raise RuntimeError(f"Excel load failed: {result.errors}")

    sheets = result.data
    ws_wo    = sheets.get("Work Order")
    ws_bq    = sheets.get("Bill Quantity")
    ws_extra = sheets.get("Extra Items", pd.DataFrame())

    if ws_wo is None or ws_bq is None:
        raise RuntimeError("Required sheets (Work Order, Bill Quantity) not found")

    first_page, _, _, extra_items_data, _ = process_bill(
        ws_wo, ws_bq, ws_extra,
        premium_percent=0.0,
        premium_type="above",
        previous_bill_amount=0.0
    )

    # Build title data from header rows
    title_data = {}
    for row in first_page.get("header", []):
        cells = [str(c).strip() for c in row if str(c).strip() and str(c).strip() != "nan"]
        for i, cell in enumerate(cells):
            if i + 1 < len(cells):
                title_data[cell] = cells[i + 1]

    # Convert items to BillItem models
    bill_items = []
    for item in first_page.get("items", []):
        if item.get("is_divider"):
            continue
        try:
            qty = float(item.get("quantity", 0) or 0)
            rate = float(item.get("rate", 0) or 0)
            amount = float(item.get("amount", 0) or 0)
        except (TypeError, ValueError):
            qty = rate = amount = 0.0
        bill_items.append(BillItem(
            itemNo=str(item.get("serial_no", "")),
            description=str(item.get("description", "")),
            unit=str(item.get("unit", "")),
            quantitySince=qty,
            quantityUpto=qty,
            quantity=qty,
            rate=rate,
            amount=amount,
        ))

    extra_items = []
    for item in extra_items_data.get("items", []):
        if item.get("is_divider"):
            continue
        try:
            qty = float(item.get("quantity", 0) or 0)
            rate = float(item.get("rate", 0) or 0)
            amount = float(item.get("amount", 0) or 0)
        except (TypeError, ValueError):
            qty = rate = amount = 0.0
        extra_items.append(ExtraItem(
            itemNo=str(item.get("serial_no", "")),
            bsr=str(item.get("remark", "")),
            description=str(item.get("description", "")),
            quantity=qty,
            unit=str(item.get("unit", "")),
            rate=rate,
            amount=amount,
        ))

    total = first_page.get("totals", {}).get("grand_total", 0) or 0

    return ParsedBillData(
        fileId=file_id,
        fileName=filename,
        titleData=title_data,
        billItems=bill_items,
        extraItems=extra_items,
        totalAmount=float(total),
        hasExtraItems=len(extra_items) > 0,
        sheets=list(sheets.keys()),
    )


# ── Generate ──────────────────────────────────────────────────────────────────

@router.post("/generate", response_model=JobStatus)
async def generate_bill(req: GenerateRequest, background_tasks: BackgroundTasks):
    """Enqueue bill document generation. Returns job_id immediately."""
    job_id = str(uuid.uuid4())
    out_dir = OUTPUT_DIR / job_id
    out_dir.mkdir(parents=True, exist_ok=True)

    JOBS[job_id] = {
        "jobId": job_id,
        "status": "pending",
        "progress": 0,
        "message": "Queued",
        "documents": [],
        "error": None,
        "output_dir": str(out_dir),
    }
    background_tasks.add_task(_run_generation, job_id, req)
    logger.info(f"Job {job_id} queued")
    return JobStatus(jobId=job_id, status="pending", message="Generation queued")


async def _run_generation(job_id: str, req: GenerateRequest):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _generate_documents, job_id, req)


def _generate_documents(job_id: str, req: GenerateRequest):
    """Synchronous generation — calls engine directly."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "engine"))

    from calculation.bill_processor import process_bill
    from model.document import BillDocument
    from rendering.html_renderer_enterprise import (
        EnterpriseHTMLRenderer, RenderConfig, DocumentType
    )
    from rendering.pdf_generator import PDFGenerator
    import pandas as pd

    job = JOBS[job_id]
    out_dir = Path(job["output_dir"])
    opts = req.options

    try:
        job.update(status="processing", progress=10, message="Building document model...")

        # ── Reconstruct DataFrames from edited items ──────────────────────────
        # Build minimal DataFrames that process_bill() can consume
        wo_rows = []
        bq_rows = []
        for item in req.billItems:
            wo_rows.append([
                item.itemNo, item.description, item.unit,
                item.quantityUpto, item.rate, item.amount, ""
            ])
            bq_rows.append([
                item.itemNo, item.description, item.unit,
                item.quantitySince, item.rate, item.amount, ""
            ])

        ws_wo = pd.DataFrame(wo_rows)
        ws_bq = pd.DataFrame(bq_rows)

        extra_rows = []
        for ei in req.extraItems:
            extra_rows.append([
                ei.itemNo, ei.bsr, ei.description,
                ei.quantity, ei.unit, ei.rate, ei.amount, ei.remark
            ])
        ws_extra = pd.DataFrame(extra_rows) if extra_rows else pd.DataFrame()

        # ── Inject title header rows ──────────────────────────────────────────
        header_rows = [[k, v] for k, v in req.titleData.items()]
        # Pad to 19 rows (process_bill reads header as ws_wo.iloc[:19, :7])
        while len(header_rows) < 19:
            header_rows.append(["", ""])
        # Prepend header rows to ws_wo and ws_bq (process_bill starts items at row 21)
        header_df = pd.DataFrame(header_rows[:19])
        spacer = pd.DataFrame([[""] * 7])  # row 20 spacer
        ws_wo = pd.concat([header_df, spacer, ws_wo], ignore_index=True)
        ws_bq = pd.concat([header_df, spacer, ws_bq], ignore_index=True)

        job.update(progress=25, message="Running calculation engine...")

        first_page, _, deviation, extra_items_data, _ = process_bill(
            ws_wo, ws_bq, ws_extra,
            premium_percent=opts.premiumPercent,
            premium_type=opts.premiumType,
            previous_bill_amount=opts.previousBillAmount,
        )

        # ── Build BillDocument ────────────────────────────────────────────────
        from calculation.bill_processor import number_to_words
        payable = float(first_page["totals"].get("payable", 0) or 0)
        net_payable = float(first_page["totals"].get("net_payable", payable) or payable)
        cheque = int(round(payable - (
            round(payable * 0.10) + round(payable * 0.02) +
            (int(round(payable * 0.02 + 0.5)) // 2 * 2) +
            round(payable * 0.01)
        )))

        # Extract metadata from titleData
        td = req.titleData
        def _td(key): return td.get(key, "")

        doc = BillDocument(
            header=header_rows[:19],
            items=first_page.get("items", []),
            totals=first_page.get("totals", {}),
            deviation_items=deviation.get("items", []),
            deviation_summary=deviation.get("summary", {}),
            extra_items=extra_items_data.get("items", []),
            agreement_no=_td("Agreement No.") or _td("Agreement No"),
            name_of_work=_td("Name of Work") or _td("Name of work"),
            name_of_firm=_td("Name of Contractor or supplier") or _td("Contractor"),
            work_order_amount=float(str(_td("WORK ORDER AMOUNT RS.") or "0").replace(",", "") or 0),
            extra_item_amount=float(first_page["totals"].get("extra_items_sum", 0) or 0),
        )

        template_data = doc.to_template_dict()

        job.update(progress=40, message="Rendering HTML templates...")

        # ── Render HTML ───────────────────────────────────────────────────────
        engine_dir = Path(__file__).parent.parent.parent / "engine"
        template_dir = engine_dir / "templates" / opts.templateVersion
        if not template_dir.exists():
            template_dir = engine_dir / "templates" / "v1"

        config = RenderConfig(
            template_dir=template_dir,
            output_dir=out_dir,
            enable_security_checks=True,
            pdf_ready=True,
        )
        renderer = EnterpriseHTMLRenderer(config)

        doc_types = [
            DocumentType.FIRST_PAGE,
            DocumentType.DEVIATION_STATEMENT,
            DocumentType.NOTE_SHEET,
            DocumentType.CERTIFICATE_II,
            DocumentType.CERTIFICATE_III,
            DocumentType.LAST_PAGE,
        ]
        if doc.extra_items:
            doc_types.insert(2, DocumentType.EXTRA_ITEMS)

        html_paths = []
        for i, doc_type in enumerate(doc_types):
            result = renderer.render(doc_type, {"data": template_data},
                                     f"{doc_type.value}.html")
            if result.success:
                html_paths.append(result.output_path)
            job["progress"] = 40 + int(30 * (i + 1) / len(doc_types))

        docs = [DocumentInfo(name=p.name, format="html",
                             size=p.stat().st_size) for p in html_paths]

        # ── Generate PDFs ─────────────────────────────────────────────────────
        if opts.generatePdf and html_paths:
            job.update(progress=72, message="Generating PDFs...")
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
        job.update(progress=92, message="Creating ZIP archive...")
        zip_path = out_dir / "bill_documents.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in out_dir.glob("*"):
                if f.suffix in {".html", ".pdf", ".docx"}:
                    zf.write(f, f.name)

        job.update(
            status="complete", progress=100,
            message="Generation complete",
            documents=[d.model_dump() for d in docs],
        )
        logger.info(f"Job {job_id} complete — {len(docs)} documents")

    except Exception as e:
        logger.exception(f"Job {job_id} failed")
        job.update(status="error", error=str(e), message="Generation failed")


# ── Job Status & Download ─────────────────────────────────────────────────────

@router.get("/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return JobStatus(**{k: v for k, v in job.items() if k != "output_dir"})


@router.get("/jobs/{job_id}/download")
async def download_result(job_id: str, format: str = "zip"):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if job["status"] != "complete":
        raise HTTPException(400, f"Job not complete (status: {job['status']})")

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
