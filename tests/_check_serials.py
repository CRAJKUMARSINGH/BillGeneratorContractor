import sys
sys.path.insert(0, '.')
sys.path.insert(0, 'engine')
from engine.run_engine import load_excel_sheets, build_document
from pathlib import Path

for fname in ['0511Wextra', 'FirstFINALnoExtra', 'FirstFINALvidExtra']:
    p = Path(f'SAMPLE_PACK/01_inputs/{fname}.xlsx')
    sheets = load_excel_sheets(p)
    doc = build_document(sheets, 0.0, 'above', 0.0)

    items = [it for it in doc.items if not it.get('is_divider')]
    serials = [it['serial_no'] for it in items]
    zero_rows = [it for it in items if it.get('quantity') == 0 and it.get('rate') == 0]
    wo_items = [it for it in items if not it['serial_no'].startswith('E-')]
    ex_items = [it for it in items if it['serial_no'].startswith('E-')]
    wo_strict = [it['serial_no'] for it in wo_items] == [str(i+1) for i in range(len(wo_items))]
    ex_strict = [it['serial_no'] for it in ex_items] == [f'E-{i+1:02d}' for i in range(len(ex_items))]

    dev_items = [it for it in doc.deviation_items if not it.get('is_divider')]
    dev_wo = [it for it in dev_items if not it['serial_no'].startswith('E-')]
    dev_ex = [it for it in dev_items if it['serial_no'].startswith('E-')]
    dev_wo_strict = [it['serial_no'] for it in dev_wo] == [str(i+1) for i in range(len(dev_wo))]
    dev_ex_strict = [it['serial_no'] for it in dev_ex] == [f'E-{i+1:02d}' for i in range(len(dev_ex))]

    print(f'{fname}:')
    print(f'  first_page: {len(wo_items)} WO items (strict={wo_strict}) + {len(ex_items)} extra (strict={ex_strict})')
    print(f'  serials: {serials}')
    print(f'  Zero-qty/rate rows: {len(zero_rows)}')
    print(f'  deviation: {len(dev_wo)} WO (strict={dev_wo_strict}) + {len(dev_ex)} extra (strict={dev_ex_strict})')
    print()
