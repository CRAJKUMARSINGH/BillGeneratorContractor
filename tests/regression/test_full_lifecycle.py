import os
import sys
import uuid
import shutil
from pathlib import Path
import json

# Ensure root is in path
CURRENT_DIR = Path(__file__).parent
ROOT_DIR = CURRENT_DIR.parent.parent # BillGeneratorContractor root
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Mock environment for security checks
os.environ["ALLOW_INSECURE_SECRET"] = "1"

from backend.routes.bills import _parse_excel, _generate_documents
from backend.models import GenerateRequest, GenerateOptions
from backend.database import create_db_and_tables
import unittest.mock as mock

def test_full_lifecycle():
    # 1. Setup
    create_db_and_tables()
    # Mock Redis to avoid connection errors in dev test
    with mock.patch("backend.routes.bills.redis.from_url") as mock_redis_url, \
         mock.patch("backend.routes.bills.aioredis.from_url") as mock_aioredis_url:
        
        mock_redis = mock_redis_url.return_value
        mock_redis.get.return_value = None
        
        sample_file = ROOT_DIR / "RESOURCES_ARCHIVE" / "INPUT_FILES_LEVEL_02" / "3rdFinalVidExtra.xlsx"
    job_id = f"test-job-{uuid.uuid4().hex[:8]}"
    out_dir = ROOT_DIR / "backend" / "outputs" / job_id
    
    print(f"--- Full Lifecycle Test: {job_id} ---")

    # 2. Step 1: Ingestion (Excel -> API Model)
    print("Step 1: Parsing Excel...")
    parsed_data = _parse_excel(sample_file, "file-123", sample_file.name)
    print(f"Parsed {len(parsed_data.billItems)} items.")

    # 3. Step 2: Simulate User Edits (API Model -> GenerateRequest)
    print("Step 2: Simulating UI edits...")
    # Change rate of the first item to 9999
    if parsed_data.billItems:
        parsed_data.billItems[0].rate = 9999.0
        parsed_data.billItems[0].amount = parsed_data.billItems[0].quantityUpto * 9999.0
        print(f"Modified Item 1 rate to 9999.0")

    req = GenerateRequest(
        fileId=parsed_data.fileId,
        titleData=parsed_data.titleData,
        billItems=parsed_data.billItems,
        extraItems=parsed_data.extraItems,
        options=GenerateOptions(
            premiumPercent=10.5,
            premiumType="above",
            previousBillAmount=5000.0,
            generatePdf=True # FULL LIFECYCLE DEMO: Enable PDF
        )
    )

    # 4. Step 3: Generation (GenerateRequest -> Unified Model -> HTML)
    print("Step 3: Generating Documents...")
    try:
        _generate_documents(job_id, req)
        print("Generation call returned.")
        
        # 5. Verification
        if out_dir.exists():
            html_files = list(out_dir.glob("*.html"))
            print(f"Generated {len(html_files)} HTML files in {out_dir.name}")
            for f in html_files:
                print(f"  - {f.name} ({f.stat().st_size} bytes)")
            
            if len(html_files) == 6:
                pdf_files = list(out_dir.glob("*.pdf"))
                print(f"Generated {len(pdf_files)} PDF files in {out_dir.name}")
                for f in pdf_files:
                    print(f"  - {f.name} ({f.stat().st_size} bytes)")
                
                if len(pdf_files) == 6:
                    print("\nSUCCESS: Full Lifecycle Verified with 6 Standardized PDFs.")
                else:
                    print("\nFAILURE: PDF generation incomplete.")
            else:
                print(f"\nFAILURE: Expected 6 files, got {len(html_files)}.")
        else:
            print(f"\nFAILURE: Output directory {out_dir} not created.")

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\nERROR during generation: {e}")
    
    # Cleanup (Optional)
    # shutil.rmtree(out_dir)

if __name__ == "__main__":
    test_full_lifecycle()
