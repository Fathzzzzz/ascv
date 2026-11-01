"""Luminance conversion and contrast adjustment.

`to_grayscale` applies the ITU-R BT.601 weights required by the PRD. The
contrast stage then performs two steps, both optional: local contrast
equalization (CLAHE, PRD 11.3) and a linear contrast factor around mid-gray.
"""

from __future__ import annotations

import cv2
import numpy as np
from PIL import Image

from .errors import InvalidOptionError

# ITU-R BT.601 weights, as required by the PRD.
LUMA_WEIGHTS = np.array([0.299, 0.587, 0.114], dtype=np.float32)

# CLAHE defaults: mild clipping keeps flat skin areas from turning noisy.
DEFAULT_CLIP_LIMIT = 2.0
CLAHE_TILE_SIZE = (8, 8)


def _require_2d(gray: np.ndarray) -> np.ndarray:
    array = np.asarray(gray, dtype=np.float32)
    if array.ndim != 2:
        raise InvalidOptionError("Grayscale harus berupa array 2D.")
    return array


def to_grayscale(image: Image.Image) -> np.ndarray:
    """Convert an RGB image to a float32 luminance plane in [0, 255]."""
    rgb = np.asarray(image.convert("RGB"), dtype=np.float32)
    return np.clip(rgb @ LUMA_WEIGHTS, 0.0, 255.0)


def adjust_contrast(gray: np.ndarray, factor: float = 1.0) -> np.ndarray:
    """Scale values around mid-gray; 1.0 keeps the image unchanged."""
    array = _require_2d(gray)
    if not np.isfinite(factor) or factor < 0:
        raise InvalidOptionError("Nilai kontras harus angka >= 0.")
    if factor == 1.0:
        return np.clip(array, 0.0, 255.0).astype(np.float32, copy=False)

    adjusted = (array - 127.5) * factor + 127.5
    return np.clip(adjusted, 0.0, 255.0).astype(np.float32, copy=False)


def equalize_contrast(
    gray: np.ndarray,
    clip_limit: float = DEFAULT_CLIP_LIMIT,
    tile_size: tuple[int, int] = CLAHE_TILE_SIZE,
) -> np.ndarray:
    """Local contrast equalization (CLAHE). `clip_limit <= 0` disables it."""
    array = _require_2d(gray)
    if not np.isfinite(clip_limit) or clip_limit < 0:
        raise InvalidOptionError("Batas clip CLAHE harus angka >= 0.")
    if clip_limit == 0:
        return np.clip(array, 0.0, 255.0).astype(np.float32, copy=False)
    if tile_size[0] < 1 or tile_size[1] < 1:
        raise InvalidOptionError("Ukuran tile CLAHE minimal 1 x 1.")

    scaled = np.clip(array, 0.0, 255.0).astype(np.uint8)
    clahe = cv2.createCLAHE(clipLimit=float(clip_limit), tileGridSize=tuple(int(v) for v in tile_size))
    return clahe.apply(scaled).astype(np.float32)


def enhance_contrast(
    gray: np.ndarray,
    factor: float = 1.0,
    clip_limit: float = DEFAULT_CLIP_LIMIT,
) -> np.ndarray:
    """Full contrast stage: CLAHE, then the linear factor."""
    return adjust_contrast(equalize_contrast(gray, clip_limit), factor)
