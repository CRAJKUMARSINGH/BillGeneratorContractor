#!/usr/bin/env python3
"""
Fully Automated Bill Generator - Production Version
Professional solution with AI-powered OCR and comprehensive validation
"""

import os
import sys
import logging
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import argparse

# Add core to path
sys.path.insert(0, str(Path(__file__).parent))

# Import production modules
from core.processors.production_ocr_engine import ProductionOCREngine, create_production_ocr_engine
from core.validation.data_validator import DataValidator, create_validator
from core.generators.automated_excel_generator import AutomatedExcelGenerator, create_excel_generator, ExcelGenerationConfig


@dataclass
class ProcessingConfig:
    """Configuration for the automated bill generator"""
    # OCR Configuration
    ocr_engines: List[str] = None
    gemini_api_key: Optional[str] = None
    google_credentials_path: Optional[str] = None
    
    # Validation Configuration
    bsr_schedule_path: Optional[str] = None
    strict_validation: bool = True
    
    # Excel Configuration
    output_dir: str = "OUTPUT"
    include_validation_sheet: bool = True
    backup_existing_files: bool = True
    
    # Processing Configuration
    max_retries: int = 3
    timeout_seconds: int = 300
    enable_logging: bool = True
    
    def __post_init__(self):
        if self.ocr_engines is None:
            self.ocr_engines = ['easyocr', 'paddleocr', 'google_vision', 'gemini']


@dataclass
class ProcessingResult:
    """Result of the complete processing pipeline"""
    success: bool
    total_images: int
    processed_images: int
    total_items: int
    valid_items: int
    output_file: str
    processing_time: float
    errors: List[str]
    warnings: List[str]
    ocr_statistics: Dict[str, Any]
    validation_summary: Dict[str, Any]


class AutomatedBillGenerator:
    """Main automated bill generator class"""
    
    def __init__(self, config: ProcessingConfig):
        self.logger = self._setup_logging(config.enable_logging)
        self.config = config
        
        # Initialize components
        self.ocr_engine = self._initialize_ocr_engine()
        self.validator = self._initialize_validator()
        self.excel_generator = self._initialize_excel_generator()
        
        self.logger.info("Automated Bill Generator initialized successfully")
    
    def _setup_logging(self, enable_logging: bool) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger(__name__)
        
        if enable_logging:
            if not logger.handlers:
                # Create logs directory
                os.makedirs("logs", exist_ok=True)
                
                # Setup file handler
                log_file = f"logs/automated_generator_{datetime.now().strftime('%Y%m%d')}.log"
                file_handler = logging.FileHandler(log_file)
                file_handler.setLevel(logging.INFO)
                
                # Setup console handler
                console_handler = logging.StreamHandler()
                console_handler.setLevel(logging.INFO)
                
                # Setup formatter
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                file_handler.setFormatter(formatter)
                console_handler.setFormatter(formatter)
                
                logger.addHandler(file_handler)
                logger.addHandler(console_handler)
                logger.setLevel(logging.INFO)
        
        return logger
    
    def _initialize_ocr_engine(self) -> ProductionOCREngine:
        """Initialize OCR engine with configuration"""
        ocr_config = {
            'gemini_api_key': self.config.gemini_api_key,
            'google_credentials_path': self.config.google_credentials_path,
            'enabled_engines': self.config.ocr_engines
        }
        
        return create_production_ocr_engine()
    
    def _initialize_validator(self) -> DataValidator:
        """Initialize data validator"""
        return create_validator(self.config.bsr_schedule_path)
    
    def _initialize_excel_generator(self) -> AutomatedExcelGenerator:
        """Initialize Excel generator"""
        excel_config = ExcelGenerationConfig(
            output_dir=self.config.output_dir,
            include_validation=self.config.include_validation_sheet,
            backup_existing=self.config.backup_existing_files
        )
        
        return create_excel_generator(excel_config)
    
    def process_images(self, image_directory: str, qty_file: Optional[str] = None) -> ProcessingResult:
        """Process all images in directory and generate Excel"""
        start_time = time.time()
        
        self.logger.info(f"Starting processing of images in: {image_directory}")
        
        # Find image files
        image_files = self._find_image_files(image_directory)
        total_images = len(image_files)
        
        if total_images == 0:
            return ProcessingResult(
                success=False,
                total_images=0,
                processed_images=0,
                total_items=0,
                valid_items=0,
                output_file="",
                processing_time=0,
                errors=["No image files found in directory"],
                warnings=[],
                ocr_statistics={},
                validation_summary={}
            )
        
        self.logger.info(f"Found {total_images} image files to process")
        
        # Process images and extract items
        all_items = []
        processed_images = 0
        errors = []
        warnings = []
        
        for i, image_file in enumerate(image_files, 1):
            self.logger.info(f"Processing image {i}/{total_images}: {image_file}")
            
            try:
                # Extract items from image
                items = self.ocr_engine.extract_work_order_items(image_file)
                
                if items:
                    all_items.extend(items)
                    processed_images += 1
                    self.logger.info(f"Extracted {len(items)} items from {image_file}")
                else:
                    warnings.append(f"No items extracted from {image_file}")
                    self.logger.warning(f"No items extracted from {image_file}")
            
            except Exception as e:
                error_msg = f"Error processing {image_file}: {e}"
                errors.append(error_msg)
                self.logger.error(error_msg)
        
        # Remove duplicates based on BSR code
        unique_items = self._remove_duplicate_items(all_items)
        self.logger.info(f"Found {len(all_items)} total items, {len(unique_items)} unique items")
        
        # Validate items
        validation_report = self.validator.validate_dataset(unique_items)
        self.logger.info(f"Validation complete: {validation_report.get_summary()}")
        
        # Load quantity data
        qty_data = self._load_quantity_data(qty_file)
        
        # Generate Excel
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"INPUT_FINAL_WITH_QUANTITIES_{timestamp}.xlsx"
        
        excel_result = self.excel_generator.generate_work_order_excel(
            unique_items, filename, qty_data
        )
        
        processing_time = time.time() - start_time
        
        if excel_result.success:
            self.logger.info(f"Excel file generated: {excel_result.file_path}")
        else:
            errors.append(f"Excel generation failed: {excel_result.message}")
        
        # Get OCR statistics
        ocr_stats = self.ocr_engine.get_statistics()
        
        # Create result
        result = ProcessingResult(
            success=excel_result.success and len(errors) == 0,
            total_images=total_images,
            processed_images=processed_images,
            total_items=len(unique_items),
            valid_items=validation_report.valid_items,
            output_file=excel_result.file_path if excel_result.success else "",
            processing_time=processing_time,
            errors=errors,
            warnings=warnings,
            ocr_statistics=ocr_stats,
            validation_summary=validation_report.get_summary()
        )
        
        self.logger.info(f"Processing complete: {result.success}")
        return result
    
    def _find_image_files(self, directory: str) -> List[str]:
        """Find all image files in directory"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
        image_files = []
        
        try:
            for file_path in Path(directory).rglob('*'):
                if file_path.suffix.lower() in image_extensions:
                    image_files.append(str(file_path))
        except Exception as e:
            self.logger.error(f"Error scanning directory {directory}: {e}")
        
        return sorted(image_files)
    
    def _remove_duplicate_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate items based on BSR code"""
        seen_bsr = set()
        unique_items = []
        
        for item in items:
            bsr_code = item.get('bsr_code', '')
            if bsr_code and bsr_code not in seen_bsr:
                seen_bsr.add(bsr_code)
                unique_items.append(item)
            elif bsr_code:
                # Merge with existing item (prefer higher confidence)
                for existing in unique_items:
                    if existing.get('bsr_code') == bsr_code:
                        # Keep the one with higher confidence or better data
                        if (item.get('confidence', 0) > existing.get('confidence', 0) or
                            len(item.get('description', '')) > len(existing.get('description', ''))):
                            unique_items.remove(existing)
                            unique_items.append(item)
                        break
        
        return unique_items
    
    def _load_quantity_data(self, qty_file: Optional[str]) -> Dict[str, float]:
        """Load quantity data from qty.txt file"""
        qty_data = {}
        
        if qty_file and os.path.exists(qty_file):
            try:
                with open(qty_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if ':' in line:
                            bsr, qty = line.split(':', 1)
                            bsr = bsr.strip()
                            try:
                                qty_data[bsr] = float(qty.strip())
                            except ValueError:
                                self.logger.warning(f"Invalid quantity in line: {line}")
                
                self.logger.info(f"Loaded {len(qty_data)} quantity entries from {qty_file}")
            
            except Exception as e:
                self.logger.error(f"Error loading quantity file {qty_file}: {e}")
        
        return qty_data
    
    def print_summary(self, result: ProcessingResult):
        """Print processing summary"""
        print("\n" + "="*60)
        print("AUTOMATED BILL GENERATOR - PROCESSING SUMMARY")
        print("="*60)
        
        print(f"Success: {'✓' if result.success else '✗'}")
        print(f"Processing Time: {result.processing_time:.2f} seconds")
        print(f"Total Images: {result.total_images}")
        print(f"Processed Images: {result.processed_images}")
        print(f"Total Items: {result.total_items}")
        print(f"Valid Items: {result.valid_items}")
        print(f"Output File: {result.output_file}")
        
        if result.errors:
            print(f"\nERRORS ({len(result.errors)}):")
            for error in result.errors:
                print(f"  ✗ {error}")
        
        if result.warnings:
            print(f"\nWARNINGS ({len(result.warnings)}):")
            for warning in result.warnings:
                print(f"  ⚠ {warning}")
        
        # OCR Statistics
        if result.ocr_statistics:
            print(f"\nOCR STATISTICS:")
            stats = result.ocr_statistics
            print(f"  Success Rate: {stats['success_rate']:.1f}%")
            print(f"  Engine Usage: {stats['engine_usage']}")
            print(f"  Available Engines: {', '.join(stats['available_engines'])}")
        
        # Validation Summary
        if result.validation_summary:
            print(f"\nVALIDATION SUMMARY:")
            val = result.validation_summary
            print(f"  Success Rate: {val['success_rate']:.1f}%")
            print(f"  Overall Score: {val['overall_score']:.1f}/100")
            print(f"  Errors: {val['error_count']}")
            print(f"  Warnings: {val['warning_count']}")
        
        print("\n" + "="*60)


def create_config_from_env() -> ProcessingConfig:
    """Create configuration from environment variables"""
    return ProcessingConfig(
        ocr_engines=os.getenv('OCR_ENGINES', 'easyocr,paddleocr,google_vision,gemini').split(','),
        gemini_api_key=os.getenv('GEMINI_API_KEY'),
        google_credentials_path=os.getenv('GOOGLE_CREDENTIALS_PATH'),
        bsr_schedule_path=os.getenv('BSR_SCHEDULE_PATH'),
        strict_validation=os.getenv('STRICT_VALIDATION', 'true').lower() == 'true',
        output_dir=os.getenv('OUTPUT_DIR', 'OUTPUT'),
        include_validation_sheet=os.getenv('INCLUDE_VALIDATION_SHEET', 'true').lower() == 'true',
        backup_existing_files=os.getenv('BACKUP_EXISTING_FILES', 'true').lower() == 'true',
        max_retries=int(os.getenv('MAX_RETRIES', '3')),
        timeout_seconds=int(os.getenv('TIMEOUT_SECONDS', '300')),
        enable_logging=os.getenv('ENABLE_LOGGING', 'true').lower() == 'true'
    )


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Automated Bill Generator - Production Version')
    parser.add_argument('image_directory', help='Directory containing work order images')
    parser.add_argument('--qty-file', help='Quantity file (qty.txt)')
    parser.add_argument('--output-dir', default='OUTPUT', help='Output directory')
    parser.add_argument('--gemini-key', help='Gemini API key')
    parser.add_argument('--google-creds', help='Google Cloud credentials path')
    parser.add_argument('--engines', default='easyocr,paddleocr,google_vision,gemini', 
                       help='OCR engines to use (comma-separated)')
    parser.add_argument('--config', help='Configuration file path')
    
    args = parser.parse_args()
    
    # Load configuration
    if args.config and os.path.exists(args.config):
        with open(args.config, 'r') as f:
            config_data = json.load(f)
        config = ProcessingConfig(**config_data)
    else:
        config = create_config_from_env()
    
    # Override with command line arguments
    config.output_dir = args.output_dir
    config.gemini_api_key = args.gemini_key or config.gemini_api_key
    config.google_credentials_path = args.google_creds or config.google_credentials_path
    config.ocr_engines = args.engines.split(',') if args.engines else config.ocr_engines
    
    # Validate inputs
    if not os.path.exists(args.image_directory):
        print(f"Error: Image directory not found: {args.image_directory}")
        return 1
    
    if args.qty_file and not os.path.exists(args.qty_file):
        print(f"Warning: Quantity file not found: {args.qty_file}")
        args.qty_file = None
    
    # Create generator and process
    generator = AutomatedBillGenerator(config)
    result = generator.process_images(args.image_directory, args.qty_file)
    
    # Print summary
    generator.print_summary(result)
    
    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
