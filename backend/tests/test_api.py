"""API contract tests (PRD section 10) without loading the rembg model.

Background removal is stubbed at the pipeline boundary so the suite stays
offline and fast; the real model path is covered by scripts/check.py.
"""

from __future__ import annotations

import io
from collections.abc import Iterator
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

import core.pipeline as pipeline_module
from app.constants import MAX_FILE_BYTES
from app.main import app
from core import segmentation

ASSET_DIR = Path(__file__).resolve().parents[2] / "tests" / "assets"


def gradient_image(size: tuple[int, int] = (120, 120), fmt: str = "PNG") -> bytes:
    """Small image with real tone variation, so it is never treated as blank."""
    width, height = size
    ramp = np.linspace(0, 255, width, dtype=np.uint8)
    pixels = np.tile(ramp, (height, 1))
    rgb = np.repeat(pixels[:, :, None], 3, axis=2)
    buffer = io.BytesIO()
    Image.fromarray(rgb, "RGB").save(buffer, format=fmt)
    return buffer.getvalue()


class CenteredSegmenter:
    """Deterministic stand-in for rembg: keeps the middle half of the image."""

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name

    def segment(self, image: Image.Image) -> np.ndarray:
        mask = np.zeros((image.height, image.width), dtype=np.float32)
        top, bottom = image.height // 4, image.height * 3 // 4
        left, right = image.width // 4, image.width * 3 // 4
        mask[top:bottom, left:right] = 1.0
        return mask


@pytest.fixture(autouse=True)
def no_model_load(monkeypatch: pytest.MonkeyPatch) -> None:
    """Skip the lifespan model load so tests never touch rembg."""
    monkeypatch.setattr(segmentation, "preload_model", lambda *args, **kwargs: None)


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def stubbed_segmenter(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pipeline_module, "RembgSegmenter", CenteredSegmenter)


def post_convert(client: TestClient, data: bytes | None = None, **form: str):
    payload = gradient_image() if data is None else data
    fields = {"remove_bg": "false", **form}
    return client.post(
        "/api/convert",
        files={"image": ("foto.png", payload, "image/png")},
        data=fields,
    )


# --- health -----------------------------------------------------------------


def test_health_reports_status_version_and_model_state(client: TestClient) -> None:
    body = client.get("/api/health").json()

    assert body["status"] == "ok"
    assert body["version"] == "0.1.0"
    assert body["model_loaded"] is False  # preload stubbed out


def test_health_reports_loaded_model(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(segmentation, "is_model_loaded", lambda *args, **kwargs: True)

    assert client.get("/api/health").json()["model_loaded"] is True


# --- success path -----------------------------------------------------------


def test_convert_ascii_returns_text_and_grid_size(client: TestClient) -> None:
    response = post_convert(client, mode="ascii", width="60", remove_bg="false")

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "ascii"
    assert body["width"] == 60
    assert body["height"] == 30  # 60 cols * 1.0 * 0.5 for a square image
    lines = body["text"].split("\n")
    assert len(lines) == body["height"]
    assert all(len(line) == 60 for line in lines)
    assert body["text"].strip(" \n")


def test_convert_emoji_defaults_to_40_columns(client: TestClient) -> None:
    response = post_convert(client, mode="emoji", remove_bg="false")

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "emoji"
    assert body["width"] == 40
    assert all(len(line) == 40 for line in body["text"].split("\n"))


def test_convert_defaults_to_ascii_100_with_background_removal(
    client: TestClient, stubbed_segmenter: None
) -> None:
    response = post_convert(client)  # no form fields at all

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "ascii"
    assert body["width"] == 100
    assert body["height"] == 50


def test_convert_crops_to_the_segmented_subject(
    client: TestClient, stubbed_segmenter: None
) -> None:
    response = post_convert(client, width="40", remove_bg="true")

    body = response.json()
    # The stub keeps a centered 60x60 area of a 120x120 image.
    assert (body["width"], body["height"]) == (40, 20)


def test_invert_swaps_the_character_order(client: TestClient) -> None:
    normal = post_convert(client, width="40", remove_bg="false").json()["text"]
    inverted = post_convert(client, width="40", remove_bg="false", invert="true").json()["text"]

    assert normal != inverted
    assert normal.split("\n")[0][0] == "@"  # dark left edge
    assert inverted.split("\n")[0][0] == " "


def test_charset_preset_is_honoured(client: TestClient) -> None:
    body = post_convert(client, width="40", remove_bg="false", charset="blocks").json()

    assert set(body["text"]) - {"\n"} <= set("█▓▒░ ")


def test_uploaded_asset_converts_end_to_end(client: TestClient, stubbed_segmenter: None) -> None:
    asset = (ASSET_DIR / "person_synthetic.png").read_bytes()

    response = post_convert(client, data=asset, width="50")

    assert response.status_code == 200
    assert response.json()["width"] == 50


# --- 400: bad parameters ----------------------------------------------------


@pytest.mark.parametrize(
    ("form", "fragment"),
    [
        ({"width": "39"}, "antara 40 dan 200"),
        ({"width": "201"}, "antara 40 dan 200"),
        ({"mode": "emoji", "width": "19"}, "antara 20 dan 80"),
        ({"mode": "emoji", "width": "81"}, "antara 20 dan 80"),
        ({"width": "abc"}, "bilangan bulat"),
        ({"mode": "video"}, "Mode harus"),
        ({"mode": "emoji", "charset": "standard"}, "tidak dikenal"),
        ({"invert": "mungkin"}, "harus true atau false"),
        ({"remove_bg": "kadang"}, "harus true atau false"),
    ],
)
def test_invalid_parameters_return_400(client: TestClient, form: dict, fragment: str) -> None:
    response = post_convert(client, **form)

    assert response.status_code == 400
    assert fragment in response.json()["detail"]


def test_missing_image_field_returns_400(client: TestClient) -> None:
    response = client.post("/api/convert", data={"mode": "ascii"})

    assert response.status_code == 400
    assert "image" in response.json()["detail"]


# --- 400: bad files ---------------------------------------------------------


def test_non_image_file_returns_400(client: TestClient) -> None:
    response = post_convert(client, data=b"this is definitely not an image")

    assert response.status_code == 400
    assert "gambar" in response.json()["detail"].lower()


def test_unsupported_format_returns_400(client: TestClient) -> None:
    buffer = io.BytesIO()
    Image.new("RGB", (20, 20), (10, 40, 90)).save(buffer, format="GIF")

    response = post_convert(client, data=buffer.getvalue())

    assert response.status_code == 400
    assert "Format gambar" in response.json()["detail"]


def test_blank_image_returns_400(client: TestClient) -> None:
    buffer = io.BytesIO()
    Image.new("RGB", (80, 80), (250, 250, 250)).save(buffer, format="PNG")

    response = post_convert(client, data=buffer.getvalue())

    assert response.status_code == 400
    assert response.json()["detail"] == "Error, blank image"


def test_oversized_dimensions_return_400(client: TestClient) -> None:
    buffer = io.BytesIO()
    Image.new("RGB", (8100, 10), (0, 0, 0)).save(buffer, format="PNG")

    response = post_convert(client, data=buffer.getvalue())

    assert response.status_code == 400
    assert "Dimensi gambar maksimum" in response.json()["detail"]


# --- 413 --------------------------------------------------------------------


def test_file_over_five_megabytes_returns_413(client: TestClient) -> None:
    oversized = b"\x89PNG\r\n\x1a\n" + b"\0" * MAX_FILE_BYTES

    response = post_convert(client, data=oversized)

    assert response.status_code == 413
    assert "5 MB" in response.json()["detail"]


# --- 500 --------------------------------------------------------------------


def test_pipeline_failure_returns_structured_500(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom(model_name: str):
        raise RuntimeError("onnx session exploded")

    monkeypatch.setattr(pipeline_module, "RembgSegmenter", boom)

    response = post_convert(client, remove_bg="true")

    assert response.status_code == 500
    assert "detail" in response.json()
