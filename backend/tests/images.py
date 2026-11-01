"""Deterministic test images.

Solid fills are now rejected as blank, so pipeline tests need visible tone
variation; these helpers produce it from a seeded gradient plus noise.
"""

from __future__ import annotations

import numpy as np
from PIL import Image


def textured(size: tuple[int, int] = (80, 80), seed: int = 0) -> Image.Image:
    """Smooth gradient with mild noise: dark on the left, light on the right."""
    width, height = size
    rng = np.random.default_rng(seed)
    ramp = np.linspace(0.0, 255.0, width, dtype=np.float32)
    plane = np.tile(ramp, (height, 1))
    plane = plane + rng.normal(0.0, 4.0, size=plane.shape)
    plane = np.clip(plane, 0.0, 255.0).astype(np.uint8)
    rgb = np.repeat(plane[:, :, None], 3, axis=2)
    return Image.fromarray(rgb, mode="RGB")


def half_black_half_white(size: int = 80) -> Image.Image:
    """Hard edge at the middle: easy to assert on in mapping tests."""
    pixels = np.zeros((size, size, 3), dtype=np.uint8)
    pixels[:, size // 2:] = 255
    return Image.fromarray(pixels, mode="RGB")


def solid(size: tuple[int, int] = (80, 80), value: int = 128) -> Image.Image:
    return Image.new("RGB", size, (value, value, value))
