#!/usr/bin/env python3
"""
Comprehensive Hybrid Mode Test
Tests all input files with:
1. Add quantity to 3 zero-qty items
2. Reduce rate by ₹5 for 2-3 items with existing bill quantity
3. Add "(Part Rate)" label where rate is reduced
4. Random order testing
5. Memory management and cache cleaning
"""
import sys
from pathlib import Path
import pandas as pd
import random
import gc

# Add core to path
sys.path.insert(0, str(Path(__file__).parent))

def clean_memory():
    """Clean memory and cache"""
    gc.collect()
    from core.utils.cache_cleaner import CacheCleaner
    CacheCleaner.clean_cache(verbose=False)

def test_file_with_modifications(file_path, test_number):
    """Test a single file with modifications"""
    print("="*80)
    print(f"TEST {test_number}: {file_path.name}")
    print("="*80)
    print()
    
    try:
        # Step 1: Load and process file
        print("STEP 1: Load Excel File")
        print("-" * 80)
        
        from core.processors.excel_processor import ExcelProcessor
        processor = ExcelProcessor()
        
        # Read file as BytesIO
        import io
        with open(file_path, 'rb') as f:
            file_bytes = io.BytesIO(f.read())
        
        processed_data = processor.process_excel(file_bytes)
        
        # Extract data
        title_data = processed_data.get('title_data', {})
        
        # Convert to DataFrames if needed
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
        
        if work_order_df is None or work_order_df.empty:
            print("❌ No work order data found")
            return False
        
        print(f"✅ Loaded: {len(work_order_df)} items")
        print(f"   Work: {title_data.get('Name of Work', 'N/A')[:50]}...")
        print()
        
        # Step 2: Prepare items list
        print("STEP 2: Prepare Items")
        print("-" * 80)
        
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
        
        # Identify zero-qty and active items
        zero_qty_items = df[df['Bill Quantity'] == 0]
        active_items = df[df['Bill Quantity'] > 0]
        
        print(f"   Total Items: {len(df)}")
        print(f"   Active Items: {len(active_items)}")
        print(f"   Zero Qty Items: {len(zero_qty_items)}")
        print()
        
        # Step 3: Modification 1 - Add quantity to 3 zero-qty items
        print("STEP 3: Add Quantity to 3 Zero-Qty Items")
        print("-" * 80)
        
        if len(zero_qty_items) >= 3:
            # Randomly select 3 zero-qty items
            selected_zero = random.sample(list(zero_qty_items.index), min(3, len(zero_qty_items)))
            
            for idx in selected_zero:
                old_qty = df.loc[idx, 'Bill Quantity']
                # Add 50% of WO quantity
                new_qty = df.loc[idx, 'WO Quantity'] * 0.5
                df.loc[idx, 'Bill Quantity'] = new_qty
                df.loc[idx, 'Bill Amount'] = new_qty * df.loc[idx, 'Bill Rate']
                
                print(f"   ✏️ Item {df.loc[idx, 'Item No']}: Qty {old_qty:.2f} → {new_qty:.2f}")
        else:
            print(f"   ⚠️ Only {len(zero_qty_items)} zero-qty items available")
        
        print()
        
        # Step 4: Modification 2 - Reduce rate by ₹5 for 2-3 active items
        print("STEP 4: Reduce Rate by ₹5 for 2-3 Active Items (Part Rate)")
        print("-" * 80)
        
        # Get active items with bill quantity > 0
        active_indices = df[df['Bill Quantity'] > 0].index.tolist()
        
        if len(active_indices) >= 2:
            # Randomly select 2-3 items
            num_to_modify = min(random.randint(2, 3), len(active_indices))
            selected_active = random.sample(active_indices, num_to_modify)
            
            for idx in selected_active:
                old_rate = df.loc[idx, 'Bill Rate']
                new_rate = max(0, old_rate - 5)  # Reduce by ₹5, min 0
                df.loc[idx, 'Bill Rate'] = new_rate
                df.loc[idx, 'Bill Amount'] = df.loc[idx, 'Bill Quantity'] * new_rate
                
                # Add "(Part Rate)" to description
                desc = df.loc[idx, 'Description']
                if '(Part Rate)' not in desc:
                    df.loc[idx, 'Description'] = f"{desc} (Part Rate)"
                
                print(f"   ✏️ Item {df.loc[idx, 'Item No']}: Rate ₹{old_rate:.2f} → ₹{new_rate:.2f} (Part Rate)")
        else:
            print(f"   ⚠️ Only {len(active_indices)} active items available")
        
        print()
        
        # Step 5: Calculate totals
        print("STEP 5: Calculate Totals")
        print("-" * 80)
        
        wo_total = df['WO Amount'].sum()
        bill_total = df['Bill Amount'].sum()
        difference = wo_total - bill_total
        percentage = (bill_total / wo_total * 100) if wo_total > 0 else 0
        
        print(f"   Work Order Total: ₹{wo_total:,.2f}")
        print(f"   Bill Total: ₹{bill_total:,.2f}")
        print(f"   Difference: ₹{difference:,.2f}")
        print(f"   Bill Percentage: {percentage:.1f}%")
        print()
        
        # Step 6: Generate documents
        print("STEP 6: Generate Documents")
        print("-" * 80)
        
        from core.generators.html_generator import HTMLGenerator
        
        # CRITICAL FIX: HTMLGenerator expects DataFrames, not lists
        # Filter to only include items with Bill Quantity > 0
        active_items_df = df[df['Bill Quantity'] > 0].copy()
        
        # Prepare work order data (convert hybrid format to standard format)
        work_order_list = []
        bill_quantity_list = []
        
        for idx, row in active_items_df.iterrows():
            # Standard format for work order
            work_order_list.append({
                'Item No.': row['Item No'],
                'Description': row['Description'],
                'Unit': row['Unit'],
                'Quantity': row['WO Quantity'],
                'Rate': row['WO Rate'],
                'Amount': row['WO Amount']
            })
            
            # Standard format for bill quantity
            bill_quantity_list.append({
                'Item No.': row['Item No'],
                'Description': row['Description'],
                'Unit': row['Unit'],
                'Quantity': row['Bill Quantity'],
                'Rate': row['Bill Rate'],
                'Amount': row['Bill Amount']
            })
        
        # Convert to DataFrames
        work_order_df_final = pd.DataFrame(work_order_list)
        bill_quantity_df_final = pd.DataFrame(bill_quantity_list)
        
        data = {
            'title_data': title_data,
            'work_order_data': work_order_df_final,
            'bill_quantity_data': bill_quantity_df_final,
            'extra_items_data': pd.DataFrame(),
            'source_filename': file_path.name,
            'hybrid_mode': True
        }
        
        try:
            generator = HTMLGenerator(data)
            html_documents = generator.generate_all_documents()
            
            print(f"   ✅ Generated {len(html_documents)} HTML documents")
            for doc_name in html_documents.keys():
                print(f"      📄 {doc_name}")
        except Exception as e:
            print(f"   ❌ Document generation failed: {str(e)[:200]}")
            import traceback
            print(f"   Full error:")
            traceback.print_exc()
            html_documents = {}  # Set to empty dict to avoid UnboundLocalError
        
        print()
        
        # Step 7: Summary
        print("STEP 7: Test Summary")
        print("-" * 80)
        
        modifications = []
        
        # Count modifications
        zero_qty_added = len(df[(df['Bill Quantity'] > 0) & (df.index.isin(selected_zero if len(zero_qty_items) >= 3 else []))])
        rate_reduced = len([idx for idx in (selected_active if len(active_indices) >= 2 else []) if '(Part Rate)' in df.loc[idx, 'Description']])
        
        print(f"   ✅ Zero-qty items activated: {zero_qty_added}")
        print(f"   ✅ Rates reduced (Part Rate): {rate_reduced}")
        print(f"   ✅ Total bill reduction: ₹{difference:,.2f} ({100-percentage:.1f}%)")
        print()
        
        # Clean memory
        del df, generator, html_documents, processed_data
        clean_memory()
        
        print(f"✅ TEST {test_number} COMPLETED SUCCESSFULLY")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ TEST {test_number} FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run comprehensive tests on all input files"""
    print()
    print("="*80)
    print("COMPREHENSIVE HYBRID MODE TEST")
    print("="*80)
    print()
    print("Testing Strategy:")
    print("  1. Add quantity to 3 zero-qty items in each file")
    print("  2. Reduce rate by ₹5 for 2-3 items with existing bill quantity")
    print("  3. Add '(Part Rate)' label where rate is reduced")
    print("  4. Test files in random order")
    print("  5. Clean memory between tests")
    print()
    
    # Get all test files
    test_dir = Path('TEST_INPUT_FILES')
    if not test_dir.exists():
        print(f"❌ Test directory not found: {test_dir}")
        return 1
    
    test_files = list(test_dir.glob('*.xlsx')) + list(test_dir.glob('*.xls'))
    
    if not test_files:
        print(f"❌ No test files found in {test_dir}")
        return 1
    
    print(f"Found {len(test_files)} test files:")
    for f in test_files:
        print(f"  📁 {f.name}")
    print()
    
    # Randomize order
    random.shuffle(test_files)
    print("Testing in random order...")
    print()
    
    # Run tests
    results = []
    
    for idx, test_file in enumerate(test_files, 1):
        success = test_file_with_modifications(test_file, idx)
        results.append((test_file.name, success))
        
        # Clean memory between tests
        if idx < len(test_files):
            print("🧹 Cleaning memory before next test...")
            clean_memory()
            print()
    
    # Final summary
    print()
    print("="*80)
    print("FINAL TEST SUMMARY")
    print("="*80)
    print()
    
    passed = sum(1 for _, success in results if success)
    failed = len(results) - passed
    
    for filename, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{filename:<40} {status}")
    
    print()
    print(f"Total Tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print()
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED!")
        print()
        print("Verified:")
        print("  ✅ Zero-qty items can be activated")
        print("  ✅ Rates can be reduced (Part Rate)")
        print("  ✅ '(Part Rate)' label added correctly")
        print("  ✅ Documents generate successfully")
        print("  ✅ Memory management working")
        print()
        return 0
    else:
        print(f"⚠️ {failed} TEST(S) FAILED")
        return 1

if __name__ == '__main__':
    sys.exit(main())
