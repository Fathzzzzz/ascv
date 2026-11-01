import numpy as np
import pytest
from PIL import Image

import core.segmentation as segmentation
from core.errors import SegmentationError
from core.segmentation import FullMaskSegmenter, RembgSegmenter, normalize_mask


def test_full_mask_segmenter_returns_valid_mask() -> None:
    image = Image.new("RGB", (7, 5))
    mask = FullMaskSegmenter().segment(image)

    assert mask.shape == (5, 7)
    assert mask.dtype == np.float32
    assert np.all(mask == 1.0)


def test_normalize_uint8_mask_to_unit_range() -> None:
    raw = np.array([[0, 128, 255]], dtype=np.uint8)
    mask = normalize_mask(raw, (3, 1))

    assert mask.dtype == np.float32
    assert mask.shape == (1, 3)
    assert mask.min() == pytest.approx(0.0)
    assert mask.max() == pytest.approx(1.0)
    assert mask[0, 1] == pytest.approx(128 / 255)


def test_normalize_mask_resizes_to_image_size() -> None:
    raw = np.array([[255, 0], [0, 255]], dtype=np.uint8)
    mask = normalize_mask(raw, (8, 6))

    assert mask.shape == (6, 8)
    assert np.isfinite(mask).all()
    assert 0.0 <= float(mask.min()) <= float(mask.max()) <= 1.0


def test_normalize_accepts_boolean_and_single_channel_masks() -> None:
    boolean = normalize_mask(np.array([[True, False]], dtype=bool), (2, 1))
    channel = normalize_mask(np.ones((1, 2, 1), dtype=np.uint8) * 255, (2, 1))

    assert np.array_equal(boolean, np.array([[1.0, 0.0]], dtype=np.float32))
    assert np.all(channel == 1.0)


def test_normalize_sanitizes_non_finite_and_out_of_range_values() -> None:
    raw = np.array([[np.nan, -1.0, 2.0, np.inf]], dtype=np.float32)
    mask = normalize_mask(raw, (4, 1))

    assert np.isfinite(mask).all()
    assert np.all(mask >= 0.0) and np.all(mask <= 1.0)


@pytest.mark.parametrize(
    "raw",
    [
        np.array([0, 255], dtype=np.uint8),  # 1D
        np.zeros((2, 2, 3), dtype=np.uint8),  # RGB is not a mask
        np.zeros((2, 2), dtype=np.uint16),  # unsupported dtype
        np.array([], dtype=np.uint8),
    ],
)
def test_normalize_rejects_invalid_masks(raw: np.ndarray) -> None:
    with pytest.raises(SegmentationError):
        normalize_mask(raw, (2, 2))


def test_rembg_segmenter_normalizes_model_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(segmentation, "_get_session", lambda model: object())
    monkeypatch.setattr(
        segmentation,
        "remove_mask",
        lambda image, session: Image.new("L", image.size, 255),
    )

    mask = RembgSegmenter("u2net").segment(Image.new("RGB", (10, 6)))

    assert mask.shape == (6, 10)
    assert mask.dtype == np.float32
    assert np.isfinite(mask).all()
    assert np.all(mask == 1.0)


def test_rembg_segmenter_wraps_model_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(image: Image.Image, session: object) -> Image.Image:
        raise RuntimeError("onnx exploded")

    monkeypatch.setattr(segmentation, "_get_session", lambda model: object())
    monkeypatch.setattr(segmentation, "remove_mask", boom)

    with pytest.raises(SegmentationError):
        RembgSegmenter().segment(Image.new("RGB", (4, 4)))
