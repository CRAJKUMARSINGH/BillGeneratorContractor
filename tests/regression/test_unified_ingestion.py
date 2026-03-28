import logging
import json
from pathlib import Path
from ingestion.excel_parser import parse_excel_to_raw
from ingestion.normalizer import normalize_to_unified_model

# Configure logging to see parser details
logging.basicConfig(level=logging.INFO)

def test_ingestion():
    # Sample file from archive
    sample_file = r"E:\Rajkumar\BillGeneratorContractor\RESOURCES_ARCHIVE\INPUT_FILES_LEVEL_02\3rdFinalVidExtra.xlsx"
    
    if not Path(sample_file).exists():
        print(f"Sample file not found: {sample_file}")
        return

    print(f"Testing Unified Ingestion on: {sample_file}")
    
    # 1. Parse Excel
    raw_data = parse_excel_to_raw(sample_file)
    print(f"Parser Confidence: {raw_data.get('confidence')}")
    print(f"Metadata Keys: {list(raw_data.get('metadata', {}).keys())}")
    print(f"Raw Rows Count: {len(raw_data.get('raw_rows', []))}")
    
    # 2. Normalize to Unified Model
    unified_doc = normalize_to_unified_model(raw_data)
    print(f"Unified Document ID: {unified_doc.document_id}")
    print(f"Total Rows: {len(unified_doc.rows)}")
    print(f"Total Amount: {unified_doc.total_amount:,.2f}")
    
    # 3. Sample Row Check
    if unified_doc.rows:
        first_row = unified_doc.rows[0]
        print("\nSample Row 1:")
        print(f"  Item: {first_row.serial_no}")
        print(f"  Desc: {first_row.description[:60]}...")
        print(f"  Qty Since Last: {first_row.qty_since_last_bill}")
        print(f"  Qty To Date: {first_row.qty_to_date}")
        print(f"  Rate: {first_row.rate}")
        print(f"  Amount: {first_row.amount}")

if __name__ == "__main__":
    test_ingestion()
