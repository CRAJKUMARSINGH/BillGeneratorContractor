import sys, os
sys.path.insert(0,'.')
sys.path.insert(0,'engine')
os.environ['ALLOW_INSECURE_SECRET']='1'
from ingestion.excel_parser import parse_excel_to_raw
from pathlib import Path

for name in ['3rdFinalVidExtra.xlsx','0511Wextra.xlsx','FirstFINALvidExtra.xlsx','9th and final Amli Fala with extra items.xlsx']:
    f = Path('RESOURCES_ARCHIVE/TEST_INPUT_FILES') / name
    if f.exists():
        data = parse_excel_to_raw(str(f))
        items = data.get('items',[])
        extra = data.get('extra_items',[])
        meta = data.get('metadata',{})
        print(f"FILE: {name}")
        print(f"  items={len(items)}, extra={len(extra)}")
        print(f"  meta={meta}")
        if extra:
            print(f"  first extra: {extra[0]}")
        print()
