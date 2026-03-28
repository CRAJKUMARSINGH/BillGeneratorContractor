#!/usr/bin/env python3
"""
Hybrid Mode Workflow Test
Demonstrates: Upload Excel → Edit Bill Qty → Change Rates → Generate Documents
"""
import sys
from pathlib import Path
import pandas as pd

# Add core to path
sys.path.insert(0, str(Path(__file__).parent))

def test_hybrid_workflow():
    """Test complete hybrid workflow with qty and rate changes"""
    print("="*70)
    print("HYBRID MODE WORKFLOW TEST")
    print("="*70)
    print()
    print("Scenario: Part-rate payment with quantity adjustments")
    print()
    
    # Step 1: Load Excel file
    print("STEP 1: Upload Excel File")
    print("-" * 70)
    
    from core.processors.excel_processor_enterprise import ExcelProcessor
    
    test_file = Path('TEST_INPUT_FILES/0511Wextra.xlsx')
    if not test_file.exists():
        test_files = list(Path('TEST_INPUT_FILES').glob('*.xlsx'))
        if test_files:
            test_file = test_files[0]
        else:
            print("❌ No test files found")
            return False
    
    print(f"📁 File: {test_file.name}")
    
    processor = ExcelProcessor(sanitize_strings=True, validate_schemas=False)
    result = processor.process_file(test_file)
    
    if not result.success:
        print("❌ Failed to process Excel")
        return False
    
    print(f"✅ Extracted {len(result.data)} sheets")
    
    # Extract work order data
    work_order_df = result.data.get('Work Order')
    bill_quantity_df = result.data.get('Bill Quantity')
    
    if work_order_df is None or work_order_df.empty:
        print("❌ No work order data found")
        return False
    
    print(f"✅ Found {len(work_order_df)} work order items")
    print()
    
    # Step 2: Display original data
    print("STEP 2: Original Work Order Data")
    print("-" * 70)
    
    items_list = []
    for idx, row in work_order_df.iterrows():
        item_no = row.get('Item No.', f"{idx+1:03d}")
        description = row.get('Description of Item', row.get('Description', ''))
        unit = row.get('Unit', 'NOS')
        
        # Handle empty or invalid numeric values
        try:
            wo_quantity = float(row.get('Quantity', 0) or 0)
        except (ValueError, TypeError):
            wo_quantity = 0.0
        
        try:
            wo_rate = float(row.get('Rate', 0) or 0)
        except (ValueError, TypeError):
            wo_rate = 0.0
        
        # Get bill quantity if available
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
            'Description': description[:40] + '...' if len(description) > 40 else description,
            'Unit': unit,
            'WO Quantity': wo_quantity,
            'Bill Quantity': bill_qty,
            'WO Rate': wo_rate,
            'Bill Rate': wo_rate,
            'WO Amount': wo_quantity * wo_rate,
            'Bill Amount': bill_qty * wo_rate
        })
    
    original_df = pd.DataFrame(items_list)
    print(original_df.to_string(index=False))
    print()
    
    wo_total = original_df['WO Amount'].sum()
    bill_total = original_df['Bill Amount'].sum()
    
    print(f"Work Order Total: ₹{wo_total:,.2f}")
    print(f"Bill Total: ₹{bill_total:,.2f}")
    print()
    
    # Step 3: Make edits (simulate user changes)
    print("STEP 3: User Edits (Simulated)")
    print("-" * 70)
    print()
    
    edited_df = original_df.copy()
    
    # Edit 1: Change bill quantity for item 1 (partial work done)
    if len(edited_df) > 0:
        old_qty = edited_df.loc[0, 'Bill Quantity']
        new_qty = old_qty * 0.75  # 75% of work order quantity
        edited_df.loc[0, 'Bill Quantity'] = new_qty
        print(f"✏️ Edit 1: Item {edited_df.loc[0, 'Item No']}")
        print(f"   Changed Bill Quantity: {old_qty:.2f} → {new_qty:.2f} (75% of WO)")
        print()
    
    # Edit 2: Change rate for item 2 (part-rate payment)
    if len(edited_df) > 1:
        old_rate = edited_df.loc[1, 'Bill Rate']
        new_rate = old_rate * 0.60  # 60% part-rate
        edited_df.loc[1, 'Bill Rate'] = new_rate
        print(f"✏️ Edit 2: Item {edited_df.loc[1, 'Item No']}")
        print(f"   Changed Bill Rate: ₹{old_rate:.2f} → ₹{new_rate:.2f} (60% part-rate)")
        print()
    
    # Edit 3: Change both quantity and rate for item 3
    if len(edited_df) > 2:
        old_qty = edited_df.loc[2, 'Bill Quantity']
        new_qty = old_qty * 0.50  # 50% quantity
        old_rate = edited_df.loc[2, 'Bill Rate']
        new_rate = old_rate * 0.80  # 80% rate
        edited_df.loc[2, 'Bill Quantity'] = new_qty
        edited_df.loc[2, 'Bill Rate'] = new_rate
        print(f"✏️ Edit 3: Item {edited_df.loc[2, 'Item No']}")
        print(f"   Changed Bill Quantity: {old_qty:.2f} → {new_qty:.2f} (50% of WO)")
        print(f"   Changed Bill Rate: ₹{old_rate:.2f} → ₹{new_rate:.2f} (80% of WO)")
        print()
    
    # Recalculate amounts
    edited_df['Bill Amount'] = edited_df['Bill Quantity'] * edited_df['Bill Rate']
    
    # Step 4: Display edited data
    print("STEP 4: Edited Data (After User Changes)")
    print("-" * 70)
    print(edited_df.to_string(index=False))
    print()
    
    new_bill_total = edited_df['Bill Amount'].sum()
    difference = wo_total - new_bill_total
    percentage = (new_bill_total / wo_total * 100) if wo_total > 0 else 0
    
    print(f"Work Order Total: ₹{wo_total:,.2f}")
    print(f"New Bill Total: ₹{new_bill_total:,.2f}")
    print(f"Difference: ₹{difference:,.2f} ({100-percentage:.1f}% reduction)")
    print(f"Bill Percentage: {percentage:.1f}%")
    print()
    
    # Step 5: Generate documents
    print("STEP 5: Generate Documents with Edited Data")
    print("-" * 70)
    
    from core.generators.html_generator import HTMLGenerator
    
    # Extract title data
    title_data = {}
    if 'Title' in result.data:
        title_df = result.data['Title']
        for index, row in title_df.iterrows():
            if len(row) >= 2:
                key = str(row.iloc[0]).strip()
                value = row.iloc[1]
                if key:
                    title_data[key] = value
    
    # Prepare data for document generation
    work_order_data = edited_df.to_dict('records')
    
    data = {
        'title_data': title_data,
        'work_order_data': work_order_data,
        'bill_quantity_data': work_order_data,
        'extra_items_data': [],
        'source_filename': test_file.name,
        'hybrid_mode': True
    }
    
    # Generate HTML
    generator = HTMLGenerator(data)
    html_documents = generator.generate_all_documents()
    
    print(f"✅ Generated {len(html_documents)} HTML documents")
    
    for doc_name in html_documents.keys():
        print(f"   📄 {doc_name}")
    
    print()
    
    # Step 6: Summary
    print("STEP 6: Summary of Changes")
    print("-" * 70)
    print()
    
    print("📊 Changes Made:")
    changes_made = 0
    
    for idx in range(len(edited_df)):
        qty_changed = edited_df.loc[idx, 'Bill Quantity'] != original_df.loc[idx, 'Bill Quantity']
        rate_changed = edited_df.loc[idx, 'Bill Rate'] != original_df.loc[idx, 'Bill Rate']
        
        if qty_changed or rate_changed:
            changes_made += 1
            print(f"\n   Item {edited_df.loc[idx, 'Item No']}:")
            
            if qty_changed:
                print(f"      Quantity: {original_df.loc[idx, 'Bill Quantity']:.2f} → {edited_df.loc[idx, 'Bill Quantity']:.2f}")
            
            if rate_changed:
                print(f"      Rate: ₹{original_df.loc[idx, 'Bill Rate']:.2f} → ₹{edited_df.loc[idx, 'Bill Rate']:.2f}")
            
            print(f"      Amount: ₹{original_df.loc[idx, 'Bill Amount']:,.2f} → ₹{edited_df.loc[idx, 'Bill Amount']:,.2f}")
    
    print()
    print(f"✅ Total items changed: {changes_made}")
    print(f"✅ Bill reduction: ₹{difference:,.2f} ({100-percentage:.1f}%)")
    print()
    
    print("="*70)
    print("✅ HYBRID WORKFLOW TEST COMPLETED SUCCESSFULLY")
    print("="*70)
    print()
    
    print("This demonstrates:")
    print("  ✅ Upload Excel file")
    print("  ✅ Extract work order data")
    print("  ✅ Edit bill quantities (partial work)")
    print("  ✅ Edit bill rates (part-rate payments)")
    print("  ✅ Recalculate amounts automatically")
    print("  ✅ Generate documents with edited data")
    print()
    
    return True

if __name__ == '__main__':
    success = test_hybrid_workflow()
    sys.exit(0 if success else 1)
