"""
AI Excel Input Route
POST /ai-excel/parse   — upload any Excel, get AI-parsed structured data
POST /ai-excel/commit  — accept edited rows, write to standard pipeline format
"""
import asyncio
import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Any

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-excel", tags=["ai-excel"])

UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


# ── Request / Response models ─────────────────────────────────────────────────

class AIRow(BaseModel):
    itemNo: str = ""
    description: str = ""
    unit: str = ""
    quantity: float = 0.0
    rate: float = 0.0
    amount: float = 0.0
    remark: str = ""
    confidence: float = 1.0
    aiNote: str = ""


class CommitRequest(BaseModel):
    fileId: str
    fileName: str
    titleData: dict[str, Any] = {}
    rows: list[AIRow]
    premiumPercent: float = 0.0
    premiumType: str = "above"


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/parse")
async def parse_excel_ai(
    file: UploadFile = File(...),
    use_llm: bool = False,
):
    """
    Upload any Excel file (haphazard format).
    Returns AI-parsed structured data with column mappings and confidence scores.
    """
    if not file.filename:
        raise HTTPException(400, "No file provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in {".xlsx", ".xls", ".xlsm"}:
        raise HTTPException(400, f"Unsupported file type: {ext}")

    content = await file.read()
    if len(content) > 30 * 1024 * 1024:
        raise HTTPException(413, "File too large (max 30 MB)")

    file_id = str(uuid.uuid4())
    save_path = UPLOAD_DIR / f"{file_id}{ext}"
    save_path.write_bytes(content)
    logger.info(f"AI parse: saved {file.filename} → {save_path}")

    try:
        from services.ai_excel_parser import parse_excel_ai, ai_parse_result_to_dict

        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: parse_excel_ai(save_path, file_id, file.filename, use_llm=use_llm),
        )
        return JSONResponse(content=ai_parse_result_to_dict(result))

    except Exception as e:
        save_path.unlink(missing_ok=True)
        logger.exception("AI Excel parse failed")
        raise HTTPException(500, f"Parse failed: {e}")


@router.post("/commit")
async def commit_rows(req: CommitRequest):
    """
    Accept user-edited rows from the browser table.
    Writes a clean structured JSON that the engine pipeline can consume.
    Returns the same ParsedBillData shape as /bills/upload so the
    existing BillEditor flow works unchanged.
    """
    from models import BillItem, ExtraItem, ParsedBillData

    bill_items = []
    extra_items = []

    for i, row in enumerate(req.rows):
        item = BillItem(
            itemNo=row.itemNo or str(i + 1),
            description=row.description,
            unit=row.unit,
            quantitySince=row.quantity,
            quantityUpto=row.quantity,
            quantity=row.quantity,
            rate=row.rate,
            amount=row.amount,
        )
        bill_items.append(item)

    total = sum(r.amount for r in req.rows)

    return ParsedBillData(
        fileId=req.fileId,
        fileName=req.fileName,
        titleData={str(k): str(v) for k, v in req.titleData.items()},
        billItems=bill_items,
        extraItems=extra_items,
        totalAmount=total,
        hasExtraItems=False,
        sheets=["AI Parsed"],
        anomaly_warnings=[],
    )
