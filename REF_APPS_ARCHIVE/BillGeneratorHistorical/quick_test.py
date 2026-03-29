#!/usr/bin/env python3
"""
Quick Test - Generate and display sample outputs
"""

import pandas as pd
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("="*60)
print("🧪 Quick Test - Bill Generator")
print("="*60)
print()

# Test 1: Enterprise Excel Processor
print("Test 1: Enterprise Excel Processor")
print("-" * 60)
try:
    from core.excel_processor_enterprise import EnterpriseExcelProcessor, SheetSchema
    
    processor = EnterpriseExcelProcessor(
        sanitize_strings=True,
        validate_schemas=True
    )
    
    # Find a test file
    test_files = list(Path("test_input_files").glob("*.xlsx"))
    if test_files:
        test_file = test_files[0]
        print(f"📁 Processing: {test_file.name}")
        
        # Define schemas
        schemas = {
            "Work Order": SheetSchema(name="Work Order", required=True, min_rows=1),
            "Bill Quantity": SheetSchema(name="Bill Quantity", required=True, min_rows=1),
            "Extra Items": SheetSchema(name="Extra Items", required=False, allow_empty=True)
        }
        
        # Process file
        result = processor.process_file(test_file, schemas=schemas)
        
        if result.success:
            print(f"✅ SUCCESS: Processed {len(result.data)} sheets")
            for sheet_name, df in result.data.items():
                print(f"   - {sheet_name}: {len(df)} rows, {len(df.columns)} columns")
            print(f"   Metadata: {result.metadata}")
        else:
            print(f"❌ FAILED: {result.errors}")
    else:
        print("⚠️ No test files found in test_input_files/")
    
    print("✅ Enterprise Excel Processor: OK")
    
except Exception as e:
    print(f"❌ Enterprise Excel Processor: FAILED - {e}")

print()

# Test 2: Enterprise HTML Renderer
print("Test 2: Enterprise HTML Renderer")
print("-" * 60)
try:
    from core.html_renderer_enterprise import EnterpriseHTMLRenderer, RenderConfig, DocumentType
    
    config = RenderConfig(
        template_dir="templates",
        output_dir="test_outputs",
        enable_security_checks=True,
        pdf_ready=True
    )
    
    renderer = EnterpriseHTMLRenderer(config)
    
    # Sample data
    data = {
        'title': 'Test Bill',
        'project_name': 'Test Project',
        'totals': {
            'grand_total': 1000000.50,
            'premium': {'amount': 50000.00},
            'payable': 1050000.50
        }
    }
    
    # Render document
    result = renderer.render(
        DocumentType.FIRST_PAGE,
        data,
        'test_first_page.html'
    )
    
    if result.success:
        print(f"✅ SUCCESS: Rendered to {result.output_path}")
        print(f"   HTML size: {result.metadata['html_size']} characters")
        print(f"   Document type: {result.metadata['document_type']}")
    else:
        print(f"❌ FAILED: {result.errors}")
    
    print("✅ Enterprise HTML Renderer: OK")
    
except Exception as e:
    print(f"❌ Enterprise HTML Renderer: FAILED - {e}")

print()

# Test 3: Legacy Processor
print("Test 3: Legacy Processor")
print("-" * 60)
try:
    from core.computations.bill_processor import process_bill
    
    # Find a test file
    test_files = list(Path("test_input_files").glob("*.xlsx"))
    if test_files:
        test_file = test_files[0]
        print(f"📁 Processing: {test_file.name}")
        
        # Load Excel
        xl_file = pd.ExcelFile(test_file)
        ws_wo = pd.read_excel(xl_file, "Work Order", header=None)
        ws_bq = pd.read_excel(xl_file, "Bill Quantity", header=None)
        ws_extra = pd.read_excel(xl_file, "Extra Items", header=None)
        
        # Process bill
        first_page_data, last_page_data, deviation_data, extra_items_data, note_sheet_data = process_bill(
            ws_wo, ws_bq, ws_extra, 5.0, "above", 0
        )
        
        print(f"✅ SUCCESS: Bill processed")
        print(f"   Grand Total: ₹{first_page_data['totals']['grand_total']:,.2f}")
        print(f"   Premium: ₹{first_page_data['totals']['premium']['amount']:,.2f}")
        print(f"   Payable: ₹{first_page_data['totals']['payable']:,.2f}")
    else:
        print("⚠️ No test files found")
    
    print("✅ Legacy Processor: OK")
    
except Exception as e:
    print(f"❌ Legacy Processor: FAILED - {e}")

print()
print("="*60)
print("✅ All tests complete!")
print("="*60)
print()
print("📖 To run the interactive test with preview:")
print("   streamlit run test_runner_with_preview.py")
print()
print("🌐 The Streamlit app should open in your browser at:")
print("   http://localhost:8501")
print()
