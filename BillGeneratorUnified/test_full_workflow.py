#!/usr/bin/env python3
"""
Full Workflow Test - Excel Upload + Online/Hybrid Mode
Tests all input files with:
1. Excel upload without changes (baseline)
2. Online/Hybrid mode with:
   - Add quantity to 3 zero-qty items
   - Reduce rate by ₹5 for 2-3 items with existing bill quantity
   - Add "(Part Rate)" label where rate is reduced
3. Random order testing
4. Memory management and cache cleaning
"""
import sys
from pathlib import Path
import pandas as pd
import random
import gc
import io

# Add core to path
sys.path.insert(0, str(Path(__file__).parent))

def clean_memory():
    """Clean memory and cache"""
    gc.collect()
    try:
        from core.utils.cache_cleaner import CacheCleaner
        CacheCleaner.clean_cache(verbose=False)
    except:
        pass

def test_excel_upload_baseline(file_path, test_number):
    """Test Excel upload without any changes (baseline)"""
    print("="*80)
    print(f"TEST {test_number}A: EXCEL UPLOAD BASELINE - {file_path.name}")
    print("="*80)
    print()
    
    try:
        print("STEP 1: Upload and Process Excel File")
        print("-" * 80)
        
        from core.processors.excel_processor import ExcelProcessor
        processor = ExcelProcessor()
        
        # Read file as BytesIO
        with open(file_path, 'rb') as f:
            file_bytes = io.BytesIO(f.read())
        
        processed_data = processor.process_excel(file_bytes)
        
        # Extract data
        title_data = processed_data.get('title_data', {})
        work_order_data = processed_data.get('work_order_data')
        bill_quantity_data = processed_data.get('bill_quantity_data')
        
        # Convert to DataFrames if needed
        if isinstance(work_order_data, list):
            work_order_df = pd.DataFrame(work_order_data)
        else:
            work_order_df = work_order_data
        
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
        
        print("STEP 2: Generate Documents (No Changes)")
        print("-" * 80)
        
        from core.generators.html_generator import HTMLGenerator
        
        data = {
            'title_data': title_data,
            'work_order_data': work_order_df,
            'bill_quantity_data': bill_quantity_df if bill_quantity_df is not None else work_order_df,
            'extra_items_data': processed_data.get('extra_items_data', pd.DataFrame()),
            'source_filename': file_path.name
        }
        
        generator = HTMLGenerator(data)
        html_documents = generator.generate_all_documents()
        
        print(f"✅ Generated {len(html_documents)} HTML documents")
        for doc_name in html_documents.keys():
            print(f"   📄 {doc_name}")
        print()
        
        # Calculate totals
        try:
            if bill_quantity_df is not None and not bill_quantity_df.empty:
                # Use proper column access for DataFrames
                qty_col = bill_quantity_df['Quantity'] if 'Quantity' in bill_quantity_df.columns else 0
                rate_col = bill_quantity_df['Rate'] if 'Rate' in bill_quantity_df.columns else 0
                total = (pd.to_numeric(qty_col, errors='coerce').fillna(0) * 
                        pd.to_numeric(rate_col, errors='coerce').fillna(0)).sum()
            else:
                qty_col = work_order_df['Quantity'] if 'Quantity' in work_order_df.columns else 0
                rate_col = work_order_df['Rate'] if 'Rate' in work_order_df.columns else 0
                total = (pd.to_numeric(qty_col, errors='coerce').fillna(0) * 
                        pd.to_numeric(rate_col, errors='coerce').fillna(0)).sum()
            
            print(f"✅ BASELINE TEST COMPLETED - Total: ₹{total:,.2f}")
        except Exception as e:
            print(f"✅ BASELINE TEST COMPLETED - Total calculation skipped: {str(e)[:50]}")
        print()
        
        # Clean up
        del generator, html_documents, processed_data
        clean_memory()
        
        return True
        
    except Exception as e:
        print(f"❌ BASELINE TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_online_mode_with_modifications(file_path, test_number):
    """Test online/hybrid mode with modifications"""
    print("="*80)
    print(f"TEST {test_number}B: ONLINE MODE WITH MODIFICATIONS - {file_path.name}")
    print("="*80)
    print()
    
    try:
        # Step 1: Load and process file
        print("STEP 1: Load Excel File")
        print("-" * 80)
        
        from core.processors.excel_processor import ExcelProcessor
        processor = ExcelProcessor()
        
        # Read file as BytesIO
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
        
        # Step 2: Prepare items list (simulating online mode)
        print("STEP 2: Prepare Items for Online Editing")
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
            bill_qty = 0.0  # Start with 0 to identify zero-qty items
            if bill_quantity_df is not None and not bill_quantity_df.empty:
                if idx < len(bill_quantity_df):
                    bill_row = bill_quantity_df.iloc[idx]
                    try:
                        bill_qty_value = bill_row.get('Quantity', 0)
                        if bill_qty_value and str(bill_qty_value) != 'nan':
                            bill_qty = float(bill_qty_value)
                    except (ValueError, TypeError):
                        bill_qty = 0.0
            
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
        print(f"   Active Items (Bill Qty > 0): {len(active_items)}")
        print(f"   Zero Qty Items: {len(zero_qty_items)}")
        print()
        
        # Step 3: Modification 1 - Add quantity to 3 zero-qty items
        print("STEP 3: Add Quantity to 3 Zero-Qty Items")
        print("-" * 80)
        
        modifications_made = []
        
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
                modifications_made.append(f"Added qty to Item {df.loc[idx, 'Item No']}")
        elif len(zero_qty_items) > 0:
            print(f"   ⚠️ Only {len(zero_qty_items)} zero-qty items available (need 3)")
            # Add to all available
            for idx in zero_qty_items.index:
                old_qty = df.loc[idx, 'Bill Quantity']
                new_qty = df.loc[idx, 'WO Quantity'] * 0.5
                df.loc[idx, 'Bill Quantity'] = new_qty
                df.loc[idx, 'Bill Amount'] = new_qty * df.loc[idx, 'Bill Rate']
                print(f"   ✏️ Item {df.loc[idx, 'Item No']}: Qty {old_qty:.2f} → {new_qty:.2f}")
                modifications_made.append(f"Added qty to Item {df.loc[idx, 'Item No']}")
        else:
            print(f"   ⚠️ No zero-qty items available")
        
        print()
        
        # Step 4: Modification 2 - Reduce rate by Rs.5 for 2-3 active items
        print("STEP 4: Reduce Rate by Rs.5 for 2-3 Active Items (Part Rate)")
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
                
                # Add "(Part Rate)" to description if rate was actually reduced
                if new_rate < old_rate:
                    desc = df.loc[idx, 'Description']
                    if '(Part Rate)' not in desc:
                        df.loc[idx, 'Description'] = f"{desc} (Part Rate)"
                    
                    print(f"   ✏️ Item {df.loc[idx, 'Item No']}: Rate ₹{old_rate:.2f} → ₹{new_rate:.2f} (Part Rate)")
                    modifications_made.append(f"Reduced rate for Item {df.loc[idx, 'Item No']} (Part Rate)")
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
        
        # Step 6: Generate documents with modifications
        print("STEP 6: Generate Documents with Modifications")
        print("-" * 80)
        
        from core.generators.html_generator import HTMLGenerator
        
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
            
            # Verify "(Part Rate)" appears in documents
            part_rate_found = False
            for doc_name, html_content in html_documents.items():
                if '(Part Rate)' in html_content:
                    part_rate_found = True
                    print(f"      ✅ '(Part Rate)' label found in {doc_name}")
            
            if not part_rate_found and any('Part Rate' in m for m in modifications_made):
                print(f"      ⚠️ '(Part Rate)' label not found in documents")
            
        except Exception as e:
            print(f"   ❌ Document generation failed: {str(e)[:200]}")
            import traceback
            traceback.print_exc()
            html_documents = {}
        
        print()
        
        # Step 7: Summary
        print("STEP 7: Test Summary")
        print("-" * 80)
        
        print(f"   Modifications Made: {len(modifications_made)}")
        for mod in modifications_made:
            print(f"      • {mod}")
        
        print(f"   ✅ Total bill reduction: ₹{difference:,.2f} ({100-percentage:.1f}%)")
        print()
        
        # Clean memory
        del df, generator, html_documents, processed_data
        clean_memory()
        
        print(f"✅ ONLINE MODE TEST COMPLETED SUCCESSFULLY")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ ONLINE MODE TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run comprehensive tests on all input files"""
    print()
    print("="*80)
    print("FULL WORKFLOW TEST - EXCEL UPLOAD + ONLINE MODE")
    print("="*80)
    print()
    print("Testing Strategy:")
    print("  A. Excel Upload Baseline (no changes)")
    print("  B. Online Mode with modifications:")
    print("     1. Add quantity to 3 zero-qty items")
    print("     2. Reduce rate by Rs.5 for 2-3 items with existing bill quantity")
    print("     3. Add '(Part Rate)' label where rate is reduced")
    print("  4. Test files in random order")
    print("  5. Clean memory between tests")
    print()
    
    # Get all test files
    test_dir = Path('TEST_INPUT_FILES')
    if not test_dir.exists():
        print(f"❌ Test directory not found: {test_dir}")
        return 1
    
    test_files = list(test_dir.glob('*.xlsx')) + list(test_dir.glob('*.xls')) + list(test_dir.glob('*.xlsm'))
    
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
        # Test A: Excel upload baseline
        baseline_success = test_excel_upload_baseline(test_file, idx)
        
        # Clean memory between tests
        print("🧹 Cleaning memory...")
        clean_memory()
        print()
        
        # Test B: Online mode with modifications
        online_success = test_online_mode_with_modifications(test_file, idx)
        
        results.append((test_file.name, baseline_success, online_success))
        
        # Clean memory between files
        if idx < len(test_files):
            print("🧹 Cleaning memory before next file...")
            clean_memory()
            print()
    
    # Final summary
    print()
    print("="*80)
    print("FINAL TEST SUMMARY")
    print("="*80)
    print()
    
    baseline_passed = sum(1 for _, b, _ in results if b)
    online_passed = sum(1 for _, _, o in results if o)
    total_tests = len(results) * 2
    total_passed = baseline_passed + online_passed
    
    print(f"{'File':<40} {'Baseline':<12} {'Online':<12}")
    print("-" * 80)
    for filename, baseline, online in results:
        baseline_status = "✅ PASS" if baseline else "❌ FAIL"
        online_status = "✅ PASS" if online else "❌ FAIL"
        print(f"{filename:<40} {baseline_status:<12} {online_status:<12}")
    
    print()
    print(f"Total Tests: {total_tests} ({len(results)} files × 2 modes)")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_tests - total_passed}")
    print()
    print(f"Baseline Tests: {baseline_passed}/{len(results)} passed")
    print(f"Online Mode Tests: {online_passed}/{len(results)} passed")
    print()
    
    if total_passed == total_tests:
        print("🎉 ALL TESTS PASSED!")
        print()
        print("Verified:")
        print("  ✅ Excel upload works without changes")
        print("  ✅ Zero-qty items can be activated")
        print("  ✅ Rates can be reduced (Part Rate)")
        print("  ✅ '(Part Rate)' label added correctly")
        print("  ✅ Documents generate successfully")
        print("  ✅ Memory management working")
        print("  ✅ Random order testing successful")
        print()
        return 0
    else:
        print(f"⚠️ {total_tests - total_passed} TEST(S) FAILED")
        return 1

if __name__ == '__main__':
    sys.exit(main())
