import os
import sys
from pathlib import Path
import json

# Ensure root and backend are in path
ROOT_DIR = Path(__file__).parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from backend.routes.bills import _parse_excel

def test_e2e_parsing():
    # 1. Pick a complex PWD sample from archive
    sample_path = ROOT_DIR / "RESOURCES_ARCHIVE" / "INPUT_FILES_LEVEL_02" / "3rdFinalVidExtra.xlsx"
    
    if not sample_path.exists():
        print(f"Sample not found: {sample_path}")
        return

    print(f"End-to-End Test: Parsing {sample_path.name}")
    
    try:
        # 2. Run the actual backend parsing logic
        result = _parse_excel(sample_path, "test-file-id", sample_path.name)
        
        print("\n--- RESULTS ---")
        print(f"Success! Model: {type(result).__name__}")
        print(f"Metadata (Title Data):")
        for k, v in result.title_data.items():
            print(f"  {k}: {v}")
            
        print(f"\nItems Count: {len(result.bill_items)}")
        if result.bill_items:
            first = result.bill_items[0]
            print(f"First Item: [{first.itemNo}] {first.description[:50]}...")
            print(f"  Qty Since: {first.quantitySince}, Qty Upto: {first.quantityUpto}, Rate: {first.rate}")
            
        print(f"\nTotal Amount: {result.total_amount:,.2f}")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\nFAILURE: {e}")

if __name__ == "__main__":
    test_e2e_parsing()
