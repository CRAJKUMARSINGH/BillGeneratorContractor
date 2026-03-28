#!/usr/bin/env python3
"""
Generate note sheets for all test input files
"""
import sys
from pathlib import Path
from datetime import datetime

# Add core to path
sys.path.insert(0, str(Path(__file__).parent))

from core.processors.excel_processor_enterprise import ExcelProcessor
from core.generators.html_generator import HTMLGenerator
import pandas as pd

def process_excel_file(file_path: Path):
    """Process a single Excel file and generate note sheet"""
    print(f"\n{'='*80}")
    print(f"Processing: {file_path.name}")
    print(f"{'='*80}\n")
    
    try:
        # Read Excel file
        processor = ExcelProcessor(sanitize_strings=True, validate_schemas=False)
        result = processor.process_file(file_path)
        
        if not result.success:
            print(f"❌ Failed to process file: {', '.join(result.errors)}")
            return None
        
        # Extract sheets
        sheets = result.data
        
        # Identify sheet types
        title_sheet = None
        work_order_sheet = None
        bill_quantity_sheet = None
        extra_items_sheet = None
        
        for sheet_name, df in sheets.items():
            sheet_lower = sheet_name.lower()
            if 'title' in sheet_lower or 'info' in sheet_lower:
                title_sheet = df
            elif 'work order' in sheet_lower or 'wo' in sheet_lower:
                work_order_sheet = df
            elif 'bill' in sheet_lower and 'quantity' in sheet_lower:
                bill_quantity_sheet = df
            elif 'extra' in sheet_lower:
                extra_items_sheet = df
        
        # If sheets not identified by name, use first few sheets
        sheet_list = list(sheets.values())
        if title_sheet is None and len(sheet_list) > 0:
            title_sheet = sheet_list[0]
        if work_order_sheet is None and len(sheet_list) > 1:
            work_order_sheet = sheet_list[1]
        if bill_quantity_sheet is None and len(sheet_list) > 2:
            bill_quantity_sheet = sheet_list[2]
        if extra_items_sheet is None and len(sheet_list) > 3:
            extra_items_sheet = sheet_list[3]
        
        # Convert title sheet to dictionary
        title_data = {}
        if title_sheet is not None and not title_sheet.empty:
            for index, row in title_sheet.iterrows():
                if len(row) >= 2:
                    key = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ''
                    value = row.iloc[1] if pd.notna(row.iloc[1]) else ''
                    if key:
                        title_data[key] = value
        
        # Prepare data structure
        data = {
            'title_data': title_data,
            'work_order_data': work_order_sheet if work_order_sheet is not None else pd.DataFrame(),
            'bill_quantity_data': bill_quantity_sheet if bill_quantity_sheet is not None else pd.DataFrame(),
            'extra_items_data': extra_items_sheet if extra_items_sheet is not None else pd.DataFrame(),
            'source_filename': file_path.name
        }
        
        # Generate HTML
        generator = HTMLGenerator(data)
        template_data = generator._prepare_template_data()
        
        # Display key information
        print(f"Work Order Amount: ₹{template_data.get('work_order_amount', 0):,.0f}")
        print(f"Bill Amount: ₹{template_data.get('bill_grand_total', 0):,.0f}")
        print(f"Extra Items: ₹{template_data.get('extra_items_sum', 0):,.0f}")
        print(f"Delay Days: {template_data.get('delay_days', 0)}")
        print(f"Liquidated Damages: ₹{template_data.get('liquidated_damages_amount', 0):,.0f}")
        
        # Generate note sheet
        html_content = generator._render_template('note_sheet_new.html')
        
        # Save to OUTPUT folder
        output_dir = Path('OUTPUT')
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = file_path.stem
        html_file = output_dir / f'{base_name}_note_sheet_{timestamp}.html'
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\n✅ Note Sheet saved: {html_file}")
        
        return {
            'file': file_path.name,
            'status': 'success',
            'output': html_file,
            'ld_amount': template_data.get('liquidated_damages_amount', 0),
            'delay_days': template_data.get('delay_days', 0)
        }
        
    except Exception as e:
        print(f"❌ Error processing file: {e}")
        import traceback
        traceback.print_exc()
        return {
            'file': file_path.name,
            'status': 'failed',
            'error': str(e)
        }

def main():
    """Process all test input files"""
    print("="*80)
    print("GENERATE NOTE SHEETS FOR ALL TEST INPUT FILES")
    print("="*80)
    
    # Get all Excel files from TEST_INPUT_FILES
    test_dir = Path('TEST_INPUT_FILES')
    
    if not test_dir.exists():
        print(f"❌ Test directory not found: {test_dir}")
        return
    
    excel_files = list(test_dir.glob('*.xlsx')) + list(test_dir.glob('*.xlsm'))
    
    if not excel_files:
        print(f"❌ No Excel files found in {test_dir}")
        return
    
    print(f"\nFound {len(excel_files)} Excel files to process\n")
    
    results = []
    
    for excel_file in sorted(excel_files):
        result = process_excel_file(excel_file)
        if result:
            results.append(result)
    
    # Summary
    print("\n" + "="*80)
    print("PROCESSING SUMMARY")
    print("="*80 + "\n")
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    failed_count = sum(1 for r in results if r['status'] == 'failed')
    
    print(f"Total Files: {len(results)}")
    print(f"✅ Success: {success_count}")
    print(f"❌ Failed: {failed_count}")
    print()
    
    # Detailed results
    print("Detailed Results:")
    print("-"*80)
    
    for result in results:
        if result['status'] == 'success':
            print(f"✅ {result['file']}")
            print(f"   Output: {result['output']}")
            print(f"   Delay: {result['delay_days']} days | LD: ₹{result['ld_amount']:,.0f}")
        else:
            print(f"❌ {result['file']}")
            print(f"   Error: {result.get('error', 'Unknown error')}")
        print()
    
    print("="*80)
    print("ALL FILES PROCESSED")
    print("="*80)

if __name__ == '__main__':
    main()
