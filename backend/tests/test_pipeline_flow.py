"""End-to-end pipeline tests using a fake segmenter (no rembg, no network)."""

import numpy as np
import pytest
from PIL import Image

from tests.images import half_black_half_white, textured

from core import ConversionOptions, ConversionResult, convert_image, resolve_width
from core.errors import EmptySubjectError, InvalidOptionError


class FakeSegmenter:
    def __init__(self, mask: np.ndarray) -> None:
        self.mask = mask
        self.calls: list[tuple[int, int]] = []

    def segment(self, image: Image.Image) -> np.ndarray:
        self.calls.append(image.size)
        return self.mask


def ones(size: tuple[int, int]) -> np.ndarray:
    width, height = size
    return np.ones((height, width), dtype=np.float32)


def test_ascii_result_has_requested_columns_and_corrected_rows() -> None:
    image = textured((200, 100))
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
    image = textured((200, 100))
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
    image = textured((200, 50))
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
    image = textured((100, 100))

    ascii_result = convert_image(image, segmenter=FakeSegmenter(ones((100, 100))))
    emoji_result = convert_image(
        image,
        ConversionOptions(mode="emoji"),
        segmenter=FakeSegmenter(ones((100, 100))),
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
    image = textured((60, 60))
    fake = FakeSegmenter(np.zeros((60, 60), dtype=np.float32))

    without_bg_removal = convert_image(
        image,
        ConversionOptions(width=40, remove_bg=False),
        segmenter=fake,
    )
    reference = convert_image(
        image,
        ConversionOptions(width=40, remove_bg=False),
        segmenter=FakeSegmenter(ones((60, 60))),
    )

    assert fake.calls == []
    assert without_bg_removal.text == reference.text
    assert without_bg_removal.text.strip(" \n") != ""


def test_emoji_with_ascii_charset_is_rejected() -> None:
    with pytest.raises(InvalidOptionError):
        convert_image(
            textured((40, 40)),
            ConversionOptions(mode="emoji", charset="standard"),
            segmenter=FakeSegmenter(ones((40, 40))),
        )


def test_pipeline_is_deterministic() -> None:
    image = textured((90, 70), seed=7)
    mask = ones((90, 70))

    first = convert_image(image, ConversionOptions(width=60), segmenter=FakeSegmenter(mask))
    second = convert_image(image, ConversionOptions(width=60), segmenter=FakeSegmenter(mask))

    assert first.text == second.text


def test_charset_option_reaches_the_mapping_stage() -> None:
    image = textured((80, 80))
    result = convert_image(
        image,
        ConversionOptions(width=40, charset="blocks"),
        segmenter=FakeSegmenter(ones((80, 80))),
    )

    assert set(result.text) - {"\n"} <= set("█▓▒░ ")


def test_emoji_output_respects_requested_width_in_tokens() -> None:
    image = textured((80, 80))

    for width in (20, 40, 80):
        result = convert_image(
            image,
            ConversionOptions(mode="emoji", width=width),
            segmenter=FakeSegmenter(ones((80, 80))),
        )
        lines = result.text.split("\n")
        assert len(lines) == width  # square cells keep rows == cols for a square crop
        assert all(len(line) == width for line in lines)


# --- blank / unprocessable images -------------------------------------------


def test_empty_mask_raises_blank_image_error() -> None:
    with pytest.raises(EmptySubjectError, match="^Error, blank image$"):
        convert_image(
            textured((40, 40)),
            ConversionOptions(width=40),
            segmenter=FakeSegmenter(np.zeros((40, 40), dtype=np.float32)),
        )


def test_flat_image_is_rejected_before_segmentation() -> None:
    fake = FakeSegmenter(ones((40, 40)))

    with pytest.raises(EmptySubjectError, match="^Error, blank image$"):
        convert_image(
            Image.new("RGB", (40, 40), (255, 255, 255)),
            ConversionOptions(width=40),
            segmenter=fake,
        )

    assert fake.calls == [], "a flat frame must not pay for model inference"


def test_flat_image_is_rejected_even_without_background_removal() -> None:
    with pytest.raises(EmptySubjectError):
        convert_image(
            Image.new("RGB", (60, 60), (12, 12, 12)),
            ConversionOptions(width=40, remove_bg=False),
        )


def test_mask_on_a_featureless_region_is_rejected() -> None:
    # Left half is flat white, right half has tone; the mask grabs the flat half.
    pixels = np.zeros((60, 60, 3), dtype=np.uint8)
    pixels[:, :30] = 255
    pixels[:, 30:] = np.linspace(0, 255, 30, dtype=np.uint8)[None, :, None]
    mask = np.zeros((60, 60), dtype=np.float32)
    mask[:, :30] = 1.0

    with pytest.raises(EmptySubjectError, match="^Error, blank image$"):
        convert_image(
            Image.fromarray(pixels, mode="RGB"),
            ConversionOptions(width=40),
            segmenter=FakeSegmenter(mask),
        )


def test_soft_mask_below_crop_threshold_counts_as_blank() -> None:
    faint = np.full((40, 40), 0.05, dtype=np.float32)  # below CROP_MASK_THRESHOLD

    with pytest.raises(EmptySubjectError):
        convert_image(
            textured((40, 40)),
            ConversionOptions(width=40),
            segmenter=FakeSegmenter(faint),
        )
