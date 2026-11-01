"""Brightness-to-character mapping.

Every preset is ordered **dark to light**: index 0 is used for the darkest
cells and the last entry for the brightest ones. `invert` flips that mapping.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from .errors import InvalidOptionError

# Classic 70-level ramp, reversed to dark-to-light.
_DENSE_LIGHT_TO_DARK = " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"

ASCII_CHARSETS: dict[str, str] = {
    "standard": "@%#*+=-:. ",
    "dense": _DENSE_LIGHT_TO_DARK[::-1],
    "blocks": "█▓▒░ ",
}

EMOJI_CHARSETS: dict[str, tuple[str, ...]] = {
    "moon": ("🌑", "🌒", "🌓", "🌔", "🌕"),
    "squares": ("⬛", "🟫", "🟪", "🟦", "🟩", "🟨", "🟧", "⬜"),
}

DEFAULT_CHARSET = {"ascii": "standard", "emoji": "moon"}
DEFAULT_EMPTY_CELL = " "


def get_charset(mode: str, name: str | None = None) -> tuple[str, ...]:
    """Return the preset tokens for a mode, validating the name."""
    if mode not in DEFAULT_CHARSET:
        raise InvalidOptionError("Mode harus 'ascii' atau 'emoji'.")

    presets: dict[str, Sequence[str]]
    if mode == "ascii":
        presets = ASCII_CHARSETS
    else:
        presets = EMOJI_CHARSETS

    charset_name = name or DEFAULT_CHARSET[mode]
    if charset_name not in presets:
        available = ", ".join(sorted(presets))
        raise InvalidOptionError(
            f"Charset '{charset_name}' tidak dikenal untuk mode {mode}. Pilihan: {available}."
        )
    return tuple(presets[charset_name])


def map_grid(
    gray_grid: np.ndarray,
    mask_grid: np.ndarray,
    charset: Sequence[str],
    *,
    invert: bool = False,
    mask_threshold: float = 0.5,
    empty_cell: str = DEFAULT_EMPTY_CELL,
) -> str:
    """Map each luminance cell to a charset token; blank cells outside the mask."""
    if gray_grid.ndim != 2 or mask_grid.ndim != 2:
        raise InvalidOptionError("Grayscale dan mask harus array 2D.")
    if gray_grid.shape != mask_grid.shape:
        raise InvalidOptionError("Grayscale dan mask harus berukuran sama.")
    if not charset:
        raise InvalidOptionError("Charset tidak boleh kosong.")
    if any(not isinstance(token, str) or token == "" for token in charset):
        raise InvalidOptionError("Setiap token charset harus string tidak kosong.")
    if not 0.0 <= mask_threshold <= 1.0:
        raise InvalidOptionError("Ambang mask harus di antara 0 dan 1.")
    if not isinstance(empty_cell, str):
        raise InvalidOptionError("Sel kosong harus berupa string.")

    tokens = np.asarray(list(charset), dtype=object)
    brightness = np.clip(gray_grid.astype(np.float32), 0.0, 255.0) / 255.0
    if invert:
        brightness = 1.0 - brightness

    indices = np.rint(brightness * (len(tokens) - 1)).astype(np.intp)
    outside = mask_grid < mask_threshold

    lines: list[str] = []
    for row_indices, row_outside in zip(indices, outside, strict=True):
        cells = tokens[row_indices]
        lines.append("".join(empty_cell if is_outside else str(cell)
                             for cell, is_outside in zip(cells, row_outside, strict=True)))
    return "\n".join(lines)
