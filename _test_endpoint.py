"""Quick test of the /ai-excel/parse endpoint."""
import requests
from pathlib import Path

BASE = "http://localhost:8001"
f = list(Path("INPUT HAPHHAZARD").glob("*.xlsx"))[0]
print(f"Testing with: {f.name}")

with open(f, "rb") as fh:
    r = requests.post(f"{BASE}/ai-excel/parse", files={"file": (f.name, fh)}, timeout=30)

print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    wo = data.get("workOrderSheet", {})
    rows = wo.get("rows", []) if wo else []
    print(f"fileId:     {data['fileId'][:8]}...")
    print(f"confidence: {data['confidenceOverall']:.0%}")
    print(f"sheets:     {[s['sheetName'] for s in data['sheets']]}")
    print(f"WO rows:    {len(rows)}")
    print(f"suggestions:{data['aiSuggestions']}")
    print(f"\nFirst 3 rows with qty:")
    for row in [r for r in rows if r['quantity'] > 0][:3]:
        print(f"  {row['itemNo']:8} qty={row['quantity']:6.1f} rate={row['rate']:8.2f} amt={row['amount']:8.0f}  {row['description'][:40]}")
else:
    print(r.text[:500])
