import numpy as np
import pytest
from PIL import Image

import core.pipeline as pipeline_module
from scripts.convert import main
from tests.images import textured

from core import ASCII_CHARSETS, EMOJI_CHARSETS
from core.errors import BLANK_IMAGE_MESSAGE


def save_textured(path, size=(80, 80)) -> None:
    textured(size).save(path)


def test_cli_prints_ascii_art_without_background_removal(tmp_path, capsys) -> None:
    image_path = tmp_path / "photo.png"
    save_textured(image_path)

    exit_code = main([str(image_path), "--no-remove-bg", "--width", "40"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err.strip().endswith("40 kolom x 20 baris")
    lines = captured.out.strip("\n").split("\n")
    assert len(lines) == 20
    assert all(len(line) == 40 for line in lines)
    assert set("".join(lines)) - {" "}  # not blank


def test_cli_writes_emoji_output_file(tmp_path, capsys) -> None:
    image_path = tmp_path / "photo.png"
    output_path = tmp_path / "hasil.txt"
    save_textured(image_path)

    exit_code = main(
        [
            str(image_path),
            "--no-remove-bg",
            "--mode",
            "emoji",
            "--width",
            "20",
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0
    content = output_path.read_text(encoding="utf-8")
    first_line = content.splitlines()[0]
    assert len(first_line) == 20
    assert set(first_line) <= set(EMOJI_CHARSETS["moon"])
    assert "Hasil disimpan" in capsys.readouterr().err


def test_cli_charset_flag_changes_glyphs(tmp_path, capsys) -> None:
    image_path = tmp_path / "photo.png"
    save_textured(image_path)

    exit_code = main(
        [str(image_path), "--no-remove-bg", "--charset", "blocks", "--width", "40"]
    )

    assert exit_code == 0
    used = set(capsys.readouterr().out) - {"\n"}
    assert used <= set(ASCII_CHARSETS["blocks"])


def test_cli_returns_blank_image_error_for_missing_file(tmp_path, capsys) -> None:
    exit_code = main([str(tmp_path / "missing.png")])

    assert exit_code == 1
    assert capsys.readouterr().err.strip() == BLANK_IMAGE_MESSAGE


def test_cli_returns_blank_image_error_for_unreadable_file(tmp_path, capsys) -> None:
    corrupt = tmp_path / "corrupt.png"
    corrupt.write_bytes(b"not really a png")

    exit_code = main([str(corrupt)])

    assert exit_code == 1
    assert capsys.readouterr().err.strip() == BLANK_IMAGE_MESSAGE


def test_cli_returns_blank_image_error_for_flat_image(tmp_path, capsys) -> None:
    flat = tmp_path / "flat.png"
    Image.new("RGB", (100, 100), (255, 255, 255)).save(flat)

    exit_code = main([str(flat), "--no-remove-bg"])

    assert exit_code == 1
    assert capsys.readouterr().err.strip() == BLANK_IMAGE_MESSAGE


def test_cli_returns_blank_image_error_when_subject_is_missing(tmp_path, capsys, monkeypatch) -> None:
    image_path = tmp_path / "photo.png"
    save_textured(image_path)
    empty_mask = np.zeros((80, 80), dtype=np.float32)

    class NoSubject:
        def segment(self, image):
            return empty_mask

    monkeypatch.setattr(pipeline_module, "RembgSegmenter", lambda model: NoSubject())

    exit_code = main([str(image_path), "--width", "40"])

    assert exit_code == 1
    assert capsys.readouterr().err.strip() == BLANK_IMAGE_MESSAGE


def test_cli_reports_option_errors_with_detail(tmp_path, capsys) -> None:
    image_path = tmp_path / "photo.png"
    save_textured(image_path)

    exit_code = main([str(image_path), "--no-remove-bg", "--width", "500"])

    assert exit_code == 1
    assert "antara 40 dan 200" in capsys.readouterr().err


def test_cli_blank_message_constant_matches_core() -> None:
    assert BLANK_IMAGE_MESSAGE == "Error, blank image"


@pytest.mark.parametrize("width", ["40", "200"])
def test_cli_accepts_ascii_width_bounds(tmp_path, capsys, width: str) -> None:
    image_path = tmp_path / "photo.png"
    save_textured(image_path, (120, 120))

    assert main([str(image_path), "--no-remove-bg", "--width", width]) == 0
    assert f"{width} kolom" in capsys.readouterr().err
