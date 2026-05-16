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

print('WO shape after pad:', ws_wo.shape)
print('BQ shape after pad:', ws_bq.shape)
print()
print('WO rows 21-27 (col0=code, col3=qty, col4=rate):')
for i in range(21, min(28, ws_wo.shape[0])):
    print(f'  row{i}: code={ws_wo.iloc[i,0]}  qty_wo={ws_wo.iloc[i,3]}  rate={ws_wo.iloc[i,4]}')
print()
print('BQ rows 21-27 (col0=code, col3=qty):')
for i in range(21, min(28, ws_bq.shape[0])):
    print(f'  row{i}: code={ws_bq.iloc[i,0]}  qty_bq={ws_bq.iloc[i,3]}')

fp, _, dev, _, _ = process_bill(ws_wo, ws_bq, ws_extra, 11.22, 'above', 0)
print()
print('Items produced:', len(fp['items']))
for it in fp['items'][:10]:
    print(f"  sno={it['serial_no']}  qty={it.get('quantity','')}  rate={it.get('rate','')}  amt={it.get('amount','')}")
print()
print('Grand total:', fp['totals'].get('grand_total'))
print('Payable:',     fp['totals'].get('payable'))
