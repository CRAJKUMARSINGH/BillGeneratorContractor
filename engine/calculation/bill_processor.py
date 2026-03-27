"""
Core computation logic for bill processing.
Refactored: DRY violation fixed — all cell parsing goes through parse_cell().
Magic numbers replaced with named constants.
"""
import logging
from datetime import date, datetime
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ── Excel layout constants ────────────────────────────────────────────────────
HEADER_END_ROW   = 19   # ws_wo.iloc[:19]  = header block
ITEM_START_ROW   = 21   # 0-indexed; items begin at row 21
EXTRA_START_ROW  = 6    # extra items sheet data starts at row 6

# Work Order column indices
COL_SERIAL   = 0
COL_DESC     = 1
COL_UNIT     = 2
COL_QTY_WO   = 3   # work-order quantity
COL_RATE     = 4
COL_REMARK   = 6

# Bill Quantity column indices
COL_QTY_BQ  = 3   # executed quantity

# Extra Items column indices
COL_EX_SERIAL = 0
COL_EX_BSR    = 1
COL_EX_DESC   = 2
COL_EX_QTY    = 3
COL_EX_UNIT   = 4
COL_EX_RATE   = 5


# ── Helpers ───────────────────────────────────────────────────────────────────

def parse_cell(value: Any, default: float = 0.0) -> float:
    """
    Safely convert any Excel cell value to float.
    Handles int/float, numeric strings (with commas), and blanks.
    Logs unrecognised values at DEBUG level instead of silently zeroing.
    """
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "").replace(" ", "")
        if not cleaned:
            return default
        try:
            return float(cleaned)
        except ValueError:
            logger.debug("parse_cell: cannot convert %r — using default %s", value, default)
            return default
    return default


def _cell_str(series: pd.Series, col: int) -> str:
    """Return cell as string, empty string if null."""
    val = series.iloc[col] if col < len(series) else None
    return str(val) if pd.notnull(val) else ""


def _make_blank_item(serial: str, desc: str, remark: str) -> Dict[str, Any]:
    """Zero-rate row — only serial, description, remark are populated."""
    return {
        "serial_no": serial, "description": desc, "remark": remark,
        "unit": "", "quantity": "", "quantity_since_last": "",
        "quantity_upto_date": "", "rate": "", "amount": "",
        "amount_previous": "", "is_divider": False,
    }


def _make_item(serial: str, desc: str, unit: str, remark: str,
               qty: float, rate: float) -> Dict[str, Any]:
    """Regular item with calculated amounts."""
    amount = round(qty * rate) if qty and rate else 0
    return {
        "serial_no": serial, "description": desc, "unit": unit, "remark": remark,
        "quantity": qty, "quantity_since_last": qty, "quantity_upto_date": qty,
        "rate": rate, "amount": amount, "amount_previous": amount,
        "is_divider": False,
    }


def _apply_premium(base: float, pct: float, ptype: str) -> float:
    """Calculate premium amount; negative for 'below' type."""
    multiplier = 1 if ptype == "above" else -1
    return round(base * (pct / 100) * multiplier)


def safe_float(value: Any, default: float = 0.0) -> float:
    """Public alias kept for backward compatibility."""
    return parse_cell(value, default)


def number_to_words(number: Any) -> str:
    """Convert number to words (Indian English). Falls back to str()."""
    try:
        from num2words import num2words  # imported once per call; cached by Python
        return num2words(int(number), lang="en_IN").title()
    except (ImportError, ValueError, TypeError):
        return str(number)


# ── Main processor ────────────────────────────────────────────────────────────

def process_bill(ws_wo, ws_bq, ws_extra,
                 premium_percent: float,
                 premium_type: str,
                 previous_bill_amount: float = 0.0):
    """
    Process bill data from Excel DataFrames.

    Args:
        ws_wo:                Work Order DataFrame
        ws_bq:                Bill Quantity DataFrame
        ws_extra:             Extra Items DataFrame
        premium_percent:      Tender premium %
        premium_type:         "above" or "below"
        previous_bill_amount: Amount paid in previous bill

    Returns:
        tuple: (first_page_data, last_page_data, deviation_data,
                extra_items_data, note_sheet_data)
    """
    first_page_data  = {"header": [], "items": [], "totals": {}}
    last_page_data   = {"payable_amount": 0, "amount_words": ""}
    deviation_data   = {"items": [], "summary": {}}
    extra_items_data = {"items": []}
    note_sheet_data  = {"notes": []}

    # ── Header block ──────────────────────────────────────────────────────────
    header_data = ws_wo.iloc[:HEADER_END_ROW, :7].replace(np.nan, "").values.tolist()
    for i, row in enumerate(header_data):
        for j, val in enumerate(row):
            if isinstance(val, (pd.Timestamp, datetime, date)):
                header_data[i][j] = val.strftime("%d-%m-%Y")
    first_page_data["header"] = header_data

    # ── Work Order items ──────────────────────────────────────────────────────
    last_row_wo = ws_wo.shape[0]
    for i in range(ITEM_START_ROW, last_row_wo):
        qty_raw  = ws_bq.iloc[i, COL_QTY_BQ] if i < ws_bq.shape[0] and pd.notnull(ws_bq.iloc[i, COL_QTY_BQ]) else None
        rate_raw = ws_wo.iloc[i, COL_RATE]    if pd.notnull(ws_wo.iloc[i, COL_RATE]) else None

        qty  = parse_cell(qty_raw)
        rate = parse_cell(rate_raw)

        row_wo = ws_wo.iloc[i]
        serial = _cell_str(row_wo, COL_SERIAL)
        desc   = _cell_str(row_wo, COL_DESC)
        unit   = _cell_str(row_wo, COL_UNIT)
        remark = _cell_str(row_wo, COL_REMARK)

        item = (_make_blank_item(serial, desc, remark)
                if rate == 0
                else _make_item(serial, desc, unit, remark, qty, rate))
        first_page_data["items"].append(item)

    # ── Extra Items divider ───────────────────────────────────────────────────
    first_page_data["items"].append({
        "description": "Extra Items (With Premium)", "bold": True,
        "underline": True, "amount": 0, "amount_previous": 0,
        "quantity": 0, "quantity_since_last": 0, "quantity_upto_date": 0,
        "rate": 0, "serial_no": "", "unit": "", "remark": "", "is_divider": True,
    })

    # ── Extra Items ───────────────────────────────────────────────────────────
    last_row_extra = ws_extra.shape[0]
    for j in range(EXTRA_START_ROW, last_row_extra):
        qty_raw  = ws_extra.iloc[j, COL_EX_QTY]  if pd.notnull(ws_extra.iloc[j, COL_EX_QTY])  else None
        rate_raw = ws_extra.iloc[j, COL_EX_RATE]  if pd.notnull(ws_extra.iloc[j, COL_EX_RATE]) else None

        qty  = parse_cell(qty_raw)
        rate = parse_cell(rate_raw)

        row_ex = ws_extra.iloc[j]
        serial = _cell_str(row_ex, COL_EX_SERIAL)
        desc   = _cell_str(row_ex, COL_EX_DESC)
        unit   = _cell_str(row_ex, COL_EX_UNIT)
        remark = _cell_str(row_ex, COL_EX_BSR)

        if rate == 0:
            item = _make_blank_item(serial, desc, remark)
        else:
            item = _make_item(serial, desc, unit, remark, qty, rate)

        first_page_data["items"].append(item)
        extra_items_data["items"].append(item.copy())

    # ── Totals ────────────────────────────────────────────────────────────────
    data_items   = [it for it in first_page_data["items"] if not it.get("is_divider")]
    total_amount = round(sum(parse_cell(it.get("amount", 0)) for it in data_items))
    premium_amt  = _apply_premium(total_amount, premium_percent, premium_type)
    payable      = round(total_amount + premium_amt)
    net_payable  = round(payable - previous_bill_amount)

    # Extra items sub-total (with premium)
    try:
        divider_idx = next(
            i for i, it in enumerate(first_page_data["items"])
            if it.get("description") == "Extra Items (With Premium)"
        )
        extra_only = [
            it for it in first_page_data["items"][divider_idx + 1:]
            if not it.get("is_divider")
        ]
        extra_sum     = round(sum(parse_cell(it.get("amount", 0)) for it in extra_only))
        extra_premium = _apply_premium(extra_sum, premium_percent, premium_type)
        extra_total   = extra_sum + extra_premium
    except StopIteration:
        extra_total = 0

    first_page_data["totals"] = {
        "grand_total":      total_amount,
        "premium":          {"percent": premium_percent / 100, "type": premium_type, "amount": premium_amt},
        "payable":          payable,
        "last_bill_amount": previous_bill_amount if previous_bill_amount > 0 else 0,
        "net_payable":      net_payable if previous_bill_amount > 0 else payable,
        "extra_items_sum":  extra_total,
    }

    last_page_data = {"payable_amount": payable, "amount_words": number_to_words(payable)}

    # ── Deviation Statement ───────────────────────────────────────────────────
    work_order_total = executed_total = overall_excess = overall_saving = 0

    for i in range(ITEM_START_ROW, last_row_wo):
        qty_wo_raw   = ws_wo.iloc[i, COL_QTY_WO] if pd.notnull(ws_wo.iloc[i, COL_QTY_WO]) else None
        rate_raw     = ws_wo.iloc[i, COL_RATE]    if pd.notnull(ws_wo.iloc[i, COL_RATE])   else None
        qty_bill_raw = ws_bq.iloc[i, COL_QTY_BQ]  if i < ws_bq.shape[0] and pd.notnull(ws_bq.iloc[i, COL_QTY_BQ]) else None

        qty_wo   = parse_cell(qty_wo_raw)
        rate     = parse_cell(rate_raw)
        qty_bill = parse_cell(qty_bill_raw)

        row_wo = ws_wo.iloc[i]
        serial = _cell_str(row_wo, COL_SERIAL)
        desc   = _cell_str(row_wo, COL_DESC)
        unit   = _cell_str(row_wo, COL_UNIT)
        remark = _cell_str(row_wo, COL_REMARK)

        if rate == 0:
            dev_item = {
                "serial_no": serial, "description": desc, "remark": remark,
                "unit": "", "qty_wo": "", "rate": "", "amt_wo": "",
                "qty_bill": "", "amt_bill": "", "excess_qty": "",
                "excess_amt": "", "saving_qty": "", "saving_amt": "",
            }
            amt_wo = amt_bill = excess_amt = saving_amt = 0
        else:
            amt_wo   = round(qty_wo   * rate)
            amt_bill = round(qty_bill * rate)
            excess_qty  = max(qty_bill - qty_wo, 0)
            saving_qty  = max(qty_wo  - qty_bill, 0)
            excess_amt  = round(excess_qty * rate)
            saving_amt  = round(saving_qty * rate)

            dev_item = {
                "serial_no": serial, "description": desc, "unit": unit, "remark": remark,
                "qty_wo": qty_wo, "rate": rate, "amt_wo": amt_wo,
                "qty_bill": qty_bill, "amt_bill": amt_bill,
                "excess_qty": excess_qty, "excess_amt": excess_amt,
                "saving_qty": saving_qty, "saving_amt": saving_amt,
            }
            work_order_total += amt_wo
            executed_total   += amt_bill
            overall_excess   += excess_amt
            overall_saving   += saving_amt

        deviation_data["items"].append(dev_item)

    # Extra items divider in deviation
    deviation_data["items"].append({
        "serial_no": "", "description": "Extra Items (With Premium)",
        "unit": "", "qty_wo": 0, "rate": 0, "amt_wo": 0,
        "qty_bill": 0, "amt_bill": 0, "excess_qty": 0,
        "excess_amt": 0, "saving_qty": 0, "saving_amt": 0,
        "remark": "", "is_divider": True,
    })

    extra_bill_total = 0
    for j in range(EXTRA_START_ROW, last_row_extra):
        qty_raw  = ws_extra.iloc[j, COL_EX_QTY]  if pd.notnull(ws_extra.iloc[j, COL_EX_QTY])  else None
        rate_raw = ws_extra.iloc[j, COL_EX_RATE]  if pd.notnull(ws_extra.iloc[j, COL_EX_RATE]) else None

        qty  = parse_cell(qty_raw)
        rate = parse_cell(rate_raw)

        row_ex = ws_extra.iloc[j]
        serial = _cell_str(row_ex, COL_EX_SERIAL)
        desc   = _cell_str(row_ex, COL_EX_DESC)
        unit   = _cell_str(row_ex, COL_EX_UNIT)
        remark = _cell_str(row_ex, COL_EX_BSR)

        if rate == 0:
            ex_dev = {
                "serial_no": serial, "description": desc, "remark": remark,
                "unit": "", "qty_wo": "", "rate": "", "amt_wo": "",
                "qty_bill": "", "amt_bill": "", "excess_qty": "",
                "excess_amt": "", "saving_qty": "", "saving_amt": "",
            }
        else:
            amt_bill = round(qty * rate)
            ex_dev = {
                "serial_no": serial, "description": desc, "unit": unit, "remark": remark,
                "qty_wo": 0, "rate": rate, "amt_wo": 0,
                "qty_bill": qty, "amt_bill": amt_bill,
                "excess_qty": qty, "excess_amt": amt_bill,
                "saving_qty": 0, "saving_amt": 0,
            }
            extra_bill_total += amt_bill

        deviation_data["items"].append(ex_dev)

    executed_total += extra_bill_total
    overall_excess += extra_bill_total

    # Deviation summary with premium
    tp_f = _apply_premium(work_order_total, premium_percent, premium_type)
    tp_h = _apply_premium(executed_total,   premium_percent, premium_type)
    tp_j = _apply_premium(overall_excess,   premium_percent, premium_type)
    tp_l = _apply_premium(overall_saving,   premium_percent, premium_type)
    gt_f = round(work_order_total + tp_f)
    gt_h = round(executed_total   + tp_h)
    gt_j = round(overall_excess   + tp_j)
    gt_l = round(overall_saving   + tp_l)
    net_diff = round(gt_h - gt_f)
    pct_dev  = round(abs(net_diff / gt_f * 100), 2) if gt_f else 0.0

    deviation_data["summary"] = {
        "work_order_total": round(work_order_total),
        "executed_total":   round(executed_total),
        "overall_excess":   round(overall_excess),
        "overall_saving":   round(overall_saving),
        "premium":          {"percent": premium_percent / 100, "type": premium_type},
        "tender_premium_f": tp_f, "tender_premium_h": tp_h,
        "tender_premium_j": tp_j, "tender_premium_l": tp_l,
        "grand_total_f": gt_f, "grand_total_h": gt_h,
        "grand_total_j": gt_j, "grand_total_l": gt_l,
        "net_difference":       abs(net_diff),
        "is_saving":            net_diff < 0,
        "percentage_deviation": pct_dev,
    }

    return first_page_data, last_page_data, deviation_data, extra_items_data, note_sheet_data
