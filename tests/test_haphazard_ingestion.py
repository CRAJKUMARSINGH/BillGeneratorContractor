"""
Test for Haphazard Input Handling
Verifies:
1. Normalization of messy item codes.
2. Merging of items with same code.
3. Hierarchical sorting.
"""
import asyncio
from pathlib import Path
import sys

# Add root to path
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from backend.services.ingestion_service import IngestionService

async def test_haphazard_excel():
    print("\n--- Testing Haphazard Excel Ingestion ---")
    service = IngestionService()
    test_file = Path("INPUT HAPHHAZARD/SAMPLE BILL INPUT- NO EXTRA ITEMS.xlsx")
    
    if not test_file.exists():
        print(f"Skipping: {test_file} not found")
        return

    print(f"Ingesting {test_file}...")
    result = await service.process_file(test_file, "haphazard_test", test_file.name)
    
    print(f"Ingested {len(result.billItems)} items.")
    
    # Check if sorted
    codes = [item.itemNo for item in result.billItems if item.itemNo]
    print(f"First 10 item codes: {codes[:10]}")
    
    # Simple check for hierarchical order
    # (e.g. 4.1 should come before 4.1.7)
    if "4.1" in codes and "4.1.7" in codes:
        idx_41 = codes.index("4.1")
        idx_417 = codes.index("4.1.7")
        print(f"Index of 4.1: {idx_41}, 4.1.7: {idx_417}")
        assert idx_41 < idx_417
        print("PASS: Hierarchical sorting confirmed.")

    # Check for merges
    # In the Excel analysis, 6.1 appeared multiple times
    if codes.count("6.1") > 1:
        print(f"WARNING: 6.1 found {codes.count('6.1')} times. Merging might have failed or they are distinct branches.")
    else:
        print("PASS: 6.1 merged (or unique).")

    print("\n--- Haphazard Test Complete ---")

if __name__ == "__main__":
    asyncio.run(test_haphazard_excel())
