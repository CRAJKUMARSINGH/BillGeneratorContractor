"""
Brilliant Batch Processor

Integrates with BrilliantBatchInputManager to process batches of bills.
Handles both individual and batch processing modes.
"""
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import json

# Add project root to path
root_dir = Path(__file__).parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from batch.input_manager import BrilliantBatchInputManager, InputFileMetadata
from backend.models import GenerateRequest, BillItem, ExtraItem, GenerateOptions, BillRecord
from backend.services.bill_generation_service import generate_documents
from backend.database import Session
import uuid

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)


class BrilliantBatchProcessor:
    """
    Processes batches of bill inputs using the BrilliantBatchInputManager.
    
    Features:
    - Parallel processing support
    - Progress tracking
    - Error handling and recovery
    - Detailed result reporting
    """
    
    def __init__(self, input_manager: Optional[BrilliantBatchInputManager] = None):
        self.input_manager = input_manager or BrilliantBatchInputManager()
        self.results = []
        
    async def process_batch(self, 
                           max_concurrent: int = 4,
                           template_version: str = "v2",
                           generate_pdf: bool = True) -> dict:
        """
        Process all pending files in batch mode.
        
        Args:
            max_concurrent: Maximum number of concurrent processing tasks
            template_version: Template version to use
            generate_pdf: Whether to generate PDFs
            
        Returns:
            Dictionary with batch processing statistics
        """
        pending_files = self.input_manager.get_pending_files()
        
        if not pending_files:
            logger.info("No pending files to process")
            return {"total": 0, "completed": 0, "failed": 0}
        
        logger.info(f"Starting batch processing of {len(pending_files)} files")
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)
        
        # Create tasks
        tasks = []
        for file_meta in pending_files:
            task = self._process_single_with_semaphore(
                file_meta, 
                semaphore,
                template_version,
                generate_pdf
            )
            tasks.append(task)
        
        # Execute all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate results
        completed = sum(1 for r in results if isinstance(r, bool) and r)
        failed = len(results) - completed
        
        logger.info(f"Batch complete: {completed} succeeded, {failed} failed")
        
        return {
            "total": len(pending_files),
            "completed": completed,
            "failed": failed,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _process_single_with_semaphore(self, 
                                            file_meta: InputFileMetadata,
                                            semaphore: asyncio.Semaphore,
                                            template_version: str,
                                            generate_pdf: bool) -> bool:
        """Process a single file with semaphore-controlled concurrency."""
        async with semaphore:
            return await self._process_single_file(
                file_meta, 
                template_version,
                generate_pdf
            )
    
    async def _process_single_file(self, 
                                  file_meta: InputFileMetadata,
                                  template_version: str,
                                  generate_pdf: bool) -> bool:
        """
        Process a single input file.
        
        Returns:
            True if successful, False otherwise
        """
        filename = file_meta.filename
        filepath = file_meta.filepath
        
        try:
            # Update status to processing (this moves the file!)
            self.input_manager.update_file_status(filename, "processing")
            
            # Re-fetch metadata to get the new physical filepath
            updated_meta = self.input_manager.metadata["files"][filename]
            processing_filepath = updated_meta["filepath"]
            
            # Parse the Excel file to extract data
            parsed_data = await self._parse_input_file(processing_filepath)
            
            if not parsed_data:
                raise RuntimeError("Failed to parse input file")
            
            # Create GenerateRequest from parsed data
            request = self._build_generate_request(
                parsed_data, 
                template_version,
                generate_pdf
            )
            
            # Generate unique job ID
            job_id = str(uuid.uuid4())
            
            # Get output directory
            output_dir = root_dir / "backend" / "outputs"
            
            # Run document generation in executor (it's synchronous)
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,
                generate_documents,
                job_id,
                request,
                output_dir
            )
            
            # Update metadata on success
            output_path = str(output_dir / job_id)
            self.input_manager.update_file_status(
                filename, 
                "completed",
                output_path=output_path
            )
            
            logger.info(f"Successfully processed: {filename}")
            return True
            
        except Exception as e:
            logger.exception(f"Processing failed for {filename}: {e}")
            self.input_manager.update_file_status(
                filename,
                "failed",
                error_message=str(e)
            )
            return False
    
    async def _parse_input_file(self, filepath: str) -> Optional[dict]:
        """Parse an input Excel file and extract structured data."""
        try:
            from ingestion.excel_parser import parse_excel_to_raw
            from ingestion.normalizer import normalize_to_unified_model
            
            # Parse Excel
            raw_data = parse_excel_to_raw(filepath)
            
            if raw_data.get("error"):
                raise RuntimeError(f"Parse error: {raw_data['error']}")
            
            # Normalize
            unified_doc = normalize_to_unified_model(raw_data)
            
            # Return as dict for request building
            return {
                "metadata": unified_doc.raw_metadata,
                "rows": [row.dict() if hasattr(row, 'dict') else row 
                        for row in unified_doc.rows],
                "total_amount": unified_doc.total_amount
            }
            
        except Exception as e:
            logger.error(f"Parse failed: {e}")
            return None
    
    def _build_generate_request(self, 
                               parsed_data: dict,
                               template_version: str,
                               generate_pdf: bool) -> GenerateRequest:
        """Build GenerateRequest from parsed data."""
        metadata = parsed_data.get("metadata", {})
        rows = parsed_data.get("rows", [])
        
        # Convert rows to BillItems and ExtraItems
        bill_items = []
        extra_items = []
        
        for row in rows:
            # Determine if it's an extra item (you may need custom logic here)
            is_extra = row.get('is_extra', False)
            
            item_data = {
                "itemNo": str(row.get("serial_no", len(bill_items) + 1)),
                "description": row.get("description", ""),
                "unit": row.get("unit", ""),
                "quantitySince": row.get("qty_since_last_bill", 0),
                "quantityUpto": row.get("qty_to_date", 0),
                "rate": row.get("rate", 0),
                "amount": row.get("amount", 0)
            }
            
            if is_extra:
                extra_items.append(ExtraItem(**item_data))
            else:
                bill_items.append(BillItem(**item_data))
        
        # Build options
        options = GenerateOptions(
            templateVersion=template_version,
            generatePdf=generate_pdf,
            premiumPercent=metadata.get("tender_premium_percentage", 0),
            premiumType=metadata.get("premium_type", "above"),
            previousBillAmount=metadata.get("last_bill_deduction", 0)
        )
        
        return GenerateRequest(
            fileId=str(uuid.uuid4()),  # Generate unique file ID
            titleData=metadata,
            billItems=bill_items,
            extraItems=extra_items,
            options=options
        )
    
    def generate_batch_report(self, output_path: Optional[Path] = None) -> str:
        """Generate detailed batch processing report."""
        return self.input_manager.generate_report(output_path)


async def main():
    """Example batch processing run."""
    processor = BrilliantBatchProcessor()
    
    # Process batch
    results = await processor.process_batch(
        max_concurrent=4,
        template_version="v2",
        generate_pdf=True
    )
    
    print("\n=== BATCH PROCESSING RESULTS ===")
    print(f"Total: {results['total']}")
    print(f"Completed: {results['completed']}")
    print(f"Failed: {results['failed']}")
    
    # Generate report
    report = processor.generate_batch_report()
    print("\n" + report)


if __name__ == "__main__":
    asyncio.run(main())
