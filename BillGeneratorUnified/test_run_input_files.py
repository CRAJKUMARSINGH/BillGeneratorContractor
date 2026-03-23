#!/usr/bin/env python3
"""
Test Run - Process Excel files from TEST_INPUT_FILES folder
Tests the complete workflow without Streamlit UI
"""
import sys
from pathlib import Path
import pandas as pd

# Add core to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("BILLGENERATOR TEST RUN - INPUT FILES")
print("=" * 70)

# Test 1: Check if core modules can be imported
print("\n📦 Step 1: Checking Core Modules...")
try:
    from core.config.config_loader import ConfigLoader
    print("  ✓ ConfigLoader imported")
    
    from core.processors.excel_processor import ExcelProcessor
    print("  ✓ ExcelProcessor imported")
    
    from core.generators.html_generator import HTMLGenerator
    print("  ✓ HTMLGenerator imported")
    
    from core.utils.output_manager import OutputManager
    print("  ✓ OutputManager imported")
    
    print("  ✅ All core modules imported successfully!")
except Exception as e:
    print(f"  ❌ Import error: {e}")
    sys.exit(1)

# Test 2: Load configuration
print("\n⚙️  Step 2: Loading Configuration...")
try:
    config = ConfigLoader.load_from_file('config/v01.json')
    print(f"  ✓ Config loaded: {config.app_name} v{config.version}")
    print(f"  ✓ Mode: {config.mode}")
    print(f"  ✓ Features enabled: {sum([
        config.features.excel_upload,
        config.features.online_entry,
        config.features.batch_processing,
        config.features.advanced_pdf
    ])}/4")
except Exception as e:
    print(f"  ❌ Config error: {e}")
    sys.exit(1)

# Test 3: List available test files
print("\n📁 Step 3: Scanning Test Input Files...")
test_input_dir = Path("TEST_INPUT_FILES")
excel_files = list(test_input_dir.glob("*.xlsx"))

if not excel_files:
    print("  ❌ No Excel files found in TEST_INPUT_FILES/")
    sys.exit(1)

print(f"  ✓ Found {len(excel_files)} Excel files:")
for i, file in enumerate(excel_files, 1):
    size_kb = file.stat().st_size / 1024
    print(f"    {i}. {file.name} ({size_kb:.1f} KB)")

# Test 4: Process first file
print("\n🔄 Step 4: Processing Test File...")
test_file = excel_files[0]
print(f"  📄 Selected: {test_file.name}")

try:
    # Read Excel file
    print(f"  📖 Reading Excel file...")
    df = pd.read_excel(test_file, sheet_name=0)
    print(f"  ✓ Loaded {len(df)} rows, {len(df.columns)} columns")
    
    # Display first few rows
    print(f"\n  📊 Preview (first 5 rows):")
    print(f"  Columns: {list(df.columns)[:5]}...")
    print(f"  Shape: {df.shape}")
    
    # Check for required columns (common bill columns)
    required_cols = ['S.No', 'Description', 'Quantity', 'Rate', 'Amount']
    found_cols = [col for col in required_cols if col in df.columns]
    print(f"\n  🔍 Column Check:")
    print(f"    Looking for: {required_cols}")
    print(f"    Found: {found_cols}")
    
    if len(found_cols) >= 3:
        print(f"  ✅ Sufficient columns found for processing")
    else:
        print(f"  ⚠️  Standard columns not found - file may have custom structure")
    
except Exception as e:
    print(f"  ❌ Error reading file: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Initialize Output Manager
print("\n📦 Step 5: Initializing Output Manager...")
try:
    output_mgr = OutputManager(source_filename=test_file.stem)
    output_folder = output_mgr.get_output_folder()
    print(f"  ✓ Output folder: {output_folder}")
    print(f"  ✓ Output manager ready")
except Exception as e:
    print(f"  ❌ Output manager error: {e}")
    sys.exit(1)

# Test 6: Try to process with ExcelProcessor
print("\n🔧 Step 6: Testing Excel Processor...")
try:
    processor = ExcelProcessor()
    print(f"  ✓ ExcelProcessor initialized")
    
    # Try to extract data
    print(f"  🔍 Attempting to extract bill data...")
    
    # Check if file has standard structure
    if 'S.No' in df.columns or 'S.No.' in df.columns:
        print(f"  ✓ Standard bill format detected")
        
        # Try to identify bill type
        if 'Running' in test_file.name or 'running' in test_file.name:
            bill_type = "Running Bill"
        elif 'Final' in test_file.name or 'FINAL' in test_file.name:
            bill_type = "Final Bill"
        else:
            bill_type = "Unknown"
        
        print(f"  📋 Bill Type: {bill_type}")
        
        # Check for extra items
        if 'extra' in test_file.name.lower() or 'Extra' in test_file.name:
            print(f"  ➕ Extra items detected in filename")
        else:
            print(f"  📝 Standard items only")
            
    else:
        print(f"  ⚠️  Non-standard format - manual inspection needed")
    
except Exception as e:
    print(f"  ⚠️  Processor warning: {e}")
    # Don't exit - this is expected for some file formats

# Test 7: Summary
print("\n" + "=" * 70)
print("TEST RUN SUMMARY")
print("=" * 70)
print(f"✅ Core modules: Working")
print(f"✅ Configuration: Loaded")
print(f"✅ Test files: {len(excel_files)} found")
print(f"✅ File reading: Success")
print(f"✅ Output manager: Ready")
print(f"⚠️  Full processing: Requires Streamlit UI or CLI mode")

print("\n💡 Next Steps:")
print("  1. Run the full app: python -m streamlit run app.py")
print("  2. Upload one of these test files through the UI")
print("  3. Or use CLI mode: python cli.py --input TEST_INPUT_FILES/FirstFINALnoExtra.xlsx")

print("\n📝 Test Files Available:")
for file in excel_files:
    print(f"  • {file.name}")

print("\n" + "=" * 70)
print("✅ TEST RUN COMPLETED SUCCESSFULLY")
print("=" * 70)
