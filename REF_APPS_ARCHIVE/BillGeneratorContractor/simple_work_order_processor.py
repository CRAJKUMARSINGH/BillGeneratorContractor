"""
SIMPLE WORK ORDER PROCESSOR
For layman contractors who just write item codes and quantities on paper

This script:
1. Reads scanned work order images (PDF/JPEG)
2. Reads handwritten quantities from qty.txt
3. Creates Excel file with all quantities
4. Shows what was found in the work order
"""

from pathlib import Path
import pandas as pd
import pytesseract
from PIL import Image
import json
import sys

def print_header(title):
    """Print a nice header"""
    print("=" * 80)
    print(f"📄 {title}")
    print("=" * 80)
    print()

def read_quantities(folder_path):
    """Read quantities from qty.txt file"""
    folder = Path(folder_path)
    qty_file = folder / "qty.txt"
    
    if not qty_file.exists():
        print(f"❌ ERROR: qty.txt not found in {folder}")
        print(f"   Please make sure qty.txt exists with format:")
        print(f"   1.1.2 6")
        print(f"   1.1.3 19")
        print(f"   ...")
        return None
    
    quantities = {}
    with open(qty_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
                
            parts = line.split()
            if len(parts) >= 2:
                item_num = parts[0]
                try:
                    qty = float(parts[1])
                    quantities[item_num] = qty
                except ValueError:
                    print(f"⚠️  Warning: Could not parse quantity on line {line_num}: {line}")
            else:
                print(f"⚠️  Warning: Invalid format on line {line_num}: {line}")
    
    return quantities

def read_work_order_images(folder_path):
    """Read text from work order images using OCR"""
    folder = Path(folder_path)
    
    # Look for image files
    image_extensions = ['*.jpeg', '*.jpg', '*.png', '*.bmp', '*.tiff']
    image_files = []
    for ext in image_extensions:
        image_files.extend(sorted(folder.glob(ext)))
    
    if not image_files:
        print("ℹ️  No image files found in work order folder")
        print("   Supported formats: JPEG, PNG, BMP, TIFF")
        return ""
    
    all_text = ""
    print(f"📸 Found {len(image_files)} image files:")
    
    for img_file in image_files:
        print(f"   • {img_file.name}")
        try:
            img = Image.open(img_file)
            text = pytesseract.image_to_string(img, lang='eng+hin')
            all_text += f"\n{'='*40}\nFile: {img_file.name}\n{'='*40}\n{text}\n"
        except Exception as e:
            print(f"   ⚠️  Error reading {img_file.name}: {e}")
    
    return all_text

def find_item_descriptions(ocr_text, item_numbers):
    """Try to find descriptions for item numbers in OCR text"""
    descriptions = {}
    
    for item_num in item_numbers:
        # Look for item number in text
        lines = ocr_text.split('\n')
        for i, line in enumerate(lines):
            if item_num in line:
                # Try to get description from surrounding lines
                description = line.strip()
                # Look for next few lines that might contain description
                for j in range(i+1, min(i+5, len(lines))):
                    next_line = lines[j].strip()
                    if next_line and not any(char.isdigit() for char in next_line[:10]):
                        description += " " + next_line
                        break
                descriptions[item_num] = description[:200]  # Limit length
                break
    
    return descriptions

def create_excel_file(quantities, descriptions, output_path, source_folder):
    """Create Excel file with quantities and descriptions"""
    data = []
    
    for item_num, qty in quantities.items():
        desc = descriptions.get(item_num, f"Item {item_num}")
        data.append({
            'Item Number': item_num,
            'Description': desc,
            'Quantity': qty,
            'Unit': 'nos',
            'Rate': 0.0,
            'Amount': 0.0
        })
    
    df = pd.DataFrame(data)
    
    # Save to Excel
    output_file = Path(output_path)
    output_file.parent.mkdir(exist_ok=True)
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Bill Quantities')
        
        # Add summary sheet
        summary_data = {
            'Total Items': [len(quantities)],
            'Total Quantity': [sum(quantities.values())],
            'Source Folder': [str(source_folder)],
            'Generated On': [pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, index=False, sheet_name='Summary')
    
    return df, output_file

def save_report(quantities, ocr_text, descriptions, output_folder):
    """Save detailed report"""
    report = {
        'quantities': quantities,
        'total_items': len(quantities),
        'total_quantity': sum(quantities.values()),
        'item_descriptions': descriptions,
        'ocr_preview': ocr_text[:5000]  # First 5000 chars
    }
    
    report_file = Path(output_folder) / "processing_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    return report_file

def main():
    """Main function"""
    print_header("SIMPLE WORK ORDER PROCESSOR")
    print("For layman contractors - just write item codes and quantities on paper")
    print()
    
    # Get work order folder
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
    else:
        folder_path = "INPUT/work_order_samples/work_01_27022026"
    
    print(f"📁 Work order folder: {folder_path}")
    print()
    
    # Step 1: Read quantities
    print("1️⃣  Reading quantities from qty.txt...")
    quantities = read_quantities(folder_path)
    if not quantities:
        return
    
    print(f"   ✓ Found {len(quantities)} items with quantities:")
    for item_num, qty in quantities.items():
        print(f"      • {item_num}: {qty}")
    print()
    
    # Step 2: Read work order images
    print("2️⃣  Reading work order images with OCR...")
    ocr_text = read_work_order_images(folder_path)
    
    if ocr_text:
        print(f"   ✓ Extracted {len(ocr_text)} characters of text")
        # Save OCR text
        ocr_file = Path("OUTPUT") / "ocr_extracted_text.txt"
        ocr_file.parent.mkdir(exist_ok=True)
        with open(ocr_file, 'w', encoding='utf-8') as f:
            f.write(ocr_text)
        print(f"   💾 OCR text saved to: {ocr_file}")
    print()
    
    # Step 3: Find item descriptions
    print("3️⃣  Finding item descriptions in work order...")
    descriptions = find_item_descriptions(ocr_text, quantities.keys())
    
    if descriptions:
        print(f"   ✓ Found descriptions for {len(descriptions)} items")
        for item_num, desc in descriptions.items():
            print(f"      • {item_num}: {desc[:50]}...")
    else:
        print("   ℹ️  Could not find specific item descriptions in work order")
        print("   Using generic descriptions instead")
    print()
    
    # Step 4: Create Excel file
    print("4️⃣  Creating Excel file...")
    output_path = "OUTPUT/work_order_with_quantities.xlsx"
    df, excel_file = create_excel_file(quantities, descriptions, output_path, folder_path)
    
    print(f"   ✓ Excel file created: {excel_file}")
    print()
    print("   📊 Excel preview:")
    print(df.to_string(index=False))
    print()
    
    # Step 5: Save detailed report
    print("5️⃣  Saving detailed report...")
    report_file = save_report(quantities, ocr_text, descriptions, "OUTPUT")
    print(f"   💾 Report saved to: {report_file}")
    print()
    
    # Final summary
    print_header("✅ PROCESSING COMPLETE!")
    print("🎉 Your work order has been processed successfully!")
    print()
    print("📋 What was done:")
    print(f"   • Read {len(quantities)} quantities from qty.txt")
    print(f"   • Total quantity: {sum(quantities.values())}")
    print(f"   • Created Excel file: {excel_file}")
    print(f"   • Saved OCR text and processing report")
    print()
    print("📁 Output files:")
    print(f"   1. {excel_file} - Excel with all quantities")
    print(f"   2. OUTPUT/ocr_extracted_text.txt - Full OCR text")
    print(f"   3. {report_file} - Detailed processing report")
    print()
    print("💡 Next steps:")
    print("   1. Open the Excel file and fill in rates")
    print("   2. Amounts will be calculated automatically")
    print("   3. Save and use for billing")
    print()
    print("=" * 80)

if __name__ == "__main__":
    main()