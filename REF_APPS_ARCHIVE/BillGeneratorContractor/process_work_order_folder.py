"""
Process Complete Work Order Folder
Reads work order from images and quantities from txt file
Intelligently matches items even with OCR errors
"""
import sys
from pathlib import Path
import re
import importlib.util

# Add core to path
sys.path.insert(0, str(Path(__file__).parent))

# Direct import to avoid __init__ issues
spec = importlib.util.spec_from_file_location(
    "document_processor",
    "core/processors/document/document_processor.py"
)
doc_proc_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(doc_proc_module)
DocumentProcessor = doc_proc_module.DocumentProcessor

import json


def read_qty_file(qty_file: Path) -> dict:
    """Read quantities from text file"""
    quantities = {}
    
    print(f"📝 Reading quantities from: {qty_file.name}")
    with open(qty_file, 'r') as f:
        content = f.read()
        print(f"   Content:\n{content}")
    
    with open(qty_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            # Parse: item_number quantity
            parts = line.split()
            if len(parts) >= 2:
                item_number = parts[0]
                try:
                    quantity = float(parts[1])
                    quantities[item_number] = quantity
                    print(f"   ✓ Item {item_number}: Qty = {quantity}")
                except ValueError:
                    print(f"   ⚠️  Line {line_num}: Invalid quantity '{parts[1]}'")
    
    return quantities


def smart_match_items(work_order_items, quantities):
    """
    Intelligently match work order items with quantities
    Handles OCR errors and partial matches
    """
    print()
    print("🔍 Smart Matching Items...")
    print()
    
    matched_items = []
    unmatched_quantities = list(quantities.keys())
    
    # Strategy 1: Exact match
    print("Strategy 1: Exact Match")
    for wo_item in work_order_items:
        if wo_item.item_number in quantities:
            qty = quantities[wo_item.item_number]
            matched_items.append({
                'item_number': wo_item.item_number,
                'description': wo_item.description,
                'unit': wo_item.unit or 'nos',
                'quantity': qty,
                'match_type': 'exact',
                'confidence': wo_item.confidence_score
            })
            unmatched_quantities.remove(wo_item.item_number)
            print(f"   ✓ Exact: {wo_item.item_number} → Qty {qty}")
    
    # Strategy 2: Partial match (e.g., "1" matches "1.1.2")
    print()
    print("Strategy 2: Partial Match (OCR extracted partial item numbers)")
    for wo_item in work_order_items:
        if wo_item.item_number not in [m['item_number'] for m in matched_items]:
            # Check if work order item number is a prefix of any quantity item
            for qty_item in unmatched_quantities[:]:
                if qty_item.startswith(wo_item.item_number + '.'):
                    qty = quantities[qty_item]
                    matched_items.append({
                        'item_number': qty_item,  # Use the full item number from qty.txt
                        'description': wo_item.description,
                        'unit': wo_item.unit or 'nos',
                        'quantity': qty,
                        'match_type': 'partial',
                        'confidence': wo_item.confidence_score * 0.9  # Slightly lower confidence
                    })
                    unmatched_quantities.remove(qty_item)
                    print(f"   ✓ Partial: WO '{wo_item.item_number}' → Qty '{qty_item}' (Qty {qty})")
                    break
    
    # Strategy 3: Add remaining quantities as new items
    print()
    print("Strategy 3: Unmatched Quantities (will be added as new items)")
    for qty_item in unmatched_quantities:
        qty = quantities[qty_item]
        matched_items.append({
            'item_number': qty_item,
            'description': f"Item {qty_item} (from qty.txt, no work order match)",
            'unit': 'nos',
            'quantity': qty,
            'match_type': 'qty_only',
            'confidence': 0.5  # Low confidence since no work order match
        })
        print(f"   ⚠️  No match: {qty_item} → Qty {qty} (added as new item)")
    
    # Add work order items with zero quantity
    print()
    print("Strategy 4: Work Order Items Without Quantities")
    for wo_item in work_order_items:
        if wo_item.item_number not in [m['item_number'] for m in matched_items]:
            matched_items.append({
                'item_number': wo_item.item_number,
                'description': wo_item.description,
                'unit': wo_item.unit or 'nos',
                'quantity': 0.0,
                'match_type': 'wo_only',
                'confidence': wo_item.confidence_score
            })
            print(f"   ○ Zero qty: {wo_item.item_number} (no quantity in qty.txt)")
    
    return matched_items


def process_folder(folder_path: Path):
    """Process complete work order folder"""
    
    print("=" * 80)
    print("PROCESSING WORK ORDER FOLDER")
    print("=" * 80)
    print(f"Folder: {folder_path}")
    print()
    
    # Find files
    image_files = sorted(list(folder_path.glob("*.jpeg")) + 
                        list(folder_path.glob("*.jpg")) + 
                        list(folder_path.glob("*.png")))
    
    txt_files = list(folder_path.glob("*.txt"))
    qty_file = txt_files[0] if txt_files else None
    
    if not image_files:
        print("❌ No image files found!")
        return False
    
    if not qty_file:
        print("❌ No qty.txt file found!")
        return False
    
    print(f"📋 Found {len(image_files)} work order image(s)")
    print(f"📝 Found quantities file: {qty_file.name}")
    print()
    
    # Step 1: Process work order images
    print("-" * 80)
    print("STEP 1: Processing Work Order Images with OCR")
    print("-" * 80)
    
    processor = DocumentProcessor()
    work_order_data = processor.process_work_order(image_files)
    
    print(f"✅ Extracted {len(work_order_data.items)} items from work order")
    print()
    print("Work Order Items:")
    for i, item in enumerate(work_order_data.items, 1):
        print(f"   {i}. Item {item.item_number}: {item.description[:60]}...")
    print()
    
    # Step 2: Read quantities
    print("-" * 80)
    print("STEP 2: Reading Quantities from qty.txt")
    print("-" * 80)
    
    quantities = read_qty_file(qty_file)
    print(f"✅ Loaded {len(quantities)} quantities")
    print()
    
    # Step 3: Smart matching
    print("-" * 80)
    print("STEP 3: Smart Matching")
    print("-" * 80)
    
    matched_items = smart_match_items(work_order_data.items, quantities)
    
    # Step 4: Generate results
    print()
    print("=" * 80)
    print("FINAL BILL ITEMS")
    print("=" * 80)
    print()
    
    items_with_qty = [item for item in matched_items if item['quantity'] > 0]
    items_without_qty = [item for item in matched_items if item['quantity'] == 0]
    
    print(f"📊 Summary:")
    print(f"   Total Items: {len(matched_items)}")
    print(f"   Items WITH Quantity: {len(items_with_qty)}")
    print(f"   Items WITHOUT Quantity: {len(items_without_qty)}")
    print(f"   Total Quantity: {sum(item['quantity'] for item in matched_items)}")
    print()
    
    print("Items WITH Quantities:")
    for item in items_with_qty:
        print(f"\n   Item {item['item_number']} ({item['match_type']} match)")
        print(f"      Description: {item['description'][:70]}...")
        print(f"      Unit: {item['unit']}")
        print(f"      Quantity: {item['quantity']}")
        print(f"      Confidence: {item['confidence']:.0%}")
    
    # Save results
    output_file = Path("OUTPUT/work_order_processed.json")
    output_file.parent.mkdir(exist_ok=True)
    
    result = {
        'folder': str(folder_path),
        'work_order_images': len(image_files),
        'quantities_file': qty_file.name,
        'total_items': len(matched_items),
        'items_with_quantity': len(items_with_qty),
        'items_without_quantity': len(items_without_qty),
        'total_quantity': sum(item['quantity'] for item in matched_items),
        'items': matched_items
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print()
    print(f"💾 Results saved to: {output_file}")
    print()
    print("=" * 80)
    print("✅ PROCESSING COMPLETE!")
    print("=" * 80)
    
    return True


if __name__ == "__main__":
    folder = Path("INPUT/work_order_samples/work_01_27022026")
    success = process_folder(folder)
    sys.exit(0 if success else 1)
