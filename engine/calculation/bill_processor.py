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

# ============================================================================
# CALCULATION HELPERS
# ============================================================================

def _apply_premium(base: float, pct: float) -> float:
    """Calculate premium amount. pct is percentage (e.g. 10.5)"""
    return round(base * (pct / 100))

def number_to_words(number: float) -> str:
    """Convert number to words (Indian English)."""
    try:
        from num2words import num2words
        return num2words(int(number), lang="en_IN").title() + " Only"
    except (ImportError, ValueError, TypeError):
        return f"Rupees {number:,.2f}"

def _parse_float(val: Any) -> float:
    if val is None or val == "": return 0.0
    try:
        if isinstance(val, str):
            val = val.replace(",", "").replace("Rs.", "").strip()
        return float(val)
    except (ValueError, TypeError):
        return 0.0

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
            "extra_items_sum": extra_total,
            "amount_words": number_to_words(net_payable)
        },
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
