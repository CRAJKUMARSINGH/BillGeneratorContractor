import sys
import asyncio
import pandas as pd
from pathlib import Path
from pprint import pprint

# Setup path
root = Path(__file__).parent.parent
sys.path.append(str(root))
sys.path.append(str(root / "backend"))

from backend.services.ingestion_service import IngestionService
from engine.models import UnifiedBillDocument

async def test_mode1_strict():
    print("\n--- Testing Mode 1: Strict Excel ---")
    file_path = root / "Order-Fixer" / "Input_Test_Files" / "FirstFINALnoExtra.xlsx"
    doc = await IngestionService.process_file(file_path, "test_m1", "FirstFINALnoExtra.xlsx")
    
    print(f"Mode: {doc.mode}")
    print(f"File: {doc.fileName}")
    print(f"Items: {len(doc.billItems)}")
    print(f"Total Amount: {doc.totalAmount:,.2f}")
    assert doc.mode == "mode1"
    assert len(doc.billItems) > 0
    assert doc.totalAmount > 0

async def test_mode2_hybrid():
    print("\n--- Testing Mode 2: Hybrid (WO only) ---")
    # Create a mock Excel with only Work Order
    temp_wo = root / "tests" / "temp_wo_only.xlsx"
    df_wo = pd.DataFrame([
        ["1", "Excavation", "cum", 100, 50, 5000],
        ["2", "Concrete", "cum", 10, 4000, 40000]
    ], columns=["Item No.", "Description of Item", "Unit", "Quantity", "Rate", "Amount"])
    
    # We need to pad it for the AI parser to find it easily or name the sheet "Work Order"
    with pd.ExcelWriter(temp_wo) as writer:
        df_wo.to_excel(writer, sheet_name="Work Order", index=False)
        
    doc = await IngestionService.process_file(temp_wo, "test_m2", "temp_wo_only.xlsx")
    
    print(f"Mode: {doc.mode}")
    print(f"Items: {len(doc.billItems)}")
    if doc.billItems:
        print(f"First Item: {doc.billItems[0].description} (Qty: {doc.billItems[0].quantity}, WO Qty: {doc.billItems[0].wo_quantity})")
    
    assert doc.mode == "mode2"
    assert all(item.quantity == 0 for item in doc.billItems)
    temp_wo.unlink()

async def main():
    try:
        await test_mode1_strict()
        await test_mode2_hybrid()
        print("\n✅ Phase 1 Ingestion Tests Passed!")
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
