"""API-layer errors that have no core equivalent."""

from __future__ import annotations


class PayloadTooLargeError(Exception):
    """The upload exceeds MAX_FILE_BYTES (mapped to HTTP 413)."""

    def __init__(self, limit_bytes: int) -> None:
        self.limit_bytes = limit_bytes
        super().__init__(f"Ukuran file maksimum {limit_bytes // (1024 * 1024)} MB.")


class UnsupportedImageError(Exception):
    """The upload declares/contains a format outside ALLOWED_IMAGE_FORMATS."""


class ImageDimensionsError(Exception):
    """The decoded image exceeds the pixel/dimension guard."""
