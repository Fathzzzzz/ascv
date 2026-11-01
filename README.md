# Image to ASCII/Emoji Converter

Mengubah foto menjadi ASCII/emoji art dengan menghapus latar belakang lebih dulu,
sehingga subjek tetap terbaca. Pipeline pengolahan gambar berada di `backend/core/`
dan tidak bergantung pada FastAPI, jadi bisa dijalankan lewat terminal maupun dites
sendiri.

Status: **M1 selesai** — modul `core/` dan skrip terminal. API (M3) dan frontend (M4)
belum dibuat.

## Struktur

```
backend/
  core/            # pipeline: segmentation > crop > grayscale > grid > mapping
  scripts/convert.py  # runner terminal untuk core
  tests/           # unit test per tahap pipeline
frontend/          # menyusul di M4
```

## Prasyarat

- Python 3.10–3.13 (disarankan 3.12; `rembg` belum mendukung 3.14)
- Koneksi internet pada pemakaian pertama, untuk mengunduh model rembg

## Setup backend

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Opsional: salin konfigurasi contoh, lalu sesuaikan bila perlu.

```bash
cp .env.example .env
export REMBG_MODEL=u2net   # atau isi variabel lain lewat mekanisme shell Anda
```

## Menjalankan converter di terminal

```bash
cd backend
source .venv/bin/activate

# ASCII, lebar default 100 kolom
python -m scripts.convert /path/foto.jpg

# Mode emoji, lebar 40, hasil disimpan ke file
python -m scripts.convert /path/foto.jpg --mode emoji --width 40 --output hasil.txt

# Tanpa penghapusan latar belakang (tanpa model rembg)
python -m scripts.convert /path/foto.jpg --no-remove-bg --width 80
```

Opsi lain: `--charset`, `--invert`, `--contrast`, `--clahe`, `--model`.
Daftar lengkap: `python -m scripts.convert --help`.

Run pertama dengan penghapusan latar belakang akan mengunduh model rembg
(`u2net`, sekitar 176 MB) ke `~/.u2net` dan bisa terasa lambat. Run berikutnya
memakai cache model dan jauh lebih cepat.

## Menjalankan test

```bash
cd backend
source .venv/bin/activate
pytest
```

## Pipeline

1. **Segmentation** — `rembg` menghasilkan mask subjek; model dimuat sekali lalu dipakai ulang.
2. **Crop** — gambar dan mask dipotong ke bounding box subjek (mask kosong = tanpa crop).
3. **Grayscale** — luminance BT.601 `0.299R + 0.587G + 0.114B`, lalu CLAHE dan faktor kontras linear.
4. **Grid** — resize ke jumlah kolom yang diminta; tinggi dikoreksi rasio karakter
   (ASCII 0.5, emoji 1.0).
5. **Mapping** — brightness tiap sel dipetakan ke ramp gelap→terang (`--invert` membalik urutannya);
   sel di luar mask menjadi spasi.

Lebar yang diterima: ASCII 40–200 (default 100), emoji 20–80 (default 40).

## Milestone

| Tahap | Isi | Status |
| --- | --- | --- |
| M1 | Modul `core/` + skrip terminal | selesai |
| M2 | Unit test pipeline & preset charset | menyusul |
| M3 | API FastAPI `/api/convert` | menyusul |
| M4 | Frontend React | menyusul |
| M5 | Integrasi & uji set foto | menyusul |
| M6 | Rilis MVP & dokumentasi | menyusul |
