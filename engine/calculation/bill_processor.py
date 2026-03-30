"""
Unified Calculation Engine
Decoupled from Excel layout; operates on UnifiedDocumentModel.
Supports PWD-style quantity tracking (Since Last Bill vs Upto Date) 
and provides structured data for the V2 Jinja2 templates (Historical ground truth).
"""
import logging
from typing import Any, Dict, List, Optional, Tuple

from ingestion.models import UnifiedDocumentModel, DocumentRow

logger = logging.getLogger(__name__)

# ── num2words: import once at module level, fall back gracefully ──────────────
try:
    from num2words import num2words as _num2words
    _NUM2WORDS_AVAILABLE = True
except ImportError:
    _num2words = None
    _NUM2WORDS_AVAILABLE = False

# ============================================================================
# CALCULATION HELPERS
# ============================================================================

# Row/column constants — avoids magic numbers scattered through the code
ITEM_START_ROW = 21   # 0-indexed Excel row where bill items begin

def _apply_premium(base: float, pct: float) -> float:
    """Calculate premium amount. pct is percentage (e.g. 10.5)"""
    return round(base * (pct / 100))

def number_to_words(number: float) -> str:
    """Convert number to words (Indian English)."""
    if _NUM2WORDS_AVAILABLE:
        try:
            return _num2words(int(number), lang="en_IN").title() + " Only"
        except (ValueError, TypeError):
            pass
    return f"Rupees {number:,.2f}"

def _parse_float(val: Any, default: float = 0.0) -> float:
    """
    Safely convert any cell value to float.
    Handles None, empty string, comma-formatted numbers, and Rs. prefix.
    Returns `default` on any failure (logged at debug level).
    """
    if val is None or val == "":
        return default
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        cleaned = val.replace(",", "").replace("Rs.", "").strip()
        if cleaned == "":
            return default
        try:
            return float(cleaned)
        except ValueError:
            logger.debug("Could not parse numeric value: %r", val)
            return default
    return default

# ============================================================================
# MAIN PROCESSOR
# ============================================================================

def process_unified_bill(doc: UnifiedDocumentModel) -> Dict[str, Any]:
    """
    Main entry point for calculating bill data from a Unified Model.
    Produces a dictionary structure compatible with the v2 templates.
    """
    raw_meta = doc.raw_metadata or {}
    
    # Standardize metadata naming for templates
    # v2 templates expect: agreement_no, name_of_work, name_of_firm, work_order_amount
    meta = {
        "agreement_no": raw_meta.get("agreement_number") or raw_meta.get("Agreement No.") or "---",
        "name_of_work": raw_meta.get("work_name") or raw_meta.get("Name of Work") or "---",
        "name_of_firm": raw_meta.get("contractor_name") or raw_meta.get("Name of Contractor or supplier") or "---",
        "work_order_amount": _parse_float(raw_meta.get("work_order_amount") or raw_meta.get("WORK ORDER AMOUNT RS.")),
        "date_commencement": raw_meta.get("date_commencement", "---"),
        "date_completion": raw_meta.get("date_completion", "---"),
        "actual_completion": raw_meta.get("actual_completion", "---"),
        "tender_premium_percentage": _parse_float(raw_meta.get("tender_premium_percentage", 0.0)),
        "last_bill_deduction": _parse_float(raw_meta.get("last_bill_deduction", 0.0))
    }

    # --- 1. Main Bill Items ---
    processed_items = []
    grand_total_since = 0.0
    grand_total_upto = 0.0
    extra_total = 0.0
    extra_items_list = []
    
    for row in doc.rows:
        amt_since = round(row.qty_since_last_bill * row.rate, 2)
        amt_upto = round(row.qty_to_date * row.rate, 2)
        
        is_extra = row.remarks and ("Extra" in row.remarks or "E.I" in row.remarks)
        
        item_dict = {
            "serial_no": row.serial_no or "",
            "description": row.description,
            "unit": row.unit or "",
            "quantity_since_last": row.qty_since_last_bill if row.qty_since_last_bill != 0 else "",
            "quantity_upto_date": row.qty_to_date if row.qty_to_date != 0 else "",
            "rate": row.rate if row.rate != 0 else "",
            "amount": amt_upto if amt_upto != 0 else "",
            "amount_previous": amt_since if amt_since != 0 else "",
            "remark": row.remarks or "",
            "is_divider": False
        }
        
        if is_extra:
            extra_items_list.append(item_dict)
            extra_total += amt_upto
        else:
            processed_items.append(item_dict)
            grand_total_since += amt_since
            grand_total_upto += amt_upto

    # --- 2. Main Totals ---
    premium_amt = _apply_premium(grand_total_upto, meta["tender_premium_percentage"])
    payable = round(grand_total_upto + premium_amt)
    net_payable = round(payable - meta["last_bill_deduction"])

    # --- 3. Deviation Statement Data (v2) ---
    deviation_items = []
    total_excess = 0.0
    total_saving = 0.0
    total_amt_wo = 0.0
    total_amt_executed = 0.0

    for row in doc.rows:
        # Placeholder WO logic (UptoDate - SinceLast)
        qty_wo = max(0, row.qty_to_date - row.qty_since_last_bill)
        qty_bill = row.qty_to_date
        rate = row.rate
        
        amt_wo = round(qty_wo * rate, 2)
        amt_bill = round(qty_bill * rate, 2)
        
        excess_qty = max(0, qty_bill - qty_wo)
        saving_qty = max(0, qty_wo - qty_bill)
        
        excess_amt = round(excess_qty * rate, 2)
        saving_amt = round(saving_qty * rate, 2)
        
        deviation_items.append({
            "serial_no": row.serial_no,
            "description": row.description,
            "unit": row.unit,
            "qty_wo": qty_wo,
            "qty_bill": qty_bill,
            "rate": rate,
            "amt_wo": amt_wo,
            "amt_bill": amt_bill,
            "excess_qty": excess_qty,
            "excess_amt": excess_amt,
            "saving_qty": saving_qty,
            "saving_amt": saving_amt,
            "remark": row.remarks
        })
        
        total_excess += excess_amt
        total_saving += saving_amt
        total_amt_wo += amt_wo
        total_amt_executed += amt_bill

    premium_decimal = meta["tender_premium_percentage"] / 100.0
    deviation_summary = {
        "work_order_total": total_amt_wo,
        "executed_total": total_amt_executed,
        "overall_excess": total_excess,
        "overall_saving": total_saving,
        "is_saving": total_amt_executed < total_amt_wo,
        "net_difference": abs(total_amt_executed - total_amt_wo),
        "percentage_deviation": (abs(total_amt_executed - total_amt_wo) / total_amt_wo * 100) if total_amt_wo > 0 else 0,
        "premium": {"percent": premium_decimal},
        "tender_premium_f": round(total_amt_wo * premium_decimal, 2),
        "tender_premium_h": round(total_amt_executed * premium_decimal, 2),
        "tender_premium_j": round(total_excess * premium_decimal, 2),
        "tender_premium_l": round(total_saving * premium_decimal, 2),
        "grand_total_f": round(total_amt_wo * (1 + premium_decimal), 2),
        "grand_total_h": round(total_amt_executed * (1 + premium_decimal), 2),
        "grand_total_j": round(total_excess * (1 + premium_decimal), 2),
        "grand_total_l": round(total_saving * (1 + premium_decimal), 2)
    }

    # --- 5. Final Package (Flattened for v2 templates) ---
    result = {
        **meta,  # agreement_no, name_of_work, etc. at top level for note_sheet.html
        "metadata": meta, # for backend routes compatibility
        "header": [
            [f"Contractor: {meta['name_of_firm']}"],
            [f"Work: {meta['name_of_work']}"],
            [f"Agreement No: {meta['agreement_no']}"]
        ],
        "items": processed_items,
        "totals": {
            "grand_total": grand_total_upto,
            "premium": {"percent": premium_decimal, "amount": premium_amt},
            "payable": payable,
            "last_bill_amount": meta["last_bill_deduction"],
            "net_payable": net_payable,
            "cheque_amount": net_payable,  # [HIGH-5] Standardized field for templates
            "extra_items_sum": extra_total,
            "amount_words": number_to_words(net_payable)
        },
        "cheque_amount": net_payable, # directly at top level for note_sheet.html
        "extra_item_amount": extra_total, # directly at top level for note_sheet.html
        "deviation": {
            "items": deviation_items,
            "summary": deviation_summary
        },
        "extra_items": {
            "items": extra_items_list,
            "total": extra_total
        }
    }
    
    return result


# ============================================================================
# DATAFRAME-BASED PIPELINE (used by run_engine.py standalone runner)
# ============================================================================

def process_bill(
    ws_wo,          # Work Order DataFrame
    ws_bq,          # Bill Quantity DataFrame
    ws_extra,       # Extra Items DataFrame (may be empty)
    premium_percent: float = 0.0,
    premium_type: str = "above",
    previous_bill_amount: float = 0.0,
):
    """
    DataFrame-based bill processor used by run_engine.py.
    Reads the PWD 4-sheet Excel format (Title / Work Order / Bill Quantity / Extra Items).
    Returns a 5-tuple: (first_page, last_page, deviation, extra_items, note_sheet)
    each being a dict compatible with the v2 Jinja2 templates.
    """
    import pandas as pd

    # ── 1. Extract metadata from Work Order header rows ───────────────────────
    meta = _extract_wo_metadata(ws_wo)
    meta["tender_premium_percentage"] = premium_percent
    meta["last_bill_deduction"] = previous_bill_amount
    premium_decimal = premium_percent / 100.0

    # ── 2. Parse Work Order items (columns: Item, Description, Unit, Qty, Rate) ─
    wo_items = _parse_wo_items(ws_wo)

    # ── 3. Parse Bill Quantity items ──────────────────────────────────────────
    bq_items = _parse_bq_items(ws_bq)

    # ── 4. Parse Extra Items ──────────────────────────────────────────────────
    extra_rows = _parse_extra_items(ws_extra)

    # ── 5. Merge WO + BQ to get since/upto quantities ────────────────────────
    merged = _merge_wo_bq(wo_items, bq_items)

    # ── 6. Calculate totals ───────────────────────────────────────────────────
    grand_total_upto = sum(r["amount_upto"] for r in merged)
    grand_total_since = sum(r["amount_since"] for r in merged)
    extra_total = sum(_parse_float(r.get("amount", 0)) for r in extra_rows)

    premium_amt = _apply_premium(grand_total_upto, premium_percent)
    if premium_type == "below":
        premium_amt = -abs(premium_amt)

    payable = round(grand_total_upto + premium_amt + extra_total)
    net_payable = round(payable - previous_bill_amount)

    # ── 7. Build header rows for first_page template ──────────────────────────
    header_rows = [
        [f"Agreement No: {meta.get('agreement_no', '')}",
         f"Name of Work: {meta.get('name_of_work', '')}"],
        [f"Name of Contractor: {meta.get('name_of_firm', '')}",
         f"Work Order Amount Rs.: {meta.get('work_order_amount', '')}"],
        [f"Date of Commencement: {meta.get('date_commencement', '')}",
         f"Date of Completion: {meta.get('date_completion', '')}"],
    ]

    # ── 8. Build item dicts for first_page template ───────────────────────────
    items_for_template = []
    for r in merged:
        items_for_template.append({
            "serial_no": r.get("serial_no", ""),
            "description": r.get("description", ""),
            "unit": r.get("unit", ""),
            "quantity_since_last": r["qty_since"] if r["qty_since"] != 0 else "",
            "quantity_upto_date": r["qty_upto"] if r["qty_upto"] != 0 else "",
            "rate": r["rate"] if r["rate"] != 0 else "",
            "amount": r["amount_upto"] if r["amount_upto"] != 0 else "",
            "amount_previous": r["amount_since"] if r["amount_since"] != 0 else "",
            "remark": r.get("remark", ""),
            "bold": False,
            "underline": False,
            "is_divider": False,
        })

    totals = {
        "grand_total": grand_total_upto,
        "premium": {"percent": premium_decimal, "amount": premium_amt},
        "payable": payable,
        "last_bill_amount": previous_bill_amount,
        "net_payable": net_payable,
        "extra_items_sum": extra_total,
        "amount_words": number_to_words(net_payable),
    }

    # ── 9. Deviation statement ────────────────────────────────────────────────
    dev_items = []
    total_excess = total_saving = total_amt_wo = total_amt_exec = 0.0

    for r in merged:
        qty_wo = r.get("qty_wo", r["qty_upto"])
        qty_bill = r["qty_upto"]
        rate = r["rate"]
        amt_wo = round(qty_wo * rate, 2)
        amt_bill = round(qty_bill * rate, 2)
        excess_qty = max(0.0, qty_bill - qty_wo)
        saving_qty = max(0.0, qty_wo - qty_bill)
        excess_amt = round(excess_qty * rate, 2)
        saving_amt = round(saving_qty * rate, 2)

        dev_items.append({
            "serial_no": r.get("serial_no", ""),
            "description": r.get("description", ""),
            "unit": r.get("unit", ""),
            "qty_wo": qty_wo,
            "qty_bill": qty_bill,
            "rate": rate,
            "amt_wo": amt_wo,
            "amt_bill": amt_bill,
            "excess_qty": excess_qty,
            "excess_amt": excess_amt,
            "saving_qty": saving_qty,
            "saving_amt": saving_amt,
            "remark": r.get("remark", ""),
        })
        total_excess += excess_amt
        total_saving += saving_amt
        total_amt_wo += amt_wo
        total_amt_exec += amt_bill

    deviation_summary = {
        "work_order_total": total_amt_wo,
        "executed_total": total_amt_exec,
        "overall_excess": total_excess,
        "overall_saving": total_saving,
        "is_saving": total_amt_exec < total_amt_wo,
        "net_difference": abs(total_amt_exec - total_amt_wo),
        "percentage_deviation": (abs(total_amt_exec - total_amt_wo) / total_amt_wo * 100) if total_amt_wo > 0 else 0,
        "premium": {"percent": premium_decimal},
        "tender_premium_f": round(total_amt_wo * premium_decimal, 2),
        "tender_premium_h": round(total_amt_exec * premium_decimal, 2),
        "tender_premium_j": round(total_excess * premium_decimal, 2),
        "tender_premium_l": round(total_saving * premium_decimal, 2),
        "grand_total_f": round(total_amt_wo * (1 + premium_decimal), 2),
        "grand_total_h": round(total_amt_exec * (1 + premium_decimal), 2),
        "grand_total_j": round(total_excess * (1 + premium_decimal), 2),
        "grand_total_l": round(total_saving * (1 + premium_decimal), 2),
    }

    # ── 10. Extra items for template ──────────────────────────────────────────
    extra_items_for_template = []
    for i, r in enumerate(extra_rows):
        extra_items_for_template.append({
            "serial_no": r.get("serial_no", str(i + 1)),
            "bsr": r.get("bsr", ""),
            "description": r.get("description", ""),
            "unit": r.get("unit", ""),
            "quantity": r.get("quantity", ""),
            "rate": r.get("rate", ""),
            "amount": r.get("amount", ""),
            "remark": r.get("remark", ""),
            "is_divider": False,
        })

    # ── 11. Assemble the 5 return dicts ───────────────────────────────────────
    # All dicts share the same top-level meta keys so templates can access them
    base = {
        **meta,
        "metadata": meta,
        "header": header_rows,
        "items": items_for_template,
        "totals": totals,
        "extra_item_amount": extra_total,
    }

    first_page = base
    last_page = base
    deviation = {"items": dev_items, "summary": deviation_summary}
    extra_items_out = {"items": extra_items_for_template, "total": extra_total}
    note_sheet = base  # note_sheet template reads from same data

    return first_page, last_page, deviation, extra_items_out, note_sheet


# ── DataFrame parsing helpers ─────────────────────────────────────────────────

def _extract_wo_metadata(ws_wo) -> dict:
    """Extract metadata from the Work Order sheet header rows."""
    import pandas as pd

    meta = {
        "agreement_no": "---",
        "name_of_work": "---",
        "name_of_firm": "---",
        "work_order_amount": 0.0,
        "date_commencement": "---",
        "date_completion": "---",
        "actual_completion": "---",
    }

    KEY_MAP = {
        "agreement no": "agreement_no",
        "agreement no.": "agreement_no",
        "name of work": "name_of_work",
        "name of contractor or supplier": "name_of_firm",
        "name of contractor": "name_of_firm",
        "contractor": "name_of_firm",
        "work order amount rs.": "work_order_amount",
        "amount of work order": "work_order_amount",
        "date of written order to commence work": "date_commencement",
        "st. date of completion": "date_completion",
        "date of actual completion of work": "actual_completion",
    }

    if ws_wo is None or ws_wo.empty:
        return meta

    for _, row in ws_wo.iterrows():
        cells = [str(c).strip() for c in row if str(c).strip() not in ("", "nan", "NaN")]
        for i, cell in enumerate(cells):
            norm = cell.lower().rstrip(":;- ")
            field = KEY_MAP.get(norm)
            if field and i + 1 < len(cells):
                val = cells[i + 1]
                if field == "work_order_amount":
                    meta[field] = _parse_float(val)
                elif not meta.get(field) or meta[field] == "---":
                    meta[field] = val

    return meta


def _parse_wo_items(ws_wo) -> list:
    """Parse Work Order items from the DataFrame."""
    import pandas as pd
    items = []
    if ws_wo is None or ws_wo.empty:
        return items

    # Find the header row (contains 'Item' or 'S.No' and 'Description')
    header_idx = -1
    for idx, row in ws_wo.iterrows():
        cells = [str(c).strip().lower() for c in row]
        if any("item" in c or "s. no" in c or "sno" in c for c in cells) and \
           any("desc" in c or "particular" in c for c in cells):
            header_idx = idx
            break

    if header_idx < 0:
        return items

    # Use .loc (label-based) since iterrows() gives original index labels
    header_row = [str(c).strip().lower() for c in ws_wo.loc[header_idx]]
    col_map = {}
    for i, h in enumerate(header_row):
        if any(k in h for k in ["item", "s. no", "sno", "sl"]):
            col_map.setdefault("serial_no", i)
        elif any(k in h for k in ["desc", "particular", "name of work"]):
            col_map.setdefault("description", i)
        elif "unit" in h:
            col_map.setdefault("unit", i)
        elif any(k in h for k in ["qty", "quantity"]):
            col_map.setdefault("qty", i)
        elif "rate" in h:
            col_map.setdefault("rate", i)
        elif "amount" in h or "rs" in h:
            col_map.setdefault("amount", i)

    past_header = False
    for idx, row in ws_wo.iterrows():
        if idx == header_idx:
            past_header = True
            continue
        if not past_header:
            continue
        desc = str(row.iloc[col_map.get("description", 1)]).strip() if "description" in col_map else ""
        if not desc or desc in ("nan", "NaN", ""):
            continue
        qty = _parse_float(row.iloc[col_map["qty"]]) if "qty" in col_map else 0.0
        rate = _parse_float(row.iloc[col_map["rate"]]) if "rate" in col_map else 0.0
        items.append({
            "serial_no": str(row.iloc[col_map.get("serial_no", 0)]).strip() if "serial_no" in col_map else "",
            "description": desc,
            "unit": str(row.iloc[col_map["unit"]]).strip() if "unit" in col_map else "",
            "qty_wo": qty,
            "rate": rate,
            "amount_wo": round(qty * rate, 2),
        })
    return items


def _parse_bq_items(ws_bq) -> list:
    """Parse Bill Quantity items — same structure as Work Order."""
    import pandas as pd
    items = []
    if ws_bq is None or ws_bq.empty:
        return items

    header_idx = -1
    for idx, row in ws_bq.iterrows():
        cells = [str(c).strip().lower() for c in row]
        if any("item" in c or "s. no" in c or "sno" in c for c in cells) and \
           any("desc" in c or "particular" in c for c in cells):
            header_idx = idx
            break

    if header_idx < 0:
        return items

    # Use .loc (label-based) since iterrows() gives original index labels
    header_row = [str(c).strip().lower() for c in ws_bq.loc[header_idx]]
    col_map = {}
    qty_cols = []
    for i, h in enumerate(header_row):
        if any(k in h for k in ["item", "s. no", "sno", "sl"]):
            col_map.setdefault("serial_no", i)
        elif any(k in h for k in ["desc", "particular"]):
            col_map.setdefault("description", i)
        elif "unit" in h:
            col_map.setdefault("unit", i)
        elif "since" in h or "last" in h:
            col_map["qty_since"] = i
        elif "upto" in h or "to date" in h or "cumul" in h:
            col_map["qty_upto"] = i
        elif any(k in h for k in ["qty", "quantity"]):
            qty_cols.append(i)
        elif "rate" in h:
            col_map.setdefault("rate", i)
        elif "remark" in h or "note" in h:
            col_map.setdefault("remark", i)

    # If no since/upto columns found, use first two qty columns
    if "qty_since" not in col_map and len(qty_cols) >= 2:
        col_map["qty_since"] = qty_cols[0]
        col_map["qty_upto"] = qty_cols[1]
    elif "qty_upto" not in col_map and len(qty_cols) >= 1:
        col_map["qty_upto"] = qty_cols[0]

    past_header = False
    for idx, row in ws_bq.iterrows():
        if idx == header_idx:
            past_header = True
            continue
        if not past_header:
            continue
        desc = str(row.iloc[col_map.get("description", 1)]).strip() if "description" in col_map else ""
        if not desc or desc in ("nan", "NaN", ""):
            continue
        qty_since = _parse_float(row.iloc[col_map["qty_since"]]) if "qty_since" in col_map else 0.0
        qty_upto = _parse_float(row.iloc[col_map["qty_upto"]]) if "qty_upto" in col_map else 0.0
        rate = _parse_float(row.iloc[col_map["rate"]]) if "rate" in col_map else 0.0
        items.append({
            "serial_no": str(row.iloc[col_map.get("serial_no", 0)]).strip() if "serial_no" in col_map else "",
            "description": desc,
            "unit": str(row.iloc[col_map["unit"]]).strip() if "unit" in col_map else "",
            "qty_since": qty_since,
            "qty_upto": qty_upto,
            "rate": rate,
            "remark": str(row.iloc[col_map["remark"]]).strip() if "remark" in col_map else "",
        })
    return items


def _parse_extra_items(ws_extra) -> list:
    """Parse Extra Items sheet (PWD format: S.No | BSR | Particulars | Qty | Unit | Rate | Amount | Remarks)."""
    import pandas as pd
    items = []
    if ws_extra is None or ws_extra.empty:
        return items

    header_idx = -1
    for idx, row in ws_extra.iterrows():
        cells = [str(c).strip().lower() for c in row]
        # Look for the header row containing 'particulars' or 'description'
        if any("particular" in c or "desc" in c for c in cells) and \
           any("qty" in c or "quantity" in c for c in cells):
            header_idx = idx
            break

    if header_idx < 0:
        return items

    # Use .loc (label-based) since iterrows() gives original index labels
    header_row = [str(c).strip().lower() for c in ws_extra.loc[header_idx]]
    col_map = {}
    for i, h in enumerate(header_row):
        h = h.strip()
        if any(k in h for k in ["s.no", "s. no", "sno", "item no", "sl"]):
            col_map.setdefault("serial_no", i)
        elif "bsr" in h or "ref" in h:
            col_map.setdefault("bsr", i)
        elif any(k in h for k in ["particular", "desc"]):
            col_map.setdefault("description", i)
        elif any(k in h for k in ["qty", "quantity"]):
            col_map.setdefault("quantity", i)
        elif "unit" in h:
            col_map.setdefault("unit", i)
        elif "rate" in h:
            col_map.setdefault("rate", i)
        elif "amount" in h or "rs" in h:
            col_map.setdefault("amount", i)
        elif "remark" in h or "note" in h:
            col_map.setdefault("remark", i)

    if "description" not in col_map:
        return items

    # Iterate rows AFTER the header using label-based index
    past_header = False
    for idx, row in ws_extra.iterrows():
        if idx == header_idx:
            past_header = True
            continue
        if not past_header:
            continue

        desc = str(row.iloc[col_map["description"]]).strip()
        if not desc or desc in ("nan", "NaN", "") or "total" in desc.lower():
            continue
        sno = str(row.iloc[col_map.get("serial_no", 0)]).strip() if "serial_no" in col_map else ""
        if not sno or sno in ("nan", "NaN", ""):
            continue

        qty = _parse_float(row.iloc[col_map["quantity"]]) if "quantity" in col_map else 0.0
        rate = _parse_float(row.iloc[col_map["rate"]]) if "rate" in col_map else 0.0
        amount_raw = _parse_float(row.iloc[col_map["amount"]]) if "amount" in col_map else 0.0
        amount = amount_raw if amount_raw > 0 else round(qty * rate, 2)

        items.append({
            "serial_no": sno,
            "bsr": str(row.iloc[col_map["bsr"]]).strip() if "bsr" in col_map else "",
            "description": desc,
            "unit": str(row.iloc[col_map["unit"]]).strip() if "unit" in col_map else "",
            "quantity": qty,
            "rate": rate,
            "amount": amount,
            "remark": str(row.iloc[col_map["remark"]]).strip() if "remark" in col_map else "",
        })
    return items


def _merge_wo_bq(wo_items: list, bq_items: list) -> list:
    """
    Merge Work Order and Bill Quantity items by description match.
    BQ items take precedence for qty_since/qty_upto.
    WO items provide the work order quantity (qty_wo).
    """
    # Build lookup by description (normalized)
    wo_lookup = {}
    for item in wo_items:
        key = item["description"].strip().lower()[:60]
        wo_lookup[key] = item

    merged = []
    for bq in bq_items:
        key = bq["description"].strip().lower()[:60]
        wo = wo_lookup.get(key, {})
        rate = bq.get("rate") or wo.get("rate", 0.0)
        qty_since = bq.get("qty_since", 0.0)
        qty_upto = bq.get("qty_upto", 0.0)
        qty_wo = wo.get("qty_wo", qty_upto)

        merged.append({
            "serial_no": bq.get("serial_no") or wo.get("serial_no", ""),
            "description": bq["description"],
            "unit": bq.get("unit") or wo.get("unit", ""),
            "qty_since": qty_since,
            "qty_upto": qty_upto,
            "qty_wo": qty_wo,
            "rate": rate,
            "amount_since": round(qty_since * rate, 2),
            "amount_upto": round(qty_upto * rate, 2),
            "remark": bq.get("remark", ""),
        })

    # If BQ was empty, fall back to WO items
    if not merged and wo_items:
        for wo in wo_items:
            qty = wo.get("qty_wo", 0.0)
            rate = wo.get("rate", 0.0)
            merged.append({
                "serial_no": wo.get("serial_no", ""),
                "description": wo["description"],
                "unit": wo.get("unit", ""),
                "qty_since": 0.0,
                "qty_upto": qty,
                "qty_wo": qty,
                "rate": rate,
                "amount_since": 0.0,
                "amount_upto": round(qty * rate, 2),
                "remark": "",
            })

    return merged
