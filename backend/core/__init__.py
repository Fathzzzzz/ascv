"""Public surface of the FastAPI-independent conversion pipeline."""

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
    "CoreError",
    "DEFAULT_CHARSET",
    "DEFAULT_CLIP_LIMIT",
    "DEFAULT_EMPTY_CELL",
    "EMOJI_CHARSETS",
    "InvalidImageError",
    "InvalidOptionError",
    "LUMA_WEIGHTS",
    "SegmentationError",
    "adjust_contrast",
    "decode_image",
    "enhance_contrast",
    "equalize_contrast",
    "get_charset",
    "grid_dimensions",
    "map_grid",
    "resize_to_grid",
    "to_grayscale",
]
