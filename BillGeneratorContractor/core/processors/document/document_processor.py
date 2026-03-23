"""
Document Processor
Orchestrates the document processing pipeline
"""
import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
import logging

# Import processing components
from .image_preprocessor import ImagePreprocessor
from .ocr_engine import OCREngine
from .hwr_engine import HandwritingRecognizer
from .data_extractor import DataExtractor, WorkOrderItem, ExtraItem
from .data_validator import DataValidator
from .data_mapper import DataMapper, BillGeneratorInput


@dataclass
class ProcessingStatus:
    """Status of document processing"""
    status: str  # "pending", "processing", "completed", "failed", "needs_review"
    progress: float  # 0.0 to 1.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    current_step: str = ""
    
    def update(self, progress: float, step: str):
        """Update progress and current step"""
        self.progress = progress
        self.current_step = step
    
    def add_error(self, error: str):
        """Add error message"""
        self.errors.append(error)
        self.status = "failed"
    
    def add_warning(self, warning: str):
        """Add warning message"""
        self.warnings.append(warning)


@dataclass
class WorkOrderData:
    """Complete work order extraction result"""
    items: List[WorkOrderItem]
    metadata: Dict
    processing_status: ProcessingStatus


@dataclass
class BillQuantitiesData:
    """Complete bill quantities extraction result"""
    quantities: Dict[str, Tuple[float, float]]  # item_number -> (quantity, confidence)
    metadata: Dict
    processing_status: ProcessingStatus


@dataclass
class ExtraItemsData:
    """Complete extra items extraction result"""
    items: List[ExtraItem]
    metadata: Dict
    processing_status: ProcessingStatus


class DocumentProcessor:
    """Orchestrates document processing pipeline"""
    
    def __init__(self, 
                 ocr_engine: Optional[OCREngine] = None,
                 hwr_engine: Optional[HandwritingRecognizer] = None,
                 preprocessor: Optional[ImagePreprocessor] = None):
        """
        Initialize document processor
        
        Args:
            ocr_engine: OCR engine instance (creates default if None)
            hwr_engine: Handwriting recognition engine (creates default if None)
            preprocessor: Image preprocessor (creates default if None)
        """
        self.ocr_engine = ocr_engine or OCREngine()
        self.hwr_engine = hwr_engine or HandwritingRecognizer()
        self.preprocessor = preprocessor or ImagePreprocessor()
        self.data_extractor = DataExtractor()
        self.data_validator = DataValidator()
        self.data_mapper = DataMapper()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Processing status
        self.status = ProcessingStatus(status="pending", progress=0.0)
    
    def process_work_order(self, file_paths: List[Path]) -> WorkOrderData:
        """
        Extract item numbers, descriptions, and units from work order
        
        Args:
            file_paths: List of paths to work order images/PDFs
        
        Returns:
            WorkOrderData with extracted items
        """
        self.status.update(0.1, "Loading work order files")
        
        all_items = []
        metadata = {
            'file_count': len(file_paths),
            'files': [str(f) for f in file_paths],
            'processing_timestamp': datetime.now().isoformat()
        }
        
        try:
            for page_num, file_path in enumerate(file_paths, start=1):
                self.status.update(
                    0.1 + (0.8 * page_num / len(file_paths)),
                    f"Processing page {page_num}/{len(file_paths)}"
                )
                
                # Load image
                image = cv2.imread(str(file_path))
                if image is None:
                    self.status.add_warning(f"Failed to load image: {file_path}")
                    continue
                
                # Preprocess
                preprocessed = self.preprocessor.preprocess(image)
                
                # Extract text with OCR
                ocr_result = self.ocr_engine.extract_text(preprocessed)
                
                # Extract structured items
                items = self.data_extractor.extract_work_order_items(ocr_result, page_num)
                all_items.extend(items)
            
            self.status.update(0.9, "Finalizing work order data")
            
            # Create work order data
            work_order_data = WorkOrderData(
                items=all_items,
                metadata=metadata,
                processing_status=self.status
            )
            
            self.status.status = "completed"
            self.status.progress = 1.0
            
            return work_order_data
            
        except Exception as e:
            self.logger.error(f"Error processing work order: {e}")
            self.status.add_error(str(e))
            return WorkOrderData(
                items=all_items,
                metadata=metadata,
                processing_status=self.status
            )
    
    def process_bill_quantities(self, file_path: Path, 
                               valid_items: List[str]) -> BillQuantitiesData:
        """
        Extract item numbers and quantities from handwritten page
        
        Args:
            file_path: Path to bill quantities image
            valid_items: List of valid item numbers from work order
        
        Returns:
            BillQuantitiesData with extracted quantities
        """
        self.status = ProcessingStatus(status="processing", progress=0.0)
        self.status.update(0.1, "Loading bill quantities file")
        
        metadata = {
            'file': str(file_path),
            'processing_timestamp': datetime.now().isoformat()
        }
        
        try:
            # Load image
            image = cv2.imread(str(file_path))
            if image is None:
                self.status.add_error(f"Failed to load image: {file_path}")
                return BillQuantitiesData(
                    quantities={},
                    metadata=metadata,
                    processing_status=self.status
                )
            
            self.status.update(0.3, "Preprocessing image")
            
            # Preprocess
            preprocessed = self.preprocessor.preprocess(image)
            
            self.status.update(0.5, "Recognizing handwritten text")
            
            # Extract handwritten text
            hwr_result = self.hwr_engine.recognize_text(preprocessed)
            
            self.status.update(0.7, "Extracting quantities")
            
            # Extract quantities
            quantities = self.data_extractor.extract_bill_quantities(hwr_result, valid_items)
            
            self.status.update(0.9, "Finalizing bill quantities data")
            
            # Create bill quantities data
            bill_quantities_data = BillQuantitiesData(
                quantities=quantities,
                metadata=metadata,
                processing_status=self.status
            )
            
            self.status.status = "completed"
            self.status.progress = 1.0
            
            return bill_quantities_data
            
        except Exception as e:
            self.logger.error(f"Error processing bill quantities: {e}")
            self.status.add_error(str(e))
            return BillQuantitiesData(
                quantities={},
                metadata=metadata,
                processing_status=self.status
            )
    
    def process_extra_items(self, file_path: Path) -> ExtraItemsData:
        """
        Extract descriptions, quantities, and rates from handwritten page
        
        Args:
            file_path: Path to extra items image
        
        Returns:
            ExtraItemsData with extracted items
        """
        self.status = ProcessingStatus(status="processing", progress=0.0)
        self.status.update(0.1, "Loading extra items file")
        
        metadata = {
            'file': str(file_path),
            'processing_timestamp': datetime.now().isoformat()
        }
        
        try:
            # Load image
            image = cv2.imread(str(file_path))
            if image is None:
                self.status.add_error(f"Failed to load image: {file_path}")
                return ExtraItemsData(
                    items=[],
                    metadata=metadata,
                    processing_status=self.status
                )
            
            self.status.update(0.3, "Preprocessing image")
            
            # Preprocess
            preprocessed = self.preprocessor.preprocess(image)
            
            self.status.update(0.5, "Recognizing handwritten text")
            
            # Extract handwritten text
            hwr_result = self.hwr_engine.recognize_text(preprocessed)
            
            self.status.update(0.7, "Extracting extra items")
            
            # Extract extra items
            items = self.data_extractor.extract_extra_items(hwr_result)
            
            self.status.update(0.9, "Finalizing extra items data")
            
            # Create extra items data
            extra_items_data = ExtraItemsData(
                items=items,
                metadata=metadata,
                processing_status=self.status
            )
            
            self.status.status = "completed"
            self.status.progress = 1.0
            
            return extra_items_data
            
        except Exception as e:
            self.logger.error(f"Error processing extra items: {e}")
            self.status.add_error(str(e))
            return ExtraItemsData(
                items=[],
                metadata=metadata,
                processing_status=self.status
            )
    
    def process_complete_workflow(self, 
                                 work_order_files: List[Path],
                                 bill_quantities_file: Path,
                                 extra_items_file: Optional[Path] = None) -> BillGeneratorInput:
        """
        Process complete workflow: work order → bill quantities → extra items → validation → mapping
        
        Args:
            work_order_files: List of work order file paths
            bill_quantities_file: Bill quantities file path
            extra_items_file: Optional extra items file path
        
        Returns:
            BillGeneratorInput ready for bill generation
        """
        # Process work order
        work_order_data = self.process_work_order(work_order_files)
        
        # Get valid item numbers
        valid_items = [item.item_number for item in work_order_data.items]
        
        # Process bill quantities
        bill_quantities_data = self.process_bill_quantities(bill_quantities_file, valid_items)
        
        # Process extra items if provided
        if extra_items_file:
            extra_items_data = self.process_extra_items(extra_items_file)
        else:
            extra_items_data = ExtraItemsData(
                items=[],
                metadata={},
                processing_status=ProcessingStatus(status="skipped", progress=1.0)
            )
        
        # Validate all data
        validation_result = self.data_validator.validate_all(
            work_order_data,
            bill_quantities_data,
            extra_items_data
        )
        
        # Map to bill generator format
        bill_generator_input = self.data_mapper.map_to_bill_format(
            work_order_data,
            bill_quantities_data,
            extra_items_data,
            metadata={
                'validation_result': validation_result,
                'original_files': work_order_files + [bill_quantities_file] + 
                                ([extra_items_file] if extra_items_file else [])
            }
        )
        
        return bill_generator_input
    
    def get_processing_status(self) -> ProcessingStatus:
        """
        Return current processing status and progress
        
        Returns:
            ProcessingStatus object
        """
        return self.status
