#!/usr/bin/env python3
"""
OCR Demo - Test the production OCR engine
"""

import os
import sys
import logging
from pathlib import Path

# Add core to path
sys.path.insert(0, str(Path(__file__).parent))

from core.processors.production_ocr_engine import ProductionOCREngine, create_production_ocr_engine

def main():
    """Test OCR engine with sample images"""
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    # Initialize OCR engine
    logger.info("Initializing Production OCR Engine...")
    ocr_engine = create_production_ocr_engine()
    
    # Test image directory
    image_dir = "INPUT_WORK_ORDER_IMAGES_TEXT"
    
    if not os.path.exists(image_dir):
        logger.error(f"Image directory not found: {image_dir}")
        return 1
    
    # Find image files
    image_files = []
    for file_path in Path(image_dir).glob("*.jpeg"):
        image_files.append(str(file_path))
    
    if not image_files:
        logger.error("No image files found")
        return 1
    
    logger.info(f"Found {len(image_files)} images to process")
    
    # Process each image
    for i, image_path in enumerate(image_files, 1):
        logger.info(f"\n--- Processing Image {i}/{len(image_files)} ---")
        logger.info(f"Image: {os.path.basename(image_path)}")
        
        try:
            # Extract text
            result = ocr_engine.extract_text(image_path)
            
            if result.success:
                logger.info(f"✓ OCR Success with {result.engine.value}")
                logger.info(f"Confidence: {result.confidence:.2f}")
                logger.info(f"Processing time: {result.processing_time:.2f}s")
                logger.info(f"Extracted text length: {len(result.text)} chars")
                
                # Show first 200 characters
                preview = result.text[:200].replace('\n', ' ')
                logger.info(f"Text preview: {preview}...")
                
                # Extract work order items
                items = ocr_engine.extract_work_order_items(image_path)
                logger.info(f"Found {len(items)} work order items")
                
                for j, item in enumerate(items, 1):
                    logger.info(f"  Item {j}: {item.bsr_code} - {item.description[:50]}...")
                
            else:
                logger.error(f"✗ OCR Failed: {result.error_message}")
        
        except Exception as e:
            logger.error(f"✗ Error processing image: {e}")
    
    # Show statistics
    logger.info("\n=== OCR STATISTICS ===")
    stats = ocr_engine.get_statistics()
    logger.info(f"Total processed: {stats['total_processed']}")
    logger.info(f"Success count: {stats['success_count']}")
    logger.info(f"Success rate: {stats['success_rate']:.1f}%")
    logger.info(f"Engine usage: {stats['engine_usage']}")
    logger.info(f"Available engines: {', '.join(stats['available_engines'])}")
    
    if stats['recent_errors']:
        logger.info("Recent errors:")
        for error in stats['recent_errors']:
            logger.info(f"  - {error}")
    
    logger.info("\n✓ OCR Demo completed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
