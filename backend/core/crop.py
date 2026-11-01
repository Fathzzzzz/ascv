"""Crop the image and its mask to the subject bounding box."""

from __future__ import annotations

import numpy as np
from PIL import Image

from .errors import SegmentationError

BBox = tuple[int, int, int, int]

# A low threshold keeps soft mask edges (hair, shoulders) inside the crop.
CROP_MASK_THRESHOLD = 0.1


def subject_bbox(mask: np.ndarray, threshold: float = CROP_MASK_THRESHOLD) -> BBox | None:
    """Return (left, top, right, bottom) in PIL coordinates, or None if empty."""
    array = np.asarray(mask)
    if array.ndim != 2:
        raise SegmentationError("Mask subjek harus berupa gambar grayscale 2D.")
    subject = array >= threshold
    if not subject.any():
        return None

    rows = np.flatnonzero(subject.any(axis=1))
    cols = np.flatnonzero(subject.any(axis=0))
    top, bottom = int(rows[0]), int(rows[-1]) + 1
    left, right = int(cols[0]), int(cols[-1]) + 1
    return left, top, right, bottom


def crop_to_subject(
    image: Image.Image,
    mask: np.ndarray,
    threshold: float = CROP_MASK_THRESHOLD,
) -> tuple[Image.Image, np.ndarray]:
    """Crop image and mask to the subject; fall back to the full frame when empty."""
    if mask.shape != (image.height, image.width):
        raise SegmentationError("Ukuran mask tidak sesuai dengan ukuran gambar.")

    bbox = subject_bbox(mask, threshold)
    if bbox is None:
        return image.copy(), mask.copy()

    left, top, right, bottom = bbox
    cropped_mask = mask[top:bottom, left:right].copy()
    return image.crop(bbox), cropped_mask
