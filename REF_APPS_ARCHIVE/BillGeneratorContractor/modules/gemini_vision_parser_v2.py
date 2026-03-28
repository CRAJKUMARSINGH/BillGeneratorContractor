"""
GEMINI VISION PARSER V2 - Using new google-genai library
Extracts ALL items from ALL work order images
"""
import os
import json
import re
import base64
import time
from pathlib import Path
from typing import List, Dict, Optional

try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

EXTRACTION_PROMPT = """You are analyzing a PWD work order image with a table of items.

Extract EVERY row from the table in this JSON format:

[
  {
    "code": "1.1.2",
    "description": "Complete item description",
    "unit": "point",
    "quantity": 50,
    "rate": 602.0
  }
]

RULES:
- Extract ALL rows (even if 50+ rows)
- Code: BSR codes like 1.1.2, 18.13, 3.4.2
- Description: Full text
- Unit: point, mtr, Each, Sqm, etc.
- Quantity: Number from Quantity column (if present, else 0)
- Rate: Number in Rs. from Rate column
- Return ONLY valid JSON array, no markdown
- If no table, return []
"""

class GeminiVisionParserV2:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.client = None
        self.available = False
        self._init()
    
    def _init(self):
        if not GEMINI_AVAILABLE:
            print("google-genai not installed")
            return
        
        if not self.api_key:
            print("GEMINI_API_KEY not set")
            return
        
        try:
            self.client = genai.Client(api_key=self.api_key)
            self.available = True
            print("Gemini API ready (google-genai v2)")
        except Exception as e:
            print(f"Gemini init failed: {e}")
    
    def extract_items(self, image_path: Path) -> List[Dict]:
        """Extract items from one image"""
        if not self.available:
            return []
        
        print(f"   {image_path.name}")
        
        try:
            # Read image
            with open(image_path, 'rb') as f:
                image_b64 = base64.standard_b64encode(f.read()).decode('utf-8')
            
            # Call Gemini
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    EXTRACTION_PROMPT,
                    {'inline_data': {'mime_type': 'image/jpeg', 'data': image_b64}}
                ]
            )
            
            text = response.text.strip()
            
            # Clean JSON
            text = re.sub(r'```json\s*', '', text)
            text = re.sub(r'```\s*$', '', text)
            text = text.strip()
            
            # Parse
            items = json.loads(text)
            
            if not isinstance(items, list):
                return []
            
            # Validate
            valid = []
            for item in items:
                if isinstance(item, dict) and 'code' in item:
                    valid.append({
                        'code': str(item.get('code', '')).strip(),
                        'description': str(item.get('description', '')).strip(),
                        'unit': str(item.get('unit', 'nos')).strip(),
                        'rate': float(item.get('rate', 0) or 0),
                        'quantity': float(item.get('quantity', 0) or 0),
                        'source': image_path.name
                    })
            
            print(f"      {len(valid)} items")
            return valid
            
        except Exception as e:
            print(f"      Error: {e}")
            return []
    
    def extract_all(self, image_dir: Path) -> List[Dict]:
        """Extract from ALL images"""
        images = sorted(
            list(image_dir.glob("*.jpeg")) +
            list(image_dir.glob("*.jpg")) +
            list(image_dir.glob("*.png"))
        )
        
        print(f"\n   Found {len(images)} images\n")
        
        all_items = []
        for img in images:
            items = self.extract_items(img)
            all_items.extend(items)
            time.sleep(1)  # Rate limiting
        
        # Deduplicate by code
        seen = {}
        for item in all_items:
            code = item['code']
            if code not in seen:
                seen[code] = item
        
        unique = list(seen.values())
        print(f"\n   Total: {len(all_items)} items, {len(unique)} unique")
        
        return unique
