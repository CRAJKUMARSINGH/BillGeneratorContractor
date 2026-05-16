import sys
sys.path.insert(0, 'backend')
sys.path.insert(0, 'engine')
from pathlib import Path
from services.ai_excel_parser import parse_excel_ai

files = list(Path('INPUT HAPHHAZARD').glob('*.xlsx'))
print(f"Testing {len(files)} files\n")
for f in files:
    r = parse_excel_ai(f, 'test-id', f.name)
    wo = r.work_order_sheet
    rows = wo.rows if wo else []
    items_with_qty = [row for row in rows if row.quantity > 0]
    total = sum(row.amount for row in rows)
    print(f"{f.name[:50]:<50} rows={len(rows):>3}  with_qty={len(items_with_qty):>3}  total=Rs.{total:>10,.0f}  conf={r.confidence_overall:.0%}")
    # Show first 3 real items
    for row in items_with_qty[:3]:
        print(f"  {row.item_no:8} {row.description[:35]:35} qty={row.quantity:6.1f} rate={row.rate:8.2f} amt={row.amount:8.0f}")
print("\nAll files parsed successfully.")
