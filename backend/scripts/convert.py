#!/usr/bin/env python3
"""Terminal runner for the core pipeline, with no API involved.

Examples (run from backend/):
    python -m scripts.convert foto.jpg
    python -m scripts.convert foto.jpg --mode emoji --width 40 --invert
    python -m scripts.convert foto.jpg --no-remove-bg --output hasil.txt

The first run with background removal downloads the rembg model (~176 MB for
u2net) and can take a while; later runs reuse the cached session/model.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Allow both `python -m scripts.convert` and `python scripts/convert.py`.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core import (  # noqa: E402  (path bootstrap must run first)
    BLANK_IMAGE_MESSAGE,
    DEFAULT_CLIP_LIMIT,
    DEFAULT_REMBG_MODEL,
    ConversionOptions,
    CoreError,
    InvalidOptionError,
    convert_image,
    decode_image,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ubah gambar menjadi ASCII atau emoji art di terminal.",
    )
    parser.add_argument("image", type=Path, help="Path gambar (jpg, png, webp).")
    parser.add_argument("-o", "--output", type=Path, help="Simpan hasil ke file .txt.")
    parser.add_argument("--mode", choices=("ascii", "emoji"), default="ascii")
    parser.add_argument(
        "--width",
        type=int,
        default=None,
        help="Jumlah kolom (ASCII 40-200, emoji 20-80).",
    )
    parser.add_argument("--charset", default=None, help="Nama preset charset.")
    parser.add_argument("--invert", action="store_true", help="Balik gelap dan terang.")
    parser.add_argument(
        "--no-remove-bg",
        dest="remove_bg",
        action="store_false",
        help="Jangan hapus latar belakang (tanpa model rembg).",
    )
    parser.add_argument("--contrast", type=float, default=1.0, help="Faktor kontras linear.")
    parser.add_argument(
        "--clahe",
        type=float,
        default=DEFAULT_CLIP_LIMIT,
        help="Batas clip equalization lokal (0 = nonaktif).",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("REMBG_MODEL", DEFAULT_REMBG_MODEL),
        help="Nama model rembg (default dari env REMBG_MODEL atau u2net).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    options = ConversionOptions(
        width=args.width,
        mode=args.mode,
        charset=args.charset,
        invert=args.invert,
        remove_bg=args.remove_bg,
        contrast=args.contrast,
        clahe=args.clahe,
        model_name=args.model,
    )

    try:
        image = decode_image(args.image)
        result = convert_image(image, options)
    except InvalidOptionError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except CoreError:
        # Undecodable, unsegmentable, or empty subject: nothing usable to print.
        print(BLANK_IMAGE_MESSAGE, file=sys.stderr)
        return 1

    text = result.text + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
        print(f"Hasil disimpan di {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(text)
    print(
        f"[{result.mode}] {result.width} kolom x {result.height} baris",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
