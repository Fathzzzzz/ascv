"""Image decoding shared by the CLI and (later) the API layer."""

from __future__ import annotations

import io
from pathlib import Path
from typing import BinaryIO

from PIL import Image, ImageOps, UnidentifiedImageError

from .errors import InvalidImageError

ImageSource = bytes | bytearray | BinaryIO | str | Path


def decode_image(source: ImageSource) -> Image.Image:
    """Decode an image source into an upright RGB image.

    Animated images use their first frame. File handles opened here are closed
    before returning; a file object supplied by the caller stays open.
    """
    owns_source = isinstance(source, (bytes, bytearray, str, Path))
    raw: Image.Image | None = None
    try:
        if isinstance(source, (bytes, bytearray)):
            raw = Image.open(io.BytesIO(bytes(source)))
        else:
            raw = Image.open(source)
        raw.load()
        upright = ImageOps.exif_transpose(raw)
        return upright.convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise InvalidImageError("Gambar tidak dapat dibaca atau formatnya tidak didukung.") from exc
    finally:
        if owns_source and raw is not None:
            raw.close()
