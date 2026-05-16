"""
Core computation logic for bill processing - extracted from streamlit_app.py
This module contains the core business logic that should not be modified.
"""
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP

import numpy as np
import pandas as pd


def round_up(val):
    """PWD standard: Round Half Up to nearest integer"""
    if val is None: return 0
    return int(Decimal(str(float(val))).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

def safe_float(value, default=0.0):
    """Safely convert a value to float with proper error handling"""
    try:
        if value is None:
            return default
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            # Clean the string
            cleaned = value.strip().replace(',', '').replace(' ', '')
            # Handle empty string
            if cleaned == '':
                return default
            # Try to convert
            return float(cleaned)
        return default
    except (ValueError, TypeError):
        return default

def number_to_words(number):
    """Convert number to words using num2words"""
    try:
        from num2words import num2words
        return num2words(int(number), lang="en_IN").title()
    except (ImportError, ValueError, TypeError):
        # Fallback if num2words not available or invalid number
        return str(number)

def _natural_sort_key(code: str):
    """
    Natural (numeric-aware) sort key for PWD BSR dot-delimited item codes.
    Ensures "1.2" < "1.10" < "1.11" instead of lexicographic "1.10" < "1.11" < "1.2".
    """
    if not code:
        return (0,)
    parts = code.split('.')
    result = []
    for part in parts:
        try:
            result.append(int(part))
        except ValueError:
            result.append(0)
    return tuple(result)


def process_bill(ws_wo, ws_bq, ws_extra, premium_percent, premium_type, previous_bill_amount=0):
    """
    Process bill data from Excel sheets
    
    Args:
        ws_wo: Work Order worksheet
        ws_bq: Bill Quantity worksheet
        ws_extra: Extra Items worksheet
        premium_percent: Tender premium percentage
        premium_type: "above" or "below"
        previous_bill_amount: Amount paid in previous bill (default: 0)
    
    Returns:
        tuple: (first_page_data, last_page_data, deviation_data, extra_items_data, note_sheet_data)
    """
    first_page_data = {"header": [], "items": [], "totals": {}}
    last_page_data = {"payable_amount": 0, "amount_words": ""}
    deviation_data = {"items": [], "summary": {}}
    extra_items_data = {"items": []}
    note_sheet_data = {"notes": []}

    # Header (A1:G19) only — matching actual data range
    header_data = ws_wo.iloc[:19, :7].replace(np.nan, "").values.tolist()

    # Ensure all dates are formatted as date-only strings
    for i in range(len(header_data)):
        for j in range(len(header_data[i])):
            val = header_data[i][j]
            if isinstance(val, (pd.Timestamp, datetime, date)):
                header_data[i][j] = val.strftime("%d-%m-%Y")

    first_page_data["header"] = header_data

    # BQ quantity resolution strategy:
    # These Excel files use two layouts:
    #   A) Sub-items have nan item codes — WO and BQ are row-aligned, use positional match
    #   B) Items have explicit dot-notation codes (e.g. "1.1", "1.10") — use code-based lookup
    #      to survive row-count differences between sheets
    #
    # Strategy: build a code-based lookup for named items; fall back to positional
    # (ws_bq.iloc[i, 3]) for nan-coded rows where sheets are row-aligned.
    bq_qty_lookup: dict = {}
    for bq_i in range(21, ws_bq.shape[0]):
        code_raw = ws_bq.iloc[bq_i, 0] if pd.notnull(ws_bq.iloc[bq_i, 0]) else None
        qty_raw_bq = ws_bq.iloc[bq_i, 3] if pd.notnull(ws_bq.iloc[bq_i, 3]) else None
        if code_raw is not None:
            code_str = str(code_raw).strip()
            if code_str and code_str.lower() not in ('nan', 'item', 'item no.', 'item no'):
                qty_val = 0.0
                if isinstance(qty_raw_bq, (int, float)):
                    qty_val = float(qty_raw_bq)
                elif isinstance(qty_raw_bq, str):
                    cleaned = qty_raw_bq.strip().replace(',', '').replace(' ', '')
                    try:
                        qty_val = float(cleaned) if cleaned else 0.0
                    except ValueError:
                        qty_val = 0.0
                bq_qty_lookup[code_str] = qty_val

    # SORT STRATEGY: preserve original Excel row order within each parent group.
    # Only reorder top-level parent items (those with a non-nan code) relative to
    # each other using natural sort. Sub-items (nan code) stay glued to their parent.
    #
    # Algorithm:
    #   1. Walk rows in original order, grouping each named parent with its
    #      immediately following nan-coded children.
    #   2. Sort the groups by the parent's natural key.
    #   3. Flatten back to a list of row indices.
    last_row_wo = ws_wo.shape[0]

    # Build groups: each group = [parent_row_idx, child_row_idx, child_row_idx, ...]
    groups = []
    current_group = []
    for i in range(21, last_row_wo):
        code_raw = ws_wo.iloc[i, 0] if pd.notnull(ws_wo.iloc[i, 0]) else None
        code_str = str(code_raw).strip() if code_raw is not None else ""
        is_nan = (not code_str or code_str.lower() in ('nan', 'item', 'item no.'))
        if is_nan:
            # sub-item — append to current group
            current_group.append(i)
        else:
            # new named item — save previous group, start new one
            if current_group:
                groups.append(current_group)
            current_group = [i]
    if current_group:
        groups.append(current_group)

    # Sort groups by the natural key of their first (parent) row's item code
    def _group_sort_key(grp):
        i = grp[0]
        code_raw = ws_wo.iloc[i, 0] if pd.notnull(ws_wo.iloc[i, 0]) else None
        code_str = str(code_raw).strip() if code_raw is not None else ""
        return _natural_sort_key(code_str)

    groups.sort(key=_group_sort_key)

    # Flatten back to ordered row indices
    wo_row_indices = [i for grp in groups for i in grp]

    serial_counter = 0  # strict sequential counter for items that appear
    for i in wo_row_indices:
        item_code_raw = ws_wo.iloc[i, 0] if pd.notnull(ws_wo.iloc[i, 0]) else None
        item_code_str = str(item_code_raw).strip() if item_code_raw is not None else ""
        is_nan_code = (not item_code_str or item_code_str.lower() in ('nan', 'item', 'item no.'))

        # Quantity resolution: code-based for named items, positional for nan-coded sub-items
        if not is_nan_code and item_code_str in bq_qty_lookup:
            qty_raw = bq_qty_lookup[item_code_str]
        else:
            # Positional fallback — sheets are row-aligned for nan-coded sub-items
            qty_raw = ws_bq.iloc[i, 3] if i < ws_bq.shape[0] and pd.notnull(ws_bq.iloc[i, 3]) else None

        rate_raw = ws_wo.iloc[i, 4] if pd.notnull(ws_wo.iloc[i, 4]) else None

        qty = 0
        if isinstance(qty_raw, (int, float)):
            qty = float(qty_raw)
        elif isinstance(qty_raw, str):
            cleaned_qty = qty_raw.strip().replace(',', '').replace(' ', '')
            if cleaned_qty == '':
                qty = 0
            else:
                try:
                    qty = float(cleaned_qty)
                except ValueError:
                    qty = 0

        rate = 0
        if isinstance(rate_raw, (int, float)):
            rate = float(rate_raw)
        elif isinstance(rate_raw, str):
            cleaned_rate = rate_raw.strip().replace(',', '').replace(' ', '')
            if cleaned_rate == '':
                rate = 0
            else:
                try:
                    rate = float(cleaned_rate)
                except ValueError:
                    rate = 0

        # Keep parent/heading rows that have a description but zero rate AND zero quantity.
        # Only skip truly blank rows (no description) and Excel summary label rows.
        has_description = bool(str(ws_wo.iloc[i, 1]).strip()) if pd.notnull(ws_wo.iloc[i, 1]) else False
        desc_text = str(ws_wo.iloc[i, 1]).strip().lower() if pd.notnull(ws_wo.iloc[i, 1]) else ""
        is_summary = desc_text in ('total', 'grand total', 'add tender premium',
                                   'prem', 'premium', 'description') \
                     or 'tender premium' in desc_text
        if is_summary:
            continue  # skip Excel summary rows
        if (rate == 0) and (qty == 0) and not has_description:
            continue  # truly blank row — skip

        # FIX (Anomaly 2): Preserve item code exactly as stored in Excel.
        # Float codes like 3.0 stay as "3.0"; dot-notation "1.10" stays as "1.10".
        # Blank for nan-coded sub-items (cleaner than showing literal "nan").
        serial_no_display = "" if is_nan_code else item_code_str

        # Zero-rate rows (sub-headings with description only) — include description only
        if rate is None or rate == 0:
            serial_counter += 1
            item = {
                "serial_no": serial_no_display,
                "description": str(ws_wo.iloc[i, 1]) if pd.notnull(ws_wo.iloc[i, 1]) else "",
                "unit": "",
                "quantity": "",
                "quantity_since_last": "",
                "quantity_upto_date": "",
                "rate": "",
                "remark": str(ws_wo.iloc[i, 6]) if pd.notnull(ws_wo.iloc[i, 6]) else "",
                "amount": "",
                "amount_previous": "",
                "is_divider": False
            }
        else:
            # Calculate amounts
            amount_upto_date = round_up(qty * rate) if qty and rate else 0
            amount_since_previous = amount_upto_date  # Same as upto_date for first bill
            serial_counter += 1
            item = {
                "serial_no": serial_no_display,
                "description": str(ws_wo.iloc[i, 1]) if pd.notnull(ws_wo.iloc[i, 1]) else "",
                "unit": str(ws_wo.iloc[i, 2]) if pd.notnull(ws_wo.iloc[i, 2]) else "",
                "quantity": qty,
                "quantity_since_last": qty,
                "quantity_upto_date": qty,
                "rate": rate,
                "remark": str(ws_wo.iloc[i, 6]) if pd.notnull(ws_wo.iloc[i, 6]) else "",
                "amount": amount_upto_date,
                "amount_previous": amount_since_previous,
                "is_divider": False
            }
        first_page_data["items"].append(item)

    # Extra Items divider
    first_page_data["items"].append({
        "description": "Extra Items (With Premium)",
        "bold": True,
        "underline": True,
        "amount": 0,
        "amount_previous": 0,
        "quantity": 0,
        "quantity_since_last": 0,
        "quantity_upto_date": 0,
        "rate": 0,
        "serial_no": "",
        "unit": "",
        "remark": "",
        "is_divider": True
    })

    # Extra Items — serial numbers continue as E-1, E-2, ...
    last_row_extra = ws_extra.shape[0]
    extra_serial = 0
    for j in range(6, last_row_extra):
        qty_raw = ws_extra.iloc[j, 3] if pd.notnull(ws_extra.iloc[j, 3]) else None
        rate_raw = ws_extra.iloc[j, 5] if pd.notnull(ws_extra.iloc[j, 5]) else None

        qty = 0
        if isinstance(qty_raw, (int, float)):
            qty = float(qty_raw)
        elif isinstance(qty_raw, str):
            cleaned_qty = qty_raw.strip().replace(',', '').replace(' ', '')
            # Handle empty string case
            if cleaned_qty == '':
                qty = 0
            else:
                try:
                    qty = float(cleaned_qty)
                except ValueError:
                    qty = 0

        rate = 0
        if isinstance(rate_raw, (int, float)):
            rate = float(rate_raw)
        elif isinstance(rate_raw, str):
            cleaned_rate = rate_raw.strip().replace(',', '').replace(' ', '')
            # Handle empty string case
            if cleaned_rate == '':
                rate = 0
            else:
                try:
                    rate = float(cleaned_rate)
                except ValueError:
                    rate = 0

        # Skip blank extra item rows
        if (rate is None or rate == 0) and (qty is None or qty == 0):
            continue

        extra_serial += 1
        # Check if rate is blank or zero - if so, only populate S.No., Item of *, and Remarks
        if rate is None or rate == 0:
            item = {
                "serial_no": f"E-{extra_serial:02d}",
                "description": str(ws_extra.iloc[j, 2]) if pd.notnull(ws_extra.iloc[j, 2]) else "",
                "unit": "",
                "quantity": "",
                "quantity_since_last": "",
                "quantity_upto_date": "",
                "rate": "",
                "remark": str(ws_extra.iloc[j, 1]) if pd.notnull(ws_extra.iloc[j, 1]) else "",
                "amount": "",
                "amount_previous": "",
                "is_divider": False
            }
        else:
            item = {
                "serial_no": f"E-{extra_serial:02d}",
                "description": str(ws_extra.iloc[j, 2]) if pd.notnull(ws_extra.iloc[j, 2]) else "",
                "unit": str(ws_extra.iloc[j, 4]) if pd.notnull(ws_extra.iloc[j, 4]) else "",
                "quantity": qty,
                "quantity_since_last": qty,  # For template compatibility
                "quantity_upto_date": qty,   # For template compatibility
                "rate": rate,
                "remark": str(ws_extra.iloc[j, 1]) if pd.notnull(ws_extra.iloc[j, 1]) else "",
                "amount": round_up(qty * rate) if qty and rate else 0,
                "amount_previous": round_up(qty * rate) if qty and rate else 0,  # For template compatibility
                "is_divider": False
            }
        first_page_data["items"].append(item)
        extra_items_data["items"].append(item.copy())  # Copy for standalone Extra Items

    # Totals
    data_items = [item for item in first_page_data["items"] if not item.get("is_divider", False)]
    total_amount = round_up(sum(safe_float(item.get("amount", 0)) for item in data_items))
    premium_amount = round_up(total_amount * (premium_percent / 100) if premium_type == "above" else -total_amount * (premium_percent / 100))
    payable_amount = round_up(safe_float(total_amount) + safe_float(premium_amount))

    # Calculate net payable after deducting previous bill amount
    net_payable = round_up(safe_float(payable_amount) - safe_float(previous_bill_amount))
    
    first_page_data["totals"] = {
        "grand_total": total_amount,
        "premium": {"percent": premium_percent / 100, "type": premium_type, "amount": premium_amount},
        "payable": payable_amount,
        "last_bill_amount": previous_bill_amount if previous_bill_amount > 0 else 0,
        "net_payable": net_payable if previous_bill_amount > 0 else payable_amount
    }

    try:
        extra_items_start = next(i for i, item in enumerate(first_page_data["items"]) if item.get("description") == "Extra Items (With Premium)")
        extra_items = [item for item in first_page_data["items"][extra_items_start + 1:] if not item.get("is_divider", False)]
        extra_items_sum = round_up(sum(safe_float(item.get("amount", 0)) for item in extra_items))
        extra_items_premium = round_up(extra_items_sum * (premium_percent / 100) if premium_type == "above" else -extra_items_sum * (premium_percent / 100))
        first_page_data["totals"]["extra_items_sum"] = extra_items_sum + extra_items_premium
    except StopIteration:
        first_page_data["totals"]["extra_items_sum"] = 0

    # Last Page
    last_page_data = {"payable_amount": payable_amount, "amount_words": number_to_words(payable_amount)}

    # Deviation Statement — only non-zero rate items, strict serial numbers
    work_order_total = 0
    executed_total = 0
    overall_excess = 0
    overall_saving = 0
    dev_serial = 0
    # FIX: iterate in group-sorted order (same parent-child grouping as first_page)
    # and use hybrid quantity resolution.
    for i in wo_row_indices:
        item_code_raw_dev = ws_wo.iloc[i, 0] if pd.notnull(ws_wo.iloc[i, 0]) else None
        item_code_str_dev = str(item_code_raw_dev).strip() if item_code_raw_dev is not None else ""
        is_nan_code_dev = (not item_code_str_dev or item_code_str_dev.lower() in ('nan', 'item', 'item no.'))
        qty_wo_raw = ws_wo.iloc[i, 3] if pd.notnull(ws_wo.iloc[i, 3]) else None
        rate_raw = ws_wo.iloc[i, 4] if pd.notnull(ws_wo.iloc[i, 4]) else None
        # Hybrid BQ quantity resolution
        if not is_nan_code_dev and item_code_str_dev in bq_qty_lookup:
            qty_bill_raw = bq_qty_lookup[item_code_str_dev]
        else:
            qty_bill_raw = ws_bq.iloc[i, 3] if i < ws_bq.shape[0] and pd.notnull(ws_bq.iloc[i, 3]) else None

        qty_wo = 0
        if isinstance(qty_wo_raw, (int, float)):
            qty_wo = float(qty_wo_raw)
        elif isinstance(qty_wo_raw, str):
            cleaned_qty_wo = qty_wo_raw.strip().replace(',', '').replace(' ', '')
            if cleaned_qty_wo == '':
                qty_wo = 0
            else:
                try:
                    qty_wo = float(cleaned_qty_wo)
                except ValueError:
                    qty_wo = 0
        # Note: extra items get qty_wo = 0 explicitly in the extra-items loop below

        rate = 0
        if isinstance(rate_raw, (int, float)):
            rate = float(rate_raw)
        elif isinstance(rate_raw, str):
            cleaned_rate = rate_raw.strip().replace(',', '').replace(' ', '')
            # Handle empty string case
            if cleaned_rate == '':
                rate = 0
            else:
                try:
                    rate = float(cleaned_rate)
                except ValueError:
                    rate = 0

        qty_bill = 0
        if isinstance(qty_bill_raw, (int, float)):
            qty_bill = float(qty_bill_raw)
        elif isinstance(qty_bill_raw, str):
            cleaned_qty_bill = qty_bill_raw.strip().replace(',', '').replace(' ', '')
            # Handle empty string case
            if cleaned_qty_bill == '':
                qty_bill = 0
            else:
                try:
                    qty_bill = float(cleaned_qty_bill)
                except ValueError:
                    qty_bill = 0

        amt_wo = round_up(qty_wo * rate)
        amt_bill = round_up(qty_bill * rate)
        excess_qty = qty_bill - qty_wo if qty_bill > qty_wo else 0
        excess_amt = round_up(excess_qty * rate) if excess_qty > 0 else 0
        saving_qty = qty_wo - qty_bill if qty_bill < qty_wo else 0
        saving_amt = round_up(saving_qty * rate) if saving_qty > 0 else 0

        # Skip truly blank rows AND Excel summary/header label rows
        has_desc_dev = bool(str(ws_wo.iloc[i, 1]).strip()) if pd.notnull(ws_wo.iloc[i, 1]) else False
        desc_lower = str(ws_wo.iloc[i, 1]).strip().lower() if pd.notnull(ws_wo.iloc[i, 1]) else ""
        is_summary_label = desc_lower in ('total', 'grand total', 'add tender premium',
                                          'prem', 'premium', 'description') \
                           or 'tender premium' in desc_lower
        if is_summary_label:
            continue
        if (rate is None or rate == 0) and qty_wo == 0 and qty_bill == 0 and not has_desc_dev:
            continue  # truly blank row

        # Use actual item code as serial_no for deviation; blank for nan-coded sub-items
        dev_serial_no_display = "" if is_nan_code_dev else item_code_str_dev

        # Check if rate is blank or zero - if so, only populate Item No.
        if rate is None or rate == 0:
            dev_serial += 1
            item = {
                "serial_no": dev_serial_no_display,
                "description": str(ws_wo.iloc[i, 1]) if pd.notnull(ws_wo.iloc[i, 1]) else "",
                "unit": "",
                "qty_wo": "",
                "rate": "",
                "amt_wo": "",
                "qty_bill": "",
                "amt_bill": "",
                "excess_qty": "",
                "excess_amt": "",
                "saving_qty": "",
                "saving_amt": "",
                "remark": str(ws_wo.iloc[i, 6]) if pd.notnull(ws_wo.iloc[i, 6]) else ""
            }
            deviation_item_amt_wo = 0
            deviation_item_amt_bill = 0
            deviation_item_excess_amt = 0
            deviation_item_saving_amt = 0
        else:
            dev_serial += 1
            full_description = str(ws_wo.iloc[i, 1]) if pd.notnull(ws_wo.iloc[i, 1]) else ""
            item = {
                "serial_no": dev_serial_no_display,
                "description": full_description,
                "unit": str(ws_wo.iloc[i, 2]) if pd.notnull(ws_wo.iloc[i, 2]) else "",
                "qty_wo": qty_wo,
                "rate": rate,
                "amt_wo": amt_wo,
                "qty_bill": qty_bill,
                "amt_bill": amt_bill,
                "excess_qty": excess_qty,
                "excess_amt": excess_amt,
                "saving_qty": saving_qty,
                "saving_amt": saving_amt,
                "remark": str(ws_wo.iloc[i, 6]) if pd.notnull(ws_wo.iloc[i, 6]) else ""
            }
            deviation_item_amt_wo = amt_wo
            deviation_item_amt_bill = amt_bill
            deviation_item_excess_amt = excess_amt
            deviation_item_saving_amt = saving_amt

        deviation_data["items"].append(item)
        work_order_total += deviation_item_amt_wo
        executed_total += deviation_item_amt_bill
        overall_excess += deviation_item_excess_amt
        overall_saving += deviation_item_saving_amt

    # Add Extra Items divider to deviation statement
    deviation_data["items"].append({
        "serial_no": "",
        "description": "Extra Items (With Premium)",
        "unit": "",
        "qty_wo": 0,
        "rate": 0,
        "amt_wo": 0,
        "qty_bill": 0,
        "amt_bill": 0,
        "excess_qty": 0,
        "excess_amt": 0,
        "saving_qty": 0,
        "saving_amt": 0,
        "remark": "",
        "is_divider": True
    })

    # Process Extra Items for Deviation Statement — strict E-01, E-02 serial numbers
    extra_items_wo_total = 0
    extra_items_bill_total = 0
    dev_extra_serial = 0

    for j in range(6, last_row_extra):
        qty_raw = ws_extra.iloc[j, 3] if pd.notnull(ws_extra.iloc[j, 3]) else None
        rate_raw = ws_extra.iloc[j, 5] if pd.notnull(ws_extra.iloc[j, 5]) else None

        qty = 0
        if isinstance(qty_raw, (int, float)):
            qty = float(qty_raw)
        elif isinstance(qty_raw, str):
            cleaned_qty = qty_raw.strip().replace(',', '').replace(' ', '')
            if cleaned_qty == '':
                qty = 0
            else:
                try:
                    qty = float(cleaned_qty)
                except ValueError:
                    qty = 0

        rate = 0
        if isinstance(rate_raw, (int, float)):
            rate = float(rate_raw)
        elif isinstance(rate_raw, str):
            cleaned_rate = rate_raw.strip().replace(',', '').replace(' ', '')
            if cleaned_rate == '':
                rate = 0
            else:
                try:
                    rate = float(cleaned_rate)
                except ValueError:
                    rate = 0

        # For extra items in deviation: qty_wo = 0 (not in work order), qty_bill = qty (executed)
        amt_bill = round_up(qty * rate) if qty and rate else 0
        excess_qty = qty  # All extra item quantity is excess
        excess_amt = amt_bill  # All extra item amount is excess

        # Skip blank rows
        if (rate is None or rate == 0) and (qty is None or qty == 0):
            continue

        dev_extra_serial += 1
        if rate is None or rate == 0:
            extra_item = {
                "serial_no": f"E-{dev_extra_serial:02d}",
                "description": str(ws_extra.iloc[j, 2]) if pd.notnull(ws_extra.iloc[j, 2]) else "",
                "unit": "",
                "qty_wo": "",
                "rate": "",
                "amt_wo": "",
                "qty_bill": "",
                "amt_bill": "",
                "excess_qty": "",
                "excess_amt": "",
                "saving_qty": "",
                "saving_amt": "",
                "remark": str(ws_extra.iloc[j, 1]) if pd.notnull(ws_extra.iloc[j, 1]) else ""
            }
        else:
            extra_item = {
                "serial_no": f"E-{dev_extra_serial:02d}",
                "description": str(ws_extra.iloc[j, 2]) if pd.notnull(ws_extra.iloc[j, 2]) else "",
                "unit": str(ws_extra.iloc[j, 4]) if pd.notnull(ws_extra.iloc[j, 4]) else "",
                "qty_wo": 0,  # Not in work order
                "rate": rate,
                "amt_wo": 0,  # Not in work order
                "qty_bill": qty,
                "amt_bill": amt_bill,
                "excess_qty": excess_qty,
                "excess_amt": excess_amt,
                "saving_qty": 0,  # No savings for extra items
                "saving_amt": 0,  # No savings for extra items
                "remark": str(ws_extra.iloc[j, 1]) if pd.notnull(ws_extra.iloc[j, 1]) else ""
            }
            # Add to totals
            extra_items_wo_total += 0  # Not in work order
            extra_items_bill_total += amt_bill
        
        deviation_data["items"].append(extra_item)
    
    # Update totals to include extra items
    work_order_total += extra_items_wo_total  # 0 for extra items
    executed_total += extra_items_bill_total
    overall_excess += extra_items_bill_total  # All extra items are excess

    # Deviation Summary
    tender_premium_f = round_up(safe_float(work_order_total) * (premium_percent / 100) if premium_type == "above" else -safe_float(work_order_total) * (premium_percent / 100))
    tender_premium_h = round_up(safe_float(executed_total) * (premium_percent / 100) if premium_type == "above" else -safe_float(executed_total) * (premium_percent / 100))
    tender_premium_j = round_up(safe_float(overall_excess) * (premium_percent / 100) if premium_type == "above" else -safe_float(overall_excess) * (premium_percent / 100))
    tender_premium_l = round_up(safe_float(overall_saving) * (premium_percent / 100) if premium_type == "above" else -safe_float(overall_saving) * (premium_percent / 100))
    grand_total_f = round_up(safe_float(work_order_total) + safe_float(tender_premium_f))
    grand_total_h = round_up(safe_float(executed_total) + safe_float(tender_premium_h))
    grand_total_j = round_up(safe_float(overall_excess) + safe_float(tender_premium_j))
    grand_total_l = round_up(safe_float(overall_saving) + safe_float(tender_premium_l))
    net_difference = round_up(safe_float(grand_total_h) - safe_float(grand_total_f))
    
    # Calculate percentage of deviation
    # Percentage = (net_difference / grand_total_f) * 100
    percentage_deviation = 0.0
    if grand_total_f != 0:
        percentage_deviation = abs((net_difference / grand_total_f) * 100)
    
    # Net difference should always be shown as absolute value with proper label
    # If negative, it's a saving; if positive, it's excess
    net_difference_abs = abs(net_difference)
    is_saving = net_difference < 0

    deviation_data["summary"] = {
        "work_order_total": round(work_order_total),
        "executed_total": round(executed_total),
        "overall_excess": round(overall_excess),
        "overall_saving": round(overall_saving),
        "premium": {"percent": premium_percent / 100, "type": premium_type},
        "tender_premium_f": tender_premium_f,
        "tender_premium_h": tender_premium_h,
        "tender_premium_j": tender_premium_j,
        "tender_premium_l": tender_premium_l,
        "grand_total_f": grand_total_f,
        "grand_total_h": grand_total_h,
        "grand_total_j": grand_total_j,
        "grand_total_l": grand_total_l,
        "net_difference": net_difference_abs,  # Always positive
        "is_saving": is_saving,  # True if saving, False if excess
        "percentage_deviation": round_up(percentage_deviation * 100) / 100.0  # Percentage with 2 decimals (approx)
    }

    return first_page_data, last_page_data, deviation_data, extra_items_data, note_sheet_data