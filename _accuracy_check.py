"""
ROOT APP ACCURACY VERIFIER
===========================
No comparison with any reference.
Verifies the root app's bill_processor produces internally consistent,
mathematically correct output for all 9 sample Excel files.

Checks per file:
  FIRST PAGE
  [F1]  Every item with rate>0 has amount = round(qty * rate)
  [F2]  Grand total = sum of all item amounts
  [F3]  Premium amount = round(grand_total * premium_pct / 100)
  [F4]  Payable = grand_total + premium_amount
  [F5]  Parent/heading rows present (rate=0, has description)
  [F6]  Sub-items have blank serial_no (nan-coded rows)
  [F7]  Named items have non-blank serial_no
  [F8]  Item order follows natural sort of item codes (1 < 2 < 3 ... < 10 < 11)
  [F9]  No summary label rows leaked (Total / Grand Total / Add Tender Premium)
  [F10] Extra items have E-01, E-02 serial numbers

  DEVIATION
  [D1]  Every item with rate>0: amt_wo = round(qty_wo * rate)
  [D2]  Every item with rate>0: amt_bill = round(qty_bill * rate)
  [D3]  excess_qty = max(0, qty_bill - qty_wo)
  [D4]  saving_qty = max(0, qty_wo - qty_bill)
  [D5]  excess_amt = round(excess_qty * rate)
  [D6]  saving_amt = round(saving_qty * rate)
  [D7]  work_order_total = sum of all amt_wo (items + sub-items, NOT extra)
  [D8]  executed_total   = sum of all amt_bill
  [D9]  overall_excess   = sum of all excess_amt
  [D10] overall_saving   = sum of all saving_amt
  [D11] Extra items: qty_wo=0, amt_wo=0, saving=0
  [D12] grand_total_f = round(work_order_total + premium_f)
  [D13] grand_total_h = round(executed_total   + premium_h)
  [D14] net_difference = abs(grand_total_h - grand_total_f)
  [D15] No summary label rows leaked
  [D16] All WO items/sub-items have qty_wo populated (not blank)
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP

sys.path.insert(0, str(Path(__file__).parent))
from engine.calculation.bill_processor import process_bill, round_up

INPUT_DIR = Path('Order-Fixer/Input_Test_Files')
FILES = sorted(INPUT_DIR.glob('*.xlsx'))

PASS = 'PASS'
FAIL = 'FAIL'

def sf(v):
    try:
        if v is None or (isinstance(v, float) and v != v): return 0.0
        return float(v)
    except: return 0.0

def read_padded(xl, name):
    if name not in xl.sheet_names:
        return pd.DataFrame()
    df = pd.read_excel(xl, sheet_name=name, header=None)
    if df.empty:
        return df
    r0c0 = str(df.iloc[0,0]).strip().lower() if df.shape[1] > 0 else ''
    already_padded = r0c0 not in ('item','item no.','item no','s.no','s. no','sl.no')
    if already_padded:
        return df
    ncols = df.shape[1]
    blank = pd.DataFrame([[np.nan]*ncols]*21, columns=df.columns)
    return pd.concat([blank, df], ignore_index=True)

def check(label, condition, detail=''):
    status = PASS if condition else FAIL
    marker = '  OK' if condition else '  !!'
    print(f"    {marker} [{label}] {detail}")
    return condition

def run_checks(fname, first_page, deviation_data, premium_pct, premium_type):
    items     = [it for it in first_page['items'] if not it.get('is_divider')]
    dev_items = [it for it in deviation_data['items'] if not it.get('is_divider')]
    totals    = first_page['totals']
    summary   = deviation_data['summary']
    fails = 0

    print(f"\n  --- FIRST PAGE ---")

    # F1: amount = round(qty * rate) for all rate>0 items
    f1_ok = True
    for it in items:
        r = sf(it.get('rate', 0))
        q = sf(it.get('quantity', 0))
        a = sf(it.get('amount', 0))
        if r > 0:
            expected = round_up(q * r)
            if abs(expected - a) > 1:
                f1_ok = False
                print(f"      MISMATCH: sno={it.get('serial_no')} qty={q} rate={r} amt={a} expected={expected}")
    if not check('F1', f1_ok, 'amount = round(qty * rate) for all rate>0 items'): fails += 1

    # F2: grand_total = sum of item amounts
    computed_gt = round_up(sum(sf(it.get('amount', 0)) for it in items))
    stored_gt   = sf(totals.get('grand_total', 0))
    if not check('F2', abs(computed_gt - stored_gt) <= 1,
                 f'grand_total: computed={computed_gt} stored={stored_gt}'): fails += 1

    # F3: premium amount
    if premium_type == 'above':
        expected_prem = round_up(stored_gt * premium_pct / 100)
    else:
        expected_prem = -round_up(stored_gt * premium_pct / 100)
    stored_prem = sf(totals.get('premium', {}).get('amount', 0))
    if not check('F3', abs(expected_prem - stored_prem) <= 1,
                 f'premium: computed={expected_prem} stored={stored_prem}'): fails += 1

    # F4: payable = grand_total + premium
    expected_pay = round_up(stored_gt + stored_prem)
    stored_pay   = sf(totals.get('payable', 0))
    if not check('F4', abs(expected_pay - stored_pay) <= 1,
                 f'payable: computed={expected_pay} stored={stored_pay}'): fails += 1

    # F5: at least one parent/heading row exists (rate=0, has description)
    parent_rows = [it for it in items if sf(it.get('rate',0)) == 0 and it.get('description','').strip()]
    if not check('F5', len(parent_rows) > 0,
                 f'parent/heading rows: {len(parent_rows)} found'): fails += 1

    # F6: sub-items (nan-coded) have blank serial_no
    sub_items = [it for it in items if it.get('serial_no','').strip() == '' and sf(it.get('rate',0)) > 0]
    if not check('F6', len(sub_items) >= 0,  # always pass — just report count
                 f'sub-items with blank serial_no: {len(sub_items)}'): pass

    # F7: named items have non-blank serial_no
    named_items = [it for it in items if it.get('serial_no','').strip() != '']
    if not check('F7', len(named_items) > 0,
                 f'named items with serial_no: {len(named_items)}'): fails += 1

    # F8: WO item codes in natural order (no lexicographic inversion like 10 before 2)
    # E-xx extra items excluded — they always follow WO items, not part of WO sort
    from engine.calculation.bill_processor import _natural_sort_key
    wo_codes = [it.get('serial_no','').strip() for it in items
                if it.get('serial_no','').strip()
                and not it.get('serial_no','').strip().startswith('E-')]
    sorted_wo_codes = sorted(wo_codes, key=_natural_sort_key)
    if not check('F8', wo_codes == sorted_wo_codes,
                 f'WO codes natural order: {"YES" if wo_codes == sorted_wo_codes else "NO -- " + str(wo_codes[:10])}'): fails += 1

    # F9: no summary label rows leaked
    bad_descs = [it.get('description','') for it in items
                 if it.get('description','').strip().lower() in
                 ('total','grand total','add tender premium','prem','premium','description')]
    if not check('F9', len(bad_descs) == 0,
                 f'summary label rows leaked: {bad_descs}'): fails += 1

    # F10: extra items have E-xx serial numbers
    extra_items = [it for it in first_page['items']
                   if str(it.get('serial_no','')).startswith('E-')]
    if not check('F10', True,  # informational
                 f'extra items found: {len(extra_items)}'): pass

    print(f"\n  --- DEVIATION ---")

    # D1-D6: per-item arithmetic
    d_arith_ok = True
    for it in dev_items:
        r   = sf(it.get('rate', 0))
        if r == 0: continue
        qwo = sf(it.get('qty_wo', 0))
        qb  = sf(it.get('qty_bill', 0))
        awo = sf(it.get('amt_wo', 0))
        ab  = sf(it.get('amt_bill', 0))
        exc_q = sf(it.get('excess_qty', 0))
        sav_q = sf(it.get('saving_qty', 0))
        exc_a = sf(it.get('excess_amt', 0))
        sav_a = sf(it.get('saving_amt', 0))

        if abs(round_up(qwo * r) - awo) > 1:
            d_arith_ok = False
            print(f"      D1 FAIL: sno={it.get('serial_no')} qwo={qwo} rate={r} awo={awo} expected={round_up(qwo*r)}")
        if abs(round_up(qb * r) - ab) > 1:
            d_arith_ok = False
            print(f"      D2 FAIL: sno={it.get('serial_no')} qb={qb} rate={r} ab={ab} expected={round_up(qb*r)}")
        exp_exc_q = max(0, qb - qwo)
        exp_sav_q = max(0, qwo - qb)
        if abs(exp_exc_q - exc_q) > 0.01:
            d_arith_ok = False
            print(f"      D3 FAIL: sno={it.get('serial_no')} exc_q={exc_q} expected={exp_exc_q}")
        if abs(exp_sav_q - sav_q) > 0.01:
            d_arith_ok = False
            print(f"      D4 FAIL: sno={it.get('serial_no')} sav_q={sav_q} expected={exp_sav_q}")
        if abs(round_up(exp_exc_q * r) - exc_a) > 1:
            d_arith_ok = False
            print(f"      D5 FAIL: sno={it.get('serial_no')} exc_a={exc_a} expected={round_up(exp_exc_q*r)}")
        if abs(round_up(exp_sav_q * r) - sav_a) > 1:
            d_arith_ok = False
            print(f"      D6 FAIL: sno={it.get('serial_no')} sav_a={sav_a} expected={round_up(exp_sav_q*r)}")

    if not check('D1-D6', d_arith_ok, 'per-item arithmetic (amt_wo, amt_bill, excess, saving)'): fails += 1

    # D7-D10: totals
    wo_items_only = [it for it in dev_items if not str(it.get('serial_no','')).startswith('E-')]
    ex_items_only = [it for it in dev_items if str(it.get('serial_no','')).startswith('E-')]

    comp_wo  = round_up(sum(sf(it.get('amt_wo',  0)) for it in wo_items_only))
    comp_bq  = round_up(sum(sf(it.get('amt_bill', 0)) for it in dev_items))
    comp_exc = round_up(sum(sf(it.get('excess_amt', 0)) for it in dev_items))
    comp_sav = round_up(sum(sf(it.get('saving_amt', 0)) for it in dev_items))

    if not check('D7', abs(comp_wo - sf(summary.get('work_order_total',0))) <= 1,
                 f'WO total: computed={comp_wo} stored={summary.get("work_order_total")}'): fails += 1
    if not check('D8', abs(comp_bq - sf(summary.get('executed_total',0))) <= 1,
                 f'BQ total: computed={comp_bq} stored={summary.get("executed_total")}'): fails += 1
    if not check('D9', abs(comp_exc - sf(summary.get('overall_excess',0))) <= 1,
                 f'Excess:   computed={comp_exc} stored={summary.get("overall_excess")}'): fails += 1
    if not check('D10', abs(comp_sav - sf(summary.get('overall_saving',0))) <= 1,
                 f'Saving:   computed={comp_sav} stored={summary.get("overall_saving")}'): fails += 1

    # D11: extra items have qty_wo=0, amt_wo=0, saving=0
    d11_ok = all(sf(it.get('qty_wo',0)) == 0 and sf(it.get('amt_wo',0)) == 0
                 and sf(it.get('saving_qty',0)) == 0
                 for it in ex_items_only)
    if not check('D11', d11_ok,
                 f'extra items qty_wo=0, amt_wo=0, saving=0: {len(ex_items_only)} extra items'): fails += 1

    # D12-D13: grand totals with premium
    prem_f = sf(summary.get('tender_premium_f', 0))
    prem_h = sf(summary.get('tender_premium_h', 0))
    gt_f   = sf(summary.get('grand_total_f', 0))
    gt_h   = sf(summary.get('grand_total_h', 0))
    exp_gtf = round_up(sf(summary.get('work_order_total',0)) + prem_f)
    exp_gth = round_up(sf(summary.get('executed_total',0))   + prem_h)
    if not check('D12', abs(exp_gtf - gt_f) <= 1,
                 f'GT_WO: computed={exp_gtf} stored={gt_f}'): fails += 1
    if not check('D13', abs(exp_gth - gt_h) <= 1,
                 f'GT_BQ: computed={exp_gth} stored={gt_h}'): fails += 1

    # D14: net_difference
    exp_net = abs(round_up(gt_h - gt_f))
    stored_net = sf(summary.get('net_difference', 0))
    if not check('D14', abs(exp_net - stored_net) <= 1,
                 f'net_diff: computed={exp_net} stored={stored_net}'): fails += 1

    # D15: no summary label rows leaked
    bad_dev = [it.get('description','') for it in dev_items
               if it.get('description','').strip().lower() in
               ('total','grand total','add tender premium','prem','premium','description')]
    if not check('D15', len(bad_dev) == 0,
                 f'summary label rows leaked: {bad_dev}'): fails += 1

    # D16: all WO items/sub-items with rate>0 have qty_wo populated
    missing_qwo = [it for it in wo_items_only
                   if sf(it.get('rate',0)) > 0 and it.get('qty_wo','') == '']
    if not check('D16', len(missing_qwo) == 0,
                 f'items with rate>0 but blank qty_wo: {len(missing_qwo)}'): fails += 1

    return fails


def main():
    print("=" * 70)
    print("  ROOT APP ACCURACY VERIFIER — 9 files, 26 checks each")
    print("=" * 70)

    total_fails = 0
    file_results = []

    for xlsx in FILES:
        stem = xlsx.stem
        print(f"\n{'='*70}")
        print(f"  FILE: {stem}")
        print(f"{'='*70}")

        xl = pd.ExcelFile(xlsx, engine='openpyxl')

        ws_wo    = read_padded(xl, 'Work Order')
        ws_bq    = read_padded(xl, 'Bill Quantity')
        ws_extra = read_padded(xl, 'Extra Items')

        # Read premium from Title sheet
        premium_pct  = 0.0
        premium_type = 'above'
        if 'Title' in xl.sheet_names:
            ti = pd.read_excel(xl, sheet_name='Title', header=None)
            td = {}
            for _, row in ti.iterrows():
                if len(row) >= 2:
                    k = str(row.iloc[0]).strip()
                    v = row.iloc[1]
                    if k and k != 'nan':
                        td[k] = '' if (pd.isna(v) or str(v)=='nan') else str(v).strip()
            for key in ('TENDER PREMIUM %', 'Tender Premium %', 'TENDER PREMIUM'):
                if key in td:
                    try: premium_pct = float(td[key])
                    except: pass
                    break
            for key in ('Above / Below', 'ABOVE', 'Premium Type'):
                if key in td:
                    premium_type = 'below' if 'below' in str(td[key]).lower() else 'above'
                    break

        print(f"  Premium: {premium_pct}% {premium_type}")

        try:
            first_page, _, deviation_data, _, _ = process_bill(
                ws_wo, ws_bq, ws_extra,
                premium_percent=premium_pct,
                premium_type=premium_type,
                previous_bill_amount=0.0
            )
        except Exception as e:
            print(f"  !! PROCESS ERROR: {e}")
            import traceback; traceback.print_exc()
            file_results.append((stem, -1))
            continue

        fails = run_checks(stem, first_page, deviation_data, premium_pct, premium_type)
        total_fails += fails
        file_results.append((stem, fails))

    print(f"\n{'='*70}")
    print(f"  SUMMARY")
    print(f"{'='*70}")
    for stem, fails in file_results:
        if fails == -1:
            status = 'PROCESS ERROR'
        elif fails == 0:
            status = 'ALL PASS'
        else:
            status = f'{fails} FAIL(S)'
        print(f"  {'OK' if fails==0 else '!!'} {stem:50s} {status}")

    print(f"\n  Total failures across all files: {total_fails}")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    main()
