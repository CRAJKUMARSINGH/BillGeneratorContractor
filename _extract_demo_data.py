"""Extract parsed data from haphazard files as JSON for the demo HTML."""
import sys, json
sys.path.insert(0, 'backend')
sys.path.insert(0, 'engine')
from pathlib import Path
from services.ai_excel_parser import parse_excel_ai, ai_parse_result_to_dict

files = sorted(Path('INPUT HAPHHAZARD').glob('*.xlsx'))
results = []
for f in files:
    r = parse_excel_ai(f, f.stem, f.name)
    d = ai_parse_result_to_dict(r)
    wo = d.get('workOrderSheet', {})
    results.append({
        'fileName': d['fileName'],
        'confidence': d['confidenceOverall'],
        'titleData': d['titleData'],
        'columnMappings': wo.get('columnMappings', []) if wo else [],
        'rows': wo.get('rows', []) if wo else [],
        'totalAmount': wo.get('totalAmount', 0) if wo else 0,
        'warnings': wo.get('warnings', []) if wo else [],
        'aiSuggestions': d['aiSuggestions'],
    })

Path('_demo_data.json').write_text(
    json.dumps(results, ensure_ascii=True, indent=2), encoding='utf-8'
)
print(f"Written {len(results)} files to _demo_data.json")
