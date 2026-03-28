import os
import pytest
from pathlib import Path
import json
import logging
from typing import List
import sys

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("robotic_harness")

ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

from ingestion.excel_parser import parse_excel_to_raw
from ingestion.normalizer import normalize_to_unified_model

def discover_test_files() -> List[Path]:
    fldrs = [f for f in ROOT_DIR.iterdir() if f.is_dir() and (f.name.startswith("INPUT") or f.name.startswith("TEST"))]
    files = []
    
    # Supported extensions
    exts = ["*.xlsx", "*.xls", "*.xlsm", "*.pdf", "*.jpeg", "*.jpg", "*.png"]
    for folder in fldrs:
        for ex in exts:
            for f in folder.rglob(ex):
                if not f.name.startswith("~$"):
                    files.append(f)
            
    return files

@pytest.mark.parametrize("test_file", discover_test_files(), ids=lambda x: x.name)
def test_robotic_pipeline(test_file: Path):
    logger.info(f"Robot testing file: {test_file.name}")
    
    ext = test_file.suffix.lower()
    
    try:
        if ext in ['.xlsx', '.xls', '.xlsm']:
            # 1. Excel Pipeline
            parsed_raw = parse_excel_to_raw(str(test_file))
            assert parsed_raw is not None
            
            # 2. Normalization Pipeline
            unified = normalize_to_unified_model(parsed_raw)
            assert unified.total_amount >= 0
            assert len(unified.rows) > 0
            
            logger.info(f"SUCCESS: {test_file.name} - Rows: {len(unified.rows)}")

        elif ext in ['.pdf', '.jpeg', '.jpg', '.png']:
            # 3. OCR Pipeline (Stub/Mock check)
            from ingestion.ocr_extractor import extract_table_from_image
            result = extract_table_from_image(str(test_file))
            assert "billItems" in result
            logger.info(f"SUCCESS: OCR route verified for {test_file.name}")

        else:
            pytest.skip(f"No robotic handler for extension {ext}")

    except Exception as e:
        logger.error(f"FAILURE: {test_file.name} - {str(e)}")
        raise e
