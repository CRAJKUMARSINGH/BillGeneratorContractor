"""
OCR Engine
Extracts printed text from work order documents using Tesseract.

Robustness guarantee: all methods catch exceptions internally and return
safe empty results rather than raising.
"""
import logging
import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)

# Tesseract is optional – degrade gracefully when not installed
try:
    import pytesseract
    _TESSERACT_AVAILABLE = True
except ImportError:
    _TESSERACT_AVAILABLE = False
    logger.warning("pytesseract not installed – OCREngine will return empty results")


@dataclass
class Word:
    """Represents a single word extracted by OCR"""
    text: str
    confidence: float
    x: int
    y: int
    width: int
    height: int


@dataclass
class OCRResult:
    """Raw OCR output with words and confidence scores"""
    text: str
    words: List[Word]
    confidence: float
    language: str


@dataclass
class StructuredOCRResult:
    """Structured OCR result with extracted fields"""
    items: List[Dict[str, any]]
    confidence_scores: Dict[str, float]
    raw_text: str


class OCREngine:
    """OCR engine for extracting printed text from documents"""

    def __init__(self, language: str = "eng+hin"):
        """
        Initialize Tesseract OCR with language support.

        Args:
            language: Language codes (e.g., "eng", "hin", "eng+hin")
        """
        self.language = language
        self.config = r'--oem 3 --psm 6'

        if not _TESSERACT_AVAILABLE:
            logger.warning("OCREngine: Tesseract (pytesseract) not available – degraded mode")

    def _empty_ocr_result(self) -> "OCRResult":
        return OCRResult(text="", words=[], confidence=0.0, language=self.language)

    def _empty_structured_result(self) -> "StructuredOCRResult":
        return StructuredOCRResult(items=[], confidence_scores={}, raw_text="")

    def extract_text(self, image: np.ndarray) -> "OCRResult":
        """
        Extract all text from image with bounding boxes.
        Never raises – returns empty OCRResult on any failure.

        Args:
            image: Input image as numpy array

        Returns:
            OCRResult with text, words, and confidence scores
        """
        if not _TESSERACT_AVAILABLE:
            return self._empty_ocr_result()

        if image is None or (isinstance(image, np.ndarray) and image.size == 0):
            logger.warning("extract_text: empty/None image")
            return self._empty_ocr_result()

        try:
            # Ensure grayscale or BGR for Tesseract
            if image.ndim == 3 and image.shape[2] == 4:
                image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

            data = pytesseract.image_to_data(
                image,
                lang=self.language,
                config=self.config,
                output_type=pytesseract.Output.DICT
            )

            words = []
            n_boxes = len(data['text'])
            for i in range(n_boxes):
                text = data['text'][i].strip()
                conf = float(data['conf'][i])
                if text and conf > 0:
                    words.append(Word(
                        text=text,
                        confidence=conf / 100.0,
                        x=data['left'][i],
                        y=data['top'][i],
                        width=data['width'][i],
                        height=data['height'][i]
                    ))

            try:
                full_text = pytesseract.image_to_string(
                    image, lang=self.language, config=self.config
                )
            except Exception as e:
                logger.warning(f"image_to_string failed, using word join: {e}")
                full_text = " ".join(w.text for w in words)

            avg_confidence = sum(w.confidence for w in words) / len(words) if words else 0.0
            return OCRResult(text=full_text, words=words,
                             confidence=avg_confidence, language=self.language)

        except Exception as e:
            logger.error(f"extract_text failed: {e}")
            return self._empty_ocr_result()

    def extract_structured_data(self, image: np.ndarray,
                                template: Optional[str] = None) -> "StructuredOCRResult":
        """
        Extract specific fields based on document template.
        Never raises – returns empty StructuredOCRResult on any failure.
        """
        try:
            ocr_result = self.extract_text(image)
            items = self._parse_work_order_items(ocr_result)
            confidence_scores = self._calculate_field_confidences(items, ocr_result.words)
            return StructuredOCRResult(items=items, confidence_scores=confidence_scores,
                                       raw_text=ocr_result.text)
        except Exception as e:
            logger.error(f"extract_structured_data failed: {e}")
            return self._empty_structured_result()
    
    def _parse_work_order_items(self, ocr_result: OCRResult) -> List[Dict[str, any]]:
        """
        Parse work order items from OCR text
        
        Args:
            ocr_result: OCR result with text and words
        
        Returns:
            List of parsed items with item_number, description, unit
        """
        items = []
        lines = ocr_result.text.split('\n')
        
        # Pattern to match item numbers (e.g., "1", "1.1", "2.3.4", "A-5")
        item_number_pattern = r'^(\d+(?:\.\d+)*|\w+-\d+)'
        
        current_item = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line starts with item number
            match = re.match(item_number_pattern, line)
            if match:
                # Save previous item if exists
                if current_item:
                    items.append(current_item)
                
                # Start new item
                item_number = match.group(1)
                remaining_text = line[len(item_number):].strip()
                
                # Try to extract unit from end of line
                unit = self._extract_unit(remaining_text)
                description = remaining_text
                
                if unit:
                    # Remove unit from description
                    description = remaining_text.rsplit(unit, 1)[0].strip()
                
                current_item = {
                    'item_number': item_number,
                    'description': description,
                    'unit': unit or ''
                }
            elif current_item:
                # Continuation of description
                current_item['description'] += ' ' + line
        
        # Add last item
        if current_item:
            items.append(current_item)
        
        return items
    
    def _extract_unit(self, text: str) -> Optional[str]:
        """
        Extract unit from text (e.g., sqm, cum, kg, nos, rmt)
        
        Args:
            text: Text to extract unit from
        
        Returns:
            Unit string or None
        """
        # Common units in work orders
        units = ['sqm', 'cum', 'kg', 'nos', 'rmt', 'mt', 'ltr', 'each', 'set', 'pair']
        
        text_lower = text.lower()
        for unit in units:
            if text_lower.endswith(unit):
                return unit
            # Check with space
            if f' {unit}' in text_lower:
                return unit
        
        return None
    
    def _calculate_field_confidences(self, items: List[Dict], words: List[Word]) -> Dict[str, float]:
        """
        Calculate confidence scores for extracted fields
        
        Args:
            items: Parsed items
            words: OCR words with confidence scores
        
        Returns:
            Dictionary mapping field names to confidence scores
        """
        confidence_scores = {}
        
        for idx, item in enumerate(items):
            item_key = f"item_{idx}"
            
            # Find words that match this item's text
            item_text = f"{item['item_number']} {item['description']} {item['unit']}"
            item_words = [w for w in words if w.text in item_text]
            
            # Calculate average confidence for this item
            if item_words:
                avg_conf = sum(w.confidence for w in item_words) / len(item_words)
                confidence_scores[f"{item_key}_item_number"] = avg_conf
                confidence_scores[f"{item_key}_description"] = avg_conf
                confidence_scores[f"{item_key}_unit"] = avg_conf
            else:
                confidence_scores[f"{item_key}_item_number"] = 0.5
                confidence_scores[f"{item_key}_description"] = 0.5
                confidence_scores[f"{item_key}_unit"] = 0.5
        
        return confidence_scores
    
    def get_confidence_scores(self, result: OCRResult) -> Dict[str, float]:
        """
        Return confidence score for each extracted field
        
        Args:
            result: OCR result
        
        Returns:
            Dictionary of field confidence scores
        """
        scores = {}
        
        for idx, word in enumerate(result.words):
            scores[f"word_{idx}"] = word.confidence
        
        scores['overall'] = result.confidence
        
        return scores
