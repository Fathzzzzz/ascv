"""Resize the luminance and mask planes to the character grid."""

from __future__ import annotations

import cv2
import numpy as np

from .errors import InvalidOptionError

# Character cell aspect = cell width / cell height. ASCII glyphs are roughly
# half as wide as they are tall, emoji are close to square.
CHAR_ASPECT = {"ascii": 0.5, "emoji": 1.0}


def grid_dimensions(
    cols: int,
    image_width: int,
    image_height: int,
    char_aspect: float,
) -> tuple[int, int]:
    """Return (cols, rows) that preserve the subject aspect ratio on screen."""
    if cols < 1:
        raise InvalidOptionError("Lebar grid minimal 1 kolom.")
    if image_width < 1 or image_height < 1:
        raise InvalidOptionError("Dimensi gambar tidak valid.")
    if not np.isfinite(char_aspect) or char_aspect <= 0:
        raise InvalidOptionError("Rasio karakter harus angka > 0.")

    rows = max(1, int(round(cols * (image_height / image_width) * char_aspect)))
    return cols, rows


def resize_to_grid(
    gray: np.ndarray,
    mask: np.ndarray,
    cols: int,
    rows: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Resize luminance and mask to (rows, cols) with area averaging."""
    if gray.ndim != 2 or mask.ndim != 2:
        raise InvalidOptionError("Grayscale dan mask harus array 2D.")
    if gray.shape != mask.shape:
        raise InvalidOptionError("Grayscale dan mask harus berukuran sama.")
    if cols < 1 or rows < 1:
        raise InvalidOptionError("Ukuran grid minimal 1 x 1.")

    height, width = gray.shape
    shrinking = cols <= width and rows <= height
    interpolation = cv2.INTER_AREA if shrinking else cv2.INTER_LINEAR

    gray_grid = cv2.resize(gray.astype(np.float32), (cols, rows), interpolation=interpolation)
    mask_grid = cv2.resize(mask.astype(np.float32), (cols, rows), interpolation=interpolation)
    return np.clip(gray_grid, 0.0, 255.0), np.clip(mask_grid, 0.0, 1.0)
