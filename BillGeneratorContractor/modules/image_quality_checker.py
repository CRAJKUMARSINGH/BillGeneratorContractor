#!/usr/bin/env python3
"""
Image Quality Checker - Week 5 Day 1
Comprehensive image quality assessment
"""
import cv2
import numpy as np
from dataclasses import dataclass
from typing import Tuple, Optional
from pathlib import Path


@dataclass
class QualityScore:
    """Image quality assessment result"""
    overall: float  # 0.0 to 1.0
    blur_score: float
    brightness_score: float
    contrast_score: float
    resolution_score: float
    skew_score: float
    
    width: int
    height: int
    blur_variance: float
    brightness_mean: float
    contrast_std: float
    skew_angle: float
    
    @property
    def level(self) -> str:
        """Get quality level"""
        if self.overall >= 0.9:
            return "EXCELLENT"
        elif self.overall >= 0.7:
            return "GOOD"
        elif self.overall >= 0.5:
            return "ACCEPTABLE"
        else:
            return "POOR"
    
    @property
    def action(self) -> str:
        """Get recommended action"""
        if self.overall >= 0.9:
            return "PROCESS_IMMEDIATELY"
        elif self.overall >= 0.7:
            return "PROCESS_WITH_CONFIDENCE"
        elif self.overall >= 0.5:
            return "ENHANCE_THEN_PROCESS"
        else:
            return "REJECT_OR_MANUAL_REVIEW"
    
    @property
    def issues(self) -> list:
        """Get list of quality issues"""
        issues = []
        if self.blur_score < 0.5:
            issues.append(f"Blurry (variance: {self.blur_variance:.1f})")
        if self.brightness_score < 0.5:
            issues.append(f"Poor brightness (mean: {self.brightness_mean:.1f})")
        if self.contrast_score < 0.5:
            issues.append(f"Low contrast (std: {self.contrast_std:.1f})")
        if self.resolution_score < 0.5:
            issues.append(f"Low resolution ({self.width}x{self.height})")
        if self.skew_score < 0.5:
            issues.append(f"Skewed (angle: {self.skew_angle:.1f}°)")
        return issues


class ImageQualityChecker:
    """Checks image quality for OCR suitability"""
    
    def __init__(
        self,
        min_width: int = 800,
        min_height: int = 600,
        blur_threshold: float = 100.0,
        min_brightness: float = 50.0,
        max_brightness: float = 200.0,
        min_contrast: float = 30.0,
        max_skew_angle: float = 5.0
    ):
        self.min_width = min_width
        self.min_height = min_height
        self.blur_threshold = blur_threshold
        self.min_brightness = min_brightness
        self.max_brightness = max_brightness
        self.min_contrast = min_contrast
        self.max_skew_angle = max_skew_angle
    
    def check_quality(self, image_path: str) -> QualityScore:
        """Comprehensive quality check"""
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Cannot load image: {image_path}")
        
        # Get dimensions
        height, width = image.shape[:2]
        
        # Convert to grayscale for analysis
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Check blur
        blur_variance = self._check_blur(gray)
        blur_score = self._score_blur(blur_variance)
        
        # Check brightness
        brightness_mean = self._check_brightness(gray)
        brightness_score = self._score_brightness(brightness_mean)
        
        # Check contrast
        contrast_std = self._check_contrast(gray)
        contrast_score = self._score_contrast(contrast_std)
        
        # Check resolution
        resolution_score = self._score_resolution(width, height)
        
        # Check skew
        skew_angle = self._check_skew(gray)
        skew_score = self._score_skew(skew_angle)
        
        # Calculate overall score (weighted average)
        overall = (
            blur_score * 0.4 +
            brightness_score * 0.2 +
            contrast_score * 0.2 +
            resolution_score * 0.1 +
            skew_score * 0.1
        )
        
        return QualityScore(
            overall=overall,
            blur_score=blur_score,
            brightness_score=brightness_score,
            contrast_score=contrast_score,
            resolution_score=resolution_score,
            skew_score=skew_score,
            width=width,
            height=height,
            blur_variance=blur_variance,
            brightness_mean=brightness_mean,
            contrast_std=contrast_std,
            skew_angle=skew_angle
        )
    
    def _check_blur(self, gray: np.ndarray) -> float:
        """Check blur using Laplacian variance"""
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()
        return variance
    
    def _score_blur(self, variance: float) -> float:
        """Score blur (higher variance = sharper)"""
        if variance >= self.blur_threshold * 2:
            return 1.0
        elif variance >= self.blur_threshold:
            return 0.7 + (variance - self.blur_threshold) / (self.blur_threshold * 2) * 0.3
        elif variance >= self.blur_threshold * 0.5:
            return 0.5 + (variance - self.blur_threshold * 0.5) / (self.blur_threshold * 0.5) * 0.2
        else:
            return variance / (self.blur_threshold * 0.5) * 0.5
    
    def _check_brightness(self, gray: np.ndarray) -> float:
        """Check brightness (mean pixel value)"""
        return gray.mean()
    
    def _score_brightness(self, mean: float) -> float:
        """Score brightness"""
        if self.min_brightness <= mean <= self.max_brightness:
            # Optimal range
            return 1.0
        elif mean < self.min_brightness:
            # Too dark
            return max(0.0, mean / self.min_brightness)
        else:
            # Too bright
            return max(0.0, 1.0 - (mean - self.max_brightness) / (255 - self.max_brightness))
    
    def _check_contrast(self, gray: np.ndarray) -> float:
        """Check contrast (standard deviation)"""
        return gray.std()
    
    def _score_contrast(self, std: float) -> float:
        """Score contrast"""
        if std >= self.min_contrast * 2:
            return 1.0
        elif std >= self.min_contrast:
            return 0.7 + (std - self.min_contrast) / self.min_contrast * 0.3
        else:
            return std / self.min_contrast * 0.7
    
    def _score_resolution(self, width: int, height: int) -> float:
        """Score resolution"""
        if width >= self.min_width * 1.5 and height >= self.min_height * 1.5:
            return 1.0
        elif width >= self.min_width and height >= self.min_height:
            return 0.8
        elif width >= self.min_width * 0.8 and height >= self.min_height * 0.8:
            return 0.5
        else:
            return 0.2
    
    def _check_skew(self, gray: np.ndarray) -> float:
        """Check skew angle (simplified)"""
        # This is a simplified skew detection
        # For production, use more sophisticated methods
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi/180, 100)
        
        if lines is None:
            return 0.0
        
        angles = []
        for line in lines[:10]:  # Check first 10 lines
            rho, theta = line[0]
            angle = np.degrees(theta) - 90
            if abs(angle) < 45:  # Only consider near-horizontal lines
                angles.append(angle)
        
        if not angles:
            return 0.0
        
        # Return median angle
        return float(np.median(angles))
    
    def _score_skew(self, angle: float) -> float:
        """Score skew"""
        abs_angle = abs(angle)
        if abs_angle <= 1.0:
            return 1.0
        elif abs_angle <= self.max_skew_angle:
            return 0.7 + (self.max_skew_angle - abs_angle) / self.max_skew_angle * 0.3
        elif abs_angle <= self.max_skew_angle * 2:
            return 0.5
        else:
            return 0.3


if __name__ == '__main__':
    # Test the quality checker
    print("\n" + "="*80)
    print("IMAGE QUALITY CHECKER TEST - WEEK 5 DAY 1")
    print("="*80)
    
    checker = ImageQualityChecker()
    
    # Test with sample images
    test_folder = Path("INPUT_WORK_ORDER_IMAGES_TEXT")
    if test_folder.exists():
        images = list(test_folder.glob("*.jpg")) + list(test_folder.glob("*.jpeg"))
        
        if images:
            print(f"\nTesting {len(images)} images...")
            print("-" * 80)
            
            for i, image_path in enumerate(images[:3], 1):  # Test first 3
                print(f"\n{i}. {image_path.name}")
                print("-" * 80)
                
                try:
                    score = checker.check_quality(str(image_path))
                    
                    print(f"Overall Score: {score.overall:.2f} ({score.level})")
                    print(f"Action: {score.action}")
                    print(f"\nComponent Scores:")
                    print(f"  Blur:       {score.blur_score:.2f} (variance: {score.blur_variance:.1f})")
                    print(f"  Brightness: {score.brightness_score:.2f} (mean: {score.brightness_mean:.1f})")
                    print(f"  Contrast:   {score.contrast_score:.2f} (std: {score.contrast_std:.1f})")
                    print(f"  Resolution: {score.resolution_score:.2f} ({score.width}x{score.height})")
                    print(f"  Skew:       {score.skew_score:.2f} (angle: {score.skew_angle:.1f}°)")
                    
                    if score.issues:
                        print(f"\nIssues:")
                        for issue in score.issues:
                            print(f"  - {issue}")
                
                except Exception as e:
                    print(f"Error: {e}")
        else:
            print("\nNo images found in test folder")
    else:
        print(f"\nTest folder not found: {test_folder}")
    
    print("\n" + "="*80)
    print("IMAGE QUALITY CHECKER: OPERATIONAL")
    print("="*80 + "\n")
