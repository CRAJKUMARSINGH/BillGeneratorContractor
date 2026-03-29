import pandas as pd

print("\n" + "="*80)
print("EXCEL FILE SAMPLE: work_order_with_quantities.xlsx")
print("="*80 + "\n")

df = pd.read_excel('OUTPUT/work_order_with_quantities.xlsx')

print(df.to_string(index=False))

print("\n" + "="*80)
print(f"SUMMARY: {len(df)} items | Total Quantity: {df['Quantity'].sum():.0f} units")
print("="*80 + "\n")

print("OCR EXTRACTED TEXT SAMPLE (First 500 characters):")
print("-"*80)
with open('OUTPUT/ocr_extracted_text.txt', 'r', encoding='utf-8') as f:
    text = f.read()
    print(text[:500] + "...")
print("-"*80)
