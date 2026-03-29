import logging
from typing import Dict, Any, List, Optional
import pandas as pd
# from .models import RawItem, UnifiedBillModel # No longer needed, returning dict

logger = logging.getLogger(__name__)

# ─── Configuration ─────────────────────────────────────────────────────────────

COL_ALIASES = {
    'item': 'serial_no', 's. no': 'serial_no', 'sr. no': 'serial_no', 'sl no': 'serial_no',
    'sno': 'serial_no', 'no.': 'serial_no', 'id': 'serial_no', 'no': 'serial_no',
    'description': 'description', 'item description': 'description', 'particulars': 'description',
    'name': 'description', 'details': 'description', 'desc': 'description',
    'unit': 'unit', 'uom': 'unit', 'units': 'unit',
    'qty': 'qty_to_date', 'quantity': 'qty_to_date', 'qty to date': 'qty_to_date',
    'upto date': 'qty_to_date', 'total quantity': 'qty_to_date', 'quantity upto': 'qty_to_date',
    'cumulative qty': 'qty_to_date', 'to date': 'qty_to_date',
    'rate': 'rate', 'unit rate': 'rate', 'unit price': 'rate', 'price': 'rate',
    'amount': 'amount', 'total rs': 'amount', 'total': 'amount', 'cost': 'amount',
    'estimated cost': 'amount', 'totalrs': 'amount',
    'remarks': 'remarks', 'remark': 'remarks', 'notes': 'remarks', 'bsr': 'remarks'
}

TITLE_MAP = {
    'Agreement No.': 'agreement_no',
    'Name of Contractor': 'contractor_name',
    'Name of Work': 'work_name',
    'Voucher No.': 'voucher_no'
}

def norm(val: Any) -> str:
    if pd.isna(val) or val is None: return ""
    return str(val).strip().lower().replace(".", "").replace("_", " ")

# ─── Core Logic ───────────────────────────────────────────────────────────────

def _parse_item_sheet(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Parse a standard item sheet (Agreement/Work Order/Bill Quantity).
    Handles header discovery (columns vs rows) and parent-child row reconstruction.
    """
    if df.empty:
        return []

    # ── Header Discovery ───────────────────
    header_row_idx = -1
    col_map = {}
    
    # Check 1: Are columns already named correctly?
    current_map = {}
    for i, col_name in enumerate(df.columns):
        mapped = COL_ALIASES.get(norm(col_name))
        if mapped:
            current_map[mapped] = i
    
    if 'description' in current_map and ('rate' in current_map or 'qty_to_date' in current_map or 'amount' in current_map):
        header_row_idx = -1 # Data starts at row 0
        col_map = current_map
        logger.info(f"Using DataFrame columns for mapping: {col_map}")

    # Check 2: Scan first 20 rows if columns didn't match
    if header_row_idx == -1 and not col_map:
        for idx, row in df.head(20).iterrows():
            normalized_row = [norm(cell) for cell in row]
            
            found_desc = -1
            current_map = {}
            for i, cell in enumerate(normalized_row):
                mapped = COL_ALIASES.get(cell)
                if mapped:
                    current_map[mapped] = i
                    if mapped == 'description':
                        found_desc = i
                    
            if found_desc >= 0 and ('rate' in current_map or 'qty_to_date' in current_map or 'amount' in current_map):
                header_row_idx = idx
                col_map = current_map
                logger.info(f"Found headers at row {idx}: {col_map}")
                break

    if not col_map:
        logger.warning("Could not find standard headers in sheet.")
        return []

    # ── Row Extraction ─────────────────────
    rows = []
    last_parent_desc = ""
    last_parent_item = ""

    # Iterate from row after header
    start_idx = header_row_idx + 1 if header_row_idx >= 0 else 0
    
    for idx in range(start_idx, len(df)):
        row_data = df.iloc[idx]
        
        # Safe extraction based on map
        def get_val(key, default=""):
            if key not in col_map: return default
            val = row_data.iloc[col_map[key]]
            if pd.isna(val): return default
            return val

        raw_desc = str(get_val('description')).strip()
        raw_item = str(get_val('serial_no')).strip()
        unit = str(get_val('unit')).strip()
        qty = 0.0
        rate = 0.0
        amount = 0.0
        
        try:
            qty_val = get_val('qty_to_date', 0.0)
            qty = float(qty_val) if qty_val != "" else 0.0
            
            rate_val = get_val('rate', 0.0)
            rate = float(rate_val) if rate_val != "" else 0.0
            
            amt_val = get_val('amount', 0.0)
            amount = float(amt_val) if amt_val != "" else 0.0
        except (ValueError, TypeError):
            pass

        if not raw_desc and not raw_item:
            continue

        # Detect Parent/Category row (has item number but no unit/qty/rate)
        # Often these have sub-items like 1.5.1, 1.5.2 under a main description '1.5'
        if raw_item and not unit and qty == 0 and rate == 0 and amount == 0:
            last_parent_desc = raw_desc or last_parent_desc
            last_parent_item = raw_item
            continue

        # Skip rows that are clearly just empty or labels (e.g. Sub-totals)
        if not unit and qty == 0 and rate == 0 and amount == 0:
            continue

        rows.append({
            "serial_no": raw_item,
            "description": raw_desc,
            "parent_item": last_parent_item,
            "parent_description": last_parent_desc,
            "unit": unit,
            "quantity": qty,
            "rate": rate,
            "amount": amount or (qty * rate),
            "remarks": str(get_val('remarks'))
        })

    logger.info(f"Parsed {len(rows)} items from sheet.")
    return rows

def parse_excel_to_raw(path: str) -> Dict[str, Any]:
    """Main entry point for Excel ingestion."""
    logger.info(f"Parsing Excel: {path}")
    
    try:
        # Load all sheets explicitly to avoid missing any
        all_sheets = pd.read_excel(path, sheet_name=None)
    except Exception as e:
        logger.error(f"Failed to read Excel {path}: {e}")
        return {"error": str(e)}

    # PWD 4-Sheet Strategy
    # Sheets usually named: 'Bill', 'Abstract', 'Extra Items', 'Recapitulation'
    main_sheet_key = None
    # Prioritize 'Bill Quantity' as seen in 3rdFinalVidExtra.xlsx
    priority_keys = ["Bill Quantity", "Bill", "Abstract", "Measurement"]
    for pk in priority_keys:
        for k in all_sheets.keys():
            if pk.lower() in k.lower():
                main_sheet_key = k
                break
        if main_sheet_key: break
            
    if not main_sheet_key:
        # Fallback to the first non-empty sheet
        for k, v in all_sheets.items():
            if not v.empty:
                main_sheet_key = k
                break

    if not main_sheet_key:
        return {"error": "Could not identify any valid data sheet in the workbook."}

    logger.info(f"Selected main sheet: {main_sheet_key}")
    main_rows = _parse_item_sheet(all_sheets[main_sheet_key])
    
    extra_rows = []
    extra_sheet_key = None
    for k in all_sheets.keys():
        if "Extra" in k.lower():
            extra_sheet_key = k
            break
            
    if extra_sheet_key:
        logger.info(f"Selected extra items sheet: {extra_sheet_key}")
        extra_rows = _parse_item_sheet(all_sheets[extra_sheet_key])

    # Metadata Extraction (First sheet, top few rows)
    metadata = {
        "voucher_no": "",
        "contractor_name": "",
        "work_name": "",
        "agreement_no": "",
        "has_extra_items": len(extra_rows) > 0
    }
    
    # Simple top-row search for metadata in ALL sheets if main fails
    for sheet_name in [main_sheet_key] + list(all_sheets.keys()):
        df_meta = all_sheets[sheet_name].head(15)
        for idx, row in df_meta.iterrows():
            text = " ".join([str(c) for c in row if not pd.isna(c)])
            for label, key in TITLE_MAP.items():
                if label.lower() in text.lower() and not metadata[key]:
                    # Assume value is in the next cell or same cell after colon
                    metadata[key] = text.split(label)[-1].strip(": ").strip()
    
    return {
        "items": main_rows,
        "extra_items": extra_rows,
        "metadata": metadata
    }
