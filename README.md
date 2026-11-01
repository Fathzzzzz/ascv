# Image to ASCII/Emoji Converter

Foto diubah menjadi ASCII atau emoji art: latar belakang dihapus lebih dulu
(rembg), subjek dipotong, dijadikan grayscale, lalu dipetakan ke karakter.
Seluruh proses berjalan **lokal** — tidak ada deploy, database, atau login.

```
backend/core/     pipeline murni Python (tanpa FastAPI, bisa dites sendiri)
backend/app/      FastAPI: /api/convert, /api/health, validasi upload
backend/tests/    pytest untuk pipeline dan API
frontend/src/     React + Vite: upload, opsi, hasil, copy, download
scripts/check.py  pemeriksaan otomatis end-to-end (PASS/FAIL per item)
tests/assets/     gambar contoh untuk pytest dan check.py
```

## Prasyarat

- **Python 3.10–3.13** (gunakan 3.12; `rembg` belum mendukung 3.14)
- **Node.js 18+**
- Koneksi internet **sekali** di awal untuk mengunduh model rembg (`u2net`, ±176 MB, ke `~/.u2net`)

## Cara menjalankan (urut)

**1. Virtual environment dan dependency backend**

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**2. Jalankan backend (port 8000)**

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --port 8000
```

Model segmentasi dimuat sekali saat start, jadi request pertama tidak perlu
memuat ulang. Jika model belum ada, ia diunduh saat start (butuh internet).
Log akan menunjukkan `Model segmentasi u2net dimuat.`

**3. Install dependency frontend, lalu jalankan (port 5173)**

```bash
cd frontend
npm install
npm run dev
```

**4. Buka <http://localhost:5173>**

**5. Verifikasi otomatis**

```bash
python scripts/check.py      # semua pemeriksaan, termasuk pytest, vitest, build
python scripts/check.py --no-suites   # hanya health check + end-to-end
```

`check.py` mencetak PASS/FAIL per item beserta saran perbaikan, dan berhenti
dengan exit code 1 bila ada yang gagal. Butuh backend dan frontend berjalan.

## Konfigurasi

Tidak ada environment variable, `.env`, atau CORS. Semua nilai ada di satu file:

| Nilai | Lokasi |
| --- | --- |
| Batas ukuran file, batas dimensi, format gambar, versi aplikasi | `backend/app/constants.py` |
| Batas lebar per mode, default lebar | `backend/core/pipeline.py` (`WIDTH_LIMITS`, `DEFAULT_WIDTH`) |
| Preset charset ASCII dan emoji | `backend/core/mapping.py` |
| Petunjuk UI (label, batas lebar) | `frontend/src/constants.js` |
| Port | backend 8000, frontend 5173 (`frontend/vite.config.js`) |

Frontend memanggil path relatif `/api/...`; Vite dev proxy meneruskannya ke
`http://localhost:8000`, jadi tidak ada URL backend di komponen dan tidak perlu
CORS.

## API

| Endpoint | Keterangan |
| --- | --- |
| `POST /api/convert` | multipart: `image`, `width`, `mode`, `charset`, `invert`, `remove_bg` → `{text, width, height, mode}` |
| `GET /api/health` | `{status, model_loaded, version}` |
| `GET /docs` | dokumentasi interaktif FastAPI |

| Status | Kapan |
| --- | --- |
| 200 | konversi berhasil |
| 400 | file bukan gambar / format tidak didukung / dimensi terlalu besar / parameter tidak valid / gambar kosong (`Error, blank image`) |
| 413 | file melebihi 5 MB |
| 500 | pipeline gagal (mis. model segmentasi error) |

## Pipeline

1. **Cek kosong** — frame tanpa variasi tone ditolak (`Error, blank image`) sebelum model dimuat.
2. **Segmentation** — `rembg` (`u2net`) menghasilkan mask subjek; model dimuat sekali.
3. **Crop** — gambar dan mask dipotong ke bounding box subjek.
4. **Grayscale** — luminance BT.601 (`0.299R + 0.587G + 0.114B`), lalu CLAHE + faktor kontras.
5. **Grid** — resize ke jumlah kolom; tinggi dikoreksi rasio karakter (ASCII 0.5, emoji 1.0).
6. **Mapping** — brightness → ramp gelap→terang (`invert` membalik); sel di luar mask = spasi.

Batas lebar: ASCII 40–200 (default 100), emoji 20–80 (default 40).

## Preset charset

| Mode | Preset | Isi |
| --- | --- | --- |
| ascii | `standard` (default) | `@%#*+=-:. ` |
| ascii | `dense` | 70 level |
| ascii | `blocks` | `█▓▒░ ` |
| emoji | `moon` (default) | 🌑🌒🌓🌔🌕 |
| emoji | `squares` | ⬛🟫🟪🟦🟩🟨🟧⬜ |

## Mode terminal (opsional)

Pipeline bisa dipakai tanpa API:

```bash
cd backend && source .venv/bin/activate
python -m scripts.convert tests/assets/person_synthetic.png --width 60
python -m scripts.convert tests/assets/person_synthetic.png --mode emoji --width 40 -o hasil.txt
python -m scripts.convert foto.jpg --no-remove-bg --width 80
```

Opsi: `--charset`, `--invert`, `--contrast`, `--clahe`, `--model`, `--output`.
Error gambar tidak layak dicetak sebagai `Error, blank image`.

## Test

```bash
cd backend && source .venv/bin/activate && pytest
cd frontend && npx vitest run
cd frontend && npm run build
```

## Catatan

- Request pertama bisa lambat: model dimuat (dan diunduh pada run pertama).
- Gambar diproses di memori, tidak disimpan di server.
- `tests/assets/person_synthetic.png` dibuat secara sintetis (bukan foto orang nyata),
  jadi aman dipakai sebagai fixture.
