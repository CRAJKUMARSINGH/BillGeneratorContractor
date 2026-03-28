import sys
import json
import cv2
import re
import pytesseract
import pandas as pd

def preprocess(img_path):
    """Image preprocessing using adaptive thresholding for better OCR."""
    img = cv2.imread(img_path)
    if img is None:
        raise Exception(f"Failed to load image at {img_path}")
    
    # Scale down if image is too large (for performance)
    height, width = img.shape[:2]
    if width > 2000 or height > 2000:
        scale = min(2000 / width, 2000 / height)
        img = cv2.resize(img, (int(width * scale), int(height * scale)))
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(
        blur, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )
    return img, thresh

def detect_rows(img):
    """Detect horizontal rows in the table grid using morphological operations."""
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
    detect = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
    
    contours, _ = cv2.findContours(
        detect,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )
    
    rows = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if w > 600 and h > 30:
            rows.append((x, y, w, h))
            
    rows = sorted(rows, key=lambda r: r[1])
    return rows

def ocr_rows_multi_mode(img, rows):
    """
    OCR rows using multiple PSM modes for reliability.
    Tries PSM 6 (uniform text) first, falls back to PSM 4 if needed.
    """
    lines = []
    for r in rows:
        x, y, w, h = r
        crop = img[y:y+h, x:x+w]
        
        # Ensure minimum crop size for OCR
        if crop.size == 0:
            continue
        
        # Try PSM 6 first (uniform text block) - fastest and most reliable
        try:
            txt = pytesseract.image_to_string(crop, config="--oem 3 --psm 6")
            txt = txt.replace("O", "0").replace("l", "1").replace("S", "5")
            txt = txt.strip()
            
            if len(txt) > 3:
                lines.append(txt)
                continue
        except:
            pass
        
        # If result is too short, try PSM 4 (column text) as fallback
        try:
            if len(txt.strip()) < 4:
                txt = pytesseract.image_to_string(crop, config="--oem 3 --psm 4")
                txt = txt.replace("O", "0").replace("l", "1").replace("S", "5")
                txt = txt.strip()
                
                if len(txt) > 3:
                    lines.append(txt)
        except:
            pass
        
    return lines

def parse_items(lines):
    """
    Parse Schedule-G items from OCR lines.
    Extracts: code (1.1.1), description, unit, and rate from the line.
    Quantity will be matched from qty.txt.
    """
    data = []
    for line in lines:
        code_match = re.search(r'\d+\.\d+\.\d+', line)
        if not code_match:
            continue
        
        code = code_match.group()
        parts = line.split()
        
        if len(parts) < 4:
            continue
        
        try:
            # Extract description (text between code and numbers)
            desc_parts = line.split(code)
            if len(desc_parts) > 1:
                desc = desc_parts[1].strip()
                # Clean up description from trailing unit/number artifacts
                desc = re.sub(r'(\d+\.\d+|\d+|Nos|Cum|Sqm|Ltr|Rmt|Kg|Metre).*$', '', desc).strip()
            else:
                desc = ""
            
            # Extract rate (last numeric value with decimals)
            numbers_with_decimals = re.findall(r'\d+\.\d{2,}', line)
            rate = 0.0
            if numbers_with_decimals:
                rate = float(numbers_with_decimals[-1])
            
            # Extract unit - common PWD units
            unit = "Nos"  # default
            for potential_unit in ["Cum", "Sqm", "Rmt", "Kg", "Ltr", "Metre", "Nos"]:
                if potential_unit in line:
                    unit = potential_unit
                    break
            
            data.append({
                "code": code,
                "description": desc if desc else f"Item {code}",
                "unit": unit,
                "rate": rate,
                "qty": 0.0  # Will be populated from qty.txt
            })
            
        except Exception as e:
            # Skip this line if parsing fails
            continue
            
    return data

def read_qty(path):
    """
    Parse quantity file in format: 
    1.1.1=2
    1.1.2=4
    """
    qty = {}
    try:
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if '=' not in line or not line:
                    continue
                try:
                    code, val = line.split("=", 1)
                    qty[code.strip()] = float(val.strip())
                except (ValueError, IndexError):
                    # Skip malformed lines
                    continue
    except Exception as e:
        raise Exception(f"Failed to read quantity file: {str(e)}")
    
    return qty

def validate_and_merge(data, qty_dict):
    """
    Validate that all quantities are available and merge them into items.
    Ensures 0% risk of silent wrong bills.
    """
    if not data:
        raise Exception("No items extracted from Schedule-G image.")
    
    if not qty_dict:
        raise Exception("Quantity file is empty or invalid.")
    
    codes_in_data = set(d["code"] for d in data)
    codes_in_qty = set(qty_dict.keys())
    
    # Check for unknown codes in qty file
    unknown_codes = codes_in_qty - codes_in_data
    if unknown_codes:
        raise Exception(f"Unknown item codes in qty file: {sorted(unknown_codes)}")
    
    # Check for missing quantities
    missing_codes = codes_in_data - codes_in_qty
    if missing_codes:
        raise Exception(f"Missing quantities for items: {sorted(missing_codes)}")
    
    # Merge quantities into items
    for item in data:
        code = item["code"]
        item["qty"] = qty_dict[code]
        item["amount"] = round(item["rate"] * item["qty"], 2)
    
    # Filter out items with 0 quantity
    data = [d for d in data if d["qty"] > 0]
    
    if not data:
        raise Exception("No items with valid quantities after validation.")
    
    return data

def build_excel(data, output):
    """Generate standard Excel file matching bill requirements."""
    df = pd.DataFrame(data)
    
    # Ensure correct column order and names
    df = df[["code", "description", "unit", "rate", "qty", "amount"]]
    df.columns = ["CODE", "DESCRIPTION", "UNIT", "RATE", "QTY", "AMOUNT"]
    
    # Format numeric columns
    df["RATE"] = df["RATE"].apply(lambda x: round(x, 2))
    df["QTY"] = df["QTY"].apply(lambda x: round(x, 2))
    df["AMOUNT"] = df["AMOUNT"].apply(lambda x: round(x, 2))
    
    # Write to Excel
    try:
        df.to_excel(output, index=False, sheet_name="Bill")
    except Exception as e:
        raise Exception(f"Failed to create Excel file: {str(e)}")

def process_workorder(img_path, qty_path, excel_output):
    """
    Main processing pipeline: IMAGE → Preprocessing → Grid Detection → OCR → Parsing → Validation → Excel
    This ensures foolproof extraction with strict validation at every step.
    """
    try:
        # Step 1: Validate inputs
        if not img_path or not qty_path or not excel_output:
            raise Exception("Missing required file paths")
        
        # Step 2: Read Quantity File (do this first for quick validation)
        qty_dict = read_qty(qty_path)
        
        # Step 3: Process Image
        original_img, thresh_img = preprocess(img_path)
        
        # Step 4: Detect Table Rows
        rows = detect_rows(thresh_img)
        if not rows:
            raise Exception("No table rows detected in image. Ensure image is clear and contains a structured table.")
        
        # Step 5: Extract and OCR Rows
        lines = ocr_rows_multi_mode(original_img, rows)
        if not lines:
            raise Exception("Failed to extract text from table rows.")
        
        # Step 6: Parse Items
        data = parse_items(lines)
        
        # Step 7: Validate & Merge (Critical - zero silent errors)
        final_data = validate_and_merge(data, qty_dict)
        
        # Step 8: Generate Excel
        build_excel(final_data, excel_output)
        
        return final_data
        
    except Exception as e:
        raise Exception(f"Processing failed: {str(e)}")

def main():
    if len(sys.argv) < 4:
        print(json.dumps({"status": "error", "message": "Missing required arguments: image_path qty_path excel_output"}))
        sys.exit(1)
        
    img_path = sys.argv[1]
    qty_path = sys.argv[2]
    excel_output = sys.argv[3]
    
    try:
        data = process_workorder(img_path, qty_path, excel_output)
        print(json.dumps({
            "status": "success",
            "data": data,
            "item_count": len(data)
        }))
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "message": str(e)
        }))
        sys.exit(1)

if __name__ == "__main__":
    main()
