#!/usr/bin/env python3
"""Pemeriksaan otomatis untuk aplikasi lokal.

    python scripts/check.py            # semua pemeriksaan
    python scripts/check.py --no-suites  # lewati pytest/vitest/build

Setiap item dicetak PASS atau FAIL beserta saran perbaikan. Exit code 1 bila ada
yang gagal. Skrip ini tidak mengubah apa pun: hanya membaca, memanggil HTTP, dan
menjalankan test suite.

Prasyarat: backend di port 8000 dan frontend di port 6744 sudah berjalan.
"""

from __future__ import annotations

import argparse
import json
import re
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
ASSET = ROOT / "tests" / "assets" / "person_synthetic.png"
VENV_PYTHON = BACKEND / ".venv" / "bin" / "python"

# Port tetap sesuai keputusan proyek (backend/app/constants.py, vite.config.js).
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:6744"

MIN_PYTHON = (3, 10)
MAX_PYTHON = (3, 13)  # rembg/onnxruntime belum punya wheel untuk 3.14
MIN_NODE = (18, 0)
MAX_FILE_BYTES = 5 * 1024 * 1024
HTTP_TIMEOUT = 30
MODEL_LOAD_TIMEOUT = 300
SUITE_TIMEOUT = 600


@dataclass
class Check:
    name: str
    ok: bool
    detail: str
    advice: str = ""


def backend_python() -> Path:
    """Prefer the project venv so checks work even without `source .venv/bin/activate`."""
    return VENV_PYTHON if VENV_PYTHON.exists() else Path(sys.executable)


def run(cmd: list[str], cwd: Path, timeout: int = 120) -> tuple[int, str]:
    try:
        process = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return 127, f"perintah tidak ditemukan: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return 124, f"timeout setelah {timeout} detik"
    return process.returncode, (process.stdout + process.stderr).strip()


def tail(text: str, lines: int = 12) -> str:
    return "\n".join(text.strip().splitlines()[-lines:])


def http_get(url: str, timeout: int = 5) -> tuple[int, bytes]:
    request = urllib.request.Request(url, headers={"Accept": "*/*"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()
    except (urllib.error.URLError, OSError) as exc:
        return 0, str(exc).encode()


def build_multipart(fields: dict[str, str], filename: str, content: bytes) -> tuple[bytes, str]:
    boundary = f"----ascv{uuid.uuid4().hex}"
    parts: list[bytes] = []
    for key, value in fields.items():
        parts.append(
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{key}"\r\n\r\n'
                f"{value}\r\n"
            ).encode()
        )
    parts.append(
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'
            "Content-Type: application/octet-stream\r\n\r\n"
        ).encode()
    )
    parts.append(content)
    parts.append(f"\r\n--{boundary}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def post_convert(base_url: str, content: bytes, **fields: str) -> tuple[int, dict]:
    body, content_type = build_multipart(fields, "sample.png", content)
    request = urllib.request.Request(
        f"{base_url}/api/convert",
        data=body,
        method="POST",
        headers={"Content-Type": content_type},
    )
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:
            return response.status, json.loads(response.read() or b"{}")
    except urllib.error.HTTPError as exc:
        try:
            return exc.code, json.loads(exc.read() or b"{}")
        except json.JSONDecodeError:
            return exc.code, {}
    except (urllib.error.URLError, OSError) as exc:
        return 0, {"detail": str(exc)}


# --- individual checks -------------------------------------------------------


def check_python_version() -> Check:
    version = sys.version_info
    python = backend_python()
    _, backend_version = run([str(python), "-c", "import sys;print(sys.version.split()[0])"], ROOT, 30)
    detail = f"runner Python {version.major}.{version.minor}.{version.micro}"
    if python != Path(sys.executable):
        detail += f", interpreter backend {backend_version}"

    ok = MIN_PYTHON <= (version.major, version.minor) <= MAX_PYTHON and MIN_PYTHON <= (
        tuple(int(part) for part in backend_version.split(".")[:2]) if backend_version else (0, 0)
    ) <= MAX_PYTHON
    return Check(
        "a1. Versi Python",
        ok,
        detail,
        f"Pakai Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}–{MAX_PYTHON[1]}: "
        "`python3.12 -m venv backend/.venv` (rembg belum mendukung 3.14).",
    )


def check_node_version() -> Check:
    if not shutil.which("node"):
        return Check("a2. Versi Node", False, "node tidak ditemukan", "Install Node.js 18+ (mis. brew install node).")
    code, output = run(["node", "--version"], ROOT, 30)
    raw = output.strip().lstrip("v")
    version = tuple(int(part) for part in raw.split(".")[:2]) if code == 0 else (0, 0)
    return Check("a2. Versi Node", version >= MIN_NODE, raw or output, "Install Node.js 18 atau lebih baru.")


def check_backend_deps() -> Check:
    script = (
        "import fastapi, uvicorn, PIL, numpy, cv2, rembg, pytest, httpx;"
        "print('fastapi', fastapi.__version__, '| numpy', numpy.__version__,"
        "'| opencv', cv2.__version__, '| pillow', PIL.__version__)"
    )
    code, output = run([str(backend_python()), "-c", script], BACKEND, 120)
    return Check(
        "b1. Dependency backend",
        code == 0,
        tail(output, 4),
        "Aktifkan venv lalu `pip install -r backend/requirements.txt`.",
    )


def check_frontend_deps() -> Check:
    missing = [name for name in ("vite", "react", "vitest") if not (FRONTEND / "node_modules" / name).exists()]
    return Check(
        "b2. Dependency frontend",
        not missing and (FRONTEND / "node_modules").is_dir(),
        "node_modules lengkap" if not missing else f"belum ada: {', '.join(missing)}",
        "`cd frontend && npm install`.",
    )


def check_model() -> Check:
    script = """
import os, pathlib
from rembg import new_session
session = new_session("u2net")
path = pathlib.Path(os.environ.get("U2NET_HOME", pathlib.Path.home() / ".u2net")) / "u2net.onnx"
size = path.stat().st_size // (1024 * 1024) if path.exists() else 0
print(f"sesi ok; model {path} ({size} MB)")
"""
    started = time.perf_counter()
    code, output = run([str(backend_python()), "-c", script], BACKEND, MODEL_LOAD_TIMEOUT)
    elapsed = time.perf_counter() - started
    ok = code == 0 and "sesi ok" in output
    detail = f"{tail(output, 2)} ({elapsed:.1f} detik)"
    advice = (
        "Jalankan sekali dengan koneksi internet agar model u2net (~176 MB) terunduh: "
        "`python -m scripts.convert tests/assets/person_synthetic.png`."
    )
    return Check("c. Model rembg", ok, detail, advice if not ok else "")


def check_backend_running() -> Check:
    status, body = http_get(f"{BACKEND_URL}/api/health")
    if status != 200:
        return Check(
            "d. Backend /api/health",
            False,
            f"tidak ada respons (status {status})",
            "Jalankan: `cd backend && source .venv/bin/activate && uvicorn app.main:app --port 8000`.",
        )
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return Check("d. Backend /api/health", False, "respons bukan JSON", "Periksa log uvicorn.")

    ok = payload.get("status") == "ok" and "model_loaded" in payload and "version" in payload
    detail = (
        f"status={payload.get('status')} model_loaded={payload.get('model_loaded')} "
        f"version={payload.get('version')}"
    )
    return Check("d. Backend /api/health", ok, detail, "Periksa log uvicorn untuk error saat start.")


def check_frontend_running() -> Check:
    status, body = http_get(f"{FRONTEND_URL}/")
    ok = status == 200 and b'id="root"' in body
    return Check(
        "e. Frontend dev server",
        ok,
        f"status {status}" if status else "tidak ada respons",
        "Jalankan: `cd frontend && npm run dev` (port 6744).",
    )


def check_proxy() -> Check:
    status, body = http_get(f"{FRONTEND_URL}/api/health")
    ok = False
    detail = f"status {status}"
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        detail += ", respons bukan JSON"
    else:
        # Another app could occupy the port and answer /api/health; require our contract.
        if "version" in payload and payload.get("status") == "ok":
            ok = True
            detail += f", proxy /api → :8000 (status=ok, version={payload['version']})"
        else:
            detail += f", bukan API aplikasi ini: {str(payload)[:80]}"
    return Check(
        "f. Proxy frontend → backend",
        ok,
        detail,
        "Pastikan `npm run dev` berjalan dan vite.config.js memuat proxy /api ke localhost:8000.",
    )


def check_convert(mode: str, width: int) -> Check:
    asset = ASSET.read_bytes()
    status, payload = post_convert(FRONTEND_URL, asset, mode=mode, width=str(width), remove_bg="true")
    text = payload.get("text", "")
    lines = text.split("\n") if text else []
    widths = {len(line) for line in lines}
    ok = (
        status == 200
        and bool(text.strip())
        and payload.get("width") == width
        and widths == {width}
        and payload.get("mode") == mode
    )
    detail = (
        f"status={status} mode={payload.get('mode')} "
        f"{payload.get('width')}x{payload.get('height')} baris={len(lines)}"
    )
    if status != 200:
        detail += f" detail={payload.get('detail')}"
    return Check(
        f"g. Convert {mode} ({width} kolom)",
        ok,
        detail,
        "Pastikan model termuat dan gambar contoh tests/assets/person_synthetic.png ada.",
    )


def check_error_non_image() -> Check:
    status, payload = post_convert(FRONTEND_URL, b"ini bukan gambar", mode="ascii", width="60")
    return Check(
        "h1. Error file bukan gambar → 400",
        status == 400,
        f"status={status} detail={payload.get('detail')}",
        "Pastikan validasi tipe file di backend/app/service.py aktif.",
    )


def check_error_too_large() -> Check:
    asset = ASSET.read_bytes()
    oversized = asset + b"\0" * (MAX_FILE_BYTES + 1024 - len(asset))
    status, payload = post_convert(FRONTEND_URL, oversized, mode="ascii", width="60")
    return Check(
        "h2. Error file > 5 MB → 413",
        status == 413,
        f"status={status} detail={payload.get('detail')}",
        "Pastikan batas MAX_FILE_BYTES diterapkan saat membaca upload.",
    )


def summarize(output: str, pattern: str) -> str:
    """Pick the one-line suite summary (e.g. '154 passed in 0.6s')."""
    match = re.search(pattern, output, flags=re.MULTILINE)
    return match.group(0).strip() if match else tail(output, 3)


def check_pytest() -> Check:
    code, output = run([str(backend_python()), "-m", "pytest"], BACKEND, SUITE_TIMEOUT)
    summary = summarize(output, r"^=*\s*\d+ (?:passed|failed).*$|^\d+ (?:passed|failed).*$")
    return Check("i. pytest", code == 0, summary, "Perbaiki test yang gagal: `cd backend && pytest`.")


def check_vitest() -> Check:
    npx = shutil.which("npx")
    if not npx:
        return Check("j. vitest", False, "npx tidak ditemukan", "Install Node.js lalu `cd frontend && npm install`.")
    code, output = run([npx, "vitest", "run"], FRONTEND, SUITE_TIMEOUT)
    summary = summarize(output, r"^\s*(?:Tests|Test Files)\s+.*$")
    return Check("j. vitest", code == 0, summary, "Perbaiki test frontend: `cd frontend && npx vitest run`.")


def check_build() -> Check:
    npm = shutil.which("npm")
    if not npm:
        return Check("k. Build frontend", False, "npm tidak ditemukan", "Install Node.js lalu `npm install`.")
    code, output = run([npm, "run", "build"], FRONTEND, SUITE_TIMEOUT)
    built = (FRONTEND / "dist" / "index.html").exists()
    return Check(
        "k. Build frontend",
        code == 0 and built,
        "dist/index.html dibuat" if code == 0 else tail(output, 5),
        "Perbaiki error build: `cd frontend && npm run build`.",
    )


# --- runner -----------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    global FRONTEND_URL
    parser = argparse.ArgumentParser(description="Cek aplikasi ASCII/emoji converter secara end-to-end.")
    parser.add_argument("--no-suites", action="store_true", help="Lewati pytest, vitest, dan build.")
    parser.add_argument(
        "--frontend-url",
        default=FRONTEND_URL,
        help="Alamat frontend (default http://localhost:6744; hanya untuk diagnostik).",
    )
    args = parser.parse_args(argv)
    FRONTEND_URL = args.frontend_url.rstrip("/")

    checks: list[Check] = [
        check_python_version(),
        check_node_version(),
        check_backend_deps(),
        check_frontend_deps(),
        check_model(),
        check_backend_running(),
        check_frontend_running(),
        check_proxy(),
        check_convert("ascii", 60),
        check_convert("emoji", 30),
        check_error_non_image(),
        check_error_too_large(),
    ]
    if not args.no_suites:
        checks.extend([check_pytest(), check_vitest(), check_build()])

    print(f"Interpreter backend: {backend_python()}")
    print(f"Backend {BACKEND_URL} · Frontend {FRONTEND_URL}\n")
    for check in checks:
        print(f"{'PASS' if check.ok else 'FAIL'}  {check.name}")
        for line in check.detail.splitlines():
            print(f"      {line}")
        if not check.ok and check.advice:
            print(f"      → {check.advice}")

    failed = [check for check in checks if not check.ok]
    print(f"\n{len(checks) - len(failed)}/{len(checks)} PASS")
    if failed:
        print("Gagal: " + ", ".join(check.name for check in failed))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
