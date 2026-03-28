import os
from pathlib import Path

gold_dir = Path("BillGeneratorUnified/OUTPUT")
test_dir = Path("BillGeneratorUnified/TEST_INPUT_FILES")

print("--- EXCEL TEST FILES ---")
for f in test_dir.glob("*.xlsx"):
    print(f.name)

print("\n--- GOLD OUTPUTS ---")
for f in gold_dir.rglob("*.html"):
    print(f.relative_to(gold_dir))
