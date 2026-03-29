#!/usr/bin/env python3
"""Extract ALL text from ALL images using EasyOCR"""
import sys
from pathlib import Path
import easyocr
import re

def main():
    work_dir = "INPUT/work_order_samples/work_01_27022026"
    output = "OUTPUT/ALL_TEXT_EXTRACTED.txt"
    
    # Find images
    images = []
    for ext in ['*.jpg', '*.jpeg', '*.png']:
        images.extend(sorted(Path(work_dir).glob(ext)))
    
    print(f"\n📸 Found {len(images)} images")
    
    # Initialize EasyOCR
    print("🔧 Loading EasyOCR...")
    reader = easyocr.Reader(['en', 'hi'], gpu=False)
    print("✅ Ready\n")
    
    all_text = []
    
    for idx, img in enumerate(images, 1):
        print(f"📄 {idx}/{len(images)}: {img.name}")
        result = reader.readtext(str(img))
        
        text_blocks = []
        for detection in result:
            text = detection[1]
            conf = detection[2]
            if conf > 0.3:
                text_blocks.append(text)
        
        print(f"   ✅ {len(text_blocks)} blocks")
        
        all_text.append({
            'image': img.name,
            'text': '\n'.join(text_blocks)
        })
    
    # Save
    with open(output, 'w', encoding='utf-8') as f:
        for item in all_text:
            f.write(f"\n{'='*80}\n{item['image']}\n{'='*80}\n")
            f.write(item['text'] + "\n")
    
    # Parse
    combined = '\n'.join([item['text'] for item in all_text])
    bsr_codes = sorted(set(re.findall(r'\b(\d+\.\d+(?:\.\d+)?)\b', combined)))
    
    print(f"\n✅ Saved to: {output}")
    print(f"📊 BSR codes found: {bsr_codes}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
