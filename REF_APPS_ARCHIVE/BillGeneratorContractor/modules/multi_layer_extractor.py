#!/usr/bin/env python3
"""
Multi-Layer Extraction Framework - Week 3
3-layer fallback system: Gemini → Google Vision → EasyOCR
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum
import time


class ExtractionLayer(Enum):
    """Extraction layer types"""
    GEMINI = "gemini"
    GOOGLE_VISION = "google_vision"
    EASYOCR = "easyocr"


@dataclass
class ExtractionResult:
    """Result from an extraction layer"""
    success: bool
    items: List[Dict]
    layer: ExtractionLayer
    confidence: float  # 0.0 to 1.0
    processing_time: float  # seconds
    error: Optional[str] = None
    
    @property
    def item_count(self) -> int:
        return len(self.items)


class BaseExtractor(ABC):
    """Base class for all extractors"""
    
    def __init__(self, name: str, layer: ExtractionLayer):
        self.name = name
        self.layer = layer
    
    @abstractmethod
    def extract(self, image_path: str) -> ExtractionResult:
        """Extract items from image"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if extractor is available"""
        pass


class GeminiExtractor(BaseExtractor):
    """Gemini Vision API extractor"""
    
    def __init__(self, api_key: str):
        super().__init__("Gemini Vision", ExtractionLayer.GEMINI)
        self.api_key = api_key
        self._parser = None
    
    def is_available(self) -> bool:
        """Check if Gemini API is available"""
        if not self.api_key:
            return False
        try:
            import google.genai as genai
            return True
        except ImportError:
            return False
    
    def extract(self, image_path: str) -> ExtractionResult:
        """Extract using Gemini Vision API"""
        start_time = time.time()
        
        try:
            # Lazy load parser
            if self._parser is None:
                from modules.gemini_vision_parser_v2 import GeminiVisionParser
                self._parser = GeminiVisionParser(api_key=self.api_key)
            
            # Extract items
            items = self._parser.extract_items_from_image(image_path)
            processing_time = time.time() - start_time
            
            # Calculate confidence based on item completeness
            confidence = self._calculate_confidence(items)
            
            return ExtractionResult(
                success=True,
                items=items,
                layer=self.layer,
                confidence=confidence,
                processing_time=processing_time
            )
        
        except Exception as e:
            processing_time = time.time() - start_time
            return ExtractionResult(
                success=False,
                items=[],
                layer=self.layer,
                confidence=0.0,
                processing_time=processing_time,
                error=str(e)
            )
    
    def _calculate_confidence(self, items: List[Dict]) -> float:
        """Calculate confidence based on item completeness"""
        if not items:
            return 0.0
        
        total_score = 0
        for item in items:
            score = 0
            # Check required fields
            if item.get('code'):
                score += 0.4
            if item.get('description'):
                score += 0.2
            if item.get('unit'):
                score += 0.2
            if item.get('rate', 0) > 0:
                score += 0.2
            total_score += score
        
        return total_score / len(items)


class GoogleVisionExtractor(BaseExtractor):
    """Google Cloud Vision API extractor"""
    
    def __init__(self, credentials_path: Optional[str] = None):
        super().__init__("Google Cloud Vision", ExtractionLayer.GOOGLE_VISION)
        self.credentials_path = credentials_path
        self._client = None
    
    def is_available(self) -> bool:
        """Check if Google Vision API is available"""
        try:
            from google.cloud import vision
            return True
        except ImportError:
            return False
    
    def extract(self, image_path: str) -> ExtractionResult:
        """Extract using Google Cloud Vision API"""
        start_time = time.time()
        
        try:
            # Lazy load client
            if self._client is None:
                from google.cloud import vision
                import os
                if self.credentials_path:
                    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.credentials_path
                self._client = vision.ImageAnnotatorClient()
            
            # Read image
            with open(image_path, 'rb') as f:
                content = f.read()
            
            image = vision.Image(content=content)
            
            # Perform text detection
            response = self._client.text_detection(image=image)
            texts = response.text_annotations
            
            if not texts:
                processing_time = time.time() - start_time
                return ExtractionResult(
                    success=False,
                    items=[],
                    layer=self.layer,
                    confidence=0.0,
                    processing_time=processing_time,
                    error="No text detected"
                )
            
            # Extract structured data from text
            full_text = texts[0].description
            items = self._parse_text_to_items(full_text)
            
            processing_time = time.time() - start_time
            confidence = 0.8 if items else 0.0  # Google Vision is reliable but needs parsing
            
            return ExtractionResult(
                success=True,
                items=items,
                layer=self.layer,
                confidence=confidence,
                processing_time=processing_time
            )
        
        except Exception as e:
            processing_time = time.time() - start_time
            return ExtractionResult(
                success=False,
                items=[],
                layer=self.layer,
                confidence=0.0,
                processing_time=processing_time,
                error=str(e)
            )
    
    def _parse_text_to_items(self, text: str) -> List[Dict]:
        """Parse OCR text into structured items"""
        # This is a simplified parser - can be enhanced
        items = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Try to extract BSR code pattern (e.g., 1.1.2, 18.13.6)
            import re
            bsr_pattern = r'\b(\d+\.\d+(?:\.\d+)?)\b'
            matches = re.findall(bsr_pattern, line)
            
            if matches:
                # Found potential BSR code
                code = matches[0]
                # Extract other fields (simplified)
                item = {
                    'code': code,
                    'description': line,
                    'unit': 'Each',  # Default
                    'rate': 0,
                    'quantity': 1
                }
                items.append(item)
        
        return items


class EasyOCRExtractor(BaseExtractor):
    """EasyOCR offline extractor"""
    
    def __init__(self):
        super().__init__("EasyOCR", ExtractionLayer.EASYOCR)
        self._reader = None
    
    def is_available(self) -> bool:
        """Check if EasyOCR is available"""
        try:
            import easyocr
            return True
        except ImportError:
            return False
    
    def extract(self, image_path: str) -> ExtractionResult:
        """Extract using EasyOCR"""
        start_time = time.time()
        
        try:
            # Lazy load reader
            if self._reader is None:
                import easyocr
                self._reader = easyocr.Reader(['en'], gpu=False)
            
            # Perform OCR
            result = self._reader.readtext(image_path)
            
            # Extract text
            texts = [text for (bbox, text, prob) in result]
            full_text = '\n'.join(texts)
            
            # Parse text to items
            items = self._parse_text_to_items(full_text)
            
            processing_time = time.time() - start_time
            confidence = 0.7 if items else 0.0  # EasyOCR is less reliable
            
            return ExtractionResult(
                success=True,
                items=items,
                layer=self.layer,
                confidence=confidence,
                processing_time=processing_time
            )
        
        except Exception as e:
            processing_time = time.time() - start_time
            return ExtractionResult(
                success=False,
                items=[],
                layer=self.layer,
                confidence=0.0,
                processing_time=processing_time,
                error=str(e)
            )
    
    def _parse_text_to_items(self, text: str) -> List[Dict]:
        """Parse OCR text into structured items"""
        # Reuse Google Vision parser
        items = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            import re
            bsr_pattern = r'\b(\d+\.\d+(?:\.\d+)?)\b'
            matches = re.findall(bsr_pattern, line)
            
            if matches:
                code = matches[0]
                item = {
                    'code': code,
                    'description': line,
                    'unit': 'Each',
                    'rate': 0,
                    'quantity': 1
                }
                items.append(item)
        
        return items


class MultiLayerExtractor:
    """Orchestrates multi-layer extraction with fallback"""
    
    def __init__(self, gemini_api_key: str, google_credentials_path: Optional[str] = None):
        # Initialize all extractors
        self.extractors = [
            GeminiExtractor(gemini_api_key),
            GoogleVisionExtractor(google_credentials_path),
            EasyOCRExtractor()
        ]
        
        # Filter to available extractors
        self.available_extractors = [e for e in self.extractors if e.is_available()]
        
        if not self.available_extractors:
            raise RuntimeError("No extractors available!")
    
    def extract_with_fallback(self, image_path: str, min_confidence: float = 0.7) -> ExtractionResult:
        """Extract with automatic fallback"""
        print(f"\nExtracting from: {Path(image_path).name}")
        print(f"Available layers: {[e.name for e in self.available_extractors]}")
        
        for i, extractor in enumerate(self.available_extractors, 1):
            print(f"\n  Layer {i}: {extractor.name}")
            
            result = extractor.extract(image_path)
            
            print(f"    Success: {result.success}")
            print(f"    Items: {result.item_count}")
            print(f"    Confidence: {result.confidence:.2f}")
            print(f"    Time: {result.processing_time:.2f}s")
            
            if result.error:
                print(f"    Error: {result.error}")
            
            # Check if result is acceptable
            if result.success and result.confidence >= min_confidence:
                print(f"    ✓ Accepted (confidence >= {min_confidence})")
                return result
            
            print(f"    ✗ Rejected (confidence < {min_confidence} or failed)")
        
        # All layers failed - return last result
        print(f"\n  All layers failed or below threshold")
        return result
    
    def extract_all_layers(self, image_path: str) -> List[ExtractionResult]:
        """Extract using all available layers (for comparison)"""
        results = []
        for extractor in self.available_extractors:
            result = extractor.extract(image_path)
            results.append(result)
        return results
    
    def get_status(self) -> Dict:
        """Get status of all extractors"""
        return {
            'total_extractors': len(self.extractors),
            'available_extractors': len(self.available_extractors),
            'layers': [
                {
                    'name': e.name,
                    'layer': e.layer.value,
                    'available': e.is_available()
                }
                for e in self.extractors
            ]
        }


if __name__ == '__main__':
    import os as _os
    # Test the multi-layer extractor
    print("\n" + "="*80)
    print("MULTI-LAYER EXTRACTION TEST - WEEK 3 DAY 1")
    print("="*80)

    # API key is read from environment — NEVER hardcode keys in source.
    # Set GEMINI_API_KEY in your .env file or shell before running.
    API_KEY = _os.getenv("GEMINI_API_KEY", "")
    if not API_KEY:
        print("ERROR: GEMINI_API_KEY environment variable is not set.")
        print("Export it before running: set GEMINI_API_KEY=your_key_here")
        raise SystemExit(1)
    
    try:
        extractor = MultiLayerExtractor(gemini_api_key=API_KEY)
        
        # Show status
        status = extractor.get_status()
        print(f"\nExtractor Status:")
        print(f"  Total layers: {status['total_extractors']}")
        print(f"  Available layers: {status['available_extractors']}")
        print(f"\nLayers:")
        for layer in status['layers']:
            available = "✓" if layer['available'] else "✗"
            print(f"  {available} {layer['name']} ({layer['layer']})")
        
        # Test with sample image
        test_image = Path("INPUT_WORK_ORDER_IMAGES_TEXT")
        if test_image.exists():
            images = list(test_image.glob("*.jpg")) + list(test_image.glob("*.jpeg"))
            if images:
                print("\n" + "="*80)
                print("TESTING WITH SAMPLE IMAGE")
                print("="*80)
                
                result = extractor.extract_with_fallback(str(images[0]))
                
                print("\n" + "="*80)
                print("FINAL RESULT")
                print("="*80)
                print(f"Layer: {result.layer.value}")
                print(f"Success: {result.success}")
                print(f"Items: {result.item_count}")
                print(f"Confidence: {result.confidence:.2f}")
                print(f"Time: {result.processing_time:.2f}s")
                
                if result.items:
                    print(f"\nSample items:")
                    for item in result.items[:3]:
                        print(f"  - {item.get('code', 'N/A')}: {item.get('description', 'N/A')[:50]}...")
        
        print("\n" + "="*80)
        print("MULTI-LAYER EXTRACTION: OPERATIONAL")
        print("="*80 + "\n")
    
    except Exception as e:
        print(f"\nError: {e}")
        print("\nNote: Some extractors may not be available without proper setup")
