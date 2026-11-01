import io

import pytest
from PIL import Image

from core.errors import InvalidImageError
from core.image_io import decode_image


def encode(image: Image.Image, fmt: str, **save_kwargs: object) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format=fmt, **save_kwargs)
    return buffer.getvalue()


@pytest.mark.parametrize("fmt", ["PNG", "JPEG", "WEBP"])
def test_decode_supported_formats(fmt: str) -> None:
    source = encode(Image.new("RGB", (12, 8), (10, 20, 30)), fmt)

    decoded = decode_image(source)

    assert decoded.mode == "RGB"
    assert decoded.size == (12, 8)


def test_decode_from_path(tmp_path) -> None:
    path = tmp_path / "sample.png"
    Image.new("RGB", (5, 4), (1, 2, 3)).save(path)

    decoded = decode_image(path)

    assert decoded.size == (5, 4)


def test_decode_drops_alpha_channel() -> None:
    decoded = decode_image(encode(Image.new("RGBA", (4, 4), (1, 2, 3, 0)), "PNG"))
    assert decoded.mode == "RGB"


def test_decode_applies_exif_orientation() -> None:
    source = Image.new("RGB", (30, 10), (255, 0, 0))
    exif = source.getexif()
    exif[0x0112] = 6  # rotate 90 degrees clockwise

    decoded = decode_image(encode(source, "JPEG", exif=exif))

    assert decoded.size == (10, 30)


def test_decode_rejects_invalid_bytes() -> None:
    with pytest.raises(InvalidImageError):
        decode_image(b"definitely not an image")


def test_decode_rejects_missing_file(tmp_path) -> None:
    with pytest.raises(InvalidImageError):
        decode_image(tmp_path / "missing.png")
