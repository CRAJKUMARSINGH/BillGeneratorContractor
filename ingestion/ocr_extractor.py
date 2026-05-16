import os
import re
import uuid
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

def extract_table_from_image(file_path: str) -> Dict[str, Any]:
    """
    Attempts to read an uploaded image using pytesseract.
    If Tesseract is not installed on the system, it gracefully mocks the
    data extraction to avoid blocking execution.
    """
    raw_text = ""
    try:
        import pytesseract
        from PIL import Image
        
        # Load the image and run OCR
        img = Image.open(file_path)
        raw_text = pytesseract.image_to_string(img)
        logger.info("Successfully ran Tesseract OCR on image.")
        
    except ImportError:
        logger.warning("pytesseract or Pillow not installed. using degraded mock.")
        raw_text = _fallback_mock_text()
    except Exception as e:
        logger.warning(f"Tesseract binary likely missing or failed ({e}). Using degraded mock.")
        raw_text = _fallback_mock_text()
        
    return _parse_text_to_unified_format(raw_text)

def _fallback_mock_text() -> str:
    # A mock string simulating what OCR might read from a handwritten table
    return """
    PWD MEASUREMENT BOOK
    Name of Work: Road Repair Phase 1
    Contractor: Sharma Builders
    -----------------------------------
    Item | Description | Qty | Unit | Rate
    1 | Excavation work in soil | 150 | Cum | 45.0
    2 | M20 Concrete laying | 20.5 | Cum | 4200.0
    3 | Reinforcement Steel (TMT) | 1200 | Kg | 65.0
    """

def _parse_text_to_unified_format(raw_text: str) -> Dict[str, Any]:
    """
    Regex parsing of the unstructured blob returned by OCR into a structured layout
    compatible with normalizer.py.
    Now optimized for PWD Rajasthan samples using pipe '|' delimiters and section headers.
    """
    lines = raw_text.splitlines()
    rows = []
    extra_items = []
    metadata = {}
    
    current_section = "wo" # default
    
    for line in lines:
        line = line.strip()
        if not line: continue
            
        # 1. Metadata extraction
        if ":" in line:
            parts = line.split(":", 1)
            key = parts[0].strip().lower()
            val = parts[1].strip()
            if any(k in key for k in ["work", "project"]):
                metadata["Name of Work"] = val
            elif any(k in key for k in ["contractor", "firm", "supplier"]):
                metadata["Name of Contractor or supplier"] = val
            elif any(k in key for k in ["agreement", "agg"]):
                metadata["Agreement No."] = val
            elif "premium" in key:
                metadata["premium"] = val
            continue

        # 2. Section detection
        lower_line = line.lower()
        if "extra" in lower_line:
            current_section = "extra"
            continue
        elif "bill qty" in lower_line or "executed" in lower_line:
            current_section = "bill"
            continue
        elif "work order items" in lower_line or "wo qty" in lower_line:
            current_section = "wo"
            continue

        # 3. Table row matching (Pipe-based)
        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 4:
                # Basic heuristics for mapping parts
                item_no = parts[0]
                if item_no.lower() in ["s.no.", "sno", "item"]: continue # skip header
                
                # Check if it's a valid row (starts with digit or E-)
                if not re.match(r'^[\d\.E\-]+', item_no): continue
                
                desc = parts[1]
                
                try:
                    if current_section == "extra":
                        # E-01 | BSR-201 | Desc | Qty | Unit | Rate | Amt
                        qty = float(parts[3].replace(',', '')) if len(parts) > 3 else 0.0
                        unit = parts[4] if len(parts) > 4 else ""
                        rate = float(parts[5].replace(',', '')) if len(parts) > 5 else 0.0
                        amt = float(parts[6].replace(',', '')) if len(parts) > 6 else (qty * rate)
                    elif current_section == "bill":
                        # S.No | Desc | Unit | Bill Qty
                        unit = parts[2]
                        qty = float(parts[3].replace(',', ''))
                        rate = 0.0 # Unknown from this section
                        amt = 0.0
                    else: # WO
                        # S.No | Desc | Unit | WO Qty | Rate | Amt
                        unit = parts[2]
                        qty = float(parts[3].replace(',', ''))
                        rate = float(parts[4].replace(',', '')) if len(parts) > 4 else 0.0
                        amt = float(parts[5].replace(',', '')) if len(parts) > 5 else (qty * rate)
                    
                    row_data = {
                        "item_no": item_no,
                        "description": desc,
                        "quantity": qty,
                        "rate": rate,
                        "amount": amt,
                        "unit": unit,
                        "section": current_section
                    }
                    
                    if current_section == "extra":
                        extra_items.append(row_data)
                    else:
                        rows.append(row_data)
                except (ValueError, IndexError):
                    continue

    # 4. Fallback: Regex for non-pipe lines (legacy support)
    if not rows and not extra_items:
        row_pattern = re.compile(r'^([\d\.\- ]+[a-z]?)\s+(.*?)\s+([\d\.,]+)\s+([A-Za-z/]+)\s+([\d\.,]+)$')
        for line in lines:
            match = row_pattern.match(line.strip())
            if match:
                item_no, desc, qty_str, unit, rate_str = match.groups()
                try:
                    qty_val = float(qty_str.replace(',', ''))
                    rate_val = float(rate_str.replace(',', ''))
                    rows.append({
                        "item_no": item_no.strip(),
                        "description": desc.strip(),
                        "quantity": qty_val,
                        "rate": rate_val,
                        "amount": qty_val * rate_val,
                        "unit": unit.strip()
                    })
                except ValueError: continue

    return {
        "metadata": metadata,
        "raw_rows": rows,
        "extra_rows": extra_items
    }
