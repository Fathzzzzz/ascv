# Image to ASCII/Emoji Converter

Foto diubah menjadi ASCII atau emoji art: latar belakang dihapus lebih dulu
(rembg), subjek dipotong, dijadikan grayscale, lalu dipetakan ke karakter.
Seluruh proses berjalan **lokal** — tanpa database, login, Docker, atau deploy.

PRD: [`docs/PRD.md`](docs/PRD.md).

## Struktur

```
backend/core/        pipeline murni Python (tanpa FastAPI, bisa dites sendiri)
backend/app/         FastAPI: /api/convert, /api/health, validasi upload
backend/scripts/     convert.py — pemakaian pipeline dari terminal
backend/tests/       pytest untuk pipeline dan API
frontend/src/        React + Vite: upload, opsi, hasil, copy, download
scripts/check.py     pemeriksaan otomatis end-to-end (PASS/FAIL per item)
tests/assets/        gambar contoh untuk pytest dan check.py
docs/PRD.md          dokumen requirement
```

## Prasyarat

| Kebutuhan | Versi | Catatan |
| --- | --- | --- |
| Python | 3.11–3.14 | venv proyek ini memakai 3.12. `rembg` mensyaratkan `>=3.11` |
| Node.js | 18+ | diuji dengan 26.5.0 |
| Internet | sekali | mengunduh model `u2net` (±176 MB) ke `~/.u2net` |

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

Model segmentasi dimuat sekali saat start (bukan per request). Bila model belum
ada, ia diunduh saat start — perlu internet dan bisa beberapa menit. Log akan
menampilkan `Model segmentasi u2net dimuat.`

**3. Install dependency frontend, lalu jalankan (port 6744)**

```bash
cd frontend
npm install
npm run dev
```

**4. Buka <http://localhost:6744>**

**5. Verifikasi otomatis**

```bash
python scripts/check.py                # semua item, termasuk pytest, vitest, build
python scripts/check.py --no-suites    # hanya health check + end-to-end
```

Jalankan dari root repo; skrip ini hanya memakai pustaka standar Python.
Backend dan frontend harus sudah berjalan. Output berupa `PASS`/`FAIL` per item
beserta saran perbaikan, dan exit code 1 bila ada yang gagal.

Untuk menghentikan: `Ctrl+C` di terminal backend dan frontend.

## Konfigurasi

Tidak ada environment variable, file `.env`, maupun CORS. Semua nilai ditulis
sebagai konstanta:

| Nilai | Lokasi |
| --- | --- |
| Batas ukuran file (5 MB), batas dimensi, format gambar, versi aplikasi, model | `backend/app/constants.py` |
| Batas & default lebar per mode | `backend/core/pipeline.py` (`WIDTH_LIMITS`, `DEFAULT_WIDTH`) |
| Preset charset ASCII/emoji | `backend/core/mapping.py` |
| Petunjuk UI (label, batas lebar, batas file) | `frontend/src/constants.js` |
| Port | backend 8000 (perintah `uvicorn`), frontend 6744 (`frontend/vite.config.js`) |

Frontend memanggil path relatif `/api/...`; Vite dev proxy meneruskannya ke
`http://localhost:8000`. Karena satu origin, tidak perlu CORS dan tidak ada URL
backend di dalam komponen.

## API

| Endpoint | Keterangan |
| --- | --- |
| `POST /api/convert` | multipart: `image`, `width`, `mode`, `charset`, `invert`, `remove_bg` → `{text, width, height, mode}` |
| `GET /api/health` | `{status, model_loaded, version}` |
| `GET /docs` | dokumentasi interaktif (Swagger) di <http://localhost:8000/docs> |

Parameter `width`, `mode`, `charset`, `invert`, `remove_bg` opsional; default
mengikuti PRD (ASCII 100 kolom, `charset=standard`, `invert=false`,
`remove_bg=true`). Boolean diterima sebagai `true`/`false` (juga `1`/`0`,
`on`/`off`, `yes`/`no`).

Contoh langsung ke backend:

```bash
curl -X POST http://localhost:8000/api/convert \
  -F "image=@tests/assets/person_synthetic.png" \
  -F "mode=ascii" -F "width=60" -F "remove_bg=true"
```

```bash
curl http://localhost:8000/api/health
# {"status":"ok","model_loaded":true,"version":"0.1.0"}
```

Kode status:

| Status | Kapan |
| --- | --- |
| 200 | konversi berhasil |
| 400 | file bukan gambar, format tidak didukung (selain JPG/PNG/WEBP), dimensi > 8000 px atau > 25 MP, parameter tidak valid, gambar kosong (`Error, blank image`) |
| 413 | file melebihi 5 MB |
| 500 | pipeline gagal (mis. model segmentasi error) |

## Pipeline

1. **Cek kosong** — frame tanpa variasi tone (gambar polos, file rusak) ditolak sebagai
   `Error, blank image` sebelum model dimuat.
2. **Segmentation** — `rembg` (`u2net`) menghasilkan mask subjek; sesi model dipakai ulang.
3. **Crop** — gambar dan mask dipotong ke bounding box subjek (ambang mask 0.1).
4. **Grayscale** — luminance BT.601 (`0.299R + 0.587G + 0.114B`), lalu CLAHE + faktor kontras.
5. **Grid** — resize ke jumlah kolom; tinggi dikoreksi rasio karakter (ASCII 0.5, emoji 1.0).
6. **Mapping** — brightness → ramp gelap→terang (`invert` membalik urutannya);
   sel di luar mask menjadi spasi.

Batas lebar: ASCII 40–200 (default 100), emoji 20–80 (default 40).

## Preset charset

| Mode | Preset | Isi |
| --- | --- | --- |
| ascii | `standard` (default) | `@%#*+=-:. ` |
| ascii | `dense` | 70 level, ramp klasik |
| ascii | `blocks` | `█▓▒░ ` |
| emoji | `moon` (default) | 🌑🌒🌓🌔🌕 |
| emoji | `squares` | ⬛🟫🟪🟦🟩🟨🟧⬜ |

Semua preset berurutan gelap→terang; setiap token emoji satu code point agar grid
tetap rapi. Konvensi ini dijaga oleh `backend/tests/test_charsets.py`.

## Mode terminal (tanpa API)

```bash
cd backend && source .venv/bin/activate

# gambar contoh ada di root repo, jadi path-nya ../tests/assets/...
python -m scripts.convert ../tests/assets/person_synthetic.png --width 60
python -m scripts.convert ../tests/assets/person_synthetic.png --mode emoji --width 40 -o hasil.txt

# foto sendiri, tanpa model rembg
python -m scripts.convert ~/Pictures/foto.jpg --no-remove-bg --width 80
```

Opsi: `--mode`, `--width`, `--charset`, `--invert`, `--contrast`, `--clahe`,
`--model`, `--output`. Bantuan: `python -m scripts.convert --help`.
Gambar yang tidak layak dicetak sebagai `Error, blank image` (exit code 1).

## Test

```bash
cd backend && source .venv/bin/activate && pytest     # 154 test
cd frontend && npx vitest run                          # 20 test
cd frontend && npm run build                           # build produksi lokal
```

Test API memakai segmenter pengganti, jadi tidak memuat model dan tidak butuh
internet. Jalur model sungguhan diuji oleh `scripts/check.py`.

## Troubleshooting

| Gejala | Penyebab & solusi |
| --- | --- |
| `Error, blank image` untuk foto yang jelas berisi orang | Subjek tidak terdeteksi (latar rumit / foto sangat kecil). Coba matikan "Hapus latar belakang" di UI, atau pakai model khusus orang: `--model u2net_human_seg` (mengunduh model tambahan sekali) |
| Frontend menampilkan "Backend tidak dapat dihubungi" | Backend belum jalan di port 8000; jalankan `uvicorn app.main:app --port 8000` |
| `Port 6744 is already in use` | Ada proses lain di port itu: `lsof -nP -iTCP:6744 -sTCP:LISTEN`, hentikan, atau ubah `server.port` di `frontend/vite.config.js` **dan** `FRONTEND_URL` di `scripts/check.py` |
| `check.py` gagal di item c (model) | Model belum terunduh. Jalankan sekali dengan internet: `python -m scripts.convert ../tests/assets/person_synthetic.png` |
| Request pertama lambat (10–60 detik) | Model dimuat saat server start; request berikutnya cepat. Cek `model_loaded` di `/api/health` |
| Hasil emoji tidak rapi di PNG | Mesin tidak punya font emoji berwarna; pasang *Noto Color Emoji* (Linux) atau jalankan di macOS |

## Catatan

- Gambar diproses di memori dan tidak disimpan di server.
- `tests/assets/person_synthetic.png` dibuat sintetis (bukan foto orang nyata),
  sehingga aman dipakai sebagai fixture dan tidak butuh unduhan internet.
- Ekspor PNG berguna untuk mode emoji karena tampilan emoji berbeda antar platform.
