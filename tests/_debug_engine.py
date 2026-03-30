"""Debug the run_engine pipeline on all 9 test files."""
import sys, os
sys.path.insert(0,'.')
sys.path.insert(0,'engine')
os.environ['ALLOW_INSECURE_SECRET']='1'
import logging
logging.basicConfig(level=logging.WARNING)

from pathlib import Path
from engine.run_engine import load_excel_sheets, build_document

TEST_DIR = Path('RESOURCES_ARCHIVE/TEST_INPUT_FILES')
files = sorted(TEST_DIR.glob('*.xlsx'))

for f in files:
    if f.name.startswith('~$'):
        continue
    try:
        sheets = load_excel_sheets(f)
        doc = build_document(sheets, premium_percent=0.0, premium_type='above', previous_bill_amount=0.0)
        n_extra = len(doc.extra_items)
        n_items = len(doc.items)
        print(f"OK  {f.name}: items={n_items} extra={n_extra} total={doc.totals.get('grand_total',0):.0f} payable={doc.totals.get('payable',0):.0f}")
        if n_extra > 0:
            print(f"    extra_item_amount={doc.extra_item_amount}")
            print(f"    first extra: {doc.extra_items[0]}")
    except Exception as e:
        print(f"ERR {f.name}: {e}")
