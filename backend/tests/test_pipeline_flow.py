"""End-to-end pipeline tests using a fake segmenter (no rembg, no network)."""

import numpy as np
import pytest
from PIL import Image

from core import ConversionOptions, ConversionResult, convert_image, resolve_width
from core.errors import InvalidOptionError


class FakeSegmenter:
    def __init__(self, mask: np.ndarray) -> None:
        self.mask = mask
        self.calls: list[tuple[int, int]] = []

    def segment(self, image: Image.Image) -> np.ndarray:
        self.calls.append(image.size)
        return self.mask


def half_black_half_white(size: int = 80) -> Image.Image:
    pixels = np.zeros((size, size, 3), dtype=np.uint8)
    pixels[:, size // 2:] = 255
    return Image.fromarray(pixels, mode="RGB")


def ones(size: tuple[int, int]) -> np.ndarray:
    width, height = size
    return np.ones((height, width), dtype=np.float32)


def test_ascii_result_has_requested_columns_and_corrected_rows() -> None:
    image = Image.new("RGB", (200, 100), (128, 128, 128))
    result = convert_image(
        image,
        ConversionOptions(width=40),
        segmenter=FakeSegmenter(ones((200, 100))),
    )

    assert isinstance(result, ConversionResult)
    assert result.mode == "ascii"
    assert result.width == 40
    assert result.height == 10  # 40 cols * (100/200) * 0.5
    lines = result.text.split("\n")
    assert len(lines) == 10
    assert all(len(line) == 40 for line in lines)


def test_emoji_aspect_ratio_is_square() -> None:
    image = Image.new("RGB", (200, 100), (128, 128, 128))
    result = convert_image(
        image,
        ConversionOptions(mode="emoji", width=40),
        segmenter=FakeSegmenter(ones((200, 100))),
    )

    assert result.mode == "emoji"
    assert (result.width, result.height) == (40, 20)
    lines = result.text.split("\n")
    assert len(lines) == 20
    assert all(len(line) == 40 for line in lines)  # one token per emoji, no ZWJ parts


def test_crop_removes_empty_border_before_gridding() -> None:
    image = Image.new("RGB", (200, 50), (30, 30, 30))
    mask = np.zeros((50, 200), dtype=np.float32)
    mask[:, 50:150] = 1.0  # subject occupies the middle 100 px

    result = convert_image(
        image,
        ConversionOptions(width=40),
        segmenter=FakeSegmenter(mask),
    )

    # Cropped subject is 100x50: 40 cols * 0.5 * 0.5 = 10 rows.
    assert result.width == 40
    assert result.height == 10


def test_cells_outside_mask_are_spaces_even_when_bright() -> None:
    image = half_black_half_white(80)
    mask = np.zeros((80, 80), dtype=np.float32)
    mask[:, :40] = 1.0
    mask[-1, :] = 1.0  # keep the crop at full width so the right half survives

    result = convert_image(
        image,
        ConversionOptions(width=40),
        segmenter=FakeSegmenter(mask),
    )

    first_row = result.text.split("\n")[0]
    assert first_row[0] == "@"  # dark subject
    assert first_row[-1] == " "  # bright background inside the crop


def test_empty_mask_yields_all_blanks() -> None:
    image = Image.new("RGB", (40, 40), (255, 255, 255))
    result = convert_image(
        image,
        ConversionOptions(width=40),
        segmenter=FakeSegmenter(np.zeros((40, 40), dtype=np.float32)),
    )

    lines = result.text.split("\n")
    assert len(lines) == 20
    assert all(set(line) == {" "} for line in lines)


def test_invert_flips_dark_to_light() -> None:
    image = half_black_half_white(80)
    mask = ones((80, 80))

    normal = convert_image(image, ConversionOptions(width=40), segmenter=FakeSegmenter(mask))
    inverted = convert_image(
        image,
        ConversionOptions(width=40, invert=True),
        segmenter=FakeSegmenter(mask),
    )

    normal_row = normal.text.split("\n")[0]
    inverted_row = inverted.text.split("\n")[0]
    assert normal_row[0] == "@"
    assert normal_row[-1] == " "
    assert inverted_row[0] == " "
    assert inverted_row[-1] == "@"


def test_default_width_depends_on_mode() -> None:
    image = Image.new("RGB", (100, 100), (10, 10, 10))
    mask = ones((100, 100))

    ascii_result = convert_image(image, segmenter=FakeSegmenter(mask))
    emoji_result = convert_image(
        image,
        ConversionOptions(mode="emoji"),
        segmenter=FakeSegmenter(mask),
    )

    assert ascii_result.width == 100
    assert emoji_result.width == 40


def test_width_bounds_follow_prd() -> None:
    assert resolve_width("ascii", 40) == 40
    assert resolve_width("ascii", 200) == 200
    assert resolve_width("emoji", 20) == 20
    assert resolve_width("emoji", 80) == 80
    assert resolve_width("ascii", None) == 100
    assert resolve_width("emoji", None) == 40

    for mode, width in [("ascii", 39), ("ascii", 201), ("emoji", 19), ("emoji", 81)]:
        with pytest.raises(InvalidOptionError):
            resolve_width(mode, width)


def test_width_rejects_booleans_and_non_integers() -> None:
    with pytest.raises(InvalidOptionError):
        resolve_width("ascii", True)  # type: ignore[arg-type]
    with pytest.raises(InvalidOptionError):
        resolve_width("ascii", "80")  # type: ignore[arg-type]


def test_remove_bg_false_ignores_injected_segmenter() -> None:
    image = Image.new("RGB", (60, 60), (20, 20, 20))
    fake = FakeSegmenter(np.zeros((60, 60), dtype=np.float32))

    result = convert_image(
        image,
        ConversionOptions(width=40, remove_bg=False),
        segmenter=fake,
    )

    assert result.height == 20
    assert fake.calls == []
    assert set(result.text.split("\n")) == {"%" * 40}


def test_emoji_with_ascii_charset_is_rejected() -> None:
    image = Image.new("RGB", (40, 40), (10, 10, 10))
    with pytest.raises(InvalidOptionError):
        convert_image(
            image,
            ConversionOptions(mode="emoji", charset="standard"),
            segmenter=FakeSegmenter(ones((40, 40))),
        )
