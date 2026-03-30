"""Debug extra items sheet parsing."""
import sys, os
sys.path.insert(0,'.')
sys.path.insert(0,'engine')
os.environ['ALLOW_INSECURE_SECRET']='1'
import logging
logging.basicConfig(level=logging.WARNING)
import pandas as pd
from pathlib import Path
from engine.run_engine import load_excel_sheets

f = Path('RESOURCES_ARCHIVE/TEST_INPUT_FILES/3rdFinalVidExtra.xlsx')
sheets = load_excel_sheets(f)
ws_extra = sheets.get('Extra Items')
print(f"Extra Items sheet shape: {ws_extra.shape if ws_extra is not None else 'MISSING'}")
if ws_extra is not None:
    print("First 15 rows:")
    print(ws_extra.head(15).to_string())
    print()
    # Check all rows for content
    for idx, row in ws_extra.iterrows():
        cells = [str(c).strip() for c in row if str(c).strip() not in ('','nan','NaN')]
        if cells:
            print(f"Row {idx}: {cells}")
