#!/usr/bin/env python3
"""
Test all 24 synthetic input files individually through the engine.
Then run them through the batch manager.
"""
import sys, os
sys.path.insert(0, '.')
sys.path.insert(0, 'engine')
os.environ.setdefault('ALLOW_INSECURE_SECRET', '1')
import logging
logging.basicConfig(level=logging.WARNING)

from pathlib import Path

SYNTH_DIR = Path('tests/SYNTHETIC_INPUTS')
OUT_BASE = Path('engine_output/synthetic_test')
OUT_BASE.mkdir(parents=True, exist_ok=True)

def test_individual(xlsx_path: Path) -> dict:
    from engine.run_engine import load_excel_sheets, build_document, render_html, render_pdfs
    result = {'file': xlsx_path.name, 'ok': False, 'html': 0, 'pdf': 0, 'extra': 0, 'error': ''}
    try:
        sheets = load_excel_sheets(xlsx_path)
        doc = build_document(sheets, premium_percent=0.0, premium_type='above', previous_bill_amount=0.0)
        result['extra'] = len(doc.extra_items)
        out_dir = OUT_BASE / xlsx_path.stem
        out_dir.mkdir(exist_ok=True)
        html_paths = render_html(doc, out_dir, template_version='v2')
        result['html'] = len(html_paths)
        pdf_paths = render_pdfs(html_paths, out_dir)
        result['pdf'] = len(pdf_paths)
        result['ok'] = result['html'] > 0 and result['pdf'] > 0
    except Exception as e:
        result['error'] = str(e)[:100]
    return result

def main():
    files = sorted(SYNTH_DIR.glob('*.xlsx'))
    print(f"\nTesting {len(files)} synthetic files individually...")
    print(f"{'File':<35} {'HTML':>4} {'PDF':>4} {'Extra':>5} {'Status'}")
    print('-' * 65)

    pass_count = fail_count = 0
    for f in files:
        r = test_individual(f)
        status = 'PASS' if r['ok'] else f"FAIL: {r['error']}"
        extra_flag = '[E]' if r['extra'] > 0 else '   '
        print(f"  {extra_flag} {r['file']:<32} {r['html']:>4} {r['pdf']:>4} {r['extra']:>5}  {status}")
        if r['ok']:
            pass_count += 1
        else:
            fail_count += 1

    print(f"\nIndividual: {pass_count} PASS / {fail_count} FAIL / {len(files)} TOTAL")

    # Now test batch processing
    print(f"\n{'='*65}")
    print("Running BATCH test via batch_manager.py...")
    print(f"{'='*65}")

    # Copy synthetic files to PENDING_INPUTS
    import shutil
    pending_dir = Path('BATCH_SYSTEM/PENDING_INPUTS')
    pending_dir.mkdir(parents=True, exist_ok=True)

    # Convert xlsx to JSON payloads for batch manager
    from engine.run_engine import load_excel_sheets, build_document
    import json

    batch_files_created = 0
    for f in files:
        try:
            sheets = load_excel_sheets(f)
            doc = build_document(sheets, premium_percent=0.0, premium_type='above', previous_bill_amount=0.0)

            # Build JSON payload matching batch_manager expectations
            bill_items = []
            for item in doc.items:
                bill_items.append({
                    'itemNo': str(item.get('serial_no', '')),
                    'description': item.get('description', ''),
                    'unit': item.get('unit', ''),
                    'quantitySince': float(item.get('quantity_since_last') or 0),
                    'quantityUpto': float(item.get('quantity_upto_date') or 0),
                    'quantity': float(item.get('quantity_upto_date') or 0),
                    'rate': float(item.get('rate') or 0),
                    'amount': float(item.get('amount') or 0),
                })

            extra_items = []
            for ei in doc.extra_items:
                extra_items.append({
                    'itemNo': str(ei.get('serial_no', '')),
                    'bsr': str(ei.get('bsr', '')),
                    'description': ei.get('description', ''),
                    'quantity': float(ei.get('quantity') or 0),
                    'unit': ei.get('unit', ''),
                    'rate': float(ei.get('rate') or 0),
                    'amount': float(ei.get('amount') or 0),
                    'remark': ei.get('remark', ''),
                })

            payload = {
                'fileId': f.stem,
                'fileName': f.name,
                'titleData': {
                    'Agreement No.': doc.agreement_no,
                    'Name of Work': doc.name_of_work,
                    'Name of Contractor': doc.name_of_firm,
                    'Work Order Amount Rs.': str(doc.work_order_amount),
                    'Date of written order to commence work': doc.date_commencement,
                    'St. Date of Completion': doc.date_completion,
                    'Date of actual completion of work': doc.actual_completion,
                },
                'billItems': bill_items,
                'extraItems': extra_items,
                'totalAmount': float(doc.totals.get('payable', 0)),
                'hasExtraItems': len(extra_items) > 0,
                'sheets': ['Work Order', 'Bill Quantity', 'Extra Items'],
            }

            json_path = pending_dir / f"{f.stem}.json"
            json_path.write_text(json.dumps(payload, indent=2), encoding='utf-8')
            batch_files_created += 1
        except Exception as e:
            print(f"  WARN: Could not create batch payload for {f.name}: {e}")

    print(f"Created {batch_files_created} JSON payloads in {pending_dir}")

    # Run batch manager
    import importlib.util
    spec = importlib.util.spec_from_file_location("batch_manager", "batch_manager.py")
    bm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bm)
    bm.main()

    return 0 if fail_count == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
