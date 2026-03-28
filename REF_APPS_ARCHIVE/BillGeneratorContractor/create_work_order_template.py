#!/usr/bin/env python3
"""
Create Work Order Excel Template
Use this if OCR is not available - manually fill in the data
"""
import pandas as pd
from pathlib import Path
from datetime import datetime

def create_work_order_template(output_file: str = "OUTPUT/work_order_template.xlsx"):
    """Create an Excel template for manual work order data entry"""
    
    print(f"\n{'='*80}")
    print(f"Creating Work Order Excel Template")
    print(f"{'='*80}\n")
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create Excel writer
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        
        # Sheet 1: Title
        print("Creating Title sheet...")
        title_data = {
            'Field': [
                'Work Name',
                'Agreement Number', 
                'Contractor Name',
                'Bill Type',
                'Bill Number',
                'Date',
                'Work Order Number',
                'Work Order Date',
                'Estimated Cost',
                'Agreement Amount',
                'Department',
                'Division',
                'Sub Division',
                'Section',
                'Engineer Name',
                'Engineer Designation',
                'Contractor Address',
                'Contractor GST'
            ],
            'Value': [
                'Enter work name here',
                'Enter agreement number',
                'Enter contractor name',
                'First/Running/Final',
                'Enter bill number',
                datetime.now().strftime('%d/%m/%Y'),
                'Enter work order number',
                'Enter work order date',
                'Enter estimated cost',
                'Enter agreement amount',
                'PWD',
                'Enter division',
                'Enter sub division',
                'Enter section',
                'Enter engineer name',
                'Enter designation',
                'Enter contractor address',
                'Enter GST number'
            ]
        }
        title_df = pd.DataFrame(title_data)
        title_df.to_excel(writer, sheet_name='Title', index=False)
        
        # Sheet 2: Work Order
        print("Creating Work Order sheet...")
        work_order_data = {
            'Item Number': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'],
            'Description': [
                'Enter item description',
                'Enter item description',
                'Enter item description',
                'Enter item description',
                'Enter item description',
                'Enter item description',
                'Enter item description',
                'Enter item description',
                'Enter item description',
                'Enter item description'
            ],
            'Unit': ['sqm', 'cum', 'kg', 'nos', 'rmt', 'mt', 'ltr', 'each', 'set', 'pair'],
            'Quantity': ['', '', '', '', '', '', '', '', '', ''],
            'Rate': ['', '', '', '', '', '', '', '', '', ''],
            'Amount': ['', '', '', '', '', '', '', '', '', ''],
            'Remarks': ['', '', '', '', '', '', '', '', '', '']
        }
        work_order_df = pd.DataFrame(work_order_data)
        work_order_df.to_excel(writer, sheet_name='Work Order', index=False)
        
        # Sheet 3: Bill Quantity
        print("Creating Bill Quantity sheet...")
        bill_quantity_data = {
            'Item Number': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'],
            'Description': [
                'Copy from Work Order',
                'Copy from Work Order',
                'Copy from Work Order',
                'Copy from Work Order',
                'Copy from Work Order',
                'Copy from Work Order',
                'Copy from Work Order',
                'Copy from Work Order',
                'Copy from Work Order',
                'Copy from Work Order'
            ],
            'Unit': ['sqm', 'cum', 'kg', 'nos', 'rmt', 'mt', 'ltr', 'each', 'set', 'pair'],
            'Quantity': ['', '', '', '', '', '', '', '', '', ''],
            'Rate': ['', '', '', '', '', '', '', '', '', ''],
            'Amount': ['', '', '', '', '', '', '', '', '', ''],
            'Remarks': ['', '', '', '', '', '', '', '', '', '']
        }
        bill_quantity_df = pd.DataFrame(bill_quantity_data)
        bill_quantity_df.to_excel(writer, sheet_name='Bill Quantity', index=False)
        
        # Sheet 4: Extra Items
        print("Creating Extra Items sheet...")
        extra_items_data = {
            'Item Number': ['E1', 'E2', 'E3'],
            'Description': [
                'Enter extra item description',
                'Enter extra item description',
                'Enter extra item description'
            ],
            'Unit': ['', '', ''],
            'Quantity': ['', '', ''],
            'Rate': ['', '', ''],
            'Amount': ['', '', ''],
            'Deviation %': ['', '', ''],
            'Remarks': ['', '', '']
        }
        extra_items_df = pd.DataFrame(extra_items_data)
        extra_items_df.to_excel(writer, sheet_name='Extra Items', index=False)
    
    print(f"\n✅ Template created: {output_path.absolute()}\n")
    
    # Create instruction file
    instructions_file = output_path.parent / "TEMPLATE_INSTRUCTIONS.txt"
    with open(instructions_file, 'w', encoding='utf-8') as f:
        f.write("WORK ORDER EXCEL TEMPLATE - INSTRUCTIONS\n")
        f.write("=" * 80 + "\n\n")
        f.write("This template has been created for manual data entry.\n\n")
        
        f.write("STEP 1: Fill in Title Sheet\n")
        f.write("-" * 80 + "\n")
        f.write("- Enter all project and contractor details\n")
        f.write("- Select Bill Type: First/Running/Final\n")
        f.write("- Enter dates in DD/MM/YYYY format\n\n")
        
        f.write("STEP 2: Fill in Work Order Sheet\n")
        f.write("-" * 80 + "\n")
        f.write("- Look at your work order images in:\n")
        f.write("  INPUT/work_order_samples/work_01_27022026/\n")
        f.write("- Enter each item number (1, 2, 3, etc.)\n")
        f.write("- Copy the description exactly as shown in work order\n")
        f.write("- Select appropriate unit (sqm, cum, kg, nos, rmt, etc.)\n")
        f.write("- Enter quantity, rate, and amount\n")
        f.write("- Add more rows if needed (copy and paste)\n\n")
        
        f.write("STEP 3: Fill in Bill Quantity Sheet\n")
        f.write("-" * 80 + "\n")
        f.write("- Copy all items from Work Order sheet\n")
        f.write("- Update quantities based on actual work done\n")
        f.write("- Keep rates same as Work Order\n")
        f.write("- Calculate amounts (Quantity × Rate)\n\n")
        
        f.write("STEP 4: Fill in Extra Items Sheet (if any)\n")
        f.write("-" * 80 + "\n")
        f.write("- Enter any extra items not in original work order\n")
        f.write("- Use item numbers like E1, E2, E3, etc.\n")
        f.write("- Enter deviation percentage if applicable\n\n")
        
        f.write("STEP 5: Process the Excel File\n")
        f.write("-" * 80 + "\n")
        f.write("Once you've filled in all data, run:\n\n")
        f.write("  python process_first_bill.py OUTPUT/work_order_template.xlsx\n\n")
        f.write("This will generate:\n")
        f.write("  - Certificate II\n")
        f.write("  - Certificate III\n")
        f.write("  - Bill Scrutiny Sheet\n")
        f.write("  - First Page Summary\n\n")
        
        f.write("TIPS:\n")
        f.write("-" * 80 + "\n")
        f.write("- Keep item numbers sequential (1, 2, 3, ...)\n")
        f.write("- Use consistent units throughout\n")
        f.write("- Double-check all calculations\n")
        f.write("- Save frequently while entering data\n")
        f.write("- Keep a backup copy before processing\n\n")
        
        f.write("COMMON UNITS:\n")
        f.write("-" * 80 + "\n")
        f.write("sqm  - Square meter (area)\n")
        f.write("cum  - Cubic meter (volume)\n")
        f.write("kg   - Kilogram (weight)\n")
        f.write("nos  - Numbers (count)\n")
        f.write("rmt  - Running meter (length)\n")
        f.write("mt   - Metric ton\n")
        f.write("ltr  - Liter (volume)\n")
        f.write("each - Each item\n")
        f.write("set  - Set of items\n")
        f.write("pair - Pair of items\n\n")
        
        f.write("For questions or issues, refer to:\n")
        f.write("  - WORK_ORDER_OCR_GUIDE.md\n")
        f.write("  - SESSION_SUMMARY.md\n")
        f.write("  - USER_MANUAL.md\n")
    
    print(f"✅ Instructions created: {instructions_file.absolute()}\n")
    
    print(f"{'='*80}")
    print("✅ Template Creation Complete!")
    print(f"{'='*80}\n")
    print("Next steps:")
    print("1. Open the Excel file in Microsoft Excel or LibreOffice")
    print("2. Look at your work order images in:")
    print("   INPUT/work_order_samples/work_01_27022026/")
    print("3. Fill in the data from the images")
    print("4. Save the file")
    print("5. Run: python process_first_bill.py OUTPUT/work_order_template.xlsx")
    print()
    
    return True


if __name__ == '__main__':
    import sys
    
    output_file = "OUTPUT/work_order_template.xlsx"
    if len(sys.argv) > 1:
        output_file = sys.argv[1]
    
    create_work_order_template(output_file)
