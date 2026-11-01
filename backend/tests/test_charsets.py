"""Charset preset contracts (M2).

Every preset is ordered dark to light, so the mapping stage can index it with
brightness without knowing anything about the glyphs.
"""

import re

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

ALL_ASCII_PRESETS = sorted(ASCII_CHARSETS)
ALL_EMOJI_PRESETS = sorted(EMOJI_CHARSETS)
MODE_PRESETS = [
    pytest.param(mode, name, id=f"{mode}-{name}")
    for mode, presets in (("ascii", ASCII_CHARSETS), ("emoji", EMOJI_CHARSETS))
    for name in sorted(presets)
]


def test_every_mode_has_a_default_preset() -> None:
    assert DEFAULT_CHARSET == {"ascii": "standard", "emoji": "moon"}
    assert DEFAULT_CHARSET["ascii"] in ASCII_CHARSETS
    assert DEFAULT_CHARSET["emoji"] in EMOJI_CHARSETS


@pytest.mark.parametrize("name", ALL_ASCII_PRESETS)
def test_ascii_presets_are_single_printable_glyphs(name: str) -> None:
    preset = ASCII_CHARSETS[name]

    assert len(preset) >= 2, "a ramp needs at least two levels"
    assert len(set(preset)) == len(preset), "duplicate levels waste tonal range"
    for token in preset:
        assert len(token) == 1
        assert token.isprintable()
        assert token not in "\n\r\t"


@pytest.mark.parametrize("name", ALL_ASCII_PRESETS)
def test_ascii_presets_run_dark_to_light(name: str) -> None:
    preset = ASCII_CHARSETS[name]

    assert preset[0] != " "
    assert preset[-1] == " ", "the lightest level must be blank paper"


@pytest.mark.parametrize("name", ALL_EMOJI_PRESETS)
def test_emoji_presets_are_single_codepoints(name: str) -> None:
    preset = EMOJI_CHARSETS[name]

    assert len(preset) >= 2
    assert len(set(preset)) == len(preset)
    for token in preset:
        # One code point keeps the grid aligned: no ZWJ, skin tone, or VS16.
        assert len(token) == 1
        assert not token.isspace()
        assert not re.search(r"[\u200d\ufe0f\U0001f3fb-\U0001f3ff]", token)


@pytest.mark.parametrize("name", ALL_EMOJI_PRESETS)
def test_emoji_presets_run_dark_to_light(name: str) -> None:
    preset = EMOJI_CHARSETS[name]

    assert preset[0] in {"🌑", "⬛"}
    assert preset[-1] in {"🌕", "⬜"}


def test_dense_preset_offers_more_levels_than_standard() -> None:
    assert len(ASCII_CHARSETS["dense"]) > len(ASCII_CHARSETS["standard"]) * 3


def test_get_charset_returns_an_immutable_copy() -> None:
    tokens = get_charset("ascii", "blocks")

    assert isinstance(tokens, tuple)
    assert tokens == tuple(ASCII_CHARSETS["blocks"])
    assert get_charset("emoji", "squares") == EMOJI_CHARSETS["squares"]


def test_get_charset_defaults_to_mode_preset() -> None:
    assert get_charset("ascii") == tuple(ASCII_CHARSETS[DEFAULT_CHARSET["ascii"]])
    assert get_charset("emoji", None) == EMOJI_CHARSETS[DEFAULT_CHARSET["emoji"]]


@pytest.mark.parametrize("mode", ["ascii", "emoji"])
def test_get_charset_rejects_presets_from_the_other_mode(mode: str) -> None:
    other = "emoji" if mode == "ascii" else "ascii"

    with pytest.raises(InvalidOptionError):
        get_charset(mode, DEFAULT_CHARSET[other])


def test_get_charset_rejects_unknown_mode_and_unknown_preset() -> None:
    with pytest.raises(InvalidOptionError):
        get_charset("video")
    with pytest.raises(InvalidOptionError, match="Tidak ada"):
        get_charset("ascii", "Tidak ada")


@pytest.mark.parametrize(("mode", "name"), MODE_PRESETS)
def test_mapping_is_monotonic_for_every_preset(mode: str, name: str) -> None:
    tokens = get_charset(mode, name)
    steps = 256
    ramp = np.linspace(0.0, 255.0, steps, dtype=np.float32).reshape(1, steps)
    mask = np.ones_like(ramp)

    row = map_grid(ramp, mask, tokens)

    order = {token: index for index, token in enumerate(tokens)}
    indices = [order[token] for token in row]
    assert indices == sorted(indices), "brightness must never go back down the ramp"


@pytest.mark.parametrize(("mode", "name"), MODE_PRESETS)
def test_mapping_uses_every_level_of_the_preset(mode: str, name: str) -> None:
    tokens = get_charset(mode, name)
    steps = 512
    ramp = np.linspace(0.0, 255.0, steps, dtype=np.float32).reshape(1, steps)

    row = map_grid(ramp, np.ones_like(ramp), tokens)

    assert set(row) == set(tokens)
