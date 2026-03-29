#!/usr/bin/env python3
"""
Generate PDF showing all sheets from the input Excel file
For visual verification and satisfaction
"""
import pandas as pd
from pathlib import Path
import sys

def create_html_from_excel(excel_file, output_html):
    """Convert Excel file to beautiful HTML with all sheets"""
    
    # Read Excel file
    xl = pd.ExcelFile(excel_file)
    
    # Start HTML
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Input File - All Sheets</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 20px;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        .header p {
            margin: 10px 0 0 0;
            font-size: 1.2em;
            opacity: 0.95;
        }
        .sheet-container {
            background: white;
            padding: 25px;
            margin: 25px 0;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-left: 5px solid #00b894;
        }
        .sheet-title {
            background: linear-gradient(135deg, #00b894 0%, #00cec9 100%);
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            margin: -25px -25px 20px -25px;
            font-size: 1.5em;
            font-weight: bold;
            box-shadow: 0 2px 8px rgba(0, 184, 148, 0.3);
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 0.95em;
        }
        th {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: bold;
            border: 1px solid #ddd;
        }
        td {
            padding: 10px 12px;
            border: 1px solid #ddd;
            background: white;
        }
        tr:nth-child(even) td {
            background: #f8f9fa;
        }
        tr:hover td {
            background: #e8f4f8;
        }
        .info-box {
            background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
            border-left: 4px solid #00cec9;
            padding: 15px;
            margin: 15px 0;
            border-radius: 8px;
        }
        .summary-box {
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
            border-left: 4px solid #00b894;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 10px;
            border-top: 3px solid #00b894;
        }
        .metric {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 10px 20px;
            margin: 5px;
            border-radius: 8px;
            font-weight: bold;
        }
    </style>
</head>
<body>
"""
    
    # Add header
    html_content += f"""
    <div class="header">
        <h1>📊 Input File - All Sheets</h1>
        <p>Generated from Work Order Images using OCR</p>
        <p style="font-size: 0.9em; margin-top: 10px;">File: {Path(excel_file).name}</p>
    </div>
    """
    
    # Add summary
    total_sheets = len(xl.sheet_names)
    html_content += f"""
    <div class="summary-box">
        <h2 style="margin-top: 0;">📋 File Summary</h2>
        <div class="metric">Total Sheets: {total_sheets}</div>
        <div class="metric">Source: OCR Processing</div>
        <div class="metric">Format: Excel (.xlsx)</div>
    </div>
    """
    
    # Process each sheet
    for sheet_name in xl.sheet_names:
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        
        html_content += f"""
    <div class="sheet-container">
        <div class="sheet-title">📄 Sheet: {sheet_name}</div>
        """
        
        # Add sheet info
        rows, cols = df.shape
        html_content += f"""
        <div class="info-box">
            <strong>Dimensions:</strong> {rows} rows × {cols} columns
        </div>
        """
        
        # Add table
        if not df.empty:
            html_content += df.to_html(index=True, classes='data-table', border=0, na_rep='—')
        else:
            html_content += "<p><em>This sheet is empty</em></p>"
        
        html_content += """
    </div>
        """
    
    # Add footer
    html_content += """
    <div class="footer">
        <h3 style="color: #2d3436; margin-top: 0;">✅ Input File Generated Successfully</h3>
        <p style="color: #636e72;">This file was automatically generated from work order images using OCR technology</p>
        <p style="color: #b2bec3; font-size: 0.9em; margin-top: 15px;">
            🤖 Generated by BillGenerator Contractor | 
            ⚡ Powered by Smart Cascading OCR | 
            📅 March 2026
        </p>
    </div>
</body>
</html>
    """
    
    # Write HTML
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ HTML created: {output_html}")
    return output_html

def convert_html_to_pdf(html_file, pdf_file):
    """Convert HTML to PDF using WeasyPrint"""
    try:
        from weasyprint import HTML
        HTML(html_file).write_pdf(pdf_file)
        print(f"✅ PDF created: {pdf_file}")
        return True
    except Exception as e:
        print(f"❌ PDF conversion failed: {e}")
        print(f"💡 HTML file is available at: {html_file}")
        return False

if __name__ == "__main__":
    # Input Excel file
    excel_file = "OUTPUT/INPUT_work_01_27022026.xlsx"
    
    # Check if file exists
    if not Path(excel_file).exists():
        print(f"❌ File not found: {excel_file}")
        print("\n📁 Available files in OUTPUT:")
        for f in Path("OUTPUT").glob("*.xlsx"):
            print(f"  - {f.name}")
        sys.exit(1)
    
    # Output files
    output_html = "OUTPUT/INPUT_ALL_SHEETS.html"
    output_pdf = "OUTPUT/INPUT_ALL_SHEETS.pdf"
    
    print(f"📊 Processing: {excel_file}")
    print(f"🎯 Target: {output_pdf}")
    print("=" * 60)
    
    # Create HTML
    html_file = create_html_from_excel(excel_file, output_html)
    
    # Convert to PDF
    print("\n🔄 Converting HTML to PDF...")
    success = convert_html_to_pdf(html_file, output_pdf)
    
    if success:
        print("\n" + "=" * 60)
        print("✅ SUCCESS! PDF generated with all sheets")
        print(f"📄 PDF Location: {output_pdf}")
        print(f"🌐 HTML Location: {output_html}")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("⚠️ PDF conversion failed, but HTML is available")
        print(f"🌐 HTML Location: {output_html}")
        print("💡 You can open the HTML file in a browser and print to PDF")
        print("=" * 60)
