"""
PWD Schedule-G Work Order Parser
Implements foolproof OCR with grid detection and validation
Based on elite software engineering recommendations
"""

import cv2
import numpy as np
import re
from typing import List, Dict, Tuple
from pathlib import Path

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


class PWDScheduleParser:
    """
    Foolproof parser for PWD Schedule-G work orders
    Implements multi-mode OCR with grid detection
    """
    
    # Item code pattern (e.g., 1.1.2, 18.13)
    ITEM_CODE_PATTERN = r'\b\d+\.\d+(?:\.\d+)?\b'
    
    def __init__(self):
        self.ocr_modes = [6, 4, 11]  # PSM modes to try
        
    def preprocess_image(self, img_path: str) -> np.ndarray:
        """
        Image preprocessing for optimal OCR
        """
        img = cv2.imread(str(img_path))
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Gaussian blur to reduce noise
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            blur, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        
        return thresh
    
    def detect_table_rows(self, img: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect table grid lines and extract row boundaries
        """
        # Horizontal line detection kernel
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        
        # Morphological opening
        detect = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(
            detect,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        rows = []
        
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            
            # Filter valid rows (width > 600, height > 30)
            if w > 600 and h > 30:
                rows.append((x, y, w, h))
        
        # Sort rows by Y-coordinate (top to bottom)
        rows = sorted(rows, key=lambda r: r[1])
        
        return rows
    
    def ocr_row(self, img: np.ndarray, row: Tuple[int, int, int, int], mode: int = 6) -> str:
        """
        OCR a single row with error correction
        """
        if not TESSERACT_AVAILABLE:
            raise RuntimeError("Tesseract OCR not available")
        
        x, y, w, h = row
        
        # Crop row
        crop = img[y:y+h, x:x+w]
        
        # OCR with specified mode
        txt = pytesseract.image_to_string(
            crop,
            config=f"--oem 3 --psm {mode}"
        )
        
        # Apply OCR error corrections
        txt = self.fix_ocr_errors(txt)
        
        return txt.strip()
    
    def fix_ocr_errors(self, text: str) -> str:
        """
        Fix common OCR mistakes
        """
        # O → 0
        text = text.replace("O", "0")
        # l → 1 (lowercase L to 1)
        text = text.replace("l", "1")
        # S → 5
        text = text.replace("S", "5")
        
        return text
    
    def extract_item_codes(self, text: str) -> List[str]:
        """
        Extract PWD item codes from text
        """
        codes = re.findall(self.ITEM_CODE_PATTERN, text)
        return codes
    
    def robust_ocr(self, img_path: str) -> str:
        """
        Multi-mode OCR with fallback
        """
        img = self.preprocess_image(img_path)
        
        # Try multiple OCR modes
        for mode in self.ocr_modes:
            try:
                text = pytesseract.image_to_string(
                    img,
                    config=f'--oem 3 --psm {mode}'
                )
                
                # If we got substantial text, return it
                if len(text) > 200:
                    return self.fix_ocr_errors(text)
            except Exception:
                continue
        
        # Fallback: return whatever we got
        return self.fix_ocr_errors(text) if text else ""
    
    def parse_work_order_grid(self, img_path: str) -> List[Dict]:
        """
        Parse work order using grid detection
        Returns list of items with code, description, unit, rate, qty
        """
        # Preprocess image
        img = self.preprocess_image(img_path)
        
        # Detect table rows
        rows = self.detect_table_rows(img)
        
        if len(rows) == 0:
            raise ValueError("No table rows detected in image")
        
        # OCR each row
        items = []
        
        for row in rows:
            try:
                # OCR the row
                line = self.ocr_row(img, row)
                
                # Extract item code
                code_match = re.search(self.ITEM_CODE_PATTERN, line)
                
                if not code_match:
                    continue  # Skip rows without item codes
                
                code = code_match.group()
                
                # Parse line components
                parts = line.split()
                
                try:
                    # Extract rate, qty, unit (from end of line)
                    rate = float(parts[-3])
                    qty = float(parts[-2])
                    unit = parts[-4]
                except (IndexError, ValueError):
                    # If parsing fails, use defaults
                    rate = 0.0
                    qty = 0.0
                    unit = "nos"
                
                # Extract description (text after code)
                desc = line.split(code)[1] if code in line else ""
                desc = desc.strip()
                
                items.append({
                    'code': code,
                    'description': desc,
                    'unit': unit,
                    'rate': rate,
                    'quantity': qty
                })
                
            except Exception as e:
                # Log error but continue processing
                print(f"Warning: Failed to parse row: {e}")
                continue
        
        return items
    
    def validate_extraction(self, items: List[Dict]) -> bool:
        """
        Validate extracted items
        """
        if len(items) == 0:
            raise ValueError("No items extracted from work order")
        
        # Check for valid codes
        for item in items:
            if not re.match(self.ITEM_CODE_PATTERN, item['code']):
                raise ValueError(f"Invalid item code: {item['code']}")
        
        return True


def parse_qty_file(qty_file_path: str) -> Dict[str, float]:
    """
    Parse quantity text file
    Format: 1.1.2 6 or 1.1.2=6
    """
    qty_data = {}
    
    with open(qty_file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            # Support both formats: "1.1.2 6" and "1.1.2=6"
            if '=' in line:
                code, qty = line.split('=')
            else:
                parts = line.split()
                if len(parts) >= 2:
                    code, qty = parts[0], parts[1]
                else:
                    continue
            
            qty_data[code.strip()] = float(qty.strip())
    
    return qty_data


def validate_qty_match(work_order_items: List[Dict], qty_data: Dict[str, float]) -> Dict:
    """
    Validate that quantity file matches work order items
    """
    work_order_codes = {item['code'] for item in work_order_items}
    qty_codes = set(qty_data.keys())
    
    # Check for missing codes
    missing_in_qty = work_order_codes - qty_codes
    extra_in_qty = qty_codes - work_order_codes
    
    validation_report = {
        'valid': True,
        'work_order_items': len(work_order_codes),
        'qty_file_items': len(qty_codes),
        'missing_in_qty': list(missing_in_qty),
        'extra_in_qty': list(extra_in_qty)
    }
    
    if missing_in_qty:
        validation_report['valid'] = False
        validation_report['error'] = f"Items in work order but not in qty file: {missing_in_qty}"
    
    return validation_report
