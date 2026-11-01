import numpy as np
import pytest

from core.errors import InvalidOptionError
from core.grid import CHAR_ASPECT, grid_dimensions, resize_to_grid


def test_grid_aspect_ratio_ascii() -> None:
    # 200x100 image, 100 columns, ASCII cell is half as wide as tall.
    assert grid_dimensions(100, 200, 100, CHAR_ASPECT["ascii"]) == (100, 25)


def test_grid_aspect_ratio_emoji() -> None:
    # 200x100 image, 40 columns, square emoji cells.
    assert grid_dimensions(40, 200, 100, CHAR_ASPECT["emoji"]) == (40, 20)


def test_grid_height_never_drops_below_one() -> None:
    assert grid_dimensions(40, 4000, 1, 0.5) == (40, 1)


def test_grid_rejects_invalid_inputs() -> None:
    with pytest.raises(InvalidOptionError):
        grid_dimensions(0, 100, 100, 0.5)
    with pytest.raises(InvalidOptionError):
        grid_dimensions(10, 100, 100, 0)
    with pytest.raises(InvalidOptionError):
        grid_dimensions(10, 0, 100, 0.5)


def test_resize_matches_requested_grid_and_preserves_tone() -> None:
    gray = np.full((100, 200), 120.0, dtype=np.float32)
    mask = np.ones((100, 200), dtype=np.float32)

    gray_grid, mask_grid = resize_to_grid(gray, mask, 40, 20)

    assert gray_grid.shape == (20, 40)
    assert mask_grid.shape == (20, 40)
    assert np.allclose(gray_grid, 120.0)
    assert np.allclose(mask_grid, 1.0)


def test_resize_averages_brightness_per_cell() -> None:
    gray = np.zeros((10, 20), dtype=np.float32)
    gray[:, 10:] = 255.0
    mask = np.ones_like(gray)

    gray_grid, _ = resize_to_grid(gray, mask, 2, 1)

    assert gray_grid.shape == (1, 2)
    assert gray_grid[0, 0] == pytest.approx(0.0, abs=1.0)
    assert gray_grid[0, 1] == pytest.approx(255.0, abs=1.0)


def test_resize_upscales_small_masks() -> None:
    gray = np.full((2, 2), 50.0, dtype=np.float32)
    mask = np.array([[1.0, 0.0], [1.0, 0.0]], dtype=np.float32)

    gray_grid, mask_grid = resize_to_grid(gray, mask, 8, 8)

    assert gray_grid.shape == (8, 8)
    assert mask_grid.min() == pytest.approx(0.0)
    assert mask_grid.max() == pytest.approx(1.0)


def test_resize_rejects_mismatched_shapes() -> None:
    with pytest.raises(InvalidOptionError):
        resize_to_grid(
            np.zeros((4, 4), dtype=np.float32),
            np.zeros((4, 5), dtype=np.float32),
            2,
            2,
        )
