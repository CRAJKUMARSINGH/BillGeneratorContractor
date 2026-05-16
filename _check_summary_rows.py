"""
Check whether 'Total', 'Add Tender Premium', 'Grand Total' rows in the Excel
are data rows that should appear in the bill, or just Excel formula summary rows
that duplicate what the template already renders in the footer.
"""
import pandas as pd
import numpy as np
from pathlib import Path

path = Path('Order-Fixer/Input_Test_Files/FirstFINALnoExtra.xlsx')
xl = pd.ExcelFile(path, engine='openpyxl')

print("=== WORK ORDER sheet — ALL rows (raw) ===")
wo = pd.read_excel(xl, sheet_name='Work Order', header=None)
for i in range(wo.shape[0]):
    c0 = str(wo.iloc[i,0])[:12]
    c1 = str(wo.iloc[i,1])[:50]
    c3 = str(wo.iloc[i,3])[:10]
    c4 = str(wo.iloc[i,4])[:10]
    print(f"  row{i:2d}: code={c0:12s} desc={c1:50s} qty={c3:10s} rate={c4}")

print()
print("=== BILL QUANTITY sheet — ALL rows (raw) ===")
bq = pd.read_excel(xl, sheet_name='Bill Quantity', header=None)
for i in range(bq.shape[0]):
    c0 = str(bq.iloc[i,0])[:12]
    c1 = str(bq.iloc[i,1])[:50]
    c3 = str(bq.iloc[i,3])[:10]
    print(f"  row{i:2d}: code={c0:12s} desc={c1:50s} qty={c3}")
