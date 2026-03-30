import sys, os
sys.path.insert(0,'.')
sys.path.insert(0,'engine')
os.environ['ALLOW_INSECURE_SECRET']='1'
import pandas as pd
from pathlib import Path

for name in ['3rdFinalVidExtra.xlsx','0511Wextra.xlsx','FirstFINALvidExtra.xlsx','9th and final Amli Fala with extra items.xlsx','3rdFinalNoExtra.xlsx']:
    f = Path('RESOURCES_ARCHIVE/TEST_INPUT_FILES') / name
    if f.exists():
        xl = pd.ExcelFile(str(f), engine='openpyxl')
        print(f"{name}: sheets={xl.sheet_names}")
        # Show first few rows of each sheet
        for sh in xl.sheet_names:
            df = pd.read_excel(str(f), sheet_name=sh, header=None, nrows=5)
            print(f"  [{sh}] shape={df.shape}")
            print(f"  {df.to_string(index=False, header=False)[:200]}")
        print()
