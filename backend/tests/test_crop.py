import numpy as np
import pytest
from PIL import Image

from core.crop import CROP_MASK_THRESHOLD, crop_to_subject, has_subject, subject_bbox
from core.errors import SegmentationError


def test_subject_bbox_finds_tight_bounds() -> None:
    mask = np.zeros((10, 20), dtype=np.float32)
    mask[2:7, 4:13] = 1.0

    assert subject_bbox(mask) == (4, 2, 13, 7)


def test_subject_bbox_ignores_soft_values_below_threshold() -> None:
    mask = np.zeros((5, 5), dtype=np.float32)
    mask[1, 1] = 0.05
    mask[3, 3] = 0.2

    assert subject_bbox(mask, threshold=0.1) == (3, 3, 4, 4)


def test_subject_bbox_returns_none_for_empty_mask() -> None:
    assert subject_bbox(np.zeros((4, 4), dtype=np.float32)) is None


def test_crop_cuts_image_and_mask_together() -> None:
    image = Image.new("RGB", (20, 10), (1, 2, 3))
    mask = np.zeros((10, 20), dtype=np.float32)
    mask[2:8, 5:15] = 1.0

    cropped_image, cropped_mask = crop_to_subject(image, mask)

    assert cropped_image.size == (10, 6)
    assert cropped_mask.shape == (6, 10)
    assert np.all(cropped_mask == 1.0)


def test_crop_returns_full_frame_when_mask_is_empty() -> None:
    image = Image.new("RGB", (8, 6), (4, 5, 6))
    mask = np.zeros((6, 8), dtype=np.float32)

    cropped_image, cropped_mask = crop_to_subject(image, mask)

    assert cropped_image.size == image.size
    assert cropped_image is not image
    assert np.array_equal(cropped_mask, mask)


def test_crop_rejects_mask_with_wrong_size() -> None:
    with pytest.raises(SegmentationError):
        crop_to_subject(
            Image.new("RGB", (8, 6)),
            np.zeros((6, 7), dtype=np.float32),
        )


def test_has_subject_follows_the_crop_threshold() -> None:
    mask = np.zeros((4, 4), dtype=np.float32)
    mask[1, 1] = CROP_MASK_THRESHOLD / 2

    assert not has_subject(mask)
    assert has_subject(mask, threshold=CROP_MASK_THRESHOLD / 4)
    assert not has_subject(np.zeros((4, 4), dtype=np.float32))


def test_has_subject_rejects_non_2d_mask() -> None:
    with pytest.raises(SegmentationError):
        has_subject(np.zeros((4, 4, 3), dtype=np.float32))
