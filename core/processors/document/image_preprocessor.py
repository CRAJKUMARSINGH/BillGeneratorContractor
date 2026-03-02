"""
Image Preprocessor
Enhances image quality before OCR/HWR processing
"""
import cv2
import numpy as np
from typing import Tuple, Optional
from PIL import Image


class ImagePreprocessor:
    """Preprocesses images for optimal OCR and handwriting recognition"""
    
    def __init__(self, enable_rotation_correction: bool = True,
                 enable_enhancement: bool = True,
                 enable_noise_removal: bool = True):
        """
        Initialize image preprocessor
        
        Args:
            enable_rotation_correction: Enable automatic rotation detection and correction
            enable_enhancement: Enable contrast enhancement
            enable_noise_removal: Enable noise reduction
        """
        self.enable_rotation_correction = enable_rotation_correction
        self.enable_enhancement = enable_enhancement
        self.enable_noise_removal = enable_noise_removal
    
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        Apply full preprocessing pipeline
        
        Args:
            image: Input image as numpy array (BGR format from cv2)
        
        Returns:
            Preprocessed image
        """
        processed = image.copy()
        
        # Step 1: Rotation correction
        if self.enable_rotation_correction:
            processed = self.correct_rotation(processed)
        
        # Step 2: Contrast enhancement
        if self.enable_enhancement:
            processed = self.enhance_contrast(processed)
        
        # Step 3: Noise removal
        if self.enable_noise_removal:
            processed = self.remove_noise(processed)
        
        # Step 4: Binarization for OCR
        processed = self.binarize(processed)
        
        return processed
    
    def correct_rotation(self, image: np.ndarray) -> np.ndarray:
        """
        Detect and correct image rotation using Hough line transform
        
        Args:
            image: Input image
        
        Returns:
            Rotation-corrected image
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Detect lines using Hough transform
        lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)
        
        if lines is None:
            return image
        
        # Calculate angles
        angles = []
        for rho, theta in lines[:, 0]:
            angle = np.degrees(theta) - 90
            angles.append(angle)
        
        if not angles:
            return image
        
        # Find median angle
        median_angle = np.median(angles)
        
        # Only correct if angle is significant (> 0.5 degrees)
        if abs(median_angle) > 0.5:
            # Get image center
            (h, w) = image.shape[:2]
            center = (w // 2, h // 2)
            
            # Rotate image
            M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
            rotated = cv2.warpAffine(image, M, (w, h),
                                    flags=cv2.INTER_CUBIC,
                                    borderMode=cv2.BORDER_REPLICATE)
            return rotated
        
        return image
    
    def enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """
        Improve text visibility through adaptive contrast adjustment
        
        Args:
            image: Input image
        
        Returns:
            Contrast-enhanced image
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Convert back to BGR if original was color
        if len(image.shape) == 3:
            enhanced = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
        
        return enhanced
    
    def remove_noise(self, image: np.ndarray) -> np.ndarray:
        """
        Apply noise reduction filters using morphological operations
        
        Args:
            image: Input image
        
        Returns:
            Denoised image
        """
        # Apply bilateral filter to reduce noise while preserving edges
        denoised = cv2.bilateralFilter(image, 9, 75, 75)
        
        # Apply morphological opening to remove small noise
        kernel = np.ones((2, 2), np.uint8)
        denoised = cv2.morphologyEx(denoised, cv2.MORPH_OPEN, kernel)
        
        return denoised
    
    def binarize(self, image: np.ndarray) -> np.ndarray:
        """
        Convert to black and white for optimal OCR using adaptive thresholding
        
        Args:
            image: Input image
        
        Returns:
            Binarized image
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Apply adaptive thresholding
        binary = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11, 2
        )
        
        return binary
    
    def load_image(self, image_path: str) -> np.ndarray:
        """
        Load image from file path
        
        Args:
            image_path: Path to image file
        
        Returns:
            Image as numpy array
        """
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Failed to load image from {image_path}")
        return image
    
    def save_image(self, image: np.ndarray, output_path: str) -> None:
        """
        Save preprocessed image to file
        
        Args:
            image: Image to save
            output_path: Destination file path
        """
        cv2.imwrite(output_path, image)
