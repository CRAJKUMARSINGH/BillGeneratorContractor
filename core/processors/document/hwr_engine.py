"""
Handwriting Recognition Engine
Extracts handwritten text using Google Cloud Vision API or Azure Computer Vision.

Robustness guarantee: all public methods catch exceptions internally and
always return a valid HWR/Number/Pair result – never raise to callers.
"""
import os
import time
import logging
import traceback
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)


@dataclass
class Line:
    """Represents a line of handwritten text"""
    text: str
    confidence: float
    x: int
    y: int
    width: int
    height: int


@dataclass
class HWRResult:
    """Raw handwriting recognition output"""
    text: str
    lines: List[Line]
    confidence: float


@dataclass
class NumberRecognition:
    """Recognized numerical value"""
    value: float
    confidence: float
    x: int
    y: int


@dataclass
class ItemQuantityPair:
    """Item number and quantity pair from bill quantities page"""
    item_number: str
    quantity: float
    confidence_score: float
    x: int
    y: int


class HandwritingRecognizer:
    """Handwriting recognition engine using Cloud Vision API"""

    def __init__(self, api_key: Optional[str] = None, provider: str = "google"):
        """
        Initialize handwriting recognizer.

        Args:
            api_key: API key for cloud service (optional, can use env var)
            provider: "google" for Google Cloud Vision or "azure" for Azure Computer Vision
        """
        self.provider = provider.lower()
        self.api_key = api_key or os.getenv('GOOGLE_CLOUD_VISION_API_KEY')
        self.max_retries = 3
        self.retry_delay = 1.0

        if self.provider == "google":
            self._init_google_client()
        elif self.provider == "azure":
            self._init_azure_client()
        else:
            logger.warning(f"Unsupported provider '{provider}', falling back to mock results")
            self.client = None

    def _init_google_client(self):
        """Initialize Google Cloud Vision client"""
        try:
            from google.cloud import vision
            credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            if credentials_path and os.path.exists(credentials_path):
                self.client = vision.ImageAnnotatorClient()
            else:
                self.client = vision.ImageAnnotatorClient()
        except Exception as e:
            logger.warning(f"Could not initialize Google Cloud Vision client: {e}")
            self.client = None

    def _init_azure_client(self):
        """Initialize Azure Computer Vision client"""
        try:
            from azure.cognitiveservices.vision.computervision import ComputerVisionClient
            from msrest.authentication import CognitiveServicesCredentials
            endpoint = os.getenv('AZURE_COMPUTER_VISION_ENDPOINT')
            key = os.getenv('AZURE_COMPUTER_VISION_KEY')
            if endpoint and key:
                self.client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(key))
            else:
                logger.warning("Azure credentials not found in environment")
                self.client = None
        except Exception as e:
            logger.warning(f"Could not initialize Azure Computer Vision client: {e}")
            self.client = None

    @staticmethod
    def _safe_encode(image: np.ndarray) -> Optional[bytes]:
        """Encode numpy image to JPEG bytes. Returns None on failure."""
        try:
            import cv2
            if image is None or image.size == 0:
                return None
            # Ensure BGR uint8
            if image.dtype != np.uint8:
                image = np.clip(image, 0, 255).astype(np.uint8)
            if image.ndim == 2:
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            elif image.ndim == 3 and image.shape[2] == 4:
                image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
            success, encoded = cv2.imencode('.jpg', image)
            if not success:
                return None
            return encoded.tobytes()
        except Exception as e:
            logger.error(f"_safe_encode failed: {e}")
            return None

    def recognize_text(self, image: np.ndarray) -> HWRResult:
        """
        Extract handwritten text from image.
        Never raises – returns mock result on failure.
        """
        try:
            if self.provider == "google":
                return self._recognize_text_google(image)
            elif self.provider == "azure":
                return self._recognize_text_azure(image)
            else:
                return self._mock_hwr_result()
        except Exception as e:
            logger.error(f"recognize_text failed: {e}")
            return self._mock_hwr_result()

    def _recognize_text_google(self, image: np.ndarray) -> HWRResult:
        """Recognize text using Google Cloud Vision"""
        if self.client is None:
            return self._mock_hwr_result()

        content = self._safe_encode(image)
        if content is None:
            logger.warning("_recognize_text_google: failed to encode image")
            return self._mock_hwr_result()

        try:
            from google.cloud import vision
        except ImportError:
            return self._mock_hwr_result()

        vision_image = vision.Image(content=content)

        for attempt in range(self.max_retries):
            try:
                response = self.client.document_text_detection(image=vision_image)

                if response.error.message:
                    raise Exception(f"API Error: {response.error.message}")

                full_text = (response.full_text_annotation.text
                             if response.full_text_annotation else "")
                lines = []
                if response.full_text_annotation:
                    for page in response.full_text_annotation.pages:
                        for block in page.blocks:
                            for paragraph in block.paragraphs:
                                for word in paragraph.words:
                                    word_text = ''.join(
                                        [symbol.text for symbol in word.symbols])
                                    vertices = word.bounding_box.vertices
                                    x = min(v.x for v in vertices)
                                    y = min(v.y for v in vertices)
                                    width = max(v.x for v in vertices) - x
                                    height = max(v.y for v in vertices) - y
                                    conf = word.confidence if hasattr(word, 'confidence') else 0.8
                                    lines.append(Line(text=word_text, confidence=conf,
                                                      x=x, y=y, width=width, height=height))

                avg_confidence = (sum(l.confidence for l in lines) / len(lines)
                                  if lines else 0.0)
                return HWRResult(text=full_text, lines=lines, confidence=avg_confidence)

            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))
                    continue
                logger.error(f"Google Cloud Vision API error: {e}")
                logger.debug(traceback.format_exc())

        return self._mock_hwr_result()

    def _recognize_text_azure(self, image: np.ndarray) -> HWRResult:
        """Recognize text using Azure Computer Vision"""
        if self.client is None:
            return self._mock_hwr_result()

        content = self._safe_encode(image)
        if content is None:
            logger.warning("_recognize_text_azure: failed to encode image")
            return self._mock_hwr_result()

        from io import BytesIO
        image_stream = BytesIO(content)

        for attempt in range(self.max_retries):
            try:
                read_response = self.client.read_in_stream(image_stream, raw=True)
                operation_location = read_response.headers["Operation-Location"]
                operation_id = operation_location.split("/")[-1]

                # Poll with timeout
                waited = 0
                max_wait = 30
                while waited < max_wait:
                    result = self.client.get_read_result(operation_id)
                    if result.status.lower() not in ['notstarted', 'running']:
                        break
                    time.sleep(1)
                    waited += 1

                full_text = ""
                lines = []
                if result.status.lower() == 'succeeded':
                    for page in result.analyze_result.read_results:
                        for line_result in page.lines:
                            full_text += line_result.text + "\n"
                            bbox = line_result.bounding_box
                            x = min(bbox[0], bbox[6])
                            y = min(bbox[1], bbox[3])
                            width = max(bbox[2], bbox[4]) - x
                            height = max(bbox[5], bbox[7]) - y
                            lines.append(Line(text=line_result.text, confidence=0.85,
                                             x=int(x), y=int(y),
                                             width=int(width), height=int(height)))

                avg_confidence = 0.85 if lines else 0.0
                return HWRResult(text=full_text.strip(), lines=lines, confidence=avg_confidence)

            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))
                    image_stream.seek(0)  # reset stream for retry
                    continue
                logger.error(f"Azure Computer Vision API error: {e}")
                logger.debug(traceback.format_exc())

        return self._mock_hwr_result()

    def _mock_hwr_result(self) -> HWRResult:
        """Return safe empty result for development/testing"""
        return HWRResult(text="", lines=[], confidence=0.0)

    def recognize_numbers(self, image: np.ndarray) -> List[NumberRecognition]:
        """
        Extract numerical values with high precision.
        Never raises – returns empty list on failure.
        """
        try:
            hwr_result = self.recognize_text(image)
            numbers = []
            for line in hwr_result.lines:
                for match in re.findall(r'\d+\.?\d*', line.text):
                    try:
                        numbers.append(NumberRecognition(
                            value=float(match),
                            confidence=line.confidence,
                            x=line.x, y=line.y
                        ))
                    except ValueError:
                        continue
            return numbers
        except Exception as e:
            logger.error(f"recognize_numbers failed: {e}")
            return []

    def recognize_item_quantity_pairs(self, image: np.ndarray) -> List[ItemQuantityPair]:
        """
        Extract item number and quantity pairs from structured layout.
        Never raises – returns empty list on failure.
        """
        try:
            hwr_result = self.recognize_text(image)
            pairs = []
            for line in hwr_result.lines:
                text = line.text.strip()
                match = re.match(r'^(\d+(?:\.\d+)*|\w+-\d+)\s+(\d+\.?\d*)$', text)
                if match:
                    try:
                        pairs.append(ItemQuantityPair(
                            item_number=match.group(1),
                            quantity=float(match.group(2)),
                            confidence_score=line.confidence,
                            x=line.x, y=line.y
                        ))
                    except ValueError:
                        continue
            return pairs
        except Exception as e:
            logger.error(f"recognize_item_quantity_pairs failed: {e}")
            return []
