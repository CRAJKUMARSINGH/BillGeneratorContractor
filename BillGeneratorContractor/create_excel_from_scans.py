"""
SIMPLE: Read scanned work order and create Excel with quantities
"""
from pathlib import Path
import pandas as pd
import pytesseract
from PIL import Image

print("=" * 80)
print("CREATING EXCEL FROM SCANNED WORK ORDER")
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

# Step 3: Create Excel with the data
print("Step 3: Creating Excel file...")

# Create DataFrame with quantities
data = []
for item_num, qty in quantities.items():
    data.append({
        'Item Number': item_num,
        'Quantity': qty,
        'Unit': 'nos',  # Default unit
        'Description': f'Item {item_num}',  # Placeholder
        'Rate': 0.0,  # To be filled
        'Amount': 0.0  # To be calculated
    })

df = pd.DataFrame(data)

# Save to Excel
output_file = Path("OUTPUT/work_order_with_quantities.xlsx")
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

print("=" * 80)
print("✅ DONE! Excel file ready at:")
print(f"   {output_file.absolute()}")
print("=" * 80)
