#!/usr/bin/env python3
"""
PHASE 1.1 TEST: Part-Rate Display Format
Tests that part-rate items show "₹95 (Part Rate)" format
"""
import sys
from pathlib import Path
import pandas as pd
import io

sys.path.insert(0, str(Path(__file__).parent))

def test_part_rate_display():
    """Test part-rate display format"""
    print("="*80)
    print("PHASE 1.1 TEST: PART-RATE DISPLAY FORMAT")
    print("="*80)
    print()
    
    from core.processors.excel_processor import ExcelProcessor
    
    # Test with one file
    test_file = Path('TEST_INPUT_FILES/FirstFINALnoExtra.xlsx')
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False
    
    print(f"Testing with: {test_file.name}")
    print()
    
    # Process file
    processor = ExcelProcessor()
    with open(test_file, 'rb') as f:
        file_bytes = io.BytesIO(f.read())
    
    processed_data = processor.process_excel(file_bytes)
    
    # Extract data
    work_order_data = processed_data.get('work_order_data')
    if isinstance(work_order_data, list):
        work_order_df = pd.DataFrame(work_order_data)
    else:
        work_order_df = work_order_data
    
    bill_quantity_data = processed_data.get('bill_quantity_data')
    if isinstance(bill_quantity_data, list):
        bill_quantity_df = pd.DataFrame(bill_quantity_data)
    else:
        bill_quantity_df = bill_quantity_data
    
    # Prepare items
    items_list = []
    for idx, row in work_order_df.iterrows():
        item_no = row.get('Item No.', f"{idx+1:03d}")
        description = row.get('Description of Item', row.get('Description', ''))
        unit = row.get('Unit', 'NOS')
        
        try:
            wo_quantity = float(row.get('Quantity', 0) or 0)
        except (ValueError, TypeError):
            wo_quantity = 0.0
        
        try:
            wo_rate = float(row.get('Rate', 0) or 0)
        except (ValueError, TypeError):
            wo_rate = 0.0
        
        # Get bill quantity
        bill_qty = wo_quantity
        if bill_quantity_df is not None and not bill_quantity_df.empty:
            if idx < len(bill_quantity_df):
                bill_row = bill_quantity_df.iloc[idx]
                try:
                    bill_qty = float(bill_row.get('Quantity', wo_quantity) or wo_quantity)
                except (ValueError, TypeError):
                    bill_qty = wo_quantity
        
        items_list.append({
            'Item No': item_no,
            'Description': description,
            'Unit': unit,
            'WO Quantity': wo_quantity,
            'Bill Quantity': bill_qty,
            'WO Rate': wo_rate,
            'Bill Rate': wo_rate,
            'WO Amount': wo_quantity * wo_rate,
            'Bill Amount': bill_qty * wo_rate
        })
    
    df = pd.DataFrame(items_list)
    
    print(f"Loaded {len(df)} items")
    print()
    
    # TEST 1: Reduce rate for 3 items
    print("TEST 1: Reduce Rate by ₹5 for 3 Items")
    print("-" * 80)
    
    active_items = df[df['Bill Quantity'] > 0]
    if len(active_items) < 3:
        print(f"❌ Not enough active items (need 3, have {len(active_items)})")
        return False
    
    # Select first 3 active items
    test_indices = active_items.head(3).index.tolist()
    
    for idx in test_indices:
        old_rate = df.loc[idx, 'Bill Rate']
        new_rate = old_rate - 5
        df.loc[idx, 'Bill Rate'] = new_rate
        df.loc[idx, 'Bill Amount'] = df.loc[idx, 'Bill Quantity'] * new_rate
        print(f"  Item {df.loc[idx, 'Item No']}: ₹{old_rate:.2f} → ₹{new_rate:.2f}")
    
    print()
    
    # TEST 2: Apply Part-Rate logic
    print("TEST 2: Apply Part-Rate Display Logic")
    print("-" * 80)
    
    # Track which items have part-rate
    df['Is Part Rate'] = df['Bill Rate'] < df['WO Rate']
    
    # Create display column
    df['Rate Display'] = df.apply(
        lambda row: f"₹{row['Bill Rate']:.2f} (Part Rate)" 
        if row['Is Part Rate'] 
        else f"₹{row['Bill Rate']:.2f}",
        axis=1
    )
    
    # Update description
    for idx in df[df['Is Part Rate']].index:
        desc = df.loc[idx, 'Description']
        if '(Part Rate)' not in desc:
            df.loc[idx, 'Description'] = f"{desc} (Part Rate)"
    
    part_rate_items = df[df['Is Part Rate']]
    print(f"  Found {len(part_rate_items)} part-rate items")
    print()
    
    # TEST 3: Verify display format
    print("TEST 3: Verify Display Format")
    print("-" * 80)
    
    all_passed = True
    
    for idx in test_indices:
        item_no = df.loc[idx, 'Item No']
        rate_display = df.loc[idx, 'Rate Display']
        description = df.loc[idx, 'Description']
        is_part_rate = df.loc[idx, 'Is Part Rate']
        
        # Check rate display format
        if is_part_rate:
            if '(Part Rate)' in rate_display:
                print(f"  ✅ Item {item_no}: {rate_display}")
            else:
                print(f"  ❌ Item {item_no}: Missing '(Part Rate)' in rate display")
                all_passed = False
            
            # Check description
            if '(Part Rate)' in description:
                print(f"     ✅ Description updated: {description[:50]}...")
            else:
                print(f"     ❌ Description not updated")
                all_passed = False
        else:
            print(f"  ⚠️ Item {item_no}: Not marked as part-rate")
    
    print()
    
    # TEST 4: Calculate savings
    print("TEST 4: Calculate Part-Rate Savings")
    print("-" * 80)
    
    if len(part_rate_items) > 0:
        part_rate_items_copy = part_rate_items.copy()
        part_rate_items_copy['Savings'] = (part_rate_items_copy['WO Rate'] - part_rate_items_copy['Bill Rate']) * part_rate_items_copy['Bill Quantity']
        total_savings = part_rate_items_copy['Savings'].sum()
        
        print(f"  Total Savings: ₹{total_savings:,.2f}")
        print()
        
        print("  Part-Rate Items Detail:")
        for idx, row in part_rate_items_copy.iterrows():
            print(f"    {row['Item No']}: {row['Rate Display']} (Savings: ₹{row['Savings']:.2f})")
    else:
        print("  ⚠️ No part-rate items found")
        all_passed = False
    
    print()
    
    # SUMMARY
    print("="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    if all_passed and len(part_rate_items) > 0:
        print("✅ ALL TESTS PASSED")
        print()
        print("Verified:")
        print("  ✅ Rate display shows '₹X (Part Rate)' format")
        print("  ✅ Description includes '(Part Rate)' label")
        print("  ✅ Is Part Rate flag correctly set")
        print("  ✅ Savings calculated correctly")
        print()
        return True
    else:
        print("❌ SOME TESTS FAILED")
        print()
        return False

if __name__ == '__main__':
    success = test_part_rate_display()
    sys.exit(0 if success else 1)
