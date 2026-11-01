"""Public surface of the FastAPI-independent conversion pipeline."""

from .crop import CROP_MASK_THRESHOLD, crop_to_subject, subject_bbox

from .errors import CoreError, InvalidImageError, InvalidOptionError, SegmentationError
from .grayscale import (
    DEFAULT_CLIP_LIMIT,
    LUMA_WEIGHTS,
    adjust_contrast,
    enhance_contrast,
    equalize_contrast,
    to_grayscale,
)
from .grid import CHAR_ASPECT, grid_dimensions, resize_to_grid
from .image_io import decode_image
from .segmentation import (
    DEFAULT_REMBG_MODEL,
    FullMaskSegmenter,
    RembgSegmenter,
    Segmenter,
    normalize_mask,
)
from .mapping import (
    ASCII_CHARSETS,
    DEFAULT_CHARSET,
    DEFAULT_EMPTY_CELL,
    EMOJI_CHARSETS,
    get_charset,
    map_grid,
)

__all__ = [
    "ASCII_CHARSETS",
    "CHAR_ASPECT",
    "CROP_MASK_THRESHOLD",
    "CoreError",
    "DEFAULT_CHARSET",
    "DEFAULT_CLIP_LIMIT",
    "DEFAULT_EMPTY_CELL",
    "DEFAULT_REMBG_MODEL",
    "EMOJI_CHARSETS",
    "FullMaskSegmenter",
    "InvalidImageError",
    "InvalidOptionError",
    "LUMA_WEIGHTS",
    "RembgSegmenter",
    "Segmenter",
    "SegmentationError",
    "adjust_contrast",
    "crop_to_subject",
    "decode_image",
    "enhance_contrast",
    "equalize_contrast",
    "get_charset",
    "grid_dimensions",
    "map_grid",
    "normalize_mask",
    "resize_to_grid",
    "subject_bbox",
    "to_grayscale",
]
