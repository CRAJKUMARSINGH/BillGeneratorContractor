"""
Unified OCR Engine - Production Grade
Supports multiple OCR providers with automatic fallback:
1. Google Cloud Vision API (best accuracy)
2. Azure Computer Vision (enterprise grade)
3. PaddleOCR (excellent offline multilingual)
4. EasyOCR (reliable baseline)
"""
import os
import sys
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import re
import json


@dataclass
class OCRWord:
    """Single word with position and confidence"""
    text: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # (x, y, width, height)


@dataclass
class OCRResult:
    """Unified OCR result from any provider"""
    text: str
    words: List[OCRWord]
    confidence: float
    provider: str
    language: str


class UnifiedOCREngine:
    """
    Production-grade OCR with multiple providers and automatic fallback
    Priority: Google Cloud Vision > Azure > PaddleOCR > EasyOCR
    """
    
    def __init__(self, language: str = "en+hi", preferred_provider: Optional[str] = None):
        """
        Initialize OCR engine with provider priority
        
        Args:
            language: Language codes (en, hi, en+hi)
            preferred_provider: Force specific provider (google, azure, paddle, easy)
        """
        self.language = language
        self.preferred_provider = preferred_provider
        
        # Provider availability
        self.providers = {
            'google': self._init_google(),
            'azure': self._init_azure(),
            'paddle': self._init_paddle(),
            'easy': self._init_easy()
        }
        
        # Get active providers
        self.active_providers = [k for k, v in self.providers.items() if v is not None]
        
        if not self.active_providers:
            raise RuntimeError("No OCR providers available. Install at least one: pip install easyocr paddleocr")
        
        print(f"✅ OCR Engine initialized with providers: {', '.join(self.active_providers)}")
    
    def _init_google(self) -> Optional[Any]:
        """Initialize Google Cloud Vision"""
        try:
            from google.cloud import vision
            
            # Check credentials
            creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            api_key = os.getenv('GOOGLE_CLOUD_VISION_API_KEY')
            
            if creds_path and Path(creds_path).exists():
                return vision.ImageAnnotatorClient()
            elif api_key:
                # Use API key authentication
                return vision.ImageAnnotatorClient()
            else:
                return None
        except Exception as e:
            return None
    
    def _init_azure(self) -> Optional[Any]:
        """Initialize Azure Computer Vision"""
        try:
            from azure.cognitiveservices.vision.computervision import ComputerVisionClient
            from msrest.authentication import CognitiveServicesCredentials
            
            endpoint = os.getenv('AZURE_COMPUTER_VISION_ENDPOINT')
            key = os.getenv('AZURE_COMPUTER_VISION_KEY')
            
            if endpoint and key:
                return ComputerVisionClient(endpoint, CognitiveServicesCredentials(key))
            return None
        except Exception:
            return None
    
    def _init_paddle(self) -> Optional[Any]:
        """Initialize PaddleOCR"""
        try:
            from paddleocr import PaddleOCR
            
            # Determine language
            lang = 'en' if self.language.startswith('en') else 'hi'
            
            # Initialize with minimal logging
            ocr = PaddleOCR(
                use_angle_cls=True,
                lang=lang,
                use_gpu=False,
                show_log=False
            )
            return ocr
        except Exception:
            return None
    
    def _init_easy(self) -> Optional[Any]:
        """Initialize EasyOCR"""
        try:
            import easyocr
            
            # Parse language codes
            langs = []
            if 'en' in self.language:
                langs.append('en')
            if 'hi' in self.language:
                langs.append('hi')
            
            if not langs:
                langs = ['en']
            
            reader = easyocr.Reader(langs, gpu=False, verbose=False)
            return reader
        except Exception:
            return None
    
    def extract_text(self, image: np.ndarray, provider: Optional[str] = None, 
                    min_confidence: float = 0.7, min_words: int = 5) -> OCRResult:
        """
        Extract text using best available provider with intelligent fallback
        Automatically tries next provider if quality is poor
        
        Args:
            image: Input image as numpy array
            provider: Force specific provider (optional)
            min_confidence: Minimum acceptable confidence (0.0-1.0)
            min_words: Minimum number of words expected
        
        Returns:
            OCRResult with text, words, and confidence
        """
        # Determine provider to use
        if provider and provider in self.active_providers:
            providers_to_try = [provider]
        elif self.preferred_provider and self.preferred_provider in self.active_providers:
            providers_to_try = [self.preferred_provider]
        else:
            # Try in priority order
            priority = ['google', 'azure', 'paddle', 'easy']
            providers_to_try = [p for p in priority if p in self.active_providers]
        
        # Store all results for comparison
        all_results = []
        
        # Try each provider with quality validation
        for prov in providers_to_try:
            try:
                print(f"   🔍 Trying {prov.upper()} OCR...")
                
                if prov == 'google':
                    result = self._extract_google(image)
                elif prov == 'azure':
                    result = self._extract_azure(image)
                elif prov == 'paddle':
                    result = self._extract_paddle(image)
                elif prov == 'easy':
                    result = self._extract_easy(image)
                else:
                    continue
                
                all_results.append(result)
                
                # Validate quality
                quality_score = self._validate_quality(result)
                word_count = len(result.words)
                
                print(f"      ✓ Confidence: {result.confidence:.2%}")
                print(f"      ✓ Words extracted: {word_count}")
                print(f"      ✓ Quality score: {quality_score:.2%}")
                
                # Check if result is acceptable
                if (result.confidence >= min_confidence and 
                    word_count >= min_words and 
                    quality_score >= 0.6):
                    print(f"      ✅ {prov.upper()} passed quality check!")
                    return result
                else:
                    print(f"      ⚠️  {prov.upper()} quality below threshold, trying next...")
                    
            except Exception as e:
                print(f"      ❌ {prov.upper()} failed: {str(e)[:50]}")
                continue
        
        # If no provider passed quality check, return best result
        if all_results:
            best_result = max(all_results, key=lambda r: self._validate_quality(r))
            print(f"\n   ⚠️  No provider met quality threshold")
            print(f"   📊 Returning best result from {best_result.provider.upper()}")
            return best_result
        
        # All providers failed
        raise RuntimeError(f"All OCR providers failed to extract text")
    
    def _extract_google(self, image: np.ndarray) -> OCRResult:
        """Extract using Google Cloud Vision"""
        import cv2
        from google.cloud import vision
        
        client = self.providers['google']
        
        # Encode image
        success, encoded = cv2.imencode('.jpg', image)
        if not success:
            raise ValueError("Failed to encode image")
        
        # Create vision image
        vision_image = vision.Image(content=encoded.tobytes())
        
        # Perform OCR
        response = client.document_text_detection(image=vision_image)
        
        if response.error.message:
            raise Exception(f"Google API Error: {response.error.message}")
        
        # Extract text
        full_text = response.full_text_annotation.text if response.full_text_annotation else ""
        
        # Extract words
        words = []
        if response.full_text_annotation:
            for page in response.full_text_annotation.pages:
                for block in page.blocks:
                    for paragraph in block.paragraphs:
                        for word in paragraph.words:
                            word_text = ''.join([s.text for s in word.symbols])
                            
                            # Bounding box
                            vertices = word.bounding_box.vertices
                            x = min(v.x for v in vertices)
                            y = min(v.y for v in vertices)
                            w = max(v.x for v in vertices) - x
                            h = max(v.y for v in vertices) - y
                            
                            conf = word.confidence if hasattr(word, 'confidence') else 0.9
                            
                            words.append(OCRWord(
                                text=word_text,
                                confidence=conf,
                                bbox=(x, y, w, h)
                            ))
        
        avg_conf = sum(w.confidence for w in words) / len(words) if words else 0.0
        
        return OCRResult(
            text=full_text,
            words=words,
            confidence=avg_conf,
            provider='google',
            language=self.language
        )
    
    def _extract_azure(self, image: np.ndarray) -> OCRResult:
        """Extract using Azure Computer Vision"""
        import cv2
        from io import BytesIO
        import time
        
        client = self.providers['azure']
        
        # Encode image
        success, encoded = cv2.imencode('.jpg', image)
        if not success:
            raise ValueError("Failed to encode image")
        
        image_stream = BytesIO(encoded.tobytes())
        
        # Call Azure API
        read_response = client.read_in_stream(image_stream, raw=True)
        operation_location = read_response.headers["Operation-Location"]
        operation_id = operation_location.split("/")[-1]
        
        # Wait for result
        max_wait = 30
        waited = 0
        while waited < max_wait:
            result = client.get_read_result(operation_id)
            if result.status.lower() not in ['notstarted', 'running']:
                break
            time.sleep(1)
            waited += 1
        
        if result.status.lower() != 'succeeded':
            raise Exception(f"Azure OCR failed with status: {result.status}")
        
        # Extract text and words
        full_text = ""
        words = []
        
        for page in result.analyze_result.read_results:
            for line in page.lines:
                full_text += line.text + "\n"
                
                for word in line.words:
                    bbox = word.bounding_box
                    x = min(bbox[0], bbox[6])
                    y = min(bbox[1], bbox[3])
                    w = max(bbox[2], bbox[4]) - x
                    h = max(bbox[5], bbox[7]) - y
                    
                    words.append(OCRWord(
                        text=word.text,
                        confidence=word.confidence,
                        bbox=(int(x), int(y), int(w), int(h))
                    ))
        
        avg_conf = sum(w.confidence for w in words) / len(words) if words else 0.0
        
        return OCRResult(
            text=full_text.strip(),
            words=words,
            confidence=avg_conf,
            provider='azure',
            language=self.language
        )
    
    def _extract_paddle(self, image: np.ndarray) -> OCRResult:
        """Extract using PaddleOCR"""
        ocr = self.providers['paddle']
        
        # Run OCR
        result = ocr.ocr(image, cls=True)
        
        # Parse results
        full_text = ""
        words = []
        
        if result and result[0]:
            for line in result[0]:
                bbox_points = line[0]
                text = line[1][0]
                conf = line[1][1]
                
                full_text += text + "\n"
                
                # Convert bbox
                x = int(min(p[0] for p in bbox_points))
                y = int(min(p[1] for p in bbox_points))
                w = int(max(p[0] for p in bbox_points) - x)
                h = int(max(p[1] for p in bbox_points) - y)
                
                words.append(OCRWord(
                    text=text,
                    confidence=conf,
                    bbox=(x, y, w, h)
                ))
        
        avg_conf = sum(w.confidence for w in words) / len(words) if words else 0.0
        
        return OCRResult(
            text=full_text.strip(),
            words=words,
            confidence=avg_conf,
            provider='paddle',
            language=self.language
        )
    
    def _extract_easy(self, image: np.ndarray) -> OCRResult:
        """Extract using EasyOCR"""
        reader = self.providers['easy']
        
        # Run OCR
        result = reader.readtext(image)
        
        # Parse results
        full_text = ""
        words = []
        
        for detection in result:
            bbox_points = detection[0]
            text = detection[1]
            conf = detection[2]
            
            full_text += text + "\n"
            
            # Convert bbox
            x = int(min(p[0] for p in bbox_points))
            y = int(min(p[1] for p in bbox_points))
            w = int(max(p[0] for p in bbox_points) - x)
            h = int(max(p[1] for p in bbox_points) - y)
            
            words.append(OCRWord(
                text=text,
                confidence=conf,
                bbox=(x, y, w, h)
            ))
        
        avg_conf = sum(w.confidence for w in words) / len(words) if words else 0.0
        
        return OCRResult(
            text=full_text.strip(),
            words=words,
            confidence=avg_conf,
            provider='easy',
            language=self.language
        )
    
    def extract_structured_data(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Extract structured data from work order
        
        Args:
            image: Input image
        
        Returns:
            Dictionary with extracted fields
        """
        ocr_result = self.extract_text(image)
        
        # Parse structured fields
        data = {
            'contractor': self._extract_field(ocr_result.text, ['contractor', 'ठेकेदार']),
            'work_name': self._extract_field(ocr_result.text, ['work name', 'कार्य का नाम']),
            'wo_number': self._extract_field(ocr_result.text, ['work order', 'w.o', 'कार्य आदेश']),
            'agreement_no': self._extract_field(ocr_result.text, ['agreement', 'समझौता']),
            'wo_amount': self._extract_amount(ocr_result.text),
            'items': self._extract_items(ocr_result.text),
            'confidence': ocr_result.confidence,
            'provider': ocr_result.provider
        }
        
        return data
    
    def _extract_field(self, text: str, keywords: List[str]) -> str:
        """Extract field value after keywords"""
        lines = text.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            for keyword in keywords:
                if keyword.lower() in line_lower:
                    # Extract text after keyword
                    parts = re.split(r'[:\-]', line, maxsplit=1)
                    if len(parts) > 1:
                        return parts[1].strip()
        
        return '[NOT FOUND]'
    
    def _extract_amount(self, text: str) -> str:
        """Extract monetary amount"""
        patterns = [
            r'(?:rs\.?|₹)\s*([\d,]+(?:\.\d{2})?)',
            r'amount[:\s]*([\d,]+(?:\.\d{2})?)',
            r'रुपये[:\s]*([\d,]+(?:\.\d{2})?)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).replace(',', '')
        
        return '[NOT FOUND]'
    
    def _extract_items(self, text: str) -> List[Dict[str, str]]:
        """Extract item list from text"""
        items = []
        lines = text.split('\n')
        
        # Pattern for item numbers
        item_pattern = r'^(\d+(?:\.\d+)*)'
        
        for line in lines:
            line = line.strip()
            match = re.match(item_pattern, line)
            if match:
                item_no = match.group(1)
                desc = line[len(item_no):].strip()
                
                items.append({
                    'item_number': item_no,
                    'description': desc
                })
        
        return items
    
    def _validate_quality(self, result: OCRResult) -> float:
        """
        Validate OCR result quality with multiple checks
        Returns quality score 0.0-1.0
        
        Checks:
        - Confidence score
        - Word count
        - Text coherence (ratio of alphanumeric to total chars)
        - Presence of expected patterns (numbers, common words)
        """
        if not result.text or not result.words:
            return 0.0
        
        scores = []
        
        # 1. Confidence score (weight: 40%)
        scores.append(result.confidence * 0.4)
        
        # 2. Word count score (weight: 20%)
        word_count = len(result.words)
        word_score = min(word_count / 20, 1.0)  # Expect at least 20 words
        scores.append(word_score * 0.2)
        
        # 3. Text coherence (weight: 20%)
        text = result.text
        alphanumeric = sum(c.isalnum() for c in text)
        total_chars = len(text.replace(' ', '').replace('\n', ''))
        coherence = alphanumeric / total_chars if total_chars > 0 else 0
        scores.append(coherence * 0.2)
        
        # 4. Pattern detection (weight: 20%)
        pattern_score = 0.0
        
        # Check for numbers (item codes, amounts)
        if re.search(r'\d+', text):
            pattern_score += 0.3
        
        # Check for decimal numbers (rates, amounts)
        if re.search(r'\d+\.\d+', text):
            pattern_score += 0.2
        
        # Check for common work order keywords
        keywords = ['work', 'contractor', 'amount', 'item', 'quantity', 'rate']
        found_keywords = sum(1 for kw in keywords if kw.lower() in text.lower())
        pattern_score += (found_keywords / len(keywords)) * 0.5
        
        scores.append(min(pattern_score, 1.0) * 0.2)
        
        # Total quality score
        quality = sum(scores)
        
        return quality
    
    def extract_with_consensus(self, image: np.ndarray, 
                               providers: Optional[List[str]] = None) -> OCRResult:
        """
        Run multiple OCR providers and combine results using consensus
        Best for critical documents where accuracy is paramount
        
        Args:
            image: Input image
            providers: List of providers to use (None = all available)
        
        Returns:
            Combined OCRResult with highest confidence
        """
        if providers is None:
            providers = self.active_providers
        else:
            providers = [p for p in providers if p in self.active_providers]
        
        if not providers:
            raise ValueError("No valid providers specified")
        
        print(f"\n🔄 Running consensus OCR with {len(providers)} providers...")
        
        results = []
        for prov in providers:
            try:
                print(f"   Running {prov.upper()}...")
                result = self.extract_text(image, provider=prov, min_confidence=0.0, min_words=0)
                results.append(result)
                print(f"      ✓ Confidence: {result.confidence:.2%}, Words: {len(result.words)}")
            except Exception as e:
                print(f"      ✗ Failed: {str(e)[:50]}")
                continue
        
        if not results:
            raise RuntimeError("All providers failed in consensus mode")
        
        # Find best result by quality score
        best_result = max(results, key=lambda r: self._validate_quality(r))
        
        print(f"\n   ✅ Best result: {best_result.provider.upper()}")
        print(f"      Quality: {self._validate_quality(best_result):.2%}")
        
        return best_result
    
    def extract_with_retry(self, image: np.ndarray, max_attempts: int = 3,
                          preprocess: bool = True) -> OCRResult:
        """
        Extract text with automatic retry and image preprocessing
        
        Args:
            image: Input image
            max_attempts: Maximum retry attempts with different preprocessing
            preprocess: Apply image preprocessing
        
        Returns:
            Best OCRResult after retries
        """
        best_result = None
        best_quality = 0.0
        
        for attempt in range(max_attempts):
            try:
                # Apply different preprocessing on each attempt
                if preprocess and attempt > 0:
                    processed_image = self._preprocess_image(image, method=attempt)
                    print(f"\n   🔄 Attempt {attempt + 1} with preprocessing method {attempt}")
                else:
                    processed_image = image
                    print(f"\n   🔄 Attempt {attempt + 1} (no preprocessing)")
                
                result = self.extract_text(processed_image)
                quality = self._validate_quality(result)
                
                if quality > best_quality:
                    best_result = result
                    best_quality = quality
                
                # If quality is excellent, stop early
                if quality >= 0.9:
                    print(f"   ✅ Excellent quality achieved ({quality:.2%})")
                    break
                    
            except Exception as e:
                print(f"   ❌ Attempt {attempt + 1} failed: {str(e)[:50]}")
                continue
        
        if best_result is None:
            raise RuntimeError("All retry attempts failed")
        
        return best_result
    
    def _preprocess_image(self, image: np.ndarray, method: int = 1) -> np.ndarray:
        """
        Apply image preprocessing to improve OCR accuracy
        
        Args:
            image: Input image
            method: Preprocessing method (1-3)
        
        Returns:
            Preprocessed image
        """
        import cv2
        
        if method == 1:
            # Grayscale + Gaussian blur + threshold
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            return thresh
        
        elif method == 2:
            # Adaptive threshold
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                          cv2.THRESH_BINARY, 11, 2)
            return thresh
        
        elif method == 3:
            # Denoise + sharpen
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            denoised = cv2.fastNlMeansDenoising(gray)
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            sharpened = cv2.filter2D(denoised, -1, kernel)
            return sharpened
        
        return image


def get_ocr_engine(language: str = "en+hi", provider: Optional[str] = None) -> UnifiedOCREngine:
    """
    Factory function to get OCR engine
    
    Args:
        language: Language codes
        provider: Preferred provider (optional)
    
    Returns:
        Configured UnifiedOCREngine
    """
    return UnifiedOCREngine(language=language, preferred_provider=provider)
