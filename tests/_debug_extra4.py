"""Debug extra items data rows."""
import sys, os
sys.path.insert(0,'.')
sys.path.insert(0,'engine')
os.environ['ALLOW_INSECURE_SECRET']='1'
import logging
logging.basicConfig(level=logging.WARNING)
from pathlib import Path
from engine.run_engine import load_excel_sheets

f = Path('RESOURCES_ARCHIVE/TEST_INPUT_FILES/3rdFinalVidExtra.xlsx')
sheets = load_excel_sheets(f)
ws_extra = sheets.get('Extra Items')

# Simulate _parse_extra_items step by step
header_idx = -1
for idx, row in ws_extra.iterrows():
    cells = [str(c).strip().lower() for c in row]
    if any("particular" in c or "desc" in c for c in cells) and any("qty" in c or "quantity" in c for c in cells):
        header_idx = idx
        print(f"Header at idx={idx}")
        break

header_row = [str(c).strip().lower() for c in ws_extra.iloc[header_idx]]
print(f"Header row: {header_row}")

col_map = {}
for i, h in enumerate(header_row):
    h = h.strip()
    if any(k in h for k in ["s.no", "s. no", "sno", "item no", "sl"]):
        col_map.setdefault("serial_no", i)
    elif "bsr" in h or "ref" in h:
        col_map.setdefault("bsr", i)
    elif any(k in h for k in ["particular", "desc"]):
        col_map.setdefault("description", i)
    elif any(k in h for k in ["qty", "quantity"]):
        col_map.setdefault("quantity", i)
    elif "unit" in h:
        col_map.setdefault("unit", i)
    elif "rate" in h:
        col_map.setdefault("rate", i)
    elif "amount" in h or "rs" in h:
        col_map.setdefault("amount", i)
    elif "remark" in h or "note" in h:
        col_map.setdefault("remark", i)

print(f"col_map: {col_map}")

print(f"\nData rows after header (idx {header_idx}):")
for idx in range(header_idx + 1, len(ws_extra)):
    row = ws_extra.iloc[idx]
    desc_col = col_map.get("description", 2)
    sno_col = col_map.get("serial_no", 0)
    desc = str(row.iloc[desc_col]).strip()
    sno = str(row.iloc[sno_col]).strip()
    print(f"  iloc[{idx}]: sno={repr(sno)} desc={repr(desc[:50])}")
