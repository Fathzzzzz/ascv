import numpy as np
import pytest
from PIL import Image

from core.errors import InvalidOptionError
from core.grayscale import (
    adjust_contrast,
    enhance_contrast,
    equalize_contrast,
    to_grayscale,
)


def solid(rgb: tuple[int, int, int], size: tuple[int, int] = (4, 3)) -> Image.Image:
    return Image.new("RGB", size, rgb)


def test_luminance_uses_bt601_weights() -> None:
    gray = to_grayscale(solid((10, 20, 30), (2, 1)))
    expected = 0.299 * 10 + 0.587 * 20 + 0.114 * 30
    assert gray.shape == (1, 2)
    assert gray.dtype == np.float32
    assert np.allclose(gray, expected)


def test_luminance_extremes() -> None:
    assert np.allclose(to_grayscale(solid((255, 255, 255))), 255.0)
    assert np.allclose(to_grayscale(solid((0, 0, 0))), 0.0)


def test_contrast_identity_keeps_values() -> None:
    gray = np.array([[0.0, 127.5, 255.0]], dtype=np.float32)
    assert np.array_equal(adjust_contrast(gray, 1.0), gray)


def test_contrast_expands_around_mid_gray_and_clips() -> None:
    gray = np.array([[20.0, 127.5, 200.0]], dtype=np.float32)
    adjusted = adjust_contrast(gray, 2.0)
    assert np.allclose(adjusted, [[0.0, 127.5, 255.0]])


def test_contrast_zero_flattens_to_mid_gray() -> None:
    gray = np.array([[0.0, 100.0, 255.0]], dtype=np.float32)
    assert np.allclose(adjust_contrast(gray, 0.0), 127.5)


@pytest.mark.parametrize("factor", [-1.0, float("nan"), float("inf")])
def test_contrast_rejects_invalid_factor(factor: float) -> None:
    with pytest.raises(InvalidOptionError):
        adjust_contrast(np.zeros((2, 2), dtype=np.float32), factor)


def test_contrast_rejects_non_2d_input() -> None:
    with pytest.raises(InvalidOptionError):
        adjust_contrast(np.zeros((2, 2, 3), dtype=np.float32))


def test_equalize_contrast_widens_a_flat_gradient() -> None:
    # Low-contrast ramp: CLAHE should stretch it towards the full range.
    ramp = np.tile(np.linspace(90.0, 140.0, 64, dtype=np.float32), (64, 1))
    equalized = equalize_contrast(ramp, clip_limit=2.0)

    assert equalized.shape == ramp.shape
    assert equalized.dtype == np.float32
    assert equalized.std() > ramp.std()
    assert 0.0 <= float(equalized.min()) and float(equalized.max()) <= 255.0


def test_equalize_contrast_zero_clip_is_identity() -> None:
    ramp = np.tile(np.linspace(0.0, 255.0, 32, dtype=np.float32), (32, 1))
    assert np.allclose(equalize_contrast(ramp, clip_limit=0.0), ramp)


def test_enhance_contrast_combines_clahe_and_linear_factor() -> None:
    ramp = np.tile(np.linspace(90.0, 140.0, 64, dtype=np.float32), (64, 1))
    combined = enhance_contrast(ramp, factor=1.5, clip_limit=2.0)
    clahe_only = equalize_contrast(ramp, clip_limit=2.0)

    assert not np.allclose(combined, clahe_only)
    assert combined.std() > clahe_only.std()


@pytest.mark.parametrize("clip_limit", [-1.0, float("nan")])
def test_equalize_contrast_rejects_invalid_clip(clip_limit: float) -> None:
    with pytest.raises(InvalidOptionError):
        equalize_contrast(np.zeros((4, 4), dtype=np.float32), clip_limit=clip_limit)
