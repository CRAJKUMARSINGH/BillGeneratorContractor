#!/usr/bin/env python3
"""
Generate Bill Scrutiny Sheet (Note Sheet) with PDF output
"""

from pathlib import Path
from core.processors.excel_processor import ExcelProcessor
from core.generators.document_generator import DocumentGenerator
import webbrowser
import os
import subprocess
import platform
from datetime import datetime

print("\n" + "="*80)
print("BILL SCRUTINY SHEET (NOTE SHEET) GENERATOR")
print("="*80 + "\n")

# Input file
test_file = Path("INPUT_FILES_LEVEL_02/FirstFINALvidExtra.xlsx")
print(f"📁 Input file: {test_file.name}\n")

# Process Excel
print("[1/4] Processing Excel file...")
processor = ExcelProcessor()
data = processor.process_excel(test_file)
print(f"✅ Processed {len(data)} data sections\n")

# Generate Note Sheet
print("[2/4] Generating Bill Scrutiny Sheet HTML...")
doc_gen = DocumentGenerator(data)
documents = doc_gen.generate_all_documents()
notesheet_html = documents.get('BILL SCRUTINY SHEET', '')
print(f"✅ Generated Bill Scrutiny Sheet ({len(notesheet_html):,} characters)\n")

# Save HTML
print("[3/4] Saving HTML...")
output_dir = Path("OUTPUT")
output_dir.mkdir(exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

notesheet_html_path = output_dir / f"bill_scrutiny_sheet_{timestamp}.html"
notesheet_html_path.write_text(notesheet_html, encoding='utf-8')
print(f"✅ Saved to: {notesheet_html_path}\n")

# Generate PDF
print("[4/4] Generating PDF...")
pdf_generated = False
try:
    from weasyprint import HTML
    
    notesheet_pdf_path = output_dir / f"bill_scrutiny_sheet_{timestamp}.pdf"
    HTML(string=notesheet_html).write_pdf(notesheet_pdf_path)
    print(f"✅ PDF saved to: {notesheet_pdf_path}\n")
    
    pdf_generated = True
except ImportError:
    print("⚠️  WeasyPrint not installed. Install with: pip install weasyprint")
    print("   PDF generation skipped.\n")
except Exception as e:
    print(f"❌ PDF generation failed: {e}\n")

# Open files
print("Opening files...")
print("🌐 Opening HTML in browser...")
webbrowser.open(notesheet_html_path.absolute().as_uri())

if pdf_generated:
    print("📄 Opening PDF...")
    try:
        if platform.system() == 'Windows':
            os.startfile(notesheet_pdf_path)
        elif platform.system() == 'Darwin':  # macOS
            subprocess.run(['open', notesheet_pdf_path])
        else:  # Linux
            subprocess.run(['xdg-open', notesheet_pdf_path])
    except Exception as e:
        print(f"⚠️  Could not auto-open PDF: {e}")

print()
print("="*80)
print("✅ BILL SCRUTINY SHEET GENERATED")
print("="*80)
print()

# Summary
print("Summary:")
print(f"  • Input: {test_file.name}")
print(f"  • HTML: {notesheet_html_path}")
if pdf_generated:
    print(f"  • PDF: {notesheet_pdf_path}")
print()

# Document info
title_data = data.get('title_data', {})

print("Bill Scrutiny Sheet Information:")
print(f"  • Contractor: {title_data.get('Name of Contractor or supplier :', 'N/A')}")
print(f"  • Work: {title_data.get('Name of Work ;-', 'N/A')}")
print(f"  • Bill Serial: {title_data.get('Serial No. of this bill :', 'N/A')}")
print()
