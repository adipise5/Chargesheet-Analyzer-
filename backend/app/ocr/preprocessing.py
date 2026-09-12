from __future__ import annotations

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter


def preprocess_image(image_path, adaptive: bool = False) -> Image.Image:
    """Return a derivative for OCR; the original file remains unchanged."""
    original = Image.open(image_path).convert("L")
    enhanced = ImageEnhance.Contrast(original).enhance(1.35).filter(ImageFilter.MedianFilter(3))
    array = np.array(enhanced)
    points = np.column_stack(np.where(array < 210))
    if len(points) > 40:
        angle = cv2.minAreaRect(points[:, ::-1].astype(np.float32))[-1]
        angle = -(90 + angle) if angle < -45 else -angle
        if 0.4 < abs(angle) < 7:
            h, w = array.shape
            matrix = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
            array = cv2.warpAffine(array, matrix, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    if adaptive:
        array = cv2.adaptiveThreshold(array, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                      cv2.THRESH_BINARY, 35, 12)
    return Image.fromarray(array)

