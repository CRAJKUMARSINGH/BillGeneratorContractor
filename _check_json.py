import json
from pathlib import Path
data = json.loads(Path('_demo_data.json').read_text(encoding='utf-8'))
f = data[0]
print('File:', f['fileName'])
print('Rows:', len(f['rows']))
print('TitleData keys:', list(f['titleData'].keys())[:8])
for r in f['rows'][:5]:
    print(f"  {r['itemNo']:8} qty={r['quantity']:6} rate={r['rate']:8} amt={r['amount']:8}  {r['description'][:45]}")
