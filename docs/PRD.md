# PRD: Image to ASCII/Emoji Converter

Versi 0.1 (draft) · 1 November 2026 · Penyusun: Mmsmape

## 1. Ringkasan

Image to ASCII/Emoji Converter adalah aplikasi web yang mengubah foto biasa, terutama foto orang, menjadi karya visual yang tersusun dari karakter ASCII atau emoji. Pengguna mengunggah gambar, aplikasi memisahkan subjek dari latar belakang, mengolahnya menjadi grayscale, lalu memetakan tingkat kecerahan tiap bagian gambar ke karakter atau emoji tertentu. Hasilnya dapat ditampilkan di browser, disalin sebagai teks, atau diunduh sebagai file.

Produk dibangun dengan frontend React dan backend Python (FastAPI). Seluruh logika pengolahan gambar ditempatkan pada modul pipeline Python yang terpisah dari lapisan API, sehingga mudah diuji dan dipakai ulang.

## 2. Latar Belakang dan Masalah

Konversi gambar ke ASCII sudah banyak tersedia, tetapi mayoritas hanya memetakan brightness seluruh gambar secara langsung. Akibatnya latar belakang ikut berubah menjadi karakter, sehingga subjek (misalnya wajah) sulit dikenali dan hasilnya terlihat berantakan. Proyek ini menjawab masalah tersebut dengan menambahkan tahap segmentation di awal pipeline, sehingga hanya subjek yang dikonversi.

Selain itu, proyek ini berfungsi sebagai sarana belajar bagi pengembangnya: membangun aplikasi full-stack, memakai library computer vision, serta menerapkan alur kerja Git/GitHub.

## 3. Tujuan dan Non-Tujuan

### Tujuan (Goals)

- Menghasilkan ASCII/emoji art yang subjeknya jelas terlihat karena latar belakang dihapus.
- Menyediakan antarmuka web sederhana: upload, atur opsi, lihat hasil, copy atau download.
- Mendukung dua mode keluaran: ASCII (karakter teks) dan emoji.
- Menjaga arsitektur modular: pipeline terpisah dari API dan frontend.
- Memproses gambar tanpa menyimpannya secara permanen (privacy by default).

### Non-Tujuan (Non-goals) untuk versi pertama

- Tidak ada akun pengguna, login, atau database.
- Tidak ada pemrosesan video atau webcam real-time.
- Tidak ada ASCII berwarna (color ASCII); ditunda ke versi berikutnya.
- Tidak ada segmentasi per-bagian objek (wajah, rambut, baju) dengan charset berbeda.
- Tidak ada aplikasi mobile native.

## 4. Target Pengguna dan Use Case

**Pengguna utama:** mahasiswa, hobbyist, dan pembuat konten yang ingin membuat ASCII art dari foto untuk dibagikan, dicetak, atau ditempel di media sosial.

**Pengguna sekunder:** pengembang pemula yang ingin mempelajari pipeline pengolahan gambar dan arsitektur React + FastAPI melalui kode proyek ini.

**Use case utama**

1. Pengguna mengunggah foto diri, memilih mode ASCII, lalu menyalin hasilnya untuk dibagikan di chat atau media sosial.
2. Pengguna mengubah foto menjadi susunan emoji untuk dijadikan konten visual.
3. Pengguna mengunduh hasil sebagai file `.txt` untuk dicetak atau disimpan.

## 5. Ruang Lingkup

| Fitur | MVP (v1) | Versi berikutnya |
| --- | --- | --- |
| Upload gambar (jpg, png, webp) | Ya |  |
| Segmentation / background removal | Ya | Pilihan model lain |
| Konversi grayscale + penyesuaian kontras | Ya |  |
| Mode ASCII dan emoji | Ya | Charset kustom dari pengguna |
| Atur lebar (jumlah kolom), invert, preset charset | Ya |  |
| Copy teks, download PNG, dan download `.txt` | Ya | Format ekspor tambahan |
| ASCII berwarna | Tidak | Ya |
| Segmentasi per-bagian objek | Tidak | Ya |
| Webcam / real-time | Tidak | Ya (opsional) |
| Akun dan riwayat | Tidak | Ya (opsional) |

## 6. Functional Requirements

| ID | Requirement | Prioritas |
| --- | --- | --- |
| FR-01 | Pengguna dapat mengunggah gambar berformat jpg, png, atau webp melalui tombol upload atau drag and drop. | Must |
| FR-02 | Sistem memvalidasi tipe dan ukuran file (usulan maksimum 5 MB) di sisi backend, dan menampilkan pesan error yang jelas jika tidak valid. | Must |
| FR-03 | Sistem dapat menghapus latar belakang dan menghasilkan mask subjek (orang). | Must |
| FR-04 | Pengguna dapat mengaktifkan atau menonaktifkan penghapusan latar belakang (`remove_bg`). | Should |
| FR-05 | Sistem memotong (crop) gambar ke bounding box subjek sebelum dikonversi. | Should |
| FR-06 | Sistem mengubah gambar menjadi grayscale dengan bobot luminance dan menyediakan penyesuaian kontras. | Must |
| FR-07 | Sistem membagi gambar ke grid dengan koreksi rasio karakter (tinggi sekitar 0,5 untuk ASCII dan 1,0 untuk emoji). | Must |
| FR-08 | Sistem memetakan brightness tiap sel ke karakter ASCII atau emoji sesuai preset yang dipilih. | Must |
| FR-09 | Sel di luar mask subjek diisi spasi (atau emoji kosong) agar latar tidak muncul. | Must |
| FR-10 | Pengguna dapat mengatur lebar hasil (jumlah kolom), opsi invert, mode (ASCII atau emoji), dan preset charset. | Must |
| FR-11 | Hasil ditampilkan dengan font monospace dan dapat di-scroll atau di-zoom. | Must |
| FR-12 | Pengguna dapat menyalin hasil ke clipboard dan mengunduhnya sebagai file PNG atau `.txt`. | Must |
| FR-13 | Antarmuka menampilkan indikator loading selama pemrosesan dan pesan error jika gagal. | Should |
| FR-14 | Pengguna dapat melihat pratinjau gambar asli di samping hasil. | Could |

## 7. Non-Functional Requirements

- **Performa:** target awal waktu pemrosesan di bawah 5 detik untuk gambar sampai 2 MP pada mesin pengembangan standar; request pertama boleh lebih lambat karena model dimuat.
- **Privasi:** gambar diproses di memori dan tidak disimpan permanen di server.
- **Keamanan:** validasi tipe dan ukuran file di backend, batasi dimensi gambar, aktifkan CORS hanya untuk origin yang diizinkan.
- **Reliabilitas:** kegagalan pipeline mengembalikan error terstruktur (bukan crash server).
- **Maintainability:** pipeline berada di modul `core/` yang independen dari FastAPI dan memiliki unit test.
- **Usability:** antarmuka dapat dipakai di desktop dan layar kecil; teks antarmuka menggunakan Bahasa Indonesia.
- **Portabilitas:** dapat dijalankan secara lokal dengan satu perintah per layanan (backend dan frontend).

## 8. User Flow

1. Pengguna membuka aplikasi dan melihat area upload serta panel opsi.
2. Pengguna memilih gambar. Pratinjau muncul.
3. Pengguna mengatur opsi: mode, lebar, charset, invert, remove background.
4. Pengguna menekan tombol Convert. Indikator loading tampil.
5. Frontend mengirim `POST /api/convert`; backend menjalankan pipeline dan mengembalikan teks hasil.
6. Hasil tampil dalam elemen monospace. Pengguna dapat mengubah opsi dan konversi ulang, menyalin, atau mengunduh.
7. Jika terjadi error (file tidak valid, terlalu besar, atau pipeline gagal), pesan error ditampilkan dan pengguna dapat mencoba lagi.

## 9. Arsitektur dan Tech Stack

| Lapisan | Teknologi (usulan) | Tanggung jawab |
| --- | --- | --- |
| Frontend | React + Vite | Upload, opsi, tampilan hasil, copy dan download |
| API | FastAPI + Pydantic | Routing, validasi, CORS, error handling |
| Core pipeline | Python, Pillow, NumPy, OpenCV, rembg | Segmentation, crop, grayscale, grid, mapping karakter |
| Testing | pytest (backend), Vitest (frontend) | Unit test pipeline dan komponen |
| Version control | Git + GitHub | Riwayat kode dan kolaborasi |

Struktur folder: `backend/app` (API), `backend/core` (pipeline), `backend/tests`, `frontend/src` (komponen, api, App).

## 10. Spesifikasi API

**`POST /api/convert`** (multipart/form-data)

| Parameter | Tipe | Keterangan |
| --- | --- | --- |
| image | file | jpg, png, atau webp, maksimum 5 MB |
| width | integer | Jumlah kolom karakter: ASCII 40 sampai 200, emoji 20 sampai 80 |
| mode | string | `ascii` atau `emoji` |
| charset | string | Nama preset ramp karakter |
| invert | boolean | Membalik urutan gelap ke terang |
| remove\_bg | boolean | Aktifkan segmentation |

**Response sukses (200):** `text` (string hasil, baris dipisah newline), `width`, `height`, `mode`.

**Response error:** 400 (file atau parameter tidak valid), 413 (file terlalu besar), 500 (pipeline gagal).

Endpoint tambahan yang direncanakan untuk versi berikutnya: `GET /api/charsets` untuk daftar preset.

## 11. Spesifikasi Pipeline

1. **Segmentation:** model person segmentation (rembg sebagai pilihan awal) menghasilkan mask subjek. Model dimuat sekali saat server start.
2. **Crop:** gambar dan mask dipotong ke bounding box subjek.
3. **Grayscale:** konversi dengan bobot luminance (sekitar 0,299 R + 0,587 G + 0,114 B), diikuti penyesuaian kontras atau histogram equalization.
4. **Grid:** gambar di-resize ke jumlah kolom yang diminta; tinggi dikoreksi dengan faktor rasio karakter.
5. **Mapping:** brightness tiap sel dipetakan ke karakter dari ramp gelap ke terang (misalnya ` @%#*+=-:.  `) atau ke deretan emoji gelap sampai terang. Sel di luar mask menjadi spasi.
6. **Output:** string multi-baris yang siap ditampilkan.

## 12. Metrik Keberhasilan

- Pipeline menghasilkan output untuk minimal 95 persen gambar uji yang valid tanpa error.
- Waktu proses sesuai target performa pada set gambar uji.
- Subjek dinilai dapat dikenali pada pengujian visual terhadap sekitar 10 foto contoh (variasi pencahayaan dan latar).
- Seluruh Must requirement terpenuhi pada rilis MVP.
- Cakupan unit test pada modul `core/` mencakup setiap tahap pipeline.

## 13. Risiko dan Mitigasi

| Risiko | Dampak | Mitigasi |
| --- | --- | --- |
| Segmentation gagal pada latar rumit atau subjek tidak jelas | Hasil berantakan | Sediakan opsi mematikan `remove_bg`; uji dengan beragam foto |
| Model segmentation lambat atau berat | Waktu tunggu lama | Muat model sekali saat start; batasi ukuran gambar; resize sebelum diproses |
| Hasil terlihat melar karena rasio karakter | Subjek terdistorsi | Faktor koreksi rasio yang dapat disesuaikan per mode |
| Hasil pucat karena level tonal terbatas | Detail wajah hilang | Penyesuaian kontras dan opsi charset dengan lebih banyak level |
| Tampilan emoji berbeda antar platform | Tampilan tidak konsisten | Sediakan ekspor PNG agar tampilan konsisten |
| Unggahan berbahaya atau terlalu besar | Keamanan dan stabilitas | Validasi tipe, ukuran, dan dimensi di backend |

## 14. Milestone (usulan)

| Tahap | Deliverable |
| --- | --- |
| M1 | Modul `core/` berjalan lewat skrip terminal (segmentation sampai mapping) |
| M2 | Unit test pipeline dan preset charset ASCII serta emoji |
| M3 | Backend FastAPI dengan endpoint `/api/convert` dan dokumentasi `/docs` |
| M4 | Frontend React: upload, opsi, tampilan hasil, copy dan download |
| M5 | Integrasi, penanganan error, uji dengan set foto contoh |
| M6 | Rilis MVP, README, dan dokumentasi penggunaan |

Estimasi waktu belum ditetapkan dan menunggu keputusan mengenai ketersediaan waktu pengembang.

## 15. Keputusan atas Open Questions

- **Deployment:** hanya dijalankan secara lokal. Tidak perlu hosting, dan satu-satunya batasan resource adalah mesin pengembang.
- **Model segmentation:** rembg dipakai untuk MVP karena akurasinya baik pada foto orang dan penggunaannya sederhana. MediaPipe tetap menjadi kandidat jika kelak ada fitur webcam real-time.
- **Ekspor hasil:** hasil dapat disalin ke clipboard dan diunduh, baik sebagai `.txt` maupun PNG. PNG terutama berguna untuk mode emoji karena tampilan emoji berbeda antar platform.
- **Lebar maksimum:** mode ASCII 40 sampai 200 kolom (default 100), mode emoji 20 sampai 80 kolom (default 40) karena emoji lebih lebar per karakter. Di layar kecil, hasil di-scroll secara horizontal.
