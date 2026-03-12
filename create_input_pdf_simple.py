#!/usr/bin/env python3
"""
Create PDF from Excel input file using reportlab (Windows-compatible)
"""
import pandas as pd
from pathlib import Path
import sys

def create_pdf_from_excel(excel_file, output_pdf):
    """Create PDF from Excel using reportlab"""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
    except ImportError:
        print("❌ reportlab not installed")
        print("💡 Installing reportlab...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"])
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
    
    # Read Excel
    xl = pd.ExcelFile(excel_file)
    
    # Create PDF
    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=landscape(A4),
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )
    
    # Container for elements
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    sheet_title_style = ParagraphStyle(
        'SheetTitle',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=colors.HexColor('#00b894'),
        spaceAfter=15,
        spaceBefore=15,
        fontName='Helvetica-Bold'
    )
    
    info_style = ParagraphStyle(
        'Info',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#636e72'),
        alignment=TA_CENTER
    )
    
    # Add title
    elements.append(Paragraph("📊 Input File - All Sheets", title_style))
    elements.append(Paragraph(f"Generated from: {Path(excel_file).name}", info_style))
    elements.append(Paragraph("Source: Work Order Images (OCR Processing)", info_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Add summary
    summary_data = [
        ['📋 Summary', ''],
        ['Total Sheets', str(len(xl.sheet_names))],
        ['Source', 'OCR Processing'],
        ['Format', 'Excel (.xlsx)'],
        ['Date', 'March 2026']
    ]
    
    summary_table = Table(summary_data, colWidths=[2*inch, 4*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 0.5*inch))
    
    # Process each sheet
    for idx, sheet_name in enumerate(xl.sheet_names):
        if idx > 0:
            elements.append(PageBreak())
        
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        
        # Sheet title
        elements.append(Paragraph(f"📄 Sheet {idx+1}: {sheet_name}", sheet_title_style))
        
        # Sheet info
        rows, cols = df.shape
        info_text = f"Dimensions: {rows} rows × {cols} columns"
        elements.append(Paragraph(info_text, info_style))
        elements.append(Spacer(1, 0.2*inch))
        
        if df.empty:
            elements.append(Paragraph("<i>This sheet is empty</i>", info_style))
            continue
        
        # Prepare table data
        # Replace NaN with empty string
        df = df.fillna('—')
        
        # Convert to string and truncate long text
        df = df.astype(str)
        for col in df.columns:
            df[col] = df[col].apply(lambda x: x[:100] + '...' if len(str(x)) > 100 else x)
        
        # Create table data
        table_data = [df.columns.tolist()] + df.values.tolist()
        
        # Calculate column widths
        page_width = landscape(A4)[0] - 60  # margins
        col_width = page_width / len(df.columns)
        col_widths = [col_width] * len(df.columns)
        
        # Create table
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        
        # Style table
        table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            
            # Body
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('LEFTPADDING', (0, 1), (-1, -1), 6),
            ('RIGHTPADDING', (0, 1), (-1, -1), 6),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            
            # Alternating rows
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ]))
        
        elements.append(table)
    
    # Add footer
    elements.append(Spacer(1, 0.5*inch))
    footer_text = """
    <para align="center">
        <b>✅ Input File Generated Successfully</b><br/>
        <font size="9" color="#636e72">
        This file was automatically generated from work order images using OCR technology<br/>
        🤖 BillGenerator Contractor | ⚡ Smart Cascading OCR | 📅 March 2026
        </font>
    </para>
    """
    elements.append(Paragraph(footer_text, styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    print(f"\n✅ PDF created successfully: {output_pdf}")
    return output_pdf

if __name__ == "__main__":
    excel_file = "OUTPUT/INPUT_FINAL_FROM_IMAGES.xlsx"
    output_pdf = "OUTPUT/INPUT_FINAL_ALL_SHEETS.pdf"
    
    print("=" * 60)
    print("📊 Creating PDF from Input Excel File")
    print("=" * 60)
    
    if not Path(excel_file).exists():
        print(f"❌ File not found: {excel_file}")
        sys.exit(1)
    
    try:
        create_pdf_from_excel(excel_file, output_pdf)
        print("\n" + "=" * 60)
        print("✅ SUCCESS!")
        print(f"📄 PDF: {output_pdf}")
        print(f"🌐 HTML: OUTPUT/INPUT_ALL_SHEETS.html")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
