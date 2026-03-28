"""Excel parser — migrated from artifacts/bill-api/src/main.py with improvements"""
from __future__ import annotations
import math
import logging
from pathlib import Path
from typing import Optional

from app.engine.models import BillItem, ExtraItem, UnifiedDocument, DocumentState

logger = logging.getLogger(__name__)


def _safe_str(val) -> str:
    if val is None:
        return ""
    try:
        if math.isnan(float(val)):
            return ""
    except (TypeError, ValueError):
        pass
    s = str(val).strip()
    return "" if s in ("nan", "None", "NaT") else s


def _safe_float(val) -> float:
    try:
        v = float(val)
        return 0.0 if (math.isnan(v) or math.isinf(v)) else v
    except (TypeError, ValueError):
        return 0.0


_KEY_ALIASES: dict[str, str] = {
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
    "work order amount rs.": "WORK ORDER AMOUNT RS.",
    "amount paid vide last bill": "Amount Paid Vide Last Bill",
    "above / below": "Above / Below",
}


def _extract_title(df) -> dict:
    result: dict = {}
    for r in range(len(df)):
        for c in range(len(df.columns) - 1):
            k = _safe_str(df.iloc[r, c])
            v = _safe_str(df.iloc[r, c + 1])
            if k and v:
                canon = _KEY_ALIASES.get(k.lower().rstrip(": "), k)
                result.setdefault(canon, v)
    # vertical pairs
    for c in range(len(df.columns)):
        for r in range(len(df) - 1):
            k = _safe_str(df.iloc[r, c])
            v = _safe_str(df.iloc[r + 1, c])
            if k and v:
                canon = _KEY_ALIASES.get(k.lower().rstrip(": "))
                if canon:
                    result.setdefault(canon, v)
    return result


def _parse_bill_items(df) -> tuple[list[BillItem], float]:
    items: list[BillItem] = []
    total = 0.0
    orig_cols = list(df.columns)
    lower_cols = [_safe_str(c).strip().lower() for c in orig_cols]

    col_map: dict[str, str] = {}
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
        item_no = item_no_raw or bsr

        if not item_no and not description:
            continue

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

        if amount == 0 and qty > 0 and rate > 0:
            amount = round(qty * rate, 2)

        if item_no_raw:
            try:
                n = float(item_no_raw)
                if n == int(n):
                    item_no = str(int(n))
            except ValueError:
                pass

        total += amount
        items.append(BillItem(
            itemNo=item_no, description=description, unit=unit,
            quantitySince=qty_since, quantityUpto=qty_upto,
            quantity=qty, rate=rate, amount=amount,
        ))

    return items, total


def _parse_extra_items(df) -> list[ExtraItem]:
    items: list[ExtraItem] = []
    for r in range(len(df)):
        item_no = _safe_str(df.iloc[r, 0]) if df.shape[1] > 0 else ""
        if not (item_no.upper().startswith("E-")):
            continue
        bsr = _safe_str(df.iloc[r, 1]) if df.shape[1] > 1 else ""
        desc = _safe_str(df.iloc[r, 2]) if df.shape[1] > 2 else ""
        qty = _safe_float(df.iloc[r, 3]) if df.shape[1] > 3 else 0
        unit = _safe_str(df.iloc[r, 4]) if df.shape[1] > 4 else ""
        rate = _safe_float(df.iloc[r, 5]) if df.shape[1] > 5 else 0
        amount = _safe_float(df.iloc[r, 6]) if df.shape[1] > 6 else round(qty * rate, 2)
        remark = _safe_str(df.iloc[r, 7]) if df.shape[1] > 7 else bsr
        items.append(ExtraItem(
            itemNo=item_no, bsr=bsr, description=desc,
            quantity=qty, unit=unit, rate=rate,
            amount=amount, remark=remark or bsr,
        ))
    return items


def parse_excel(path: Path, file_id: str, filename: str) -> UnifiedDocument:
    """Parse Excel file into UnifiedDocument"""
    import pandas as pd

    xl = pd.ExcelFile(str(path))
    sheets: list[str] = xl.sheet_names
    logger.info(f"Parsing {filename}: sheets={sheets}")

    # Title
    title_candidates = ["Title", "TITLE", "title", "Title Sheet", "Sheet1", "Sheet 1"]
    title_df = None
    for name in title_candidates:
        if name in sheets:
            title_df = xl.parse(name, header=None)
            break
    if title_df is None and sheets:
        title_df = xl.parse(sheets[0], header=None)
    title_data = _extract_title(title_df) if title_df is not None else {}

    # Bill Quantity
    bill_candidates = [
        "Bill Quantity", "Bill_Quantity", "BILL QUANTITY", "BillQuantity",
        "Bill", "BILL", "Quantity", "Main", "Data",
    ]
    bill_df = None
    for name in bill_candidates:
        if name in sheets:
            bill_df = xl.parse(name)
            break
    if bill_df is None:
        for sh in sheets:
            if sh not in title_candidates:
                bill_df = xl.parse(sh)
                break

    bill_items, total_amount = _parse_bill_items(bill_df) if bill_df is not None else ([], 0.0)

    # Extra Items
    extra_candidates = [
        "Extra Items", "Extra_Items", "EXTRA ITEMS", "ExtraItems",
        "Extra Item", "Extra", "EXTRA",
    ]
    extra_df = None
    for name in extra_candidates:
        if name in sheets:
            extra_df = xl.parse(name, header=None)
            break
    extra_items = _parse_extra_items(extra_df) if extra_df is not None else []

    doc = UnifiedDocument(
        fileId=file_id,
        fileName=filename,
        state=DocumentState.PARSED,
        titleData=title_data,
        billItems=bill_items,
        extraItems=extra_items,
        totalAmount=total_amount,
        hasExtraItems=len(extra_items) > 0,
        sheets=sheets,
    )
    return doc
