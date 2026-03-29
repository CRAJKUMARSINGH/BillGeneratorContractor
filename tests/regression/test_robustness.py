import os
from pathlib import Path
import logging
from ingestion.excel_parser import parse_excel_to_raw

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_robustness():
    print("\n--- Robustness Testing Suite ---")
    
    # 1. Standard Case: 3rdFinalVidExtra.xlsx (Multi-sheet, with sub-items)
    print("\nCase 1: 3rdFinalVidExtra.xlsx (The 'Blocker' file)")
    root_dir = Path(__file__).parent.parent.parent
    target_file = root_dir / "RESOURCES_ARCHIVE/INPUT_FILES_LEVEL_02/3rdFinalVidExtra.xlsx"
    if target_file.exists():
        data = parse_excel_to_raw(str(target_file))
        if "error" in data:
            print(f"FAILURE: {data['error']}")
        else:
            print(f"SUCCESS: Parsed {len(data['items'])} main items.")
            print(f"SUCCESS: Parsed {len(data['extra_items'])} extra items.")
            print(f"METADATA: {data['metadata']}")
            
            # Verify specific data fidelity
            if len(data['items']) > 0:
                first_item = data['items'][0]
                print(f"Sample Item 1: {first_item['description'][:50]}... (Rate: {first_item['rate']})")
                if first_item['rate'] > 0:
                    print("FIDELITY: OK")
                else:
                    print("FIDELITY: FAIL (Rate is 0)")
    else:
        print("SKIP: Case 1 (File missing)")

    # 2. Edge Case: Empty Bill (Simulated)
    print("\nCase 2: Emptyworkbook simulation")
    # (Testing the empty dict handle)
    import pandas as pd
    tmp_path = "tmp_empty.xlsx"
    pd.DataFrame().to_excel(tmp_path)
    data = parse_excel_to_raw(tmp_path)
    os.remove(tmp_path)
    if "error" in data:
        print("SUCCESS: Handled empty workbook correctly.")
    else:
        print("FAIL: Should have returned error for empty workbook.")

    print("\n--- Robustness Testing Complete ---")

if __name__ == "__main__":
    test_robustness()
