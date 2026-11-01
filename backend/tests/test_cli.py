from PIL import Image

from scripts.convert import main


def make_image(path, size=(80, 80), value=0) -> None:
    Image.new("RGB", size, (value, value, value)).save(path)


def test_cli_prints_ascii_art_without_background_removal(tmp_path, capsys) -> None:
    image_path = tmp_path / "dark.png"
    make_image(image_path)

    exit_code = main([str(image_path), "--no-remove-bg", "--width", "40"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err.strip().endswith("40 kolom x 20 baris")
    lines = captured.out.strip("\n").split("\n")
    assert len(lines) == 20
    assert all(line == "@" * 40 for line in lines)


def test_cli_writes_output_file(tmp_path, capsys) -> None:
    image_path = tmp_path / "dark.png"
    output_path = tmp_path / "hasil.txt"
    make_image(image_path)

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
    assert content.splitlines()[0] == "🌑" * 20
    assert "Hasil disimpan" in capsys.readouterr().err


def test_cli_returns_error_for_missing_file(tmp_path, capsys) -> None:
    exit_code = main([str(tmp_path / "missing.png")])

    assert exit_code == 1
    assert "Error:" in capsys.readouterr().err
