#!/usr/bin/env python3
"""
Enhanced OCR Extractor for PWD Work Orders
Based on Action Plan Phase 2 & 3
Implements hybrid approach with image preprocessing
"""
import sys
from pathlib import Path
import pandas as pd
import re
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    import pytesseract
    from PIL import Image
    import cv2
    import numpy as np
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("\nPlease install required packages:")
    print("  pip install pytesseract pillow opencv-python-headless")
    print("\nAlso install Tesseract OCR:")
    print("  Windows: https://github.com/UB-Mannheim/tesseract/wiki")
    sys.exit(1)


class PWDWorkOrderExtractor:
    """
    PWD Work Order Extractor with OCR
    Implements Phase 2 & 3 of Action Plan
    """
    
    def __init__(self, tesseract_path=None):
        """Initialize with optional Tesseract path"""
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # OCR config for Hindi + English
        self.config = '--psm 6 -l eng+hin'
        
        # Work Order Schema (Phase 2.1)
        self.schema = {
            "header": {
                "department": "",
                "work_order_no": "",
                "date": "",
                "contractor_name": "",
                "contractor_license": "",
                "agreement_no": "",
                "estimated_cost": "",
                "sanctioned_amount": ""
            },
            "items": []
        }
    
    def preprocess_image(self, image_path):
        """
        Phase 2.2: Image Preprocessing
        - Deskew
        - Denoise
        - Binarization
        """
        print(f"  Preprocessing: {image_path.name}")
        
        # Load image
        img = cv2.imread(str(image_path))
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        # Binarization (Otsu's method)
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Deskew (if needed)
        # coords = np.column_stack(np.where(binary > 0))
        # angle = cv2.minAreaRect(coords)[-1]
        # if angle < -45:
        #     angle = -(90 + angle)
        # else:
        #     angle = -angle
        # (h, w) = binary.shape[:2]
        # center = (w // 2, h // 2)
        # M = cv2.getRotationMatrix2D(center, angle, 1.0)
        # binary = cv2.warpAffine(binary, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        
        return binary
    
    def extract_text_from_image(self, image_path):
        """Extract text using Tesseract OCR"""
        print(f"  OCR Processing: {image_path.name}")
        
        try:
            # Preprocess
            preprocessed = self.preprocess_image(image_path)
            
            # Convert to PIL Image
            pil_image = Image.fromarray(preprocessed)
            
            # Extract text
            text = pytesseract.image_to_string(pil_image, config=self.config)
            
            # Get confidence
            data = pytesseract.image_to_data(pil_image, config=self.config, output_type=pytesseract.Output.DICT)
            confidences = [int(conf) for conf in data['conf'] if conf != '-1']
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            print(f"    Confidence: {avg_confidence:.1f}%")
            print(f"    Characters extracted: {len(text)}")
            
            return text, avg_confidence
            
        except Exception as e:
            print(f"    ❌ Error: {e}")
            return "", 0
    
    def extract_from_images(self, image_dir):
        """
        Extract data from all images in directory
        Phase 2: Data Extraction Engine
        """
        image_path = Path(image_dir)
        
        # Find all image files
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.tif', '*.tiff']:
            image_files.extend(list(image_path.glob(ext)))
        
        if not image_files:
            print(f"❌ No image files found in: {image_path}")
            return None
        
        print(f"\nFound {len(image_files)} images")
        print("=" * 80)
        
        # Sort images by name
        image_files = sorted(image_files)
        
        all_text = []
        data = {"header": {}, "items": [], "raw_text": []}
        
        for idx, img_file in enumerate(image_files, 1):
            print(f"\nImage {idx}/{len(image_files)}: {img_file.name}")
            
            text, confidence = self.extract_text_from_image(img_file)
            
            all_text.append({
                'file': img_file.name,
                'text': text,
                'confidence': confidence
            })
            
            # Parse based on image number
            if idx == 1:
                # First image: Extract header
                header = self._parse_header(text)
                data["header"].update(header)
            
            # All images: Extract items
            items = self._parse_items(text, page_num=idx)
            data["items"].extend(items)
        
        data["raw_text"] = all_text
        
        return data
    
    def _parse_header(self, text):
        """
        Phase 2.1: Parse header metadata
        Extract: WO No, Date, Contractor, Department, etc.
        """
        header = {}
        
        # Regex patterns for header fields
        patterns = {
            "work_order_no": r"(?i)work\s*order\s*no[.:]\s*([A-Z0-9/\-]+)",
            "date": r"(?i)date[.:]\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            "contractor_name": r"(?i)contractor[.:]\s*([A-Za-z\s.&]+)",
            "department": r"(?i)(public\s*works\s*department[^,\n]*)",
            "agreement_no": r"(?i)agreement\s*no[.:]\s*([A-Z0-9/\-]+)",
            "estimated_cost": r"(?i)estimated\s*cost[.:]\s*[₹Rs.]*\s*([\d,]+\.?\d*)",
            "sanctioned_amount": r"(?i)sanctioned\s*amount[.:]\s*[₹Rs.]*\s*([\d,]+\.?\d*)"
        }
        
        for field, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                value = match.group(1).strip()
                # Clean numeric values
                if 'cost' in field or 'amount' in field:
                    value = value.replace(',', '')
                header[field] = value
        
        return header
    
    def _parse_items(self, text, page_num=1):
        """
        Phase 2.1: Parse work order items
        Extract: Item No, Description, Unit, Rate, Quantity, Amount
        """
        items = []
        lines = text.split('\n')
        
        current_item = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Pattern 1: Item number at start (1, 1.1, 2, etc.)
            item_match = re.match(r'^(\d+\.?\d*)\s+(.+)', line)
            if item_match:
                # Save previous item
                if current_item:
                    items.append(current_item)
                
                item_no = item_match.group(1)
                rest = item_match.group(2)
                
                # Try to extract unit, quantity, rate, amount
                # Pattern: Description Unit Qty Rate Amount
                parts = rest.split()
                
                current_item = {
                    'item_no': item_no,
                    'description': rest,  # Will be refined
                    'unit': '',
                    'quantity': '',
                    'rate': '',
                    'amount': '',
                    'page': page_num
                }
                
                # Try to extract numeric values from end
                numeric_parts = []
                desc_parts = []
                
                for part in reversed(parts):
                    # Check if numeric (with commas and decimals)
                    if re.match(r'^[\d,]+\.?\d*$', part):
                        numeric_parts.insert(0, part.replace(',', ''))
                    else:
                        desc_parts.insert(0, part)
                
                # Assign numeric values (Amount, Rate, Quantity from right to left)
                if len(numeric_parts) >= 3:
                    current_item['amount'] = numeric_parts[-1]
                    current_item['rate'] = numeric_parts[-2]
                    current_item['quantity'] = numeric_parts[-3]
                
                # Description is remaining text
                current_item['description'] = ' '.join(desc_parts)
                
                # Try to extract unit (sqm, cum, kg, nos, rmt, etc.)
                unit_match = re.search(r'\b(sqm|cum|kg|nos|rmt|mt|ltr|each|set|pair)\b', 
                                      current_item['description'], re.IGNORECASE)
                if unit_match:
                    current_item['unit'] = unit_match.group(1).lower()
                    # Remove unit from description
                    current_item['description'] = current_item['description'].replace(unit_match.group(0), '').strip()
            
            elif current_item:
                # Continuation of description
                current_item['description'] += ' ' + line
        
        # Add last item
        if current_item:
            items.append(current_item)
        
        return items
    
    def to_excel(self, data, output_path):
        """
        Phase 3: Generate TEST_INPUT format Excel
        Sheet 1: TITLE (Metadata)
        Sheet 2: WORK ORDER (Line items)
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"\nGenerating Excel file...")
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Sheet 1: TITLE
            title_data = {
                'Field': [
                    'FOR CONTRACTORS & SUPPLIERS ONLY FOR PAYMENT FROM GOVT. TREASURY',
                    'Bill Number',
                    'Running or Final',
                    'Cash Book Voucher No. and Date',
                    'Name of Contractor or supplier :',
                    'Name of Work ;-',
                    'Serial No. of this bill :',
                    'No. and date of the last bill-',
                    'Reference to work order or Agreement :',
                    'Agreement No.',
                    'WORK ORDER AMOUNT RS.',
                    'Date of written order to commence work :',
                    'St. date of Start :',
                    'St. date of completion :',
                    'Date of actual completion of work :',
                    'Date of measurement :',
                    'TENDER PREMIUM %',
                    'Above / Below',
                    'Amount Paid Vide Last Bill'
                ],
                'Value': [
                    '',
                    '',
                    'Final',
                    '',
                    data['header'].get('contractor_name', ''),
                    '',
                    '',
                    'Not Applicable',
                    data['header'].get('work_order_no', ''),
                    data['header'].get('agreement_no', ''),
                    data['header'].get('sanctioned_amount', ''),
                    data['header'].get('date', ''),
                    '',
                    '',
                    '',
                    '',
                    '',
                    'Above',
                    '0'
                ]
            }
            
            title_df = pd.DataFrame(title_data)
            title_df.to_excel(writer, sheet_name='Title', index=False, header=False)
            
            # Sheet 2: WORK ORDER
            if data['items']:
                items_df = pd.DataFrame(data['items'])
                # Reorder columns
                columns = ['item_no', 'description', 'unit', 'quantity', 'rate', 'amount', 'page']
                items_df = items_df[[col for col in columns if col in items_df.columns]]
                
                # Rename columns to match TEST_INPUT format
                items_df.columns = ['Item', 'Description', 'Unit', 'Quantity', 'Rate', 'Amount', 'BSR']
                
                items_df.to_excel(writer, sheet_name='Work Order', index=False)
            
            # Sheet 3: Bill Quantity (copy of Work Order)
            if data['items']:
                items_df.to_excel(writer, sheet_name='Bill Quantity', index=False)
            
            # Sheet 4: Extra Items (empty)
            extra_df = pd.DataFrame(columns=['Item', 'Description', 'Unit', 'Quantity', 'Rate', 'Amount', 'Deviation %', 'BSR'])
            extra_df.to_excel(writer, sheet_name='Extra Items', index=False)
        
        print(f"✅ Excel file created: {output_path.absolute()}")
        
        return output_path
    
    def save_raw_text(self, data, output_path):
        """Save raw OCR text for verification"""
        output_path = Path(output_path)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("PWD WORK ORDER - RAW OCR TEXT\n")
            f.write("=" * 80 + "\n\n")
            
            for item in data['raw_text']:
                f.write(f"\nFile: {item['file']}\n")
                f.write(f"Confidence: {item['confidence']:.1f}%\n")
                f.write("-" * 80 + "\n")
                f.write(item['text'])
                f.write("\n" + "=" * 80 + "\n")
        
        print(f"✅ Raw text saved: {output_path.absolute()}")


def main():
    """Main execution function"""
    
    # Default paths
    image_dir = "INPUT/work_order_samples/work_01_27022026"
    output_excel = "OUTPUT/work_order_ocr_extracted.xlsx"
    output_text = "OUTPUT/work_order_ocr_raw_text.txt"
    
    # Override from command line
    if len(sys.argv) > 1:
        image_dir = sys.argv[1]
    if len(sys.argv) > 2:
        output_excel = sys.argv[2]
    
    print(f"\n{'='*80}")
    print(f"PWD WORK ORDER OCR EXTRACTOR")
    print(f"{'='*80}\n")
    print(f"Input:  {image_dir}")
    print(f"Output: {output_excel}\n")
    
    # Check if Tesseract is available
    try:
        pytesseract.get_tesseract_version()
        print("✅ Tesseract OCR found")
    except Exception as e:
        print("❌ Tesseract OCR not found!")
        print("\nPlease install Tesseract OCR:")
        print("  Windows: https://github.com/UB-Mannheim/tesseract/wiki")
        print("  Download installer and add to PATH")
        print("\nOr specify path manually:")
        print("  pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'")
        return False
    
    try:
        # Initialize extractor
        extractor = PWDWorkOrderExtractor()
        
        # Extract from images
        print("\nPhase 1: Extracting text from images...")
        data = extractor.extract_from_images(image_dir)
        
        if not data:
            return False
        
        # Save raw text
        print("\nPhase 2: Saving raw OCR text...")
        extractor.save_raw_text(data, output_text)
        
        # Generate Excel
        print("\nPhase 3: Generating Excel file...")
        excel_path = extractor.to_excel(data, output_excel)
        
        # Summary
        print(f"\n{'='*80}")
        print("✅ OCR EXTRACTION COMPLETE!")
        print(f"{'='*80}\n")
        print(f"Extracted Data:")
        print(f"  - Header fields: {len([v for v in data['header'].values() if v])}")
        print(f"  - Work items: {len(data['items'])}")
        print(f"\nOutput Files:")
        print(f"  1. Excel: {excel_path.absolute()}")
        print(f"  2. Raw Text: {Path(output_text).absolute()}")
        print(f"\n⚠️  IMPORTANT: Please review and verify the extracted data!")
        print(f"   OCR may have errors. Manual verification is required.")
        print(f"\nNext Steps:")
        print(f"  1. Open Excel file and verify data")
        print(f"  2. Correct any OCR errors")
        print(f"  3. Fill in missing fields")
        print(f"  4. Run: python process_first_bill.py {output_excel}")
        print()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
