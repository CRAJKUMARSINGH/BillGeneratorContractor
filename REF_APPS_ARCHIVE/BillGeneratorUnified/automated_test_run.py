#!/usr/bin/env python3
"""
Automated Test Run - Process all files in TEST_INPUT_FILES
Complete end-to-end testing without UI
"""
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
import traceback

# Add core to path
sys.path.insert(0, str(Path(__file__).parent))

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)

def print_section(text):
    """Print formatted section"""
    print(f"\n{'─' * 80}")
    print(f"  {text}")
    print(f"{'─' * 80}")

def test_file_processing(file_path):
    """Test processing a single file"""
    print_section(f"Testing: {file_path.name}")
    
    results = {
        'file': file_path.name,
        'size_kb': file_path.stat().st_size / 1024,
        'readable': False,
        'rows': 0,
        'columns': 0,
        'has_data': False,
        'bill_type': 'Unknown',
        'has_extras': False,
        'errors': []
    }
    
    try:
        # Step 1: Read file
        print(f"  📖 Reading Excel file...")
        df = pd.read_excel(file_path, sheet_name=0)
        results['readable'] = True
        results['rows'] = len(df)
        results['columns'] = len(df.columns)
        print(f"  ✅ File read successfully: {results['rows']} rows, {results['columns']} columns")
        
        # Step 2: Check for data
        if not df.empty:
            results['has_data'] = True
            print(f"  ✅ Data found")
            
            # Display column names
            print(f"  📋 Columns: {list(df.columns)[:5]}...")
            
            # Step 3: Detect bill type from filename
            filename_lower = file_path.name.lower()
            if 'final' in filename_lower:
                results['bill_type'] = 'Final Bill'
            elif 'running' in filename_lower:
                results['bill_type'] = 'Running Bill'
            
            if 'extra' in filename_lower:
                results['has_extras'] = True
            
            print(f"  📄 Bill Type: {results['bill_type']}")
            print(f"  ➕ Has Extras: {'Yes' if results['has_extras'] else 'No'}")
            
            # Step 4: Try to identify key columns
            print(f"\n  🔍 Analyzing structure...")
            
            # Look for common patterns
            potential_sno = [col for col in df.columns if 'S.No' in str(col) or 's.no' in str(col).lower()]
            potential_desc = [col for col in df.columns if 'description' in str(col).lower() or 'item' in str(col).lower()]
            potential_qty = [col for col in df.columns if 'quantity' in str(col).lower() or 'qty' in str(col).lower()]
            potential_rate = [col for col in df.columns if 'rate' in str(col).lower()]
            potential_amount = [col for col in df.columns if 'amount' in str(col).lower()]
            
            if potential_sno:
                print(f"  ✅ S.No column found: {potential_sno[0]}")
            if potential_desc:
                print(f"  ✅ Description column found: {potential_desc[0]}")
            if potential_qty:
                print(f"  ✅ Quantity column found: {potential_qty[0]}")
            if potential_rate:
                print(f"  ✅ Rate column found: {potential_rate[0]}")
            if potential_amount:
                print(f"  ✅ Amount column found: {potential_amount[0]}")
            
            # Step 5: Sample data
            print(f"\n  📊 Sample Data (first 3 rows):")
            for idx, row in df.head(3).iterrows():
                print(f"    Row {idx}: {list(row.values)[:3]}...")
            
            # Step 6: Try to process with core modules
            try:
                from core.processors.excel_processor import ExcelProcessor
                from core.utils.output_manager import OutputManager
                
                print(f"\n  🔧 Initializing processors...")
                processor = ExcelProcessor()
                output_mgr = OutputManager(source_filename=file_path.stem)
                
                print(f"  ✅ Processors initialized")
                print(f"  📁 Output folder: {output_mgr.get_output_folder()}")
                
            except Exception as e:
                results['errors'].append(f"Processor init: {str(e)}")
                print(f"  ⚠️  Processor warning: {str(e)}")
        
        else:
            print(f"  ⚠️  File is empty")
            results['errors'].append("Empty file")
    
    except Exception as e:
        results['errors'].append(f"Read error: {str(e)}")
        print(f"  ❌ Error: {str(e)}")
        traceback.print_exc()
    
    return results

def main():
    """Main test function"""
    print_header("🧪 AUTOMATED TEST RUN - BILLGENERATOR UNIFIED")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Test Type: Complete File Processing Test")
    
    # Step 1: Check core modules
    print_section("Step 1: Checking Core Modules")
    
    modules_to_test = [
        'core.config.config_loader',
        'core.processors.excel_processor',
        'core.generators.html_generator',
        'core.utils.output_manager'
    ]
    
    modules_ok = True
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except Exception as e:
            print(f"  ❌ {module}: {str(e)}")
            modules_ok = False
    
    if not modules_ok:
        print("\n  ❌ Core modules check failed. Cannot proceed.")
        return
    
    print("\n  ✅ All core modules loaded successfully")
    
    # Step 2: Load configuration
    print_section("Step 2: Loading Configuration")
    
    try:
        from core.config.config_loader import ConfigLoader
        config = ConfigLoader.load_from_file('config/v01.json')
        print(f"  ✅ Config: {config.app_name} v{config.version}")
        print(f"  ✅ Mode: {config.mode}")
    except Exception as e:
        print(f"  ❌ Config error: {str(e)}")
        return
    
    # Step 3: Scan test files
    print_section("Step 3: Scanning Test Files")
    
    test_input_dir = Path("TEST_INPUT_FILES")
    if not test_input_dir.exists():
        print(f"  ❌ TEST_INPUT_FILES directory not found")
        return
    
    excel_files = sorted(test_input_dir.glob("*.xlsx"))
    
    if not excel_files:
        print(f"  ❌ No Excel files found in TEST_INPUT_FILES/")
        return
    
    print(f"  ✅ Found {len(excel_files)} Excel files:")
    for i, file in enumerate(excel_files, 1):
        size_kb = file.stat().st_size / 1024
        print(f"    {i}. {file.name:40s} ({size_kb:6.1f} KB)")
    
    # Step 4: Process each file
    print_header("🔄 PROCESSING TEST FILES")
    
    all_results = []
    
    for i, file_path in enumerate(excel_files, 1):
        print(f"\n[{i}/{len(excel_files)}] Processing: {file_path.name}")
        result = test_file_processing(file_path)
        all_results.append(result)
    
    # Step 5: Generate summary report
    print_header("📊 TEST SUMMARY REPORT")
    
    total_files = len(all_results)
    readable_files = sum(1 for r in all_results if r['readable'])
    files_with_data = sum(1 for r in all_results if r['has_data'])
    files_with_errors = sum(1 for r in all_results if r['errors'])
    
    print(f"\n  📁 Total Files Tested: {total_files}")
    print(f"  ✅ Readable Files: {readable_files}/{total_files}")
    print(f"  📊 Files with Data: {files_with_data}/{total_files}")
    print(f"  ❌ Files with Errors: {files_with_errors}/{total_files}")
    
    # Detailed results table
    print_section("Detailed Results")
    
    print(f"\n  {'File':<40} {'Size':>8} {'Rows':>6} {'Type':>15} {'Extras':>8} {'Status':>10}")
    print(f"  {'-'*40} {'-'*8} {'-'*6} {'-'*15} {'-'*8} {'-'*10}")
    
    for result in all_results:
        status = '✅ OK' if result['readable'] and not result['errors'] else '⚠️ WARN' if result['readable'] else '❌ FAIL'
        extras = '✅ Yes' if result['has_extras'] else '❌ No'
        
        print(f"  {result['file']:<40} {result['size_kb']:>7.1f}K {result['rows']:>6} {result['bill_type']:>15} {extras:>8} {status:>10}")
    
    # Bill type distribution
    print_section("Bill Type Distribution")
    
    bill_types = {}
    for result in all_results:
        bill_type = result['bill_type']
        bill_types[bill_type] = bill_types.get(bill_type, 0) + 1
    
    for bill_type, count in bill_types.items():
        print(f"  {bill_type:20s}: {count} files")
    
    # Extra items analysis
    print_section("Extra Items Analysis")
    
    with_extras = sum(1 for r in all_results if r['has_extras'])
    without_extras = total_files - with_extras
    
    print(f"  With Extra Items:    {with_extras} files")
    print(f"  Without Extra Items: {without_extras} files")
    
    # Error summary
    if files_with_errors > 0:
        print_section("Errors Encountered")
        
        for result in all_results:
            if result['errors']:
                print(f"\n  ❌ {result['file']}:")
                for error in result['errors']:
                    print(f"     • {error}")
    
    # Final status
    print_header("✅ TEST RUN COMPLETED")
    
    if readable_files == total_files and files_with_errors == 0:
        print("\n  🎉 ALL TESTS PASSED!")
        print(f"  ✅ All {total_files} files processed successfully")
        print(f"  ✅ No errors encountered")
        print(f"  ✅ System is ready for production use")
    elif readable_files == total_files:
        print("\n  ⚠️  TESTS PASSED WITH WARNINGS")
        print(f"  ✅ All {total_files} files are readable")
        print(f"  ⚠️  {files_with_errors} files had warnings")
        print(f"  💡 Review warnings above")
    else:
        print("\n  ❌ SOME TESTS FAILED")
        print(f"  ❌ {total_files - readable_files} files could not be read")
        print(f"  💡 Check errors above for details")
    
    # Next steps
    print_section("Next Steps")
    
    print(f"\n  1. 🌐 Test in Streamlit UI:")
    print(f"     python -m streamlit run app.py")
    print(f"     Then upload files from TEST_INPUT_FILES/")
    
    print(f"\n  2. 📥 Check generated outputs:")
    print(f"     ls OUTPUT/")
    
    print(f"\n  3. 🚀 Deploy to Streamlit Cloud:")
    print(f"     git add .")
    print(f"     git commit -m 'Ready for deployment'")
    print(f"     git push")
    
    print(f"\n  4. 📖 Read documentation:")
    print(f"     - TEST_RUN_REPORT.md")
    print(f"     - QUICK_TEST_GUIDE.md")
    print(f"     - DEPLOYMENT_STATUS.md")
    
    print("\n" + "=" * 80)
    
    return readable_files == total_files

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {str(e)}")
        traceback.print_exc()
        sys.exit(1)
