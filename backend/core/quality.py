"""Detect images with nothing to convert.

Segmentation happily "finds" a subject in a flat image (rembg returns a full
mask for a solid frame), so blank uploads are caught by their lack of tone
before any model runs, and again after cropping.
"""

from __future__ import annotations

import numpy as np

from .errors import InvalidOptionError

# Luminance standard deviation, in 0-255 units. Flat frames sit near 0; JPEG
# noise on a solid fill stays well below 1, while real photos exceed 20.
MIN_LUMA_STD = 1.0


def is_featureless(gray: np.ndarray, min_std: float = MIN_LUMA_STD) -> bool:
    """True when the luminance plane is too flat to produce recognizable art."""
    array = np.asarray(gray, dtype=np.float32)
    if array.ndim != 2:
        raise InvalidOptionError("Grayscale harus berupa array 2D.")
    if not np.isfinite(min_std) or min_std < 0:
        raise InvalidOptionError("Ambang variasi harus angka >= 0.")
    if array.size < 2:
        return True
    return float(np.nanstd(array)) < min_std
