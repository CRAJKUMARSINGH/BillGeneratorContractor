"""
Comprehensive Regression Test for Haphazard Input & Shared Pipeline
Verifies:
1. Ingestion of messy Excel (Mode 1).
2. Merging of duplicate BSR codes.
3. Hierarchical sorting.
4. Downstream calculation (Grand Total, Premium, Payable).
5. Data mapping for templates.
"""
import asyncio
import sys
from pathlib import Path

# Add root to path
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from backend.services.ingestion_service import IngestionService
from backend.services.bill_service import BillService

async def run_haphazard_regression():
    print("\nSTARTING HAPHHAZARD REGRESSION SUITE")
    
    test_file = Path("INPUT HAPHHAZARD/SAMPLE BILL INPUT- NO EXTRA ITEMS.xlsx")
    if not test_file.exists():
        print(f"Error: {test_file} not found. Skipping.")
        return

    # 1. INGESTION
    print(f"--- 1. Ingesting {test_file.name} ---")
    service = IngestionService()
    doc = await service.process_file(test_file, "reg_test_01", test_file.name)
    
    print(f"Ingested {len(doc.billItems)} items.")
    
    # 2. HIERARCHY CHECK
    print("--- 2. Checking Hierarchical Sort ---")
    codes = [item.itemNo for item in doc.billItems if item.itemNo]
    # Check if 4.1 comes before 4.1.7
    if "4.1" in codes and "4.1.7" in codes:
        if codes.index("4.1") < codes.index("4.1.7"):
            print("Sort Pass: 4.1 < 4.1.7")
        else:
            print("Sort Fail: 4.1.7 appears before 4.1")
    else:
        print("Warning: 4.1 or 4.1.7 missing from output")

    # 3. MERGE CHECK
    print("--- 3. Checking Smart Merging ---")
    # In the raw file, 6.1 appears multiple times. In unified model, it should be unique.
    code_counts = {}
    for c in codes:
        code_counts[c] = code_counts.get(c, 0) + 1
    
    duplicates = [c for c, count in code_counts.items() if count > 1]
    if duplicates:
        print(f"Merge Fail: Duplicate codes found: {duplicates}")
    else:
        print("Merge Pass: No duplicate item codes.")

    # 4. CALCULATION PIPELINE
    print("--- 4. Checking Shared Calculation Pipeline ---")
    request_data = {
        "billItems": doc.billItems,
        "titleData": doc.titleData,
        "options": {
            "premiumPercent": 10.5,
            "premiumType": "above",
            "previousBillAmount": 50000.0
        }
    }
    
    template_data = BillService.prepare_template_data(request_data)
    totals = template_data["data"]["totals"]
    summary = template_data["data"]["summary"]
    
    print(f"   Grand Total: {totals['grand_total']}")
    print(f"   Premium: {totals['premium']['amount']} ({totals['premium']['percent']*100}%)")
    print(f"   Net Payable: {totals['net_payable']}")
    
    # Consistency check
    expected_payable = round(totals['grand_total'] * 1.105)
    if abs(totals['payable'] - expected_payable) <= 2: # Small rounding diff
        print("Calc Pass: Premium & Payable are correct.")
    else:
        print(f"Calc Fail: Expected {expected_payable}, got {totals['payable']}")

    print("--- 5. Deviation Mapping ---")
    # Check if a few items have deviation data
    sample_item = template_data["data"]["items"][0]
    print(f"   Sample Item: {sample_item['serial_no']} | {sample_item['description'][:30]}...")
    print(f"   Qty WO: {sample_item['qty_wo']} | Qty Bill: {sample_item['qty_bill']}")
    
    if summary['executed_total'] > 0:
        print(f"Summary Pass: Executed Total={summary['executed_total']}, Deviation={summary['percentage_deviation']:.2f}%")
    else:
        print("Summary Fail: Executed total is zero.")

    # 6. PRUNING CHECK
    print("--- 6. Checking Hierarchical Pruning ---")
    pruned_count = doc.metadata.get("pruned_count", 0)
    final_count = len(doc.billItems)
    print(f"   Items after pruning: {final_count}")
    
    # Check if some zero-qty items are present (should be headers of non-zero items)
    zero_qty_items = [item for item in doc.billItems if item.quantity == 0]
    print(f"   Active Headers (zero-qty): {len(zero_qty_items)}")
    
    # Verify that a header exists for a known non-zero item
    # e.g. if 4.1.7 has qty, 4.1 should exist as a header
    non_zero_codes = [item.itemNo for item in doc.billItems if item.quantity > 0]
    headers_verified = True
    for code in non_zero_codes:
        if "." in code:
            parent = ".".join(code.split(".")[:-1])
            if parent and parent not in [item.itemNo for item in doc.billItems]:
                print(f"Pruning Fail: Parent {parent} missing for active item {code}")
                headers_verified = False
                break
    if headers_verified:
        print("Pruning Pass: All active items have their parent headers preserved.")

    print("\nHAPHHAZARD REGRESSION SUITE COMPLETE\n")

if __name__ == "__main__":
    asyncio.run(run_haphazard_regression())
