"""
SMART: Read scanned work order, extract item details, and create Excel with quantities
"""
from pathlib import Path
import pandas as pd
import pytesseract
from PIL import Image
import re

print("=" * 80)
print("CREATING EXCEL FROM SCANNED WORK ORDER (SMART VERSION)")
print("=" * 80)
print()

folder = Path("INPUT/work_order_samples/work_01_27022026")

# Step 1: Read quantities from qty.txt
print("Step 1: Reading quantities from qty.txt...")
qty_file = folder / "qty.txt"
quantities = {}

with open(qty_file, 'r') as f:
    for line in f:
        parts = line.strip().split()
        if len(parts) >= 2:
            quantities[parts[0]] = float(parts[1])

print(f"✓ Loaded {len(quantities)} quantities")
for item, qty in quantities.items():
    print(f"   {item}: {qty}")
print()

# Step 2: Read work order images with OCR
print("Step 2: Reading work order images with OCR...")
image_files = sorted(list(folder.glob("*.jpeg")) + list(folder.glob("*.jpg")))

all_text = ""
for img_file in image_files:
    print(f"   Processing: {img_file.name}")
    try:
        img = Image.open(img_file)
        text = pytesseract.image_to_string(img, lang='eng+hin')
        all_text += text + "\n"
    except Exception as e:
        print(f"   ⚠️  Error: {e}")

print(f"✓ Extracted text from {len(image_files)} images")
print()

# Step 3: Parse work order to extract item details
print("Step 3: Parsing work order items...")

# Split text into lines
lines = all_text.split('\n')

# Dictionary to store item details
items_dict = {}

# Pattern to match item codes like 1.1.2, 1.1.3, etc.
item_pattern = re.compile(r'^(\d+\.\d+\.?\d*)\s*\|?\s*(.+?)(?:\s*\|\s*(.+?))?(?:\s*\|\s*(\d+\.?\d*))?$')

current_item = None
current_desc = []

for line in lines:
    line = line.strip()
    if not line:
        continue
    
    # Try to match item code at start of line
    match = item_pattern.match(line)
    if match:
        # Save previous item if exists
        if current_item and current_desc:
            items_dict[current_item]['description'] = ' '.join(current_desc).strip()
        
        item_code = match.group(1)
        desc = match.group(2) if match.group(2) else ""
        unit = match.group(3) if match.group(3) else "nos"
        rate = match.group(4) if match.group(4) else "0.0"
        
        current_item = item_code
        current_desc = [desc] if desc else []
        
        items_dict[item_code] = {
            'code': item_code,
            'description': desc,
            'unit': unit.strip() if unit else 'nos',
            'rate': float(rate) if rate else 0.0
        }
    elif current_item and line and not line.startswith('|'):
        # Continue description from previous line
        current_desc.append(line)

# Save last item
if current_item and current_desc:
    items_dict[current_item]['description'] = ' '.join(current_desc).strip()

print(f"✓ Parsed {len(items_dict)} items from work order")
print()

# Step 4: Create Excel with matched data
print("Step 4: Creating Excel file with matched data...")

data = []
for item_num, qty in quantities.items():
    # Try to find matching item in work order
    if item_num in items_dict:
        item_info = items_dict[item_num]
        desc = item_info['description']
        unit = item_info['unit']
        rate = item_info['rate']
    else:
        # Item not found in work order, use defaults
        desc = f"Item {item_num} (not found in work order)"
        unit = "nos"
        rate = 0.0
    
    amount = qty * rate
    
    data.append({
        'Item Number': item_num,
        'Description': desc[:100] if desc else f"Item {item_num}",  # Limit description length
        'Quantity': qty,
        'Unit': unit,
        'Rate': rate,
        'Amount': amount
    })

df = pd.DataFrame(data)

# Save to Excel
output_file = Path("OUTPUT/work_order_with_quantities_smart.xlsx")
output_file.parent.mkdir(exist_ok=True)

df.to_excel(output_file, index=False, sheet_name='Bill')

print(f"✓ Excel file created: {output_file}")
print()

# Show preview
print("Preview of Excel data:")
print(df.to_string(index=False))
print()

# Save OCR text for reference
text_file = Path("OUTPUT/ocr_extracted_text.txt")
with open(text_file, 'w', encoding='utf-8') as f:
    f.write(all_text)

print(f"✓ OCR text saved: {text_file}")
print()

# Save parsed items for debugging
debug_file = Path("OUTPUT/parsed_items_debug.txt")
with open(debug_file, 'w', encoding='utf-8') as f:
    f.write("PARSED ITEMS FROM WORK ORDER:\n")
    f.write("=" * 80 + "\n\n")
    for code, info in items_dict.items():
        f.write(f"Code: {code}\n")
        f.write(f"Description: {info['description']}\n")
        f.write(f"Unit: {info['unit']}\n")
        f.write(f"Rate: {info['rate']}\n")
        f.write("-" * 80 + "\n")

print(f"✓ Debug info saved: {debug_file}")
print()

print("=" * 80)
print("✅ DONE! Excel file ready at:")
print(f"   {output_file.absolute()}")
print("=" * 80)
