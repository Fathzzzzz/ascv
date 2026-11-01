"""Subject segmentation.

`RembgSegmenter` wraps rembg behind a tiny protocol so the rest of the
pipeline (and its tests) never has to load a model. Sessions are cached per
model name: the first request pays the model load/download, later requests
reuse the same ONNX session.
"""

from __future__ import annotations

import threading
from typing import Any, Protocol

import cv2
import numpy as np
from PIL import Image

from .errors import SegmentationError

DEFAULT_REMBG_MODEL = "u2net"

_sessions: dict[str, Any] = {}
_sessions_lock = threading.Lock()


class Segmenter(Protocol):
    """Produces a foreground mask covering the subject."""

    def segment(self, image: Image.Image) -> np.ndarray:
        """Return a float32 mask of shape (height, width) with values in [0, 1]."""
        ...


def _get_session(model_name: str) -> Any:
    """Load a rembg session once per model name, then reuse it."""
    with _sessions_lock:
        if model_name not in _sessions:
            from rembg import new_session  # imported lazily: heavy and optional for tests

            _sessions[model_name] = new_session(model_name)
        return _sessions[model_name]


def preload_model(model_name: str = DEFAULT_REMBG_MODEL) -> None:
    """Warm the model cache at server start so requests skip the load cost."""
    _get_session(model_name)


def is_model_loaded(model_name: str = DEFAULT_REMBG_MODEL) -> bool:
    """True when the session for `model_name` is already cached in this process."""
    return model_name in _sessions


def remove_mask(image: Image.Image, session: Any) -> Image.Image:
    """Run rembg and return only the alpha mask. Kept separate for testing."""
    from rembg import remove

    return remove(image, session=session, only_mask=True)


def normalize_mask(mask: Any, size: tuple[int, int]) -> np.ndarray:
    """Validate a raw mask and normalize it to float32 in [0, 1] at `size`."""
    array = np.asarray(mask)
    if array.size == 0:
        raise SegmentationError("Mask subjek kosong.")
    if array.ndim == 3 and array.shape[2] == 1:
        array = array[:, :, 0]
    if array.ndim != 2:
        raise SegmentationError("Mask subjek harus berupa gambar grayscale 2D.")

    if array.dtype == np.bool_:
        array = array.astype(np.float32)
    elif array.dtype == np.uint8:
        array = array.astype(np.float32) / 255.0
    elif np.issubdtype(array.dtype, np.floating):
        array = array.astype(np.float32)
    else:
        raise SegmentationError(f"Tipe data mask tidak didukung: {array.dtype}.")

    array = np.nan_to_num(array, nan=0.0, posinf=1.0, neginf=0.0)
    array = np.clip(array, 0.0, 1.0)

    width, height = size
    if array.shape != (height, width):
        array = cv2.resize(array, (width, height), interpolation=cv2.INTER_LINEAR)
        array = np.clip(array, 0.0, 1.0)
    return array.astype(np.float32, copy=False)


class FullMaskSegmenter:
    """No-op segmenter used when background removal is disabled."""

    def segment(self, image: Image.Image) -> np.ndarray:
        return np.ones((image.height, image.width), dtype=np.float32)


class RembgSegmenter:
    """rembg-backed person segmentation with a process-wide cached session."""

    def __init__(self, model_name: str = DEFAULT_REMBG_MODEL) -> None:
        self.model_name = model_name

    def segment(self, image: Image.Image) -> np.ndarray:
        try:
            session = _get_session(self.model_name)
            raw_mask = remove_mask(image, session)
        except SegmentationError:
            raise
        except Exception as exc:  # rembg/onnxruntime raise many different types
            raise SegmentationError("Segmentasi subjek gagal.") from exc
        return normalize_mask(raw_mask, image.size)
