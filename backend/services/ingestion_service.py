import logging
import uuid
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd

from engine.models import UnifiedBillDocument, BillItem, ExtraItem
from engine.calculation.excel_processor_enterprise import EnterpriseExcelProcessor
from engine.calculation.bill_processor import process_bill
from .ai_excel_parser import parse_excel_ai
from ingestion.excel_parser import parse_excel_to_raw
from ingestion.ocr_extractor import extract_table_from_image
from ingestion.normalizer import normalize_to_unified_model

logger = logging.getLogger(__name__)

class IngestionService:
    @staticmethod
    async def process_file(
        file_path: Path, 
        file_id: str, 
        original_filename: str,
        preferred_mode: Optional[str] = None
    ) -> UnifiedBillDocument:
        """
        Unified entry point for all ingestion modes.
        Determines the best mode if not specified.
        """
        ext = file_path.suffix.lower()
        
        # Mode 3: Image/OCR
        if ext in {".png", ".jpg", ".jpeg", ".pdf"}:
            logger.info(f"Processing as Mode 3 (OCR): {original_filename}")
            raw_data = await asyncio.get_event_loop().run_in_executor(
                None, extract_table_from_image, str(file_path)
            )
            return normalize_to_unified_model(raw_data, source_type="mode3_ocr")

        # Excel Processing
        if ext in {".xlsx", ".xls", ".xlsm"}:
            # Check for Mode 1 vs Mode 2
            try:
                xl = pd.ExcelFile(file_path)
                sheet_names = [s.upper() for s in xl.sheet_names]
                
                has_wo = any("WORK ORDER" in s or "WO" == s for s in sheet_names)
                has_bq = any("BILL QUANTITY" in s or "BQ" == s for s in sheet_names)
                
                # Mode 1: Standard Excel (WO + BQ) - STRICT GUARDIAN PATH
                if has_wo and has_bq and preferred_mode != "mode2":
                    logger.info(f"Processing as Mode 1 (Strict): {original_filename}")
                    doc = await IngestionService._process_strict_mode1(file_path, file_id, original_filename)
                    doc.mode = "mode1"
                    return doc
                
                # Mode 2: Hybrid (WO only)
                elif has_wo:
                    logger.info(f"Processing as Mode 2 (Hybrid/WO-only): {original_filename}")
                    ai_result = parse_excel_ai(file_path, file_id, original_filename)
                    doc = IngestionService._map_ai_result_to_unified(ai_result)
                    doc.mode = "mode2"
                    # Zero out quantities for Mode 2 (ready for manual entry)
                    for item in doc.billItems:
                        item.wo_quantity = item.quantity # Store original as reference
                        item.quantity = 0.0
                        item.amount = 0.0
                    return doc
                
                # Fallback: Use AI Parser for non-standard Excel
                else:
                    logger.info(f"Processing as Mode 3 (AI Excel Parser): {original_filename}")
                    ai_result = parse_excel_ai(file_path, file_id, original_filename)
                    doc = IngestionService._map_ai_result_to_unified(ai_result)
                    doc.mode = "mode3_ai"
                    return doc
                    
            except Exception as e:
                logger.exception("Excel pre-scan failed, falling back to AI parser")
                ai_result = parse_excel_ai(file_path, file_id, original_filename)
                return IngestionService._map_ai_result_to_unified(ai_result)

        raise ValueError(f"Unsupported file format: {ext}")

    @staticmethod
    async def _process_strict_mode1(path: Path, file_id: str, filename: str) -> UnifiedBillDocument:
        """Robustly parse Mode 1 Excel files using the new ingestion layer."""
        # Use our new robust parser
        raw_data = await asyncio.get_event_loop().run_in_executor(
            None, parse_excel_to_raw, str(path)
        )
        
        # Get the document via normalizer (handles merging/sorting)
        doc = normalize_to_unified_model(raw_data, source_type="mode1")
        
        # Ensure fileId and fileName are set correctly
        doc.fileId = file_id
        doc.fileName = filename
        
        return doc

    @staticmethod
    def _map_ai_result_to_unified(ai_result) -> UnifiedBillDocument:
        """Helper to map AIParseResult to UnifiedBillDocument."""
        bill_items = []
        if ai_result.work_order_sheet:
            for r in ai_result.work_order_sheet.rows:
                bill_items.append(BillItem(
                    itemNo=r.item_no,
                    description=r.description,
                    unit=r.unit,
                    quantity=r.quantity,
                    rate=r.rate,
                    amount=r.amount,
                    confidence=r.confidence,
                    aiNote=r.ai_note
                ))
        
        return UnifiedBillDocument(
            fileId=ai_result.file_id,
            fileName=ai_result.file_name,
            titleData=ai_result.title_data,
            billItems=bill_items,
            extraItems=[],
            totalAmount=sum(item.amount for item in bill_items),
            confidenceOverall=ai_result.confidence_overall,
            sheets=[s.sheet_name for s in ai_result.sheets]
        )
