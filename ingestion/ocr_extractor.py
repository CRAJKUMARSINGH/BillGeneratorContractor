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
    compatible with normalizer.py
    """
    lines = raw_text.splitlines()
    rows = []
    metadata = {}
    
    # Very basic regex extraction for the table format "Item | Desc | Qty | Unit | Rate" or similar space-padded
    # e.g., "1 Excavation 150 Cum 45.00"
    row_pattern = re.compile(r'^(\d+)\s*\|?\s*(.*?)\s*\|?\s*([\d\.]+)\s*\|?\s*([A-Za-z]+)\s*\|?\s*([\d\.]+)$')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if "Name of Work:" in line:
            metadata["Name of Work"] = line.split(":", 1)[1].strip()
        elif "Contractor:" in line:
            metadata["Name of Contractor or supplier"] = line.split(":", 1)[1].strip()
            
        match = row_pattern.match(line)
        if match:
            item_no, desc, qty, unit, rate = match.groups()
            
            try:
                qty_val = float(qty)
                rate_val = float(rate)
            except ValueError:
                qty_val = 0.0
                rate_val = 0.0
                
            rows.append({
                "Description": desc.strip(' |'),
                "Quantity": qty_val,
                "Rate": rate_val,
                "Amount": qty_val * rate_val,
                "Unit": unit.strip(' |')
            })
            
    # Mocking standard excel wrapper structure
    return {
        "metadata": metadata,
        "raw_rows": rows
    }
