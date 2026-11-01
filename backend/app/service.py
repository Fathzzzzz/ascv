"""Validation and orchestration between HTTP and the core pipeline.

Everything here runs off the event loop except `read_upload`; the route wraps
the blocking work in a threadpool.
"""

from __future__ import annotations

import io

from PIL import Image, UnidentifiedImageError

from core import (
    ConversionOptions,
    InvalidImageError,
    InvalidOptionError,
    decode_image,
)
from .constants import (
    ALLOWED_IMAGE_FORMATS,
    MAX_IMAGE_DIMENSION,
    MAX_IMAGE_PIXELS,
    MAX_FILE_BYTES,
    REMBG_MODEL,
    UPLOAD_CHUNK_BYTES,
)
from .errors import ImageDimensionsError, PayloadTooLargeError, UnsupportedImageError

TRUE_VALUES = frozenset({"true", "1", "on", "yes"})
FALSE_VALUES = frozenset({"false", "0", "off", "no", ""})


def parse_bool(raw: str | None, field: str, default: bool) -> bool:
    """Parse a form checkbox/string into a bool with a clear error message."""
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in TRUE_VALUES:
        return True
    if value in FALSE_VALUES:
        return False
    raise InvalidOptionError(f"Parameter '{field}' harus true atau false.")


def parse_width(raw: str | None) -> int | None:
    """Parse the width form field; range validation happens in core."""
    if raw is None or raw.strip() == "":
        return None
    try:
        return int(raw.strip())
    except ValueError as exc:
        raise InvalidOptionError("Lebar harus bilangan bulat.") from exc


def parse_options(
    *,
    mode: str | None,
    width: str | None,
    charset: str | None,
    invert: str | None,
    remove_bg: str | None,
) -> ConversionOptions:
    """Build pipeline options from raw form fields (defaults follow the PRD)."""
    resolved_mode = (mode or "ascii").strip().lower()
    resolved_charset = (charset or "").strip() or None
    return ConversionOptions(
        mode=resolved_mode,
        width=parse_width(width),
        charset=resolved_charset,
        invert=parse_bool(invert, "invert", False),
        remove_bg=parse_bool(remove_bg, "remove_bg", True),
        model_name=REMBG_MODEL,
    )


async def read_upload(read_chunk) -> bytes:
    """Read an upload in chunks, aborting as soon as it passes the size limit."""
    buffer = bytearray()
    while chunk := await read_chunk(UPLOAD_CHUNK_BYTES):
        buffer.extend(chunk)
        if len(buffer) > MAX_FILE_BYTES:
            raise PayloadTooLargeError(MAX_FILE_BYTES)
    if not buffer:
        raise InvalidImageError("File kosong.")
    return bytes(buffer)


def detect_format(data: bytes) -> str:
    """Return the real image format from the bytes; reject anything unsupported."""
    try:
        with Image.open(io.BytesIO(data)) as probe:
            image_format = (probe.format or "").upper()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise InvalidImageError("File bukan gambar yang valid.") from exc

    if image_format not in ALLOWED_IMAGE_FORMATS:
        allowed = ", ".join(sorted(ALLOWED_IMAGE_FORMATS))
        raise UnsupportedImageError(f"Format gambar harus salah satu dari: {allowed}.")
    return image_format


def decode_upload(data: bytes) -> Image.Image:
    """Validate format and dimensions, then decode to RGB."""
    detect_format(data)
    image = decode_image(data)

    if max(image.size) > MAX_IMAGE_DIMENSION or image.width * image.height > MAX_IMAGE_PIXELS:
        raise ImageDimensionsError(
            f"Dimensi gambar maksimum {MAX_IMAGE_DIMENSION} piksel per sisi "
            f"dan {MAX_IMAGE_PIXELS // 1_000_000} megapiksel."
        )
    return image
