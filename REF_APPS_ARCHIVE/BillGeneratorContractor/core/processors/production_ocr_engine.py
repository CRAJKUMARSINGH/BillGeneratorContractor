#!/usr/bin/env python3
"""
Production-Grade OCR Engine with Multiple Fallback Options
Supports EasyOCR, PaddleOCR, Google Vision, and Gemini API
Includes intelligent retry logic and error handling
"""

import os
import sys
import time
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import traceback

# Image processing
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import io
import base64

# OCR Engines
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

try:
    import paddleocr
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False

try:
    from google.cloud import vision
    from google.cloud.vision import ImageAnnotatorClient
    GOOGLE_VISION_AVAILABLE = True
except ImportError:
    GOOGLE_VISION_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class OCREngine(Enum):
    EASYOCR = "easyocr"
    PADDLEOCR = "paddleocr"
    GOOGLE_VISION = "google_vision"
    GEMINI = "gemini"


@dataclass
class OCRResult:
    """Result from OCR processing"""
    text: str
    confidence: float
    engine: OCREngine
    processing_time: float
    success: bool
    error_message: Optional[str] = None


@dataclass
class ExtractedItem:
    """Extracted work order item"""
    bsr_code: str
    description: str
    unit: str
    quantity: float
    rate: float
    confidence: float
    source_engine: OCREngine


class ImagePreprocessor:
    """Intelligent image preprocessing for better OCR accuracy"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def preprocess(self, image_path: str) -> np.ndarray:
        """Apply intelligent preprocessing to improve OCR accuracy"""
        try:
            # Load image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            original_shape = img.shape
            
            # 1. Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # 2. Denoise
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # 3. Contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(denoised)
            
            # 4. Deskew if needed
            deskewed = self._deskew(enhanced)
            
            # 5. Sharpen
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            sharpened = cv2.filter2D(deskewed, -1, kernel)
            
            # 6. Binarization (adaptive)
            binary = cv2.adaptiveThreshold(
                sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            self.logger.info(f"Preprocessed image: {image_path} from {original_shape} to {binary.shape}")
            return binary
            
        except Exception as e:
            self.logger.error(f"Error preprocessing image {image_path}: {e}")
            # Return original grayscale if preprocessing fails
            img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            return img if img is not None else None
    
    def _deskew(self, image: np.ndarray) -> np.ndarray:
        """Deskew image using Hough line transform"""
        try:
            # Detect lines
            edges = cv2.Canny(image, 50, 150, apertureSize=3)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)
            
            if lines is None:
                return image
            
            # Calculate angle
            angles = []
            for line in lines:
                x1, y1, x2, y2 = line[0]
                angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
                if abs(angle) < 45:  # Only consider reasonable angles
                    angles.append(angle)
            
            if not angles:
                return image
            
            # Use median angle
            median_angle = np.median(angles)
            
            # Rotate image
            (h, w) = image.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
            rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            
            return rotated
            
        except Exception as e:
            self.logger.debug(f"Deskewing failed: {e}")
            return image


class ProductionOCREngine:
    """Production-grade OCR engine with multiple fallback options"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        self.preprocessor = ImagePreprocessor()
        
        # Initialize OCR engines
        self.easyocr_reader = None
        self.paddleocr_reader = None
        self.vision_client = None
        self.gemini_model = None
        
        # Engine priority for fallback
        self.engine_priority = [
            OCREngine.GOOGLE_VISION,
            OCREngine.GEMINI,
            OCREngine.EASYOCR,
            OCREngine.PADDLEOCR
        ]
        
        # Statistics
        self.stats = {
            'total_processed': 0,
            'success_count': 0,
            'engine_usage': {engine.value: 0 for engine in OCREngine},
            'errors': []
        }
        
        self._initialize_engines()
    
    def _initialize_engines(self):
        """Initialize available OCR engines"""
        # EasyOCR
        if EASYOCR_AVAILABLE and 'easyocr' in self.config.get('enabled_engines', ['easyocr']):
            try:
                self.easyocr_reader = easyocr.Reader(['en', 'hi'])
                self.logger.info("EasyOCR initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize EasyOCR: {e}")
        
        # PaddleOCR
        if PADDLEOCR_AVAILABLE and 'paddleocr' in self.config.get('enabled_engines', ['paddleocr']):
            try:
                self.paddleocr_reader = paddleocr.PaddleOCR(use_angle_cls=True, lang='en')
                self.logger.info("PaddleOCR initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize PaddleOCR: {e}")
        
        # Google Vision
        if GOOGLE_VISION_AVAILABLE and 'google_vision' in self.config.get('enabled_engines', ['google_vision']):
            try:
                credentials_path = self.config.get('google_credentials_path')
                if credentials_path and os.path.exists(credentials_path):
                    self.vision_client = vision.ImageAnnotatorClient.from_service_account_json(credentials_path)
                else:
                    self.vision_client = vision.ImageAnnotatorClient()
                self.logger.info("Google Vision initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize Google Vision: {e}")
        
        # Gemini
        if GEMINI_AVAILABLE and 'gemini' in self.config.get('enabled_engines', ['gemini']):
            try:
                api_key = self.config.get('gemini_api_key') or os.getenv('GEMINI_API_KEY')
                if api_key:
                    genai.configure(api_key=api_key)
                    self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                    self.logger.info("Gemini initialized successfully")
                else:
                    self.logger.warning("Gemini API key not found")
            except Exception as e:
                self.logger.error(f"Failed to initialize Gemini: {e}")
    
    def extract_text(self, image_path: str, max_retries: int = 3) -> OCRResult:
        """Extract text from image with intelligent fallback"""
        self.stats['total_processed'] += 1
        
        # Preprocess image
        processed_image = self.preprocessor.preprocess(image_path)
        if processed_image is None:
            return OCRResult(
                text="", confidence=0.0, engine=OCREngine.EASYOCR,
                processing_time=0.0, success=False,
                error_message="Image preprocessing failed"
            )
        
        last_error = None
        
        for engine in self.engine_priority:
            if not self._is_engine_available(engine):
                continue
            
            for attempt in range(max_retries):
                try:
                    start_time = time.time()
                    result = self._extract_with_engine(engine, image_path, processed_image)
                    processing_time = time.time() - start_time
                    
                    if result.success and result.text.strip():
                        self.stats['success_count'] += 1
                        self.stats['engine_usage'][engine.value] += 1
                        return OCRResult(
                            text=result.text, confidence=result.confidence,
                            engine=engine, processing_time=processing_time,
                            success=True
                        )
                    
                    last_error = result.error_message or "Empty result"
                    
                    # Exponential backoff
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 0.5
                        time.sleep(wait_time)
                
                except Exception as e:
                    last_error = str(e)
                    self.logger.warning(f"Engine {engine.value} attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        time.sleep((2 ** attempt) * 0.5)
        
        # All engines failed
        error_msg = f"All OCR engines failed. Last error: {last_error}"
        self.stats['errors'].append(error_msg)
        return OCRResult(
            text="", confidence=0.0, engine=OCREngine.EASYOCR,
            processing_time=0.0, success=False,
            error_message=error_msg
        )
    
    def extract_work_order_items(self, image_path: str) -> List[ExtractedItem]:
        """Extract structured work order items from image"""
        # First extract raw text
        ocr_result = self.extract_text(image_path)
        if not ocr_result.success:
            return []
        
        # Parse structured data from text
        items = self._parse_work_order_items(ocr_result.text, ocr_result.engine)
        
        return items
    
    def _extract_with_engine(self, engine: OCREngine, image_path: str, processed_image: np.ndarray) -> OCRResult:
        """Extract text using specific OCR engine"""
        if engine == OCREngine.EASYOCR and self.easyocr_reader:
            return self._extract_with_easyocr(image_path, processed_image)
        elif engine == OCREngine.PADDLEOCR and self.paddleocr_reader:
            return self._extract_with_paddleocr(image_path, processed_image)
        elif engine == OCREngine.GOOGLE_VISION and self.vision_client:
            return self._extract_with_google_vision(image_path)
        elif engine == OCREngine.GEMINI and self.gemini_model:
            return self._extract_with_gemini(image_path)
        else:
            return OCRResult(
                text="", confidence=0.0, engine=engine,
                processing_time=0.0, success=False,
                error_message=f"Engine {engine.value} not available"
            )
    
    def _extract_with_easyocr(self, image_path: str, processed_image: np.ndarray) -> OCRResult:
        """Extract text using EasyOCR"""
        try:
            results = self.easyocr_reader.readtext(processed_image)
            
            # Combine all text with confidence scores
            text_parts = []
            total_confidence = 0
            word_count = 0
            
            for (bbox, text, confidence) in results:
                if confidence > 0.5:  # Filter low confidence results
                    text_parts.append(text)
                    total_confidence += confidence
                    word_count += len(text.split())
            
            combined_text = "\n".join(text_parts)
            avg_confidence = total_confidence / max(word_count, 1)
            
            return OCRResult(
                text=combined_text, confidence=avg_confidence,
                engine=OCREngine.EASYOCR, processing_time=0.0,
                success=True
            )
            
        except Exception as e:
            return OCRResult(
                text="", confidence=0.0, engine=OCREngine.EASYOCR,
                processing_time=0.0, success=False,
                error_message=str(e)
            )
    
    def _extract_with_paddleocr(self, image_path: str, processed_image: np.ndarray) -> OCRResult:
        """Extract text using PaddleOCR"""
        try:
            results = self.paddleocr_reader.ocr(processed_image, cls=True)
            
            text_parts = []
            total_confidence = 0
            line_count = 0
            
            if results and results[0]:
                for line in results[0]:
                    if line and len(line) >= 2:
                        text = line[1][0]
                        confidence = line[1][1]
                        
                        if confidence > 0.5:
                            text_parts.append(text)
                            total_confidence += confidence
                            line_count += 1
            
            combined_text = "\n".join(text_parts)
            avg_confidence = total_confidence / max(line_count, 1)
            
            return OCRResult(
                text=combined_text, confidence=avg_confidence,
                engine=OCREngine.PADDLEOCR, processing_time=0.0,
                success=True
            )
            
        except Exception as e:
            return OCRResult(
                text="", confidence=0.0, engine=OCREngine.PADDLEOCR,
                processing_time=0.0, success=False,
                error_message=str(e)
            )
    
    def _extract_with_google_vision(self, image_path: str) -> OCRResult:
        """Extract text using Google Vision API"""
        try:
            with open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            image = vision.Image(content=content)
            response = self.vision_client.text_detection(image=image)
            
            if response.error.message:
                raise Exception(f"Google Vision API error: {response.error.message}")
            
            texts = response.text_annotations
            if texts:
                full_text = texts[0].description
                return OCRResult(
                    text=full_text, confidence=0.9,  # Google Vision doesn't provide per-word confidence
                    engine=OCREngine.GOOGLE_VISION, processing_time=0.0,
                    success=True
                )
            else:
                return OCRResult(
                    text="", confidence=0.0, engine=OCREngine.GOOGLE_VISION,
                    processing_time=0.0, success=False,
                    error_message="No text detected"
                )
                
        except Exception as e:
            return OCRResult(
                text="", confidence=0.0, engine=OCREngine.GOOGLE_VISION,
                processing_time=0.0, success=False,
                error_message=str(e)
            )
    
    def _extract_with_gemini(self, image_path: str) -> OCRResult:
        """Extract text using Gemini Vision API"""
        try:
            # Upload image
            image = Image.open(image_path)
            
            # Prompt for text extraction
            prompt = """
            Extract all text from this work order image. Focus on:
            1. BSR codes (numbers like 18.13, 27.01, etc.)
            2. Item descriptions
            3. Units (m, m2, m3, etc.)
            4. Quantities
            5. Rates
            
            Return the text in a clear, structured format preserving the table structure.
            """
            
            response = self.gemini_model.generate_content([prompt, image])
            
            if response.text:
                return OCRResult(
                    text=response.text, confidence=0.85,
                    engine=OCREngine.GEMINI, processing_time=0.0,
                    success=True
                )
            else:
                return OCRResult(
                    text="", confidence=0.0, engine=OCREngine.GEMINI,
                    processing_time=0.0, success=False,
                    error_message="No text extracted by Gemini"
                )
                
        except Exception as e:
            return OCRResult(
                text="", confidence=0.0, engine=OCREngine.GEMINI,
                processing_time=0.0, success=False,
                error_message=str(e)
            )
    
    def _parse_work_order_items(self, text: str, engine: OCREngine) -> List[ExtractedItem]:
        """Parse structured work order items from extracted text"""
        items = []
        
        try:
            lines = text.split('\n')
            current_item = {}
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Look for BSR code patterns (e.g., "18.13", "27.01.5")
                if self._is_bsr_code(line):
                    if current_item:
                        # Save previous item
                        item = self._create_item_from_data(current_item, engine)
                        if item:
                            items.append(item)
                    
                    # Start new item
                    current_item = {'bsr_code': line}
                
                # Look for rate patterns (numbers with decimals, typically at end of line)
                elif self._is_rate(line):
                    current_item['rate'] = line
                
                # Look for unit patterns
                elif self._is_unit(line):
                    current_item['unit'] = line
                
                # Everything else is likely description
                else:
                    if 'description' not in current_item:
                        current_item['description'] = line
                    else:
                        current_item['description'] += " " + line
            
            # Don't forget the last item
            if current_item:
                item = self._create_item_from_data(current_item, engine)
                if item:
                    items.append(item)
        
        except Exception as e:
            self.logger.error(f"Error parsing work order items: {e}")
        
        return items
    
    def _is_bsr_code(self, text: str) -> bool:
        """Check if text looks like a BSR code"""
        import re
        # BSR codes are like 18.13, 27.01.5, etc.
        pattern = r'^\d{2}\.\d{2}(\.\d+)?$'
        return bool(re.match(pattern, text.strip()))
    
    def _is_rate(self, text: str) -> bool:
        """Check if text looks like a rate"""
        import re
        # Rates are numbers with 2 decimal places
        pattern = r'^\d+\.\d{2}$'
        return bool(re.match(pattern, text.strip()))
    
    def _is_unit(self, text: str) -> bool:
        """Check if text looks like a unit"""
        units = {'m', 'm2', 'm3', 'm³', 'kg', 'nos', 'lot', 'day', 'month'}
        return text.strip().lower() in units
    
    def _create_item_from_data(self, data: Dict[str, str], engine: OCREngine) -> Optional[ExtractedItem]:
        """Create ExtractedItem from parsed data"""
        try:
            bsr_code = data.get('bsr_code', '')
            description = data.get('description', '')
            unit = data.get('unit', 'm')  # Default unit
            rate = float(data.get('rate', 0))
            
            if not bsr_code:
                return None
            
            return ExtractedItem(
                bsr_code=bsr_code,
                description=description,
                unit=unit,
                quantity=0,  # Will be filled from qty.txt
                rate=rate,
                confidence=0.8,  # Default confidence
                source_engine=engine
            )
        
        except Exception as e:
            self.logger.error(f"Error creating item from data: {e}")
            return None
    
    def _is_engine_available(self, engine: OCREngine) -> bool:
        """Check if OCR engine is available"""
        if engine == OCREngine.EASYOCR:
            return self.easyocr_reader is not None
        elif engine == OCREngine.PADDLEOCR:
            return self.paddleocr_reader is not None
        elif engine == OCREngine.GOOGLE_VISION:
            return self.vision_client is not None
        elif engine == OCREngine.GEMINI:
            return self.gemini_model is not None
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        if self.stats['total_processed'] > 0:
            success_rate = (self.stats['success_count'] / self.stats['total_processed']) * 100
        else:
            success_rate = 0
        
        return {
            'total_processed': self.stats['total_processed'],
            'success_count': self.stats['success_count'],
            'success_rate': success_rate,
            'engine_usage': self.stats['engine_usage'],
            'available_engines': [engine.value for engine in OCREngine if self._is_engine_available(engine)],
            'recent_errors': self.stats['errors'][-5:]  # Last 5 errors
        }
    
    def reset_statistics(self):
        """Reset processing statistics"""
        self.stats = {
            'total_processed': 0,
            'success_count': 0,
            'engine_usage': {engine.value: 0 for engine in OCREngine},
            'errors': []
        }


def create_production_ocr_engine(config_path: Optional[str] = None) -> ProductionOCREngine:
    """Factory function to create production OCR engine"""
    config = {}
    
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
    
    # Load from environment variables
    env_config = {
        'gemini_api_key': os.getenv('GEMINI_API_KEY'),
        'google_credentials_path': os.getenv('GOOGLE_CREDENTIALS_PATH'),
        'enabled_engines': os.getenv('OCR_ENGINES', 'easyocr,paddleocr,google_vision,gemini').split(',')
    }
    
    config.update({k: v for k, v in env_config.items() if v is not None})
    
    return ProductionOCREngine(config)


if __name__ == "__main__":
    # Test the OCR engine
    logging.basicConfig(level=logging.INFO)
    
    ocr_engine = create_production_ocr_engine()
    
    # Test with a sample image
    test_image = "INPUT_WORK_ORDER_IMAGES_TEXT/work_order_1.jpg"
    if os.path.exists(test_image):
        print(f"Testing with {test_image}")
        result = ocr_engine.extract_text(test_image)
        print(f"Result: {result}")
        print(f"Statistics: {ocr_engine.get_statistics()}")
    else:
        print(f"Test image not found: {test_image}")
