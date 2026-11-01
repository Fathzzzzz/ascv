"""End-to-end conversion pipeline: segmentation > crop > grayscale > grid > map."""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image

from .crop import crop_to_subject
from .errors import InvalidOptionError
from .grayscale import DEFAULT_CLIP_LIMIT, enhance_contrast, to_grayscale
from .grid import CHAR_ASPECT, grid_dimensions, resize_to_grid
from .mapping import DEFAULT_EMPTY_CELL, get_charset, map_grid
from .segmentation import (
    DEFAULT_REMBG_MODEL,
    FullMaskSegmenter,
    RembgSegmenter,
    Segmenter,
    normalize_mask,
)

WIDTH_LIMITS = {"ascii": (40, 200), "emoji": (20, 80)}
DEFAULT_WIDTH = {"ascii": 100, "emoji": 40}


@dataclass(frozen=True)
class ConversionOptions:
    """Pipeline options mirroring the API contract (plus internal tuning knobs)."""

    width: int | None = None
    mode: str = "ascii"
    charset: str | None = None
    invert: bool = False
    remove_bg: bool = True
    contrast: float = 1.0
    clahe: float = DEFAULT_CLIP_LIMIT
    mask_threshold: float = 0.5
    empty_cell: str = DEFAULT_EMPTY_CELL
    model_name: str = DEFAULT_REMBG_MODEL


@dataclass(frozen=True)
class ConversionResult:
    text: str
    width: int
    height: int
    mode: str


def resolve_width(mode: str, width: int | None) -> int:
    """Apply per-mode defaults and PRD width bounds."""
    if mode not in WIDTH_LIMITS:
        raise InvalidOptionError("Mode harus 'ascii' atau 'emoji'.")
    resolved = DEFAULT_WIDTH[mode] if width is None else width
    if isinstance(resolved, bool) or not isinstance(resolved, int):
        raise InvalidOptionError("Lebar harus bilangan bulat.")

    low, high = WIDTH_LIMITS[mode]
    if not low <= resolved <= high:
        raise InvalidOptionError(
            f"Lebar mode {mode} harus antara {low} dan {high} kolom."
        )
    return resolved


def convert_image(
    image: Image.Image,
    options: ConversionOptions | None = None,
    *,
    segmenter: Segmenter | None = None,
) -> ConversionResult:
    """Run the whole pipeline on an RGB PIL image.

    `segmenter` can be injected for tests; when omitted, rembg is used for
    `remove_bg=True` and a full-frame mask otherwise.
    """
    options = options or ConversionOptions()
    width = resolve_width(options.mode, options.width)
    charset = get_charset(options.mode, options.charset)

    rgb = image.convert("RGB")
    if options.remove_bg:
        masker = segmenter or RembgSegmenter(options.model_name)
    else:
        # A provided segmenter must not leak into the no-background-removal path.
        masker = FullMaskSegmenter()

    mask = normalize_mask(masker.segment(rgb), rgb.size)
    subject, subject_mask = crop_to_subject(rgb, mask)

    gray = enhance_contrast(to_grayscale(subject), options.contrast, options.clahe)
    cols, rows = grid_dimensions(
        width,
        subject.width,
        subject.height,
        CHAR_ASPECT[options.mode],
    )
    gray_grid, mask_grid = resize_to_grid(gray, subject_mask, cols, rows)

    text = map_grid(
        gray_grid,
        mask_grid,
        charset,
        invert=options.invert,
        mask_threshold=options.mask_threshold,
        empty_cell=options.empty_cell,
    )
    return ConversionResult(text=text, width=cols, height=rows, mode=options.mode)
