"""
Handwriting Recognition Engine
Extracts handwritten text using Google Cloud Vision API or Azure Computer Vision
"""
import os
import time
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import re


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
        Initialize handwriting recognizer
        
        Args:
            api_key: API key for cloud service (optional, can use env var)
            provider: "google" for Google Cloud Vision or "azure" for Azure Computer Vision
        """
        self.provider = provider.lower()
        self.api_key = api_key or os.getenv('GOOGLE_CLOUD_VISION_API_KEY')
        
        # Initialize client based on provider
        if self.provider == "google":
            self._init_google_client()
        elif self.provider == "azure":
            self._init_azure_client()
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
    
    def _init_google_client(self):
        """Initialize Google Cloud Vision client"""
        try:
            from google.cloud import vision
            
            # Check for credentials
            credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            if credentials_path and os.path.exists(credentials_path):
                self.client = vision.ImageAnnotatorClient()
            else:
                # Try to initialize without explicit credentials (uses default)
                self.client = vision.ImageAnnotatorClient()
        except Exception as e:
            print(f"Warning: Could not initialize Google Cloud Vision client: {e}")
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
                print("Warning: Azure credentials not found in environment")
                self.client = None
        except Exception as e:
            print(f"Warning: Could not initialize Azure Computer Vision client: {e}")
            self.client = None
    
    def recognize_text(self, image: np.ndarray) -> HWRResult:
        """
        Extract handwritten text from image
        
        Args:
            image: Input image as numpy array
        
        Returns:
            HWRResult with recognized text and confidence
        """
        if self.provider == "google":
            return self._recognize_text_google(image)
        elif self.provider == "azure":
            return self._recognize_text_azure(image)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _recognize_text_google(self, image: np.ndarray) -> HWRResult:
        """Recognize text using Google Cloud Vision"""
        if self.client is None:
            # Fallback: return mock result for development
            return self._mock_hwr_result()
        
        from google.cloud import vision
        import cv2
        
        # Convert numpy array to bytes
        success, encoded_image = cv2.imencode('.jpg', image)
        if not success:
            raise ValueError("Failed to encode image")
        
        content = encoded_image.tobytes()
        
        # Create vision image
        vision_image = vision.Image(content=content)
        
        # Perform handwriting recognition with retry
        for attempt in range(self.max_retries):
            try:
                response = self.client.document_text_detection(image=vision_image)
                
                if response.error.message:
                    raise Exception(f"API Error: {response.error.message}")
                
                # Extract text and lines
                full_text = response.full_text_annotation.text if response.full_text_annotation else ""
                
                lines = []
                if response.full_text_annotation:
                    for page in response.full_text_annotation.pages:
                        for block in page.blocks:
                            for paragraph in block.paragraphs:
                                for word in paragraph.words:
                                    word_text = ''.join([symbol.text for symbol in word.symbols])
                                    
                                    # Get bounding box
                                    vertices = word.bounding_box.vertices
                                    x = min(v.x for v in vertices)
                                    y = min(v.y for v in vertices)
                                    width = max(v.x for v in vertices) - x
                                    height = max(v.y for v in vertices) - y
                                    
                                    # Get confidence
                                    confidence = word.confidence if hasattr(word, 'confidence') else 0.8
                                    
                                    line = Line(
                                        text=word_text,
                                        confidence=confidence,
                                        x=x, y=y,
                                        width=width,
                                        height=height
                                    )
                                    lines.append(line)
                
                # Calculate average confidence
                avg_confidence = sum(l.confidence for l in lines) / len(lines) if lines else 0.0
                
                return HWRResult(
                    text=full_text,
                    lines=lines,
                    confidence=avg_confidence
                )
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                    continue
                else:
                    print(f"Error in Google Cloud Vision API: {e}")
                    return self._mock_hwr_result()
        
        return self._mock_hwr_result()
    
    def _recognize_text_azure(self, image: np.ndarray) -> HWRResult:
        """Recognize text using Azure Computer Vision"""
        if self.client is None:
            return self._mock_hwr_result()
        
        import cv2
        from io import BytesIO
        
        # Convert numpy array to bytes
        success, encoded_image = cv2.imencode('.jpg', image)
        if not success:
            raise ValueError("Failed to encode image")
        
        image_stream = BytesIO(encoded_image.tobytes())
        
        # Perform handwriting recognition with retry
        for attempt in range(self.max_retries):
            try:
                # Call Azure API
                read_response = self.client.read_in_stream(image_stream, raw=True)
                operation_location = read_response.headers["Operation-Location"]
                operation_id = operation_location.split("/")[-1]
                
                # Wait for result
                while True:
                    result = self.client.get_read_result(operation_id)
                    if result.status.lower() not in ['notstarted', 'running']:
                        break
                    time.sleep(1)
                
                # Extract text and lines
                full_text = ""
                lines = []
                
                if result.status.lower() == 'succeeded':
                    for page in result.analyze_result.read_results:
                        for line_result in page.lines:
                            full_text += line_result.text + "\n"
                            
                            # Get bounding box
                            bbox = line_result.bounding_box
                            x = min(bbox[0], bbox[6])
                            y = min(bbox[1], bbox[3])
                            width = max(bbox[2], bbox[4]) - x
                            height = max(bbox[5], bbox[7]) - y
                            
                            line = Line(
                                text=line_result.text,
                                confidence=0.85,  # Azure doesn't provide word-level confidence
                                x=int(x), y=int(y),
                                width=int(width),
                                height=int(height)
                            )
                            lines.append(line)
                
                avg_confidence = 0.85 if lines else 0.0
                
                return HWRResult(
                    text=full_text.strip(),
                    lines=lines,
                    confidence=avg_confidence
                )
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))
                    continue
                else:
                    print(f"Error in Azure Computer Vision API: {e}")
                    return self._mock_hwr_result()
        
        return self._mock_hwr_result()
    
    def _mock_hwr_result(self) -> HWRResult:
        """Return mock result for development/testing"""
        return HWRResult(
            text="Mock handwriting recognition result",
            lines=[],
            confidence=0.0
        )
    
    def recognize_numbers(self, image: np.ndarray) -> List[NumberRecognition]:
        """
        Extract numerical values with high precision
        
        Args:
            image: Input image
        
        Returns:
            List of recognized numbers with positions
        """
        hwr_result = self.recognize_text(image)
        
        numbers = []
        for line in hwr_result.lines:
            # Extract numbers from text
            number_matches = re.findall(r'\d+\.?\d*', line.text)
            
            for match in number_matches:
                try:
                    value = float(match)
                    number = NumberRecognition(
                        value=value,
                        confidence=line.confidence,
                        x=line.x,
                        y=line.y
                    )
                    numbers.append(number)
                except ValueError:
                    continue
        
        return numbers
    
    def recognize_item_quantity_pairs(self, image: np.ndarray) -> List[ItemQuantityPair]:
        """
        Extract item number and quantity pairs from structured layout
        
        Args:
            image: Input image of bill quantities page
        
        Returns:
            List of item-quantity pairs
        """
        hwr_result = self.recognize_text(image)
        
        pairs = []
        
        # Parse lines to find item number and quantity patterns
        for line in hwr_result.lines:
            text = line.text.strip()
            
            # Pattern: item number followed by quantity
            # Examples: "1.1 50", "2.3 100.5", "A-5 25"
            match = re.match(r'^(\d+(?:\.\d+)*|\w+-\d+)\s+(\d+\.?\d*)$', text)
            
            if match:
                item_number = match.group(1)
                quantity = float(match.group(2))
                
                pair = ItemQuantityPair(
                    item_number=item_number,
                    quantity=quantity,
                    confidence_score=line.confidence,
                    x=line.x,
                    y=line.y
                )
                pairs.append(pair)
        
        return pairs
