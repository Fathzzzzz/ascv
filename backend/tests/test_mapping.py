import numpy as np
import pytest

from core.errors import InvalidOptionError
from core.mapping import (
    ASCII_CHARSETS,
    DEFAULT_CHARSET,
    EMOJI_CHARSETS,
    get_charset,
    map_grid,
)


def test_default_charsets_exist_and_are_dark_to_light() -> None:
    assert DEFAULT_CHARSET == {"ascii": "standard", "emoji": "moon"}
    assert ASCII_CHARSETS["standard"][0] == "@"
    assert ASCII_CHARSETS["standard"][-1] == " "
    assert ASCII_CHARSETS["blocks"][0] == "█"
    assert len(ASCII_CHARSETS["dense"]) >= 60
    assert EMOJI_CHARSETS["moon"][0] == "🌑"


def test_get_charset_returns_tokens_for_mode() -> None:
    assert get_charset("ascii") == tuple(ASCII_CHARSETS["standard"])
    assert get_charset("emoji", "moon") == EMOJI_CHARSETS["moon"]


def test_get_charset_rejects_unknown_mode_and_name() -> None:
    with pytest.raises(InvalidOptionError):
        get_charset("video")
    with pytest.raises(InvalidOptionError):
        get_charset("ascii", "moon")
    with pytest.raises(InvalidOptionError):
        get_charset("emoji", "nope")


def test_mapping_maps_dark_to_light() -> None:
    gray = np.array([[0.0, 255.0]], dtype=np.float32)
    mask = np.ones_like(gray)
    assert map_grid(gray, mask, ("@", ".")) == "@."


def test_invert_flips_brightness_order() -> None:
    gray = np.array([[0.0, 255.0]], dtype=np.float32)
    mask = np.ones_like(gray)
    assert map_grid(gray, mask, ("@", "."), invert=True) == ".@"


def test_cells_outside_mask_become_spaces() -> None:
    gray = np.full((2, 3), 0.0, dtype=np.float32)
    mask = np.array([[1.0, 0.0, 1.0], [0.0, 0.0, 1.0]], dtype=np.float32)
    assert map_grid(gray, mask, ("@",)) == "@ @\n  @"


def test_mask_threshold_controls_visibility() -> None:
    gray = np.full((1, 3), 0.0, dtype=np.float32)
    mask = np.array([[0.2, 0.6, 0.8]], dtype=np.float32)
    assert map_grid(gray, mask, ("@",), mask_threshold=0.5) == " @@"


def test_mask_threshold_boundary_is_inclusive() -> None:
    gray = np.zeros((1, 2), dtype=np.float32)
    mask = np.array([[0.49, 0.5]], dtype=np.float32)
    assert map_grid(gray, mask, ("@",), mask_threshold=0.5) == " @"


def test_emoji_tokens_are_not_split() -> None:
    gray = np.array([[0.0, 255.0]], dtype=np.float32)
    mask = np.ones_like(gray)
    out = map_grid(gray, mask, ("🌑", "🌕"))
    assert out == "🌑🌕"
    assert len(out) == 2


def test_empty_cell_is_configurable() -> None:
    gray = np.zeros((1, 2), dtype=np.float32)
    mask = np.array([[1.0, 0.0]], dtype=np.float32)
    assert map_grid(gray, mask, ("@",), empty_cell="·") == "@·"


def test_mapping_validates_inputs() -> None:
    gray = np.zeros((2, 2), dtype=np.float32)
    mask = np.ones((2, 2), dtype=np.float32)
    with pytest.raises(InvalidOptionError):
        map_grid(gray, np.ones((2, 3), dtype=np.float32), ("@",))
    with pytest.raises(InvalidOptionError):
        map_grid(gray, mask, ())
    with pytest.raises(InvalidOptionError):
        map_grid(gray, mask, ("@", ""))
    with pytest.raises(InvalidOptionError):
        map_grid(gray, mask, ("@",), mask_threshold=1.5)
