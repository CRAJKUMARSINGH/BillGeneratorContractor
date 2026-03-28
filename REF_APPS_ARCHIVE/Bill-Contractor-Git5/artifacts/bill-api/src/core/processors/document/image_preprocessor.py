"""
Image Preprocessor
Enhances image quality before OCR/HWR processing.

Robustness guarantee: every public method catches all exceptions internally
and returns the original (or a safe fallback) image rather than raising.
"""
import logging
import cv2
import numpy as np
from typing import Tuple, Optional, Union
from pathlib import Path

logger = logging.getLogger(__name__)

# PIL is optional – used only as a fallback for exotic image formats
try:
    from PIL import Image as PILImage
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False


def _to_bgr_uint8(image: np.ndarray) -> np.ndarray:
    """
    Ensure image is uint8 BGR.  Returns a copy; never raises.
    """
    img = image.copy()
    # Fix dtype
    if img.dtype != np.uint8:
        img = np.clip(img * 255 if img.max() <= 1.0 else img, 0, 255).astype(np.uint8)
    # Fix channels
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    elif img.ndim == 3 and img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    elif img.ndim == 3 and img.shape[2] == 1:
        img = cv2.cvtColor(img[:, :, 0], cv2.COLOR_GRAY2BGR)
    return img


class ImagePreprocessor:
    """Preprocesses images for optimal OCR and handwriting recognition"""

    def __init__(self, enable_rotation_correction: bool = True,
                 enable_enhancement: bool = True,
                 enable_noise_removal: bool = True):
        self.enable_rotation_correction = enable_rotation_correction
        self.enable_enhancement = enable_enhancement
        self.enable_noise_removal = enable_noise_removal

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        Apply full preprocessing pipeline.
        Never raises – returns best-effort result or original on failure.
        """
        if image is None or (isinstance(image, np.ndarray) and image.size == 0):
            logger.warning("preprocess: received empty/None image, returning blank")
            return np.ones((10, 10, 3), dtype=np.uint8) * 255

        try:
            processed = _to_bgr_uint8(image)
        except Exception as e:
            logger.error(f"preprocess: normalisation failed: {e}")
            return image if image is not None else np.ones((10, 10, 3), dtype=np.uint8) * 255

        if self.enable_rotation_correction:
            try:
                processed = self.correct_rotation(processed)
            except Exception as e:
                logger.warning(f"preprocess: rotation correction skipped: {e}")

        if self.enable_enhancement:
            try:
                processed = self.enhance_contrast(processed)
            except Exception as e:
                logger.warning(f"preprocess: contrast enhancement skipped: {e}")

        if self.enable_noise_removal:
            try:
                processed = self.remove_noise(processed)
            except Exception as e:
                logger.warning(f"preprocess: noise removal skipped: {e}")

        try:
            processed = self.binarize(processed)
        except Exception as e:
            logger.warning(f"preprocess: binarization skipped: {e}")

        return processed

    def correct_rotation(self, image: np.ndarray) -> np.ndarray:
        """
        Detect and correct image rotation using Hough line transform.
        Never raises – returns original on failure.
        """
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image.copy()
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)

            if lines is None:
                return image

            angles = [np.degrees(theta) - 90 for rho, theta in lines[:, 0]]
            if not angles:
                return image

            median_angle = np.median(angles)
            if abs(median_angle) > 0.5:
                (h, w) = image.shape[:2]
                M = cv2.getRotationMatrix2D((w // 2, h // 2), median_angle, 1.0)
                return cv2.warpAffine(image, M, (w, h),
                                      flags=cv2.INTER_CUBIC,
                                      borderMode=cv2.BORDER_REPLICATE)
        except Exception as e:
            logger.warning(f"correct_rotation failed: {e}")

        return image

    def enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """
        Improve text visibility through adaptive contrast adjustment (CLAHE).
        Never raises – returns original on failure.
        """
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image.copy()
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            if image.ndim == 3:
                enhanced = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
            return enhanced
        except Exception as e:
            logger.warning(f"enhance_contrast failed: {e}")
            return image

    def remove_noise(self, image: np.ndarray) -> np.ndarray:
        """
        Apply noise reduction filters.
        Never raises – returns original on failure.
        """
        try:
            denoised = cv2.bilateralFilter(image, 9, 75, 75)
            kernel = np.ones((2, 2), np.uint8)
            return cv2.morphologyEx(denoised, cv2.MORPH_OPEN, kernel)
        except Exception as e:
            logger.warning(f"remove_noise failed: {e}")
            return image

    def binarize(self, image: np.ndarray) -> np.ndarray:
        """
        Convert to black-and-white for optimal OCR.
        Never raises – returns original on failure.
        """
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image.copy()
            return cv2.adaptiveThreshold(
                gray, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                11, 2
            )
        except Exception as e:
            logger.warning(f"binarize failed: {e}")
            return image

    def load_image(self, image_path: Union[str, Path]) -> np.ndarray:
        """
        Load image from file path with PIL fallback.
        Raises ValueError only if the file genuinely cannot be read at all.
        """
        path = str(image_path)

        # Primary: OpenCV
        try:
            img = cv2.imread(path, cv2.IMREAD_COLOR)
            if img is not None and img.size > 0:
                return img
        except Exception:
            pass

        # Fallback: PIL
        if _PIL_AVAILABLE:
            try:
                pil_img = PILImage.open(path).convert('RGB')
                img = np.array(pil_img)
                return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            except Exception:
                pass

        raise ValueError(f"Failed to load image from '{path}' (tried cv2 and PIL)")

    def save_image(self, image: np.ndarray, output_path: str) -> None:
        """
        Save preprocessed image to file.
        Never raises – logs error on failure instead.
        """
        try:
            cv2.imwrite(output_path, image)
        except Exception as e:
            logger.error(f"save_image failed for '{output_path}': {e}")
