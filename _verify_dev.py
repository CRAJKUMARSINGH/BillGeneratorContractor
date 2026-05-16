import sys, pandas as pd, numpy as np
from pathlib import Path
sys.path.insert(0, '.')
from engine.calculation.bill_processor import process_bill

path = Path('Order-Fixer/Input_Test_Files/FirstFINALnoExtra.xlsx')
xl = pd.ExcelFile(path, engine='openpyxl')

def _read_padded(name):
    df = pd.read_excel(xl, sheet_name=name, header=None)
    r0c0 = str(df.iloc[0,0]).strip().lower() if df.shape[1]>0 else ''
    already_padded = r0c0 not in ('item','item no.','item no','s.no','s. no','sl.no')
    if already_padded:
        return df
    ncols = df.shape[1]
    blank = pd.DataFrame([[np.nan]*ncols]*21, columns=df.columns)
    return pd.concat([blank, df], ignore_index=True)

ws_wo    = _read_padded('Work Order')
ws_bq    = _read_padded('Bill Quantity')
ws_extra = _read_padded('Extra Items')

_, _, dev, _, _ = process_bill(ws_wo, ws_bq, ws_extra, 11.22, 'above', 0)

print('DEVIATION ITEMS:')
for it in dev['items']:
    if it.get('is_divider'):
        print(f"  ===== {it['description']} =====")
        continue
    sno  = str(it.get('serial_no', ''))
    desc = str(it.get('description', ''))[:40]
    qwo  = str(it.get('qty_wo', ''))
    rate = str(it.get('rate', ''))
    awo  = str(it.get('amt_wo', ''))
    qb   = str(it.get('qty_bill', ''))
    ab   = str(it.get('amt_bill', ''))
    exc  = str(it.get('excess_qty', ''))
    sav  = str(it.get('saving_qty', ''))
    print(f"  sno={sno:8s} qwo={qwo:8s} rate={rate:8s} awo={awo:10s} qb={qb:8s} ab={ab:10s} exc={exc:6s} sav={sav:6s}  {desc}")

print()
s = dev['summary']
print(f"WO total:  {s['work_order_total']}")
print(f"BQ total:  {s['executed_total']}")
print(f"Excess:    {s['overall_excess']}")
print(f"Saving:    {s['overall_saving']}")
print(f"GT_WO:     {s['grand_total_f']}")
print(f"GT_BQ:     {s['grand_total_h']}")
print(f"GT_Excess: {s['grand_total_j']}")
print(f"GT_Saving: {s['grand_total_l']}")
print(f"Net diff:  {s['net_difference']}  is_saving={s['is_saving']}")
print(f"Pct dev:   {s['percentage_deviation']}%")
