"""
Bill Generator FastAPI Backend
Handles Excel parsing, HTML/PDF generation for PWD contractor bills
"""
import os
import sys
import uuid
import asyncio
import zipfile
import io
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Bill Generator API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job store (for MVP — replace with Redis/DB for production)
JOBS: dict = {}

UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
OUTPUT_DIR = Path(__file__).parent.parent / "outputs"
TEMPLATE_DIR = Path(__file__).parent / "templates"

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


# ── Pydantic Models ─────────────────────────────────────────────────────────

class TitleData(BaseModel):
    model_config = {"extra": "allow"}


class BillItem(BaseModel):
    itemNo: str = ""
    description: str = ""
    unit: str = ""
    quantitySince: float = 0
    quantityUpto: float = 0
    quantity: float = 0
    rate: float = 0
    amount: float = 0


class ExtraItem(BaseModel):
    itemNo: str = ""
    bsr: str = ""
    description: str = ""
    quantity: float = 0
    unit: str = ""
    rate: float = 0
    amount: float = 0
    remark: str = ""


class BillData(BaseModel):
    fileId: str
    fileName: str
    titleData: dict
    billItems: list[BillItem]
    extraItems: list[ExtraItem]
    totalAmount: float
    hasExtraItems: bool
    sheets: list[str]


class GenerateOptions(BaseModel):
    generatePdf: bool = True
    generateHtml: bool = True
    generateWord: bool = False


class GenerateRequest(BaseModel):
    fileId: str
    titleData: dict
    billItems: list[BillItem]
    extraItems: list[ExtraItem]
    options: GenerateOptions = Field(default_factory=GenerateOptions)


class DocumentInfo(BaseModel):
    name: str
    format: str
    size: int = 0


class JobStatus(BaseModel):
    jobId: str
    status: str  # pending | processing | complete | error
    progress: float = 0
    message: str = ""
    documents: list[DocumentInfo] = []
    error: Optional[str] = None


# ── Health ────────────────────────────────────────────────────────────────

@app.get("/healthz")
async def health():
    return {"status": "ok"}


# ── Upload & Parse Excel ──────────────────────────────────────────────────

@app.post("/bills/upload", response_model=BillData)
async def upload_excel(file: UploadFile = File(...)):
    """Upload Excel file and extract bill data for preview/editing"""
    if not file.filename:
        raise HTTPException(400, "No file provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in {".xlsx", ".xls", ".xlsm"}:
        raise HTTPException(400, f"Unsupported file type: {ext}. Use .xlsx, .xls, or .xlsm")

    MAX_SIZE = 20 * 1024 * 1024  # 20 MB
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(413, f"File too large ({len(content) // 1024}KB). Max 20MB.")

    file_id = str(uuid.uuid4())
    save_path = UPLOAD_DIR / f"{file_id}{ext}"

    save_path.write_bytes(content)
    logger.info(f"Saved upload {file.filename} → {save_path} ({len(content)} bytes)")

    try:
        data = await asyncio.get_event_loop().run_in_executor(
            None, _parse_excel, save_path, file_id, file.filename
        )
        return data
    except Exception as e:
        logger.exception("Excel parse failed")
        try:
            save_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise HTTPException(500, f"Failed to parse Excel: {str(e)}")


def _parse_excel(path: Path, file_id: str, filename: str) -> BillData:
    """Parse Excel file using the core processor"""
    import pandas as pd

    xl = pd.ExcelFile(str(path))
    sheets = xl.sheet_names
    logger.info(f"Sheets found: {sheets}")

    title_data: dict = {}
    bill_items: list[BillItem] = []
    extra_items: list[ExtraItem] = []
    total_amount = 0.0

    # ── Title Sheet ──────────────────────────────────────────────────────
    title_sheet_candidates = ["Title", "TITLE", "title", "Title Sheet", "Sheet1", "Sheet 1"]
    title_df = None
    for name in title_sheet_candidates:
        if name in sheets:
            title_df = xl.parse(name, header=None)
            break
    if title_df is None and sheets:
        title_df = xl.parse(sheets[0], header=None)

    if title_df is not None:
        title_data = _extract_title_data(title_df)

    # ── Bill Quantity Sheet ──────────────────────────────────────────────
    bill_sheet_candidates = [
        "Bill Quantity", "Bill_Quantity", "BILL QUANTITY", "BillQuantity",
        "Bill", "BILL", "Quantity", "Main", "Data"
    ]
    bill_df = None
    for name in bill_sheet_candidates:
        if name in sheets:
            bill_df = xl.parse(name)
            break

    if bill_df is None:
        # Try the second sheet if title was first
        for sh in sheets:
            if sh not in title_sheet_candidates:
                bill_df = xl.parse(sh)
                break

    if bill_df is not None:
        bill_items, total_amount = _parse_bill_items(bill_df)

    # ── Extra Items Sheet ────────────────────────────────────────────────
    extra_sheet_candidates = [
        "Extra Items", "Extra_Items", "EXTRA ITEMS", "ExtraItems",
        "Extra Item", "Extra", "EXTRA"
    ]
    extra_df = None
    for name in extra_sheet_candidates:
        if name in sheets:
            extra_df = xl.parse(name, header=None)
            break

    if extra_df is not None:
        extra_items = _parse_extra_items(extra_df)

    return BillData(
        fileId=file_id,
        fileName=filename,
        titleData=title_data,
        billItems=bill_items,
        extraItems=extra_items,
        totalAmount=total_amount,
        hasExtraItems=len(extra_items) > 0,
        sheets=sheets,
    )


def _safe_str(val) -> str:
    import pandas as pd
    if val is None or (hasattr(val, '__class__') and val.__class__.__name__ == 'float'):
        try:
            import math
            if math.isnan(float(val)):
                return ""
        except Exception:
            pass
    s = str(val).strip()
    return "" if s in ("nan", "None", "NaT") else s


def _safe_float(val) -> float:
    try:
        v = float(val)
        import math
        return 0.0 if (math.isnan(v) or math.isinf(v)) else v
    except Exception:
        return 0.0


def _extract_title_data(df) -> dict:
    """Extract key-value pairs from title sheet by scanning adjacent cells"""
    import pandas as pd
    result: dict = {}

    key_aliases = {
        "name of work": "Name of Work",
        "contractor": "Contractor",
        "name of contractor": "Contractor",
        "agreement no": "Agreement No",
        "agreement no.": "Agreement No",
        "budget head": "Budget Head",
        "serial no": "Serial No. of this bill :",
        "serial no.": "Serial No. of this bill :",
        "serial no. of this bill": "Serial No. of this bill :",
        "s.no.": "Serial No. of this bill :",
        "amount of work order": "Amount of Work Order",
        "date of start": "Date of Start",
        "stipulated date": "Stipulated Date of Completion",
        "date of completion": "Stipulated Date of Completion",
        "divisional officer": "Divisional Officer",
        "sub-division": "Sub-Division",
        "subdivision": "Sub-Division",
        "tender premium": "Tender Premium %",
        "tender premium %": "Tender Premium %",
    }

    for r in range(len(df)):
        for c in range(len(df.columns) - 1):
            key_raw = _safe_str(df.iloc[r, c])
            val_raw = _safe_str(df.iloc[r, c + 1])
            if key_raw and val_raw:
                normalized = key_raw.lower().rstrip(": ")
                canonical = key_aliases.get(normalized, key_raw)
                if canonical not in result:
                    result[canonical] = val_raw

    # Also try vertical pairs (key in one row, value in next)
    for c in range(len(df.columns)):
        for r in range(len(df) - 1):
            key_raw = _safe_str(df.iloc[r, c])
            val_raw = _safe_str(df.iloc[r + 1, c])
            if key_raw and val_raw:
                normalized = key_raw.lower().rstrip(": ")
                canonical = key_aliases.get(normalized, None)
                if canonical and canonical not in result:
                    result[canonical] = val_raw

    return result


def _parse_bill_items(df) -> tuple[list[BillItem], float]:
    """Parse bill quantity sheet into structured items"""
    import pandas as pd

    items: list[BillItem] = []
    total = 0.0

    # Keep original column names for lookup, build lowercased map
    orig_cols = list(df.columns)
    lower_cols = [_safe_str(c).strip().lower() for c in orig_cols]

    col_map: dict[str, str] = {}  # logical_key → original column name
    for orig, cl in zip(orig_cols, lower_cols):
        if any(x in cl for x in ["item no", "s.no", "item_no", "sno"]) or cl == "item":
            col_map.setdefault("itemNo", orig)
        elif any(x in cl for x in ["description", "particulars", "desc"]):
            col_map.setdefault("description", orig)
        elif any(x in cl for x in ["unit", "uom"]):
            col_map.setdefault("unit", orig)
        elif "since" in cl:
            col_map.setdefault("quantitySince", orig)
        elif "upto" in cl or "up to" in cl:
            col_map.setdefault("quantityUpto", orig)
        elif any(x in cl for x in ["qty", "quantity", "quant"]):
            col_map.setdefault("quantity", orig)
        elif cl == "rate":
            col_map.setdefault("rate", orig)
        elif "amount" in cl or "amt" in cl:
            col_map.setdefault("amount", orig)
        elif cl == "bsr":
            col_map.setdefault("bsr", orig)

    for _, row in df.iterrows():
        item_no_raw = _safe_str(row.get(col_map.get("itemNo", ""), ""))
        bsr = _safe_str(row.get(col_map.get("bsr", ""), ""))
        description = _safe_str(row.get(col_map.get("description", ""), ""))

        # Use BSR code as item number for sub-items (parent rows have integer item nos)
        item_no = item_no_raw
        if not item_no and bsr:
            item_no = bsr

        if not item_no and not description:
            continue

        # Skip total/summary rows
        desc_lower = description.lower()
        if any(kw in desc_lower for kw in ["total", "grand total", "sub total"]):
            amt = _safe_float(row.get(col_map.get("amount", ""), 0))
            if amt > total:
                total = amt
            continue

        qty_since = _safe_float(row.get(col_map.get("quantitySince", ""), 0))
        qty_upto = _safe_float(row.get(col_map.get("quantityUpto", ""), 0))
        qty = _safe_float(row.get(col_map.get("quantity", ""), 0)) or qty_upto or qty_since
        rate = _safe_float(row.get(col_map.get("rate", ""), 0))
        amount = _safe_float(row.get(col_map.get("amount", ""), 0))
        unit = _safe_str(row.get(col_map.get("unit", ""), ""))

        # Compute amount from qty × rate if missing
        if amount == 0 and qty > 0 and rate > 0:
            amount = qty * rate

        # Clean up item number: convert "1.0" → "1" etc.
        if item_no_raw:
            try:
                n = float(item_no_raw)
                if n == int(n):
                    item_no = str(int(n))
            except ValueError:
                pass

        total += amount

        items.append(BillItem(
            itemNo=item_no,
            description=description,
            unit=unit,
            quantitySince=qty_since,
            quantityUpto=qty_upto,
            quantity=qty,
            rate=rate,
            amount=amount,
        ))

    return items, total


def _parse_extra_items(df) -> list[ExtraItem]:
    """Parse extra items sheet"""
    items: list[ExtraItem] = []

    for r in range(len(df)):
        item_no = _safe_str(df.iloc[r, 0]) if df.shape[1] > 0 else ""
        if not (item_no.startswith("E-") or item_no.startswith("e-")):
            continue

        desc = _safe_str(df.iloc[r, 2]) if df.shape[1] > 2 else ""
        bsr = _safe_str(df.iloc[r, 1]) if df.shape[1] > 1 else ""
        qty = _safe_float(df.iloc[r, 3]) if df.shape[1] > 3 else 0
        unit = _safe_str(df.iloc[r, 4]) if df.shape[1] > 4 else ""
        rate = _safe_float(df.iloc[r, 5]) if df.shape[1] > 5 else 0
        amount = _safe_float(df.iloc[r, 6]) if df.shape[1] > 6 else qty * rate
        remark = _safe_str(df.iloc[r, 7]) if df.shape[1] > 7 else bsr

        items.append(ExtraItem(
            itemNo=item_no,
            bsr=bsr,
            description=desc,
            quantity=qty,
            unit=unit,
            rate=rate,
            amount=amount,
            remark=remark or bsr,
        ))

    return items


# ── Generate Bill Documents ───────────────────────────────────────────────

@app.post("/bills/generate", response_model=JobStatus)
async def generate_bill(req: GenerateRequest, background_tasks: BackgroundTasks):
    """Enqueue bill document generation"""
    job_id = str(uuid.uuid4())
    JOBS[job_id] = {
        "jobId": job_id,
        "status": "pending",
        "progress": 0,
        "message": "Queued",
        "documents": [],
        "error": None,
        "output_dir": str(OUTPUT_DIR / job_id),
    }
    background_tasks.add_task(_run_generation, job_id, req)
    return JobStatus(jobId=job_id, status="pending", message="Generation queued")


async def _run_generation(job_id: str, req: GenerateRequest):
    """Background task: generate HTML + PDF documents"""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _generate_documents, job_id, req)


def _generate_documents(job_id: str, req: GenerateRequest):
    """Synchronous generation of HTML and optionally PDF documents"""
    job = JOBS[job_id]
    job["status"] = "processing"
    job["progress"] = 5
    job["message"] = "Preparing data..."

    out_dir = Path(job["output_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        template_data = _build_template_data(req)
        docs: list[DocumentInfo] = []

        job["progress"] = 15
        job["message"] = "Building HTML documents..."

        html_files = _render_html_templates(template_data, out_dir)
        docs.extend([DocumentInfo(name=f.name, format="html", size=f.stat().st_size) for f in html_files])

        job["progress"] = 50

        if req.options.generatePdf:
            job["message"] = "Generating PDFs..."
            pdf_files = _render_pdfs(html_files, out_dir)
            docs.extend([DocumentInfo(name=f.name, format="pdf", size=f.stat().st_size) for f in pdf_files])

        job["progress"] = 85
        job["message"] = "Creating ZIP archive..."
        _create_zip(out_dir)

        job["status"] = "complete"
        job["progress"] = 100
        job["message"] = "Generation complete"
        job["documents"] = [d.model_dump() for d in docs]
        logger.info(f"Job {job_id} complete — {len(docs)} documents")

    except Exception as e:
        logger.exception(f"Job {job_id} failed")
        job["status"] = "error"
        job["error"] = str(e)
        job["message"] = "Generation failed"


def _build_template_data(req: GenerateRequest) -> dict:
    """Build the dict that Jinja2 templates expect"""
    title = dict(req.titleData)

    # ── Bill items sum (only sub-items with qty > 0) ────────────────────────
    def _enrich_item(d: dict) -> dict:
        """Add template-expected aliases to a bill item dict"""
        d["quantity_since_last"] = d.get("quantitySince", 0) or 0
        d["quantity_upto_date"]  = d.get("quantityUpto", 0) or d.get("quantity", 0) or 0
        d["serial_no"]           = d.get("itemNo", "")
        d["bold"]                = False
        d["underline"]           = False
        d["amount_previous"]     = 0.0
        d.setdefault("remark", "")
        return d

    bill_items_dicts = [_enrich_item(item.model_dump()) for item in req.billItems]
    extra_items_dicts = [_enrich_item(item.model_dump()) for item in req.extraItems]
    bill_total = sum(item.amount for item in req.billItems)
    extra_total = sum(item.amount for item in req.extraItems)

    # ── Tender premium ───────────────────────────────────────────────────────
    tender_premium_pct = 0.0
    above_below = "Above"
    try:
        tp = title.get("Tender Premium %", title.get("Tender Premium", "0"))
        tp_str = str(tp).replace("%", "").strip()
        tender_premium_pct = float(tp_str) if tp_str else 0.0
        above_below = str(title.get("Above / Below", title.get("Premium Type", "Above"))).strip()
    except Exception:
        pass

    premium_amount = bill_total * tender_premium_pct / 100
    if above_below.lower() == "below":
        payable = bill_total - premium_amount
    else:
        payable = bill_total + premium_amount

    total_bill_amount = payable + extra_total

    # ── Standard Rajasthan PWD deductions ────────────────────────────────────
    sd_amount   = round(total_bill_amount * 0.10, 2)   # 10% Security Deposit
    it_amount   = round(total_bill_amount * 0.02, 2)   # 2%  Income Tax
    gst_amount  = round(total_bill_amount * 0.02)       # 2%  GST TDS (rounded even)
    if int(gst_amount) % 2 != 0:
        gst_amount += 1
    lc_amount   = round(total_bill_amount * 0.01, 2)   # 1%  Labour Cess
    total_deductions = sd_amount + it_amount + gst_amount + lc_amount

    # ── Last bill amount ─────────────────────────────────────────────────────
    try:
        last_bill_amount = float(str(title.get("Amount Paid Vide Last Bill", "0")).replace(",", "").strip() or 0)
    except Exception:
        last_bill_amount = 0.0

    work_order_amount = 0.0
    try:
        work_order_amount = float(str(title.get("WORK ORDER AMOUNT RS.", "0")).replace(",", "").strip() or 0)
    except Exception:
        pass

    net_payable = total_bill_amount - last_bill_amount

    # ── Totals object (used by templates as data.totals) ─────────────────────
    totals = {
        "work_order_amount":  work_order_amount,
        "last_bill_amount":   last_bill_amount,
        "bill_total":         bill_total,
        "payable":            payable,
        "extra_items_sum":    extra_total,
        "total_bill_amount":  total_bill_amount,
        "sd_amount":          sd_amount,
        "it_amount":          it_amount,
        "gst_amount":         gst_amount,
        "lc_amount":          lc_amount,
        "total_deductions":   total_deductions,
        "net_payable":        net_payable,
        "grand_total":        total_bill_amount,
        "premium": {
            "percent":  tender_premium_pct / 100,
            "amount":   premium_amount,
            "above_below": above_below,
        },
    }

    grand_total = total_bill_amount

    # ── Deviation summary (used by deviation_statement.html) ─────────────────
    net_difference = work_order_amount - total_bill_amount
    summary = {
        "work_order_total":    work_order_amount,
        "executed_total":      total_bill_amount,
        "net_difference":      abs(net_difference),
        "is_saving":           net_difference >= 0,
        "overall_saving":      max(0.0, net_difference),
        "overall_excess":      max(0.0, -net_difference),
        "percentage_deviation": (net_difference / work_order_amount * 100) if work_order_amount else 0,
        "premium":             totals["premium"],
        # Per-category subtotals (f=Civil, h=Plumbing, j=Electrical, l=Misc)
        # Populated as overall until category-tagged items are implemented
        "grand_total_f":       total_bill_amount,
        "grand_total_h":       0.0,
        "grand_total_j":       0.0,
        "grand_total_l":       0.0,
        "tender_premium_f":    premium_amount,
        "tender_premium_h":    0.0,
        "tender_premium_j":    0.0,
        "tender_premium_l":    0.0,
        **totals,   # include all totals fields too
    }

    return {
        # Primary fields used by templates
        "title_data":           title,
        "bill_items":           bill_items_dicts,
        "extra_items":          extra_items_dicts,
        "items":                bill_items_dicts,   # alias: first_page.html uses data["items"]
        "totals":               totals,
        "summary":              summary,             # alias: deviation_statement.html uses data.summary
        # Flat convenience fields
        "bill_total":           bill_total,
        "extra_total":          extra_total,
        "tender_premium_pct":   tender_premium_pct,
        "tender_amount":        premium_amount,
        "above_below":          above_below,
        "grand_total":          grand_total,
        "net_payable":          net_payable,
        "grand_total_words":    _number_to_words(int(grand_total)),
        "net_payable_words":    _number_to_words(int(net_payable)),
        "generated_at":         datetime.now().strftime("%d-%m-%Y %H:%M"),
        "has_extra_items":      len(req.extraItems) > 0,
    }


def _render_html_templates(data: dict, out_dir: Path) -> list[Path]:
    """Render all Jinja2 HTML templates"""
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html"]),
    )

    template_map = {
        "first_page.html": "01_first_page.html",
        "note_sheet_new.html": "02_note_sheet.html",
        "certificate_ii.html": "03_certificate_ii.html",
        "certificate_iii.html": "04_certificate_iii.html",
    }
    if data.get("has_extra_items"):
        template_map["extra_items.html"] = "05_extra_items.html"
        template_map["deviation_statement.html"] = "06_deviation.html"

    rendered: list[Path] = []
    for tmpl_name, out_name in template_map.items():
        tmpl_path = TEMPLATE_DIR / tmpl_name
        if not tmpl_path.exists():
            logger.warning(f"Template missing: {tmpl_name}, skipping")
            continue
        try:
            tmpl = env.get_template(tmpl_name)
            html = tmpl.render(data=data)
            out_file = out_dir / out_name
            out_file.write_text(html, encoding="utf-8")
            rendered.append(out_file)
        except Exception as e:
            logger.warning(f"Failed to render {tmpl_name}: {e}")

    return rendered


def _render_pdfs(html_files: list[Path], out_dir: Path) -> list[Path]:
    """Convert HTML files to PDF using WeasyPrint"""
    pdfs: list[Path] = []
    try:
        from weasyprint import HTML
        for html_file in html_files:
            pdf_name = html_file.stem + ".pdf"
            pdf_path = out_dir / pdf_name
            try:
                HTML(filename=str(html_file)).write_pdf(str(pdf_path))
                pdfs.append(pdf_path)
                logger.info(f"PDF generated: {pdf_path.name}")
            except Exception as e:
                logger.warning(f"PDF failed for {html_file.name}: {e}")
    except ImportError:
        logger.warning("WeasyPrint not available, skipping PDF generation")
    return pdfs


def _create_zip(out_dir: Path) -> Path:
    """Create a zip of all generated documents"""
    zip_path = out_dir / "bill_documents.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in out_dir.glob("*"):
            if f.suffix in {".html", ".pdf", ".docx"} and f.name != "bill_documents.zip":
                zf.write(f, f.name)
    return zip_path


# ── Job Status & Download ─────────────────────────────────────────────────

@app.get("/bills/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return JobStatus(**{k: v for k, v in job.items() if k != "output_dir"})


@app.get("/bills/jobs/{job_id}/download")
async def download_bill_result(job_id: str, format: str = "zip"):
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
        content = zip_path.read_bytes()
        return StreamingResponse(
            io.BytesIO(content),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=bill_{job_id[:8]}.zip"},
        )

    elif format == "pdf":
        pdfs = list(out_dir.glob("*.pdf"))
        if not pdfs:
            raise HTTPException(404, "No PDF files found")
        if len(pdfs) == 1:
            content = pdfs[0].read_bytes()
            return StreamingResponse(
                io.BytesIO(content),
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={pdfs[0].name}"},
            )
        # Multiple PDFs → return zip
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in pdfs:
                zf.write(p, p.name)
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=bills_pdf_{job_id[:8]}.zip"},
        )

    elif format == "html":
        htmls = list(out_dir.glob("*.html"))
        if not htmls:
            raise HTTPException(404, "No HTML files found")
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for h in htmls:
                zf.write(h, h.name)
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=bills_html_{job_id[:8]}.zip"},
        )

    else:
        raise HTTPException(400, f"Unknown format: {format}")


# ── Number to Words (Indian system) ──────────────────────────────────────

def _number_to_words(num: int) -> str:
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
    teens = ["Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen",
             "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

    def below_hundred(n):
        if n == 0: return ""
        if n < 10: return ones[n]
        if n < 20: return teens[n - 10]
        return tens[n // 10] + ("" if n % 10 == 0 else " " + ones[n % 10])

    def below_thousand(n):
        if n == 0: return ""
        if n < 100: return below_hundred(n)
        return ones[n // 100] + " Hundred" + (" " + below_hundred(n % 100) if n % 100 else "")

    if num == 0: return "Zero"
    if num < 0: return "Minus " + _number_to_words(-num)

    parts = []
    if num >= 10_000_000:
        parts.append(below_thousand(num // 10_000_000) + " Crore")
        num %= 10_000_000
    if num >= 100_000:
        parts.append(below_thousand(num // 100_000) + " Lakh")
        num %= 100_000
    if num >= 1_000:
        parts.append(below_thousand(num // 1_000) + " Thousand")
        num %= 1_000
    if num > 0:
        parts.append(below_thousand(num))

    return " ".join(parts) + " Only"


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
