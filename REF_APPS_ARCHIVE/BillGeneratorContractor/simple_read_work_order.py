"""
Simple Work Order Reader
Just reads qty.txt and shows what we have
"""
from pathlib import Path
import json

folder = Path("INPUT/work_order_samples/work_01_27022026")

print("=" * 80)
print("READING WORK ORDER FOLDER")
print("=" * 80)
print(f"Folder: {folder}")
print()

# List all files
print("Files in folder:")
for f in sorted(folder.iterdir()):
    print(f"   - {f.name}")
print()

# Read qty.txt
qty_file = folder / "qty.txt"
if qty_file.exists():
    print("-" * 80)
    print("QUANTITIES FROM qty.txt")
    print("-" * 80)
    
    with open(qty_file, 'r') as f:
        content = f.read()
    
    print("Raw content:")
    print(content)
    print()
    
    quantities = {}
    for line in content.strip().split('\n'):
        if line.strip():
            parts = line.split()
            if len(parts) >= 2:
                item_num = parts[0]
                qty = float(parts[1])
                quantities[item_num] = qty
    
    print("Parsed quantities:")
    for item_num, qty in quantities.items():
        print(f"   Item {item_num}: Quantity = {qty}")
    
    print()
    print(f"Total: {len(quantities)} items with quantities")
    print(f"Total quantity: {sum(quantities.values())}")
    
    # Save to JSON
    output = {
        'folder': str(folder),
        'quantities_file': 'qty.txt',
        'quantities': quantities,
        'total_items': len(quantities),
        'total_quantity': sum(quantities.values())
    }
    
    output_file = Path("OUTPUT/quantities_read.json")
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print()
    print(f"💾 Saved to: {output_file}")

print()
print("=" * 80)
print("✅ DONE!")
print("=" * 80)
