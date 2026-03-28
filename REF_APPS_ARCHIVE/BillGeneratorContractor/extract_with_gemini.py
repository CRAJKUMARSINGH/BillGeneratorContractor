#!/usr/bin/env python3
"""
GOOGLE GEMINI VISION - Best FREE solution for PWD work orders
Extracts structured data from images automatically
"""
import sys
import os
from pathlib import Path
import json
import base64

def extract_with_gemini(image_path, api_key):
    """Extract structured data using Gemini Vision"""
    try:
        from google import genai
        from google.genai import types
        
        # Configure client
        client = genai.Client(api_key=api_key)
        
        # Read image
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Create prompt for PWD work order
        prompt = """
You are analyzing a PWD work order image. This is a table with items.

Extract EVERYTHING you see in this EXACT JSON format:

{
  "items": [
    {
      "sno": "1",
      "code": "1.1.2",
      "description": "Complete item description exactly as written",
      "unit": "point",
      "rate": 602.0
    }
  ],
  "header_info": {
    "work_order_number": "extract if visible",
    "contractor_name": "extract if visible",
    "work_name": "extract if visible",
    "agreement_number": "extract if visible",
    "total_amount": "extract if visible"
  }
}

CRITICAL RULES:
1. Extract EVERY row from the table
2. Code column: Numbers like 1.1.2, 18.13, 3.4.2 (BSR codes)
3. Description: Full text of item description
4. Unit: point, mtr, Each, Sqm, etc.
5. Rate: The rate/amount in Rs.
6. If table has 50 rows, extract all 50 rows
7. Return ONLY valid JSON, nothing else
8. If you can't read something clearly, put "UNCLEAR" but still include the row
"""
        
        # Generate response
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[prompt, types.Part.from_bytes(data=image_data, mime_type='image/jpeg')]
        )
        
        return response.text
    
    except ImportError:
        print("❌ Google GenAI not installed")
        print("💡 Install: pip install google-genai")
        return None
    except Exception as e:
        print(f"❌ Gemini error: {e}")
        return None

def process_all_images_with_gemini(work_order_dir, api_key):
    """Process all images with Gemini"""
    
    work_order_path = Path(work_order_dir)
    
    # Find all images
    image_files = []
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']:
        image_files.extend(sorted(work_order_path.glob(ext)))
    
    if not image_files:
        print("❌ No images found!")
        return []
    
    print(f"\n📸 Found {len(image_files)} images\n")
    
    all_results = []
    
    for idx, img_file in enumerate(image_files, 1):
        print(f"📄 Processing image {idx}/{len(image_files)}: {img_file.name}")
        
        result = extract_with_gemini(str(img_file), api_key)
        
        if result:
            print(f"   ✅ Extracted data")
            all_results.append({
                'image': img_file.name,
                'data': result
            })
        else:
            print(f"   ❌ Failed")
    
    return all_results

def main():
    work_order_dir = "INPUT/work_order_samples/work_01_27022026"
    output_file = "OUTPUT/GEMINI_EXTRACTED_DATA.json"
    
    # Load .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except:
        pass
    
    # Get API key from environment or .env
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("\n❌ GEMINI_API_KEY not found!")
        print("\n📝 To get FREE API key:")
        print("1. Go to: https://makersuite.google.com/app/apikey")
        print("2. Click 'Create API Key'")
        print("3. Copy the key")
        print("4. Set environment variable: set GEMINI_API_KEY=your_key_here")
        print("\nOr add to .env file:")
        print("GEMINI_API_KEY=your_key_here")
        return 1
    
    print(f"\n{'='*80}")
    print("🤖 GEMINI VISION - EXTRACTING FROM ALL IMAGES")
    print(f"{'='*80}")
    
    # Process all images
    all_results = process_all_images_with_gemini(work_order_dir, api_key)
    
    if not all_results:
        print("\n❌ No data extracted")
        return 1
    
    # Save results
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*80}")
    print("✅ EXTRACTION COMPLETE")
    print(f"{'='*80}\n")
    print(f"📁 Output: {output_path.absolute()}")
    print(f"📊 Images processed: {len(all_results)}")
    
    # Display extracted data
    print(f"\n{'='*80}")
    print("📋 EXTRACTED DATA PREVIEW")
    print(f"{'='*80}\n")
    
    for result in all_results:
        print(f"\n📄 {result['image']}:")
        print(result['data'][:500] + "..." if len(result['data']) > 500 else result['data'])
    
    print(f"\n💡 Next: Review {output_file} and create input Excel")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
