#!/usr/bin/env python3
"""
Process work order images and create Excel file
"""
import sys
from pathlib import Path
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.processors.document.document_processor import DocumentProcessor
from core.processors.document.image_preprocessor import ImagePreprocessor
from core.processors.document.ocr_engine import OCREngine
from core.processors.document.data_extractor import DataExtractor

def process_work_order_images(image_dir: str, output_excel: str = "OUTPUT/work_order_extracted.xlsx"):
    """
    Process work order images and create Excel file
    
    Args:
        image_dir: Directory containing work order images
        output_excel: Output Excel file path
    """
    print(f"\n{'='*80}")
    print(f"Processing Work Order Images")
    print(f"{'='*80}\n")
    
    image_path = Path(image_dir)
    output_path = Path(output_excel)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not image_path.exists():
        print(f"❌ Image directory not found: {image_path}")
        return False
    
    # Find all image files
    image_files = []
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.tif', '*.tiff']:
        image_files.extend(list(image_path.glob(ext)))
    
    if not image_files:
        print(f"❌ No image files found in: {image_path}")
        return False
    
    print(f"Found {len(image_files)} image files:")
    for img in image_files:
        print(f"  - {img.name}")
    print()
    
    try:
        # Initialize document processor
        print("Step 1: Initializing OCR engine...")
        processor = DocumentProcessor(
            use_ocr=True,
            use_hwr=False,  # Handwriting recognition disabled for now
            language="eng+hin"
        )
        print("✅ OCR engine initialized\n")
        
        # Process work order images
        print("Step 2: Processing work order images...")
        work_order_data = processor.process_work_order(image_files)
        
        if not work_order_data.items:
            print("⚠️  No items extracted from images")
            print(f"   Confidence: {work_order_data.confidence:.2%}")
            print("\nTrying to extract raw text...")
            
            # Fallback: Extract raw text from each image
            ocr_engine = OCREngine(language="eng+hin")
            preprocessor = ImagePreprocessor()
            
            all_text = []
            for img_file in image_files:
                print(f"\n  Processing: {img_file.name}")
                image = preprocessor.load_image(img_file)
                preprocessed = preprocessor.preprocess(image)
                ocr_result = ocr_engine.extract_text(preprocessed)
                
                print(f"    Confidence: {ocr_result.confidence:.2%}")
                print(f"    Words extracted: {len(ocr_result.words)}")
                
                all_text.append(f"\n--- {img_file.name} ---\n")
                all_text.append(ocr_result.text)
            
            # Save raw text
            text_file = output_path.with_suffix('.txt')
            with open(text_file, 'w', encoding='utf-8') as f:
                f.writelines(all_text)
            
            print(f"\n✅ Raw OCR text saved to: {text_file}")
            print("\nPlease review the text file and manually create the Excel structure.")
            return False
        
        print(f"✅ Extracted {len(work_order_data.items)} items")
        print(f"   Overall confidence: {work_order_data.confidence:.2%}\n")
        
        # Display extracted items
        print("Extracted Items:")
        print("-" * 80)
        for idx, item in enumerate(work_order_data.items[:5], 1):  # Show first 5
            print(f"{idx}. Item: {item.get('item_number', 'N/A')}")
            print(f"   Description: {item.get('description', 'N/A')[:60]}...")
            print(f"   Unit: {item.get('unit', 'N/A')}")
            print()
        
        if len(work_order_data.items) > 5:
            print(f"... and {len(work_order_data.items) - 5} more items\n")
        
        # Step 3: Create Excel file
        print("Step 3: Creating Excel file...")
        
        # Prepare data for Excel
        excel_data = {
            'Item Number': [],
            'Description': [],
            'Unit': [],
            'Quantity': [],
            'Rate': [],
            'Amount': [],
            'Remarks': []
        }
        
        for item in work_order_data.items:
            excel_data['Item Number'].append(item.get('item_number', ''))
            excel_data['Description'].append(item.get('description', ''))
            excel_data['Unit'].append(item.get('unit', ''))
            excel_data['Quantity'].append(item.get('quantity', ''))
            excel_data['Rate'].append(item.get('rate', ''))
            excel_data['Amount'].append(item.get('amount', ''))
            excel_data['Remarks'].append('')
        
        # Create DataFrame
        df = pd.DataFrame(excel_data)
        
        # Create Excel writer with multiple sheets
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Work Order sheet
            df.to_excel(writer, sheet_name='Work Order', index=False)
            
            # Title sheet (template)
            title_data = {
                'Field': ['Work Name', 'Agreement Number', 'Contractor Name', 
                         'Bill Type', 'Bill Number', 'Date'],
                'Value': ['', '', '', '', '', '']
            }
            title_df = pd.DataFrame(title_data)
            title_df.to_excel(writer, sheet_name='Title', index=False)
            
            # Bill Quantity sheet (copy of Work Order for editing)
            df.to_excel(writer, sheet_name='Bill Quantity', index=False)
            
            # Extra Items sheet (empty template)
            extra_data = {
                'Item Number': [],
                'Description': [],
                'Unit': [],
                'Quantity': [],
                'Rate': [],
                'Amount': [],
                'Deviation %': [],
                'Remarks': []
            }
            extra_df = pd.DataFrame(extra_data)
            extra_df.to_excel(writer, sheet_name='Extra Items', index=False)
        
        print(f"✅ Excel file created: {output_path}\n")
        
        # Step 4: Save confidence report
        print("Step 4: Generating confidence report...")
        report_file = output_path.with_suffix('.confidence_report.txt')
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("Work Order OCR Confidence Report\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Overall Confidence: {work_order_data.confidence:.2%}\n")
            f.write(f"Total Items Extracted: {len(work_order_data.items)}\n\n")
            
            f.write("Item-wise Confidence Scores:\n")
            f.write("-" * 80 + "\n")
            
            for idx, item in enumerate(work_order_data.items, 1):
                f.write(f"\nItem {idx}: {item.get('item_number', 'N/A')}\n")
                f.write(f"  Description: {item.get('description', 'N/A')}\n")
                f.write(f"  Unit: {item.get('unit', 'N/A')}\n")
                
                # Get confidence from metadata if available
                if 'confidence' in item:
                    f.write(f"  Confidence: {item['confidence']:.2%}\n")
        
        print(f"✅ Confidence report saved: {report_file}\n")
        
        print(f"{'='*80}")
        print("✅ Processing Complete!")
        print(f"{'='*80}\n")
        print(f"Output files:")
        print(f"  1. Excel: {output_path.absolute()}")
        print(f"  2. Report: {report_file.absolute()}")
        print(f"\n⚠️  Please review and verify the extracted data before using!")
        print()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    # Default: Process work order samples
    image_dir = "INPUT/work_order_samples/work_01_27022026"
    output_excel = "OUTPUT/work_order_extracted.xlsx"
    
    if len(sys.argv) > 1:
        image_dir = sys.argv[1]
    
    if len(sys.argv) > 2:
        output_excel = sys.argv[2]
    
    success = process_work_order_images(image_dir, output_excel)
    sys.exit(0 if success else 1)
