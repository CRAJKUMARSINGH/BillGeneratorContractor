#!/usr/bin/env python3
"""
PADDLEOCR - Offline, accurate, multilingual OCR
Extract ALL text from ALL 5 images
"""
import sys
from pathlib import Path
import json
import re

def extract_with_paddleocr(image_path):
    """Extract text using PaddleOCR"""
    try:
        from paddleocr import PaddleOCR
        
        # Initialize PaddleOCR (English + Hindi)
        ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False)
        
        # Perform OCR
        result = ocr.ocr(str(image_path), cls=True)
        
        # Extract text
        text_lines = []
        for line in result[0]:
            text = line[1][0]
            confidence = line[1][1]
            if confidence > 0.5:
                text_lines.append(text)
        
        return '\n'.join(text_lines)
    
    except ImportError:
        print("❌ PaddleOCR not installed")
        print("💡 Install: pip install paddlepaddle paddleocr")
        return None
    except Exception as e:
        print(f"❌ PaddleOCR error: {e}")
        return None

def process_all_images(work_order_dir):
    """Process all images"""
    
    work_order_path = Path(work_order_dir)
    
    # Find all images
    image_files = []
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']:
        image_files.extend(sorted(work_order_path.glob(ext)))
    
    if not image_files:
        print("❌ No images found!")
        return []
    
    print(f"\n📸 Found {len(image_files)} images\n")
    
    all_extracted = []
    
    for idx, img_file in enumerate(image_files, 1):
        print(f"📄 Image {idx}/{len(image_files)}: {img_file.name}")
        
        text = extract_with_paddleocr(str(img_file))
        
        if text:
            print(f"   ✅ Extracted {len(text)} characters")
            all_extracted.append({
                'image': img_file.name,
                'text': text
            })
        else:
            print(f"   ❌ Failed")
    
    return all_extracted

def parse_items_from_text(all_text):
    """Parse PWD items from all extracted text"""
    
    # Combine all text
    combined = '\n'.join([item['text'] for item in all_text])
    
    # Extract BSR codes
    bsr_pattern = r'\b(\d+\.\d+(?:\.\d+)?)\b'
    bsr_codes = re.findall(bsr_pattern, combined)
    
    # Extract rates (Rs. followed by number)
    rate_pattern = r'Rs\.?\s*(\d+(?:,\d+)*(?:\.\d+)?)'
    rates = re.findall(rate_pattern, combined)
    
    # Extract units
    unit_pattern = r'\b(point|mtr|Each|Nos|Sqm|Cum)\b'
    units = re.findall(unit_pattern, combined, re.IGNORECASE)
    
    print(f"\n📊 Parsing Results:")
    print(f"   BSR Codes: {len(set(bsr_codes))} unique - {sorted(set(bsr_codes))}")
    print(f"   Rates: {len(rates)} found")
    print(f"   Units: {len(set(units))} unique - {sorted(set(units))}")
    
    return {
        'bsr_codes': sorted(set(bsr_codes)),
        'rates': rates,
        'units': sorted(set(units)),
        'full_text': combined
    }

def main():
    work_order_dir = "INPUT/work_order_samples/work_01_27022026"
    output_file = "OUTPUT/PADDLE_EXTRACTED_DATA.txt"
    
    print(f"\n{'='*80}")
    print("🚀 PADDLEOCR - EXTRACTING FROM ALL IMAGES")
    print(f"{'='*80}")
    
    # Extract from all images
    all_extracted = process_all_images(work_order_dir)
    
    if not all_extracted:
        print("\n❌ No text extracted")
        return 1
    
    # Parse items
    parsed = parse_items_from_text(all_extracted)
    
    # Save combined text
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("EXTRACTED TEXT FROM ALL IMAGES\n")
        f.write("="*80 + "\n\n")
        
        for item in all_extracted:
            f.write(f"\n{'='*80}\n")
            f.write(f"IMAGE: {item['image']}\n")
            f.write(f"{'='*80}\n")
            f.write(item['text'])
            f.write("\n\n")
        
        f.write("\n" + "="*80 + "\n")
        f.write("PARSED DATA\n")
        f.write("="*80 + "\n")
        f.write(f"BSR Codes: {parsed['bsr_codes']}\n")
        f.write(f"Rates: {parsed['rates']}\n")
        f.write(f"Units: {parsed['units']}\n")
    
    print(f"\n{'='*80}")
    print("✅ EXTRACTION COMPLETE")
    print(f"{'='*80}\n")
    print(f"📁 Output: {output_path.absolute()}")
    print(f"📊 Images processed: {len(all_extracted)}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
