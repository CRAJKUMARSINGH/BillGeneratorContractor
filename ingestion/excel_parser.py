import logging
import os
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)

# ─── Configuration & Constants ───────────────────────────────────────────────

# Generic column aliases for fallback parsing
COL_ALIASES = {
    'sno': 'serial_no', 's.no': 'serial_no', 'sr': 'serial_no', 'sr.no': 'serial_no',
    'serial': 'serial_no', 'serial no': 'serial_no', 'serial_no': 'serial_no',
    '#': 'serial_no', 'item': 'serial_no',
    'description': 'description', 'desc': 'description',
    'description of work': 'description', 'particulars': 'description',
    'name': 'description', 'details': 'description',
    'unit': 'unit', 'uom': 'unit', 'units': 'unit',
    'qty since last': 'qty_since_last_bill', 'qty since last bill': 'qty_since_last_bill',
    'quantity since last': 'qty_since_last_bill', 'qty_since_last_bill': 'qty_since_last_bill',
    'since last': 'qty_since_last_bill', 'incremental qty': 'qty_since_last_bill',
    'qty to date': 'qty_to_date', 'quantity to date': 'qty_to_date', 'qty_to_date': 'qty_to_date',
    'cumulative qty': 'qty_to_date', 'total qty': 'qty_to_date',
    'rate': 'rate', 'unit rate': 'rate', 'unit price': 'rate', 'price': 'rate',
    'remarks': 'remarks', 'remark': 'remarks', 'notes': 'remarks', 'bsr': 'remarks',
}

TITLE_MAP = {
    'name of contractor or supplier':  'contractor_name',
    'name of contractor':              'contractor_name',
    'contractor':                      'contractor_name',
    'name of work':                    'work_name',
    'serial no. of this bill':         'serial_number',
    'serial no of this bill':          'serial_number',
    'cash book voucher no. and date':  'voucher_number',
    'cash book voucher no':            'voucher_number',
    'reference to work order or agreement': 'work_order_reference',
    'agreement no.':                   'agreement_number',
    'agreement no':                    'agreement_number',
    'tender premium %':                'tender_premium_percentage',
    'tender premium':                  'tender_premium_percentage',
    'amount paid vide last bill':      'last_bill_deduction',
    'date of written order to commence work': 'commencement_date',
    'st. date of start':               'scheduled_start_date',
    'st. date of completion':          'scheduled_completion_date',
    'date of actual completion of work': 'actual_completion_date',
    'date of measurement':             'measurement_date',
}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def norm(s: Any) -> str:
    """Normalize strings for fuzzy matching."""
    if s is None: return ""
    s = str(s).lower()
    s = re.sub(r'[_\-\/\\]+', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()

def to_num(v: Any) -> float:
    """Safely convert Excel values to float."""
    if pd.isna(v) or v == "" or v is None:
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    try:
        # Remove currency symbols and commas
        cleaned = re.sub(r'[^\d.-]', '', str(v))
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0

def to_str(v: Any) -> str:
    """Safely convert any value to trimmed string."""
    if pd.isna(v) or v is None:
        return ""
    return str(v).strip()


# ─── Core Logic ───────────────────────────────────────────────────────────────

def _parse_item_sheet(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Parse a standard item sheet (Agreement/Work Order/Bill Quantity).
    Handles header discovery and parent-child row reconstruction.
    """
    if df.empty:
        return []

    # ── Header Discovery ───────────────────
    header_row_idx = -1
    col_map = {}
    
    # Scan first 10 rows for headers
    for idx, row in df.head(10).iterrows():
        normalized_row = [norm(cell) for cell in row]
        
        # We need at least 'description' and 'rate' or 'quantity' to consider it a header row
        found_desc = -1
        for i, cell in enumerate(normalized_row):
            mapped = COL_ALIASES.get(cell)
            if mapped == 'description':
                found_desc = i
            if mapped:
                col_map[mapped] = i
                
        if found_desc >= 0 and ('rate' in col_map or 'qty_to_date' in col_map):
            header_row_idx = idx
            break

    if header_row_idx == -1:
        logger.debug("Could not find standard headers in sheet.")
        return []

    # ── Row Extraction ─────────────────────
    rows = []
    last_parent_desc = ""
    last_parent_item = ""

    # Iterate from row after header
    for idx in range(header_row_idx + 1, len(df)):
        row_data = df.iloc[idx]
        
        raw_desc = to_str(row_data.iloc[col_map['description']]) if 'description' in col_map else ""
        raw_item = to_str(row_data.iloc[col_map['serial_no']]) if 'serial_no' in col_map else ""
        qty      = to_num(row_data.iloc[col_map['qty_to_date']]) if 'qty_to_date' in col_map else 0.0
        rate     = to_num(row_data.iloc[col_map['rate']]) if 'rate' in col_map else 0.0
        unit     = to_str(row_data.iloc[col_map['unit']]) if 'unit' in col_map else ""
        remarks  = to_str(row_data.iloc[col_map['remarks']]) if 'remarks' in col_map else ""

        if not raw_desc and not raw_item:
            continue

        # Detect Parent/Category row (has item number but no unit/qty/rate)
        if raw_item and not unit and qty == 0 and rate == 0:
            last_parent_desc = raw_desc or last_parent_desc
            last_parent_item = raw_item
            continue

        # Sub-item reconstruction
        full_desc = raw_desc
        if last_parent_desc and raw_desc and len(raw_desc) < 60:
            if last_parent_desc.lower()[:15] not in raw_desc.lower():
                full_desc = f"{last_parent_desc} — {raw_desc}"
        elif not raw_desc:
            full_desc = last_parent_desc

        if not full_desc:
            continue

        rows.append({
            "serial_no": raw_item or last_parent_item or str(len(rows) + 1),
            "description": full_desc,
            "unit": unit,
            "qty_since_last_bill": 0.0,  # placeholder
            "qty_to_date": qty,
            "rate": rate,
            "remarks": remarks,
            "amount": qty * rate
        })

    return rows


def parse_excel_to_raw(file_path: str) -> Dict[str, Any]:
    """
    Main entry point. Dispatches between Domain-specific (4-sheet) and Generic parsing.
    """
    try:
        # Load all sheets into a dictionary of DataFrames
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names
        all_sheets = {name: excel_file.parse(name) for name in sheet_names}
    except Exception as e:
        logger.error(f"Failed to read Excel {file_path}: {e}")
        return {"error": str(e), "confidence": 0}

    # ── 1. Try Domain-Specific (4-sheet PWD format) ───────────────────────────
    has_title      = 'Title' in sheet_names
    has_bill_qty   = 'Bill Quantity' in sheet_names
    has_work_order = 'Work Order' in sheet_names or 'Agreement' in sheet_names
    
    if has_bill_qty:
        logger.info("Detected Domain-specific (PWD) format.")
        header = {}
        
        # 1.1 Parse Title Sheet
        if has_title:
            df_title = all_sheets['Title']
            for _, row in df_title.iterrows():
                if row.empty or pd.isna(row.iloc[0]): continue
                label = norm(to_str(row.iloc[0]).replace(':', ''))
                val = row.iloc[1] if len(row) > 1 else None
                
                mapped_key = TITLE_MAP.get(label)
                if mapped_key:
                    if mapped_key in ('tender_premium_percentage', 'last_bill_deduction'):
                        header[mapped_key] = to_num(val)
                    else:
                        header[mapped_key] = to_str(val)

        # 1.2 Parse Bill Quantity (Core data)
        bill_qty_rows = _parse_item_sheet(all_sheets['Bill Quantity'])
        
        # 1.3 Parse Work Order (for comparison)
        wo_sheet_name = 'Work Order' if 'Work Order' in sheet_names else 'Agreement'
        work_order_rows = _parse_item_sheet(all_sheets[wo_sheet_name]) if has_work_order else []
        
        # 1.4 Calculate Qty Since Last Bill
        # Map description -> qty_to_date from Work Order
        wo_map = {norm(r['description']): r['qty_to_date'] for r in work_order_rows}
        
        final_rows = []
        for r in bill_qty_rows:
            wo_qty = wo_map.get(norm(r['description']), 0.0)
            # Current - Previous (Work Order serves as baseline of previous/limit)
            r['qty_since_last_bill'] = max(0.0, r['qty_to_date'] - wo_qty)
            final_rows.append(r)

        # 1.5 Handle Extra Items
        if 'Extra Items' in sheet_names:
            extra_rows = _parse_item_sheet(all_sheets['Extra Items'])
            for er in extra_rows:
                er['qty_since_last_bill'] = er['qty_to_date'] # Extra items are usually all new
                final_rows.append(er)

        confidence = 0.9 if final_rows else 0.1
        return {
            "metadata": header,
            "raw_rows": final_rows,
            "confidence": confidence,
            "warnings": []
        }

    # ── 2. Fallback: Generic Format ───────────────────────────────────────────
    logger.info("Falling back to Generic format parsing.")
    best_rows = []
    best_sheet = ""

    for name, df in all_sheets.items():
        rows = _parse_item_sheet(df)
        if len(rows) > len(best_rows):
            best_rows = rows
            best_sheet = name

    return {
        "metadata": {"filename": os.path.basename(file_path), "parsed_sheet": best_sheet},
        "raw_rows": best_rows,
        "confidence": 0.4 if best_rows else 0.0,
        "warnings": ["Used generic parser — document structure not fully recognized."]
    }
