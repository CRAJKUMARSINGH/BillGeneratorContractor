"""
Generate all 6 PDF templates from 3rdFinalVidExtra.xlsx sample input.
Output: ANTIGRAVITY IMAGE TEXT SAMPLES/PDF_OUTPUTS/
"""
import sys, logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

root = Path(__file__).parent.absolute()
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / "engine"))

from engine.run_engine import load_excel_sheets, build_document, render_html, render_pdfs

INPUT_FILE = root / "BillGeneratorUnified" / "TEST_INPUT_FILES" / "3rdFinalVidExtra.xlsx"
OUT_DIR = root / "ANTIGRAVITY IMAGE TEXT SAMPLES" / "PDF_OUTPUTS"
OUT_DIR.mkdir(exist_ok=True, parents=True)

print(f"INPUT: {INPUT_FILE.name}")
print(f"OUTPUT DIR: {OUT_DIR}")
print("=" * 60)

# Step 1: Load Excel
print("[1/3] Loading Excel sheets...")
sheets = load_excel_sheets(str(INPUT_FILE))
print(f"  Sheets loaded: {list(sheets.keys())}")

# Step 2: Build Document with correct parameters
print("[2/3] Building BillDocument...")
doc = build_document(
    sheets,
    premium_percent=0.0,
    premium_type="above",
    previous_bill_amount=0.0
)
print(f"  Agreement: {doc.agreement_no}")
print(f"  Work: {doc.name_of_work[:50]}...")
print(f"  Extra Items: {len(doc.extra_items)} items")

# Step 3: Render HTML then PDF
print("[3/3] Rendering HTML + PDF...")
html_paths = render_html(doc, OUT_DIR, template_version="v1")
print(f"  HTML files: {len(html_paths)}")

pdf_results = render_pdfs(html_paths, OUT_DIR)
print(f"  PDF results: {len(pdf_results)} files")

# List generated files
print("\n" + "=" * 60)
print("GENERATED FILES:")
for f in sorted(OUT_DIR.iterdir()):
    if f.is_file():
        size_kb = f.stat().st_size / 1024
        emoji = "📄" if f.suffix == ".pdf" else "📋"
        print(f"  {emoji} {f.name:<45} ({size_kb:.1f} KB)")

print("\nDONE! 6 templates generated successfully.")
