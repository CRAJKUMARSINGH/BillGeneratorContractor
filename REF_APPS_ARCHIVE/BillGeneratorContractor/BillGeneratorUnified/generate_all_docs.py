#!/usr/bin/env python3
"""
Generate ALL documents (First Page, Deviation, Certificates) with PDF output
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
print("COMPLETE BILL PACKAGE GENERATOR - ALL DOCUMENTS")
print("="*80 + "\n")

# Input file
test_file = Path("TEST_INPUT_FILES/FirstFINALvidExtra.xlsx")
print(f"📁 Input file: {test_file.name}\n")

# Process Excel
print("[1/5] Processing Excel file...")
processor = ExcelProcessor()
data = processor.process_excel(test_file)
print(f"✅ Processed {len(data)} data sections\n")

# Generate all documents
print("[2/5] Generating ALL documents HTML...")
doc_gen = DocumentGenerator(data)
documents = doc_gen.generate_all_documents()

first_page_html = documents.get('First Page Summary', '')
deviation_html = documents.get('Deviation Statement', '')
notesheet_html = documents.get('BILL SCRUTINY SHEET', '')
cert_ii_html = documents.get('Certificate II', '')
cert_iii_html = documents.get('Certificate III', '')
extra_items_html = documents.get('Extra Items Statement', '')

print(f"✅ First Page: {len(first_page_html):,} characters")
if deviation_html:
    print(f"✅ Deviation Statement: {len(deviation_html):,} characters")
print(f"✅ Bill Scrutiny Sheet: {len(notesheet_html):,} characters")
print(f"✅ Certificate II: {len(cert_ii_html):,} characters")
print(f"✅ Certificate III: {len(cert_iii_html):,} characters")
if extra_items_html:
    print(f"✅ Extra Items Statement: {len(extra_items_html):,} characters")
print()

# Save HTML files
print("[3/5] Saving HTML files...")
output_dir = Path("OUTPUT")
output_dir.mkdir(exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

files = {}
file_num = 1

files['first_page'] = output_dir / f"{file_num}_first_page_{timestamp}.html"
files['first_page'].write_text(first_page_html, encoding='utf-8')
file_num += 1

if deviation_html:
    files['deviation'] = output_dir / f"{file_num}_deviation_statement_{timestamp}.html"
    files['deviation'].write_text(deviation_html, encoding='utf-8')
    file_num += 1

files['notesheet'] = output_dir / f"{file_num}_bill_scrutiny_sheet_{timestamp}.html"
files['notesheet'].write_text(notesheet_html, encoding='utf-8')
file_num += 1

files['cert_ii'] = output_dir / f"{file_num}_certificate_ii_{timestamp}.html"
files['cert_ii'].write_text(cert_ii_html, encoding='utf-8')
file_num += 1

files['cert_iii'] = output_dir / f"{file_num}_certificate_iii_{timestamp}.html"
files['cert_iii'].write_text(cert_iii_html, encoding='utf-8')
file_num += 1

if extra_items_html:
    files['extra_items'] = output_dir / f"{file_num}_extra_items_{timestamp}.html"
    files['extra_items'].write_text(extra_items_html, encoding='utf-8')
    file_num += 1

print(f"✅ Saved {len(files)} HTML files to OUTPUT/\n")

# Generate PDFs
print("[4/5] Generating PDFs...")
pdf_files = {}
pdf_generated = False

try:
    from weasyprint import HTML
    
    file_num = 1
    
    pdf_files['first_page'] = output_dir / f"{file_num}_first_page_{timestamp}.pdf"
    HTML(string=first_page_html).write_pdf(pdf_files['first_page'])
    print(f"✅ First Page PDF")
    file_num += 1
    
    if deviation_html:
        pdf_files['deviation'] = output_dir / f"{file_num}_deviation_statement_{timestamp}.pdf"
        HTML(string=deviation_html).write_pdf(pdf_files['deviation'])
        print(f"✅ Deviation Statement PDF")
        file_num += 1
    
    pdf_files['notesheet'] = output_dir / f"{file_num}_bill_scrutiny_sheet_{timestamp}.pdf"
    HTML(string=notesheet_html).write_pdf(pdf_files['notesheet'])
    print(f"✅ Bill Scrutiny Sheet PDF")
    file_num += 1
    
    pdf_files['cert_ii'] = output_dir / f"{file_num}_certificate_ii_{timestamp}.pdf"
    HTML(string=cert_ii_html).write_pdf(pdf_files['cert_ii'])
    print(f"✅ Certificate II PDF")
    file_num += 1
    
    pdf_files['cert_iii'] = output_dir / f"{file_num}_certificate_iii_{timestamp}.pdf"
    HTML(string=cert_iii_html).write_pdf(pdf_files['cert_iii'])
    print(f"✅ Certificate III PDF")
    file_num += 1
    
    if extra_items_html:
        pdf_files['extra_items'] = output_dir / f"{file_num}_extra_items_{timestamp}.pdf"
        HTML(string=extra_items_html).write_pdf(pdf_files['extra_items'])
        print(f"✅ Extra Items Statement PDF")
        file_num += 1
    
    print()
    pdf_generated = True
except ImportError:
    print("⚠️  WeasyPrint not installed. Install with: pip install weasyprint")
    print("   PDF generation skipped.\n")
except Exception as e:
    print(f"❌ PDF generation failed: {e}\n")

# Open PDFs
print("[5/5] Opening PDFs...")
if pdf_generated:
    for name, pdf_path in pdf_files.items():
        try:
            if platform.system() == 'Windows':
                os.startfile(pdf_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', pdf_path])
            else:  # Linux
                subprocess.run(['xdg-open', pdf_path])
        except Exception as e:
            print(f"⚠️  Could not auto-open {name}: {e}")
    print(f"✅ Opened {len(pdf_files)} PDFs\n")
else:
    print("⚠️  No PDFs to open\n")

print("="*80)
print("✅ COMPLETE BILL PACKAGE GENERATED")
print("="*80)
print()

# Summary
print("Summary:")
print(f"  • Input: {test_file.name}")
print(f"  • Output Directory: OUTPUT/")
print(f"  • Timestamp: {timestamp}")
print()

print("Generated Files:")
file_num = 1
print(f"  {file_num}. First Page (HTML + PDF)")
file_num += 1

if deviation_html:
    print(f"  {file_num}. Deviation Statement (HTML + PDF)")
    file_num += 1

print(f"  {file_num}. Bill Scrutiny Sheet (HTML + PDF)")
file_num += 1

print(f"  {file_num}. Certificate II (HTML + PDF) - Date/Page/MB fields blank for manual entry")
file_num += 1

print(f"  {file_num}. Certificate III (HTML + PDF)")
file_num += 1

if extra_items_html:
    print(f"  {file_num}. Extra Items Statement (HTML + PDF)")
    file_num += 1

print()

# Document info
title_data = data.get('title_data', {})
print("Document Information:")
print(f"  • Contractor: {title_data.get('Name of Contractor or supplier :', 'N/A')}")
print(f"  • Work: {title_data.get('Name of Work ;-', 'N/A')}")
print(f"  • Bill Serial: {title_data.get('Serial No. of this bill :', title_data.get('Serial No. of this bill', 'N/A'))}")
print(f"  • Agreement No: {title_data.get('Agreement No.', 'N/A')}")
print()

print("Note: Certificate II has blank fields for date, page number, and MB number")
print("      to be filled manually with ink pen by the officer.")
print()
