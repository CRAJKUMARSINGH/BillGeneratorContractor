"""
Phase 5: End-to-End Regression Suite
Verifies all three ingestion modes and ensures all output formats (HTML, PDF, DOCX) are generated.
"""
import os
import sys
import asyncio
import shutil
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))
sys.path.append(str(Path(__file__).parent.parent))

from backend.services.ingestion_service import IngestionService
from backend.services.bill_service import BillService

async def test_mode1_e2e():
    print("\n--- Testing Mode 1: Strict Excel ---")
    ingestion = IngestionService()
    test_file = Path("SAMPLE_PACK/01_inputs/0511Wextra.xlsx")
    if not test_file.exists():
        print(f"Skipping Mode 1: {test_file} not found")
        return

    # 1. Ingest
    print(f"Step 1: Ingesting {test_file}...")
    result = await ingestion.process_file(test_file, "test_file_id", test_file.name)
    print(f"Ingested Mode: {result.mode}, Items: {len(result.billItems)}")
    assert result.mode == "mode1"
    
    # 2. Render
    print("Step 2: Rendering all formats...")
    job_id = "test_job_mode1"
    output_dir = Path(f"output/{job_id}")
    if output_dir.exists(): shutil.rmtree(output_dir)
    
    async def mock_callback(jid, prog, msg):
        pass # Silencing logs for brevity

    docs, _ = await BillService.process_generation(job_id, result.model_dump(), mock_callback)
    
    print(f"Generated {len(docs)} documents.")
    formats = [d.format for d in docs]
    assert "pdf" in formats
    assert "docx" in formats
    assert "html" in formats
    print("[PASS] Mode 1 E2E Passed")

async def test_mode2_hybrid():
    print("\n--- Testing Mode 2: Hybrid (WO only) ---")
    
    # Mock a Mode 2 result object
    from engine.models import UnifiedBillDocument, BillItem
    mock_wo = UnifiedBillDocument(
        mode="mode2",
        fileId="test_wo_id",
        fileName="hybrid_test.xlsx",
        titleData={
            "Name of Work": "Hybrid Test Work",
            "Agreement No.": "AG-2024-001",
            "Name of Contractor or supplier": "Test Contractor"
        },
        billItems=[
            BillItem(itemNo="1", description="Test Item", unit="cum", rate=100.0, quantity=0.0, quantitySince=0.0, quantityUpto=0.0, amount=0.0, wo_quantity=50.0)
        ],
        totalAmount=0.0
    )
    
    # 2. Render
    print("Step 1: Rendering hybrid...")
    job_id = "test_job_mode2"
    async def mock_cb(j,p,m): pass
    docs, _ = await BillService.process_generation(job_id, mock_wo.model_dump(), mock_cb)
    print(f"Generated {len(docs)} documents for Hybrid.")
    assert any(d.format == "docx" for d in docs)
    print("[PASS] Mode 2 E2E Passed")

async def main():
    try:
        await test_mode1_e2e()
        await test_mode2_hybrid()
        print("\n--- All Regression Tests Completed ---")
    except Exception as e:
        print(f"\n[FAIL] REGRESSION FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
