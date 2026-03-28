#!/usr/bin/env python3
"""
Simple OCR to Excel converter for work order images
Uses pytesseract directly without complex dependencies
"""
import sys
from pathlib import Path
import pandas as pd

try:
    import pytesseract
    from PIL import Image
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("\nPlease install required packages:")
    print("  pip install pytesseract pillow")
    print("\nAlso install Tesseract OCR:")
    print("  Windows: https://github.com/UB-Mannheim/tesseract/wiki")
    sys.exit(1)

def extract_text_from_images(image_dir: Path):
    """Extract text from all images in directory"""
    
    # Find all image files
    image_files = []
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.tif', '*.tiff']:
        image_files.extend(list(image_dir.glob(ext)))
    
    if not image_files:
        print(f"❌ No image files found in: {image_dir}")
        return None
    
    print(f"Found {len(image_files)} image files:")
    for img in sorted(image_files):
        print(f"  - {img.name}")
    print()
    
    all_text = []
    
    for img_file in sorted(image_files):
        print(f"Processing: {img_file.name}...")
        try:
            # Open image
            image = Image.open(img_file)
            
            # Extract text using Tesseract
            # Use both English and Hindi
            text = pytesseract.image_to_string(image, lang='eng+hin')
            
            all_text.append(f"\n{'='*80}\n")
            all_text.append(f"File: {img_file.name}\n")
            all_text.append(f"{'='*80}\n")
            all_text.append(text)
            all_text.append("\n")
            
            print(f"  ✅ Extracted {len(text)} characters")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            all_text.append(f"\n[Error processing {img_file.name}: {e}]\n")
    
    return ''.join(all_text)


def parse_work_order_text(text: str):
    """Parse work order items from extracted text"""
    import re
    
    items = []
    lines = text.split('\n')
    
    current_item = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Try to match item number patterns
        # Patterns: "1.", "1.1", "A-1", "Item 1", etc.
        patterns = [
            r'^(\d+\.?\d*)\s+(.+)',  # "1.1 Description"
            r'^([A-Z]-\d+)\s+(.+)',   # "A-1 Description"
            r'^Item\s+(\d+)\s+(.+)',  # "Item 1 Description"
        ]
        
        matched = False
        for pattern in patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                # Save previous item
                if current_item:
                    items.append(current_item)
                
                # Start new item
                item_number = match.group(1)
                description = match.group(2).strip()
                
                current_item = {
                    'Item Number': item_number,
                    'Description': description,
                    'Unit': '',
                    'Quantity': '',
                    'Rate': '',
                    'Amount': '',
                    'Remarks': ''
                }
                matched = True
                break
        
        if not matched and current_item:
            # Continuation of description
            current_item['Description'] += ' ' + line
    
    # Add last item
    if current_item:
        items.append(current_item)
    
    return items


def create_excel_from_text(text: str, output_excel: Path):
    """Create Excel file from extracted text"""
    
    print("\nParsing extracted text...")
    items = parse_work_order_text(text)
    
    if not items:
        print("⚠️  No structured items found. Creating Excel with raw text...")
        
        # Create simple Excel with raw text
        df = pd.DataFrame({
            'Raw OCR Text': [text]
        })
        
        with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Raw Text', index=False)
        
        return False
    
    print(f"✅ Parsed {len(items)} items\n")
    
    # Display first few items
    print("Sample extracted items:")
    print("-" * 80)
    for idx, item in enumerate(items[:5], 1):
        print(f"{idx}. {item['Item Number']}: {item['Description'][:60]}...")
    
    if len(items) > 5:
        print(f"... and {len(items) - 5} more items")
    print()
    
    # Create DataFrame
    df = pd.DataFrame(items)
    
    # Create Excel with multiple sheets
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        # Title sheet
        title_data = {
            'Field': ['Work Name', 'Agreement Number', 'Contractor Name', 
                     'Bill Type', 'Bill Number', 'Date'],
            'Value': ['', '', '', '', '', '']
        }
        pd.DataFrame(title_data).to_excel(writer, sheet_name='Title', index=False)
        
        # Work Order sheet
        df.to_excel(writer, sheet_name='Work Order', index=False)
        
        # Bill Quantity sheet (copy for editing)
        df.to_excel(writer, sheet_name='Bill Quantity', index=False)
        
        # Extra Items sheet (empty)
        extra_cols = ['Item Number', 'Description', 'Unit', 'Quantity', 
                     'Rate', 'Amount', 'Deviation %', 'Remarks']
        pd.DataFrame(columns=extra_cols).to_excel(writer, sheet_name='Extra Items', index=False)
    
    return True


def main():
    image_dir = Path("INPUT/work_order_samples/work_01_27022026")
    output_excel = Path("OUTPUT/work_order_extracted.xlsx")
    output_text = Path("OUTPUT/work_order_raw_text.txt")
    
    if len(sys.argv) > 1:
        image_dir = Path(sys.argv[1])
    
    if len(sys.argv) > 2:
        output_excel = Path(sys.argv[2])
    
    print(f"\n{'='*80}")
    print(f"Work Order Image to Excel Converter")
    print(f"{'='*80}\n")
    print(f"Input:  {image_dir}")
    print(f"Output: {output_excel}\n")
    
    if not image_dir.exists():
        print(f"❌ Directory not found: {image_dir}")
        return False
    
    # Create output directory
    output_excel.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Step 1: Extract text from images
        print("Step 1: Extracting text from images using OCR...")
        print("-" * 80)
        text = extract_text_from_images(image_dir)
        
        if not text:
            return False
        
        # Save raw text
        print(f"\nSaving raw OCR text to: {output_text}")
        with open(output_text, 'w', encoding='utf-8') as f:
            f.write(text)
        print("✅ Raw text saved\n")
        
        # Step 2: Create Excel
        print("Step 2: Creating Excel file...")
        print("-" * 80)
        success = create_excel_from_text(text, output_excel)
        
        print(f"\n{'='*80}")
        print("✅ Processing Complete!")
        print(f"{'='*80}\n")
        print("Output files:")
        print(f"  1. Excel: {output_excel.absolute()}")
        print(f"  2. Raw Text: {output_text.absolute()}")
        print()
        print("⚠️  IMPORTANT: Please review and verify the extracted data!")
        print("   OCR may have errors. Manual verification is required.")
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
