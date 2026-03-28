#!/usr/bin/env python3
"""
Image Preprocessor - Week 5 Day 2-3
Image enhancement and correction
"""
import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, Optional


class ImagePreprocessor:
    """Enhances and corrects images for better OCR"""
    
    def __init__(self):
        pass
    
    def deskew(self, image: np.ndarray, angle: float) -> np.ndarray:
        """Correct image skew"""
        if abs(angle) < 0.5:
            return image
        
        height, width = image.shape[:2]
        center = (width // 2, height // 2)
        
        # Rotation matrix
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # Rotate image
        rotated = cv2.warpAffine(
            image, M, (width, height),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )
        
        return rotated
    
    def enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """Enhance image contrast using CLAHE"""
        # Convert to LAB color space
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE to L channel
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        # Merge and convert back
        lab = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        return enhanced
    
    def sharpen(self, image: np.ndarray) -> np.ndarray:
        """Sharpen image"""
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]])
        sharpened = cv2.filter2D(image, -1, kernel)
        return sharpened
    
    def denoise(self, image: np.ndarray) -> np.ndarray:
        """Remove noise"""
        denoised = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
        return denoised
    
    def adjust_brightness(self, image: np.ndarray, target_mean: float = 127.0) -> np.ndarray:
        """Adjust brightness to target"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        current_mean = gray.mean()
        
        if abs(current_mean - target_mean) < 10:
            return image
        
        # Calculate adjustment
        adjustment = target_mean - current_mean
        
        # Apply adjustment
        adjusted = cv2.convertScaleAbs(image, alpha=1.0, beta=adjustment)
        return adjusted
    
    def preprocess(
        self,
        image_path: str,
        deskew_angle: Optional[float] = None,
        enhance: bool = True
    ) -> np.ndarray:
        """Complete preprocessing pipeline"""
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Cannot load image: {image_path}")
        
        # Deskew if needed
        if deskew_angle and abs(deskew_angle) > 0.5:
            image = self.deskew(image, deskew_angle)
        
        if enhance:
            # Enhance contrast
            image = self.enhance_contrast(image)
            
            # Adjust brightness
            image = self.adjust_brightness(image)
            
            # Sharpen
            image = self.sharpen(image)
        
        return image


if __name__ == '__main__':
    print("\n" + "="*80)
    print("IMAGE PREPROCESSOR TEST - WEEK 5 DAY 2-3")
    print("="*80)
    
    preprocessor = ImagePreprocessor()
    
    test_folder = Path("INPUT_WORK_ORDER_IMAGES_TEXT")
    if test_folder.exists():
        images = list(test_folder.glob("*.jpg"))[:1]
        
        if images:
            image_path = images[0]
            print(f"\nTesting with: {image_path.name}")
            
            # Load original
            original = cv2.imread(str(image_path))
            print(f"Original size: {original.shape[1]}x{original.shape[0]}")
            
            # Preprocess
            enhanced = preprocessor.preprocess(str(image_path), enhance=True)
            print(f"Enhanced size: {enhanced.shape[1]}x{enhanced.shape[0]}")
            
            print("\nPreprocessing complete!")
    
    print("\n" + "="*80)
    print("IMAGE PREPROCESSOR: OPERATIONAL")
    print("="*80 + "\n")
