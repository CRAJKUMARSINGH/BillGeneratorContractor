#!/usr/bin/env python3
"""
GOOGLE CLOUD VISION API - Extract ALL text from ALL images
Most accurate OCR available (95%+ accuracy)
"""
import sys
import os
from pathlib import Path
import re

def extract_with_google_vision(image_path):
    """Extract text using Google Cloud Vision API"""
    try:
        from google.cloud import vision
        
        client = vision.ImageAnnotatorClient()
        
        with open(image_path, 'rb') as image_file:
            content = image_file.read()
        
        image = vision.Image(content=content)
        response = client.document_text_detection(image=image)
        
        if response.error.message:
            raise Exception(response.error.message)
        
        return response.full_text_annotation.text
    
    except ImportError:
        print("❌ Google Cloud Vision not installed")
        print("💡 Install: pip install google-cloud-vision")
        return None
    except Exception as e:
        print(f"❌ Google Vision error: {e}")
        return None

def extract_with_easyocr(image_path):
    """Fallback to EasyOCR"""
    try:
        import easyocr
        reader = easyocr.Reader(['en', 'hi'], gpu=False)
        result = reader.readtext(str(image_path))
        text = '\n'.join([detection[1] for detection in result if detection[2] > 0.3])
        return text
    except Exception as e:
        print(f"❌ EasyOCR error: {e}")
        return None

def process_all_images(work_order_dir):
    """Process all images and extract text"""
    
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
        
        # Try Google Vision first
        text = extract_with_google_vision(str(img_file))
        
        if not text:
            print("   ⚠️ Google Vision failed, trying EasyOCR...")
            text = extract_with_easyocr(str(img_file))
        
        if text:
            print(f"   ✅ Extracted {len(text)} characters")
            all_extracted.append({
                'image': img_file.name,
                'text': text
            })
        else:
            print(f"   ❌ Failed to extract text")
    
    return all_extracted

def parse_pwd_items(text):
    """Parse PWD items from extracted text"""
    
    items = []
    
    # Pattern for BSR codes
    bsr_pattern = r'\b(\d+\.\d+(?:\.\d+)?)\b'
    
    # Pattern for amounts (Rs. or numbers)
    amount_pattern = r'Rs\.?\s*(\d+(?:,\d+)*(?:\.\d+)?)'
    
    # Find all BSR codes
    bsr_codes = re.findall(bsr_pattern, text)
    
    # Find all amounts
    amounts = re.findall(amount_pattern, text)
    
    print(f"\n   Found {len(bsr_codes)} BSR codes: {bsr_codes}")
    print(f"   Found {len(amounts)} amounts: {amounts}")
    
    return items

def main():
    work_order_dir = "INPUT/work_order_samples/work_01_27022026"
    output_file = "OUTPUT/EXTRACTED_TEXT_GOOGLE_VISION.txt"
    
    if len(sys.argv) > 1:
        work_order_dir = sys.argv[1]
    
    print(f"\n{'='*80}")
    print("🔍 EXTRACTING TEXT FROM ALL IMAGES")
    print(f"{'='*80}")
    
    # Extract from all images
    all_extracted = process_all_images(work_order_dir)
    
    if not all_extracted:
        print("\n❌ No text extracted")
        return 1
    
    # Combine all text
    combined_text = ""
    for item in all_extracted:
        combined_text += f"\n{'='*80}\n"
        combined_text += f"IMAGE: {item['image']}\n"
        combined_text += f"{'='*80}\n"
        combined_text += item['text']
        combined_text += "\n"
    
    # Save to file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(combined_text)
    
    print(f"\n{'='*80}")
    print("✅ TEXT EXTRACTION COMPLETE")
    print(f"{'='*80}\n")
    print(f"📁 Output: {output_path.absolute()}")
    print(f"📊 Total images: {len(all_extracted)}")
    print(f"📝 Total characters: {len(combined_text)}")
    
    # Parse items
    print(f"\n{'='*80}")
    print("🔍 PARSING PWD ITEMS")
    print(f"{'='*80}")
    
    for item in all_extracted:
        print(f"\n📄 {item['image']}:")
        parse_pwd_items(item['text'])
    
    print(f"\n💡 Next: Review {output_file} and create input Excel")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
