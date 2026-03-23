#!/usr/bin/env python3
"""
Display all sheets from input Excel file in detail
"""
import pandas as pd
from pathlib import Path

def show_excel_details(excel_file):
    """Display all sheets with full details"""
    
    print("=" * 80)
    print("INPUT FILE GENERATED FROM IMAGES - COMPLETE VIEW")
    print("=" * 80)
    
    # Read Excel
    xl = pd.ExcelFile(excel_file)
    
    print(f"\n📊 File: {Path(excel_file).name}")
    print(f"📋 Total Sheets: {len(xl.sheet_names)}")
    print(f"📄 Sheets: {', '.join(xl.sheet_names)}")
    print(f"📁 Location: {excel_file}")
    
    # Process each sheet
    for idx, sheet_name in enumerate(xl.sheet_names):
        print("\n" + "=" * 80)
        print(f"SHEET {idx+1}: {sheet_name}")
        print("=" * 80)
        
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        
        # Show dimensions
        rows, cols = df.shape
        print(f"\n📐 Dimensions: {rows} rows × {cols} columns")
        
        if df.empty:
            print("\n⚠️ This sheet is empty")
            continue
        
        # Show column names
        print(f"\n📋 Columns: {', '.join(df.columns.tolist())}")
        
        # Show data
        print("\n📊 Data:")
        print("-" * 80)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 60)
        print(df.to_string(index=True))
        print("-" * 80)
        
        # Show statistics
        if sheet_name in ['Work Order', 'Bill Quantity']:
            print("\n📈 Statistics:")
            if 'Quantity' in df.columns:
                total_qty = df['Quantity'].sum()
                print(f"  Total Quantity: {total_qty}")
            if 'Amount' in df.columns:
                total_amount = df['Amount'].sum()
                print(f"  Total Amount: ₹{total_amount:,.2f}")
            if 'BSR' in df.columns:
                bsr_count = df['BSR'].notna().sum()
                print(f"  BSR Codes Found: {bsr_count}")
    
    print("\n" + "=" * 80)
    print("✅ ALL SHEETS DISPLAYED SUCCESSFULLY")
    print("=" * 80)

if __name__ == "__main__":
    excel_file = "OUTPUT/INPUT_FINAL_FROM_IMAGES.xlsx"
    
    if not Path(excel_file).exists():
        print(f"❌ File not found: {excel_file}")
        print("\n📁 Available Excel files in OUTPUT:")
        for f in Path("OUTPUT").glob("*.xlsx"):
            print(f"  - {f.name}")
    else:
        show_excel_details(excel_file)
