"""Debug extra items column mapping."""
import sys, os
sys.path.insert(0,'.')
sys.path.insert(0,'engine')
os.environ['ALLOW_INSECURE_SECRET']='1'
import logging
logging.basicConfig(level=logging.WARNING)
from pathlib import Path
from engine.run_engine import load_excel_sheets
from engine.calculation.bill_processor import _parse_extra_items

f = Path('RESOURCES_ARCHIVE/TEST_INPUT_FILES/3rdFinalVidExtra.xlsx')
sheets = load_excel_sheets(f)
ws_extra = sheets.get('Extra Items')
print(f"Shape: {ws_extra.shape}")
print(f"Columns: {list(ws_extra.columns)}")
print()

# Find header row
for idx, row in ws_extra.iterrows():
    cells = [str(c).strip().lower() for c in row]
    print(f"Row {idx}: {[str(c).strip() for c in row]}")
    if any("particular" in c or "desc" in c for c in cells) and any("qty" in c or "quantity" in c for c in cells):
        print(f"  ^^^ HEADER ROW FOUND at {idx}")
        break

print()
result = _parse_extra_items(ws_extra)
print(f"Parsed {len(result)} extra items")
for r in result:
    print(f"  {r}")
