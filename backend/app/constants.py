"""Konfigurasi aplikasi.

Seluruh nilai yang bisa berubah ada di file ini. Aplikasi hanya dijalankan di
localhost, jadi tidak ada environment variable, file .env, atau modul config.
"""

from __future__ import annotations

from core.mapping import ASCII_CHARSETS, EMOJI_CHARSETS
from core.pipeline import DEFAULT_WIDTH, WIDTH_LIMITS
from core.segmentation import DEFAULT_REMBG_MODEL

APP_VERSION = "0.1.0"

# Upload limits (FR-02): validated again in the API layer before decoding.
MAX_FILE_BYTES = 5 * 1024 * 1024
UPLOAD_CHUNK_BYTES = 64 * 1024

# Dimension guard for hostile/large uploads (NFR keamanan).
MAX_IMAGE_PIXELS = 25_000_000
MAX_IMAGE_DIMENSION = 8000

# JPEG/PNG/WEBP only; the format is sniffed from the bytes, not the filename.
ALLOWED_IMAGE_FORMATS = frozenset({"JPEG", "PNG", "WEBP"})

# Segmentation model, loaded once at server start.
REMBG_MODEL = DEFAULT_REMBG_MODEL

# Width bounds and charset presets are owned by core (it must run without this
# package), re-exported here so the API reads all limits from one place.
__all__ = [
    "ALLOWED_IMAGE_FORMATS",
    "APP_VERSION",
    "ASCII_CHARSETS",
    "DEFAULT_REMBG_MODEL",
    "DEFAULT_WIDTH",
    "EMOJI_CHARSETS",
    "MAX_FILE_BYTES",
    "MAX_IMAGE_DIMENSION",
    "MAX_IMAGE_PIXELS",
    "REMBG_MODEL",
    "UPLOAD_CHUNK_BYTES",
    "WIDTH_LIMITS",
]
