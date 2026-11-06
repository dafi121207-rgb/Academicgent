# Academicgent

Rancangan aplikasi lokal untuk membantu menyusun resume, makalah, parafrase, sitasi, artikel ilmiah, skripsi, dan dokumen Word akademik. Fokus awalnya adalah resume yang dapat ditelusuri ke halaman sumber dan diekspor dengan format yang konsisten.

**Draf 0.2 per 7 November 2026.** Alur resume sudah mencakup proyek lokal, PDF, pengurutan halaman, OCR pilihan, koreksi teks, kandidat dari Ollama, riwayat revisi, dan ekspor Word. Rancangan makalah, referensi, jurnal, serta skripsi tersedia pada dokumentasi pengembangan.

## Menjalankan di Windows

1. Unduh repositori melalui **Code → Download ZIP**, lalu ekstrak.
2. Pasang Python 3.11 atau lebih baru.
3. Buka `setup.bat` satu kali untuk memasang dependensi. Tahap ini membutuhkan internet.
4. Buka `start.bat`. Browser menampilkan Academicgent di alamat lokal.

Pilihan melalui terminal di folder proyek tersedia berikut.

```powershell
py -3 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m streamlit run app.py
```

## Alur pemakaian

1. **Identitas** — isi nama, NIM, program studi, mata kuliah, dosen, dan judul. Klik **Simpan identitas**.
2. **Bahan PDF** — unggah PDF lalu klik **Baca PDF**. Atur urutan baca, pilih halaman, dan masukkan nomor buku yang tercetak. Nomor PDF selalu mengikuti berkas asli.
3. Periksa pratinjau dan teks. Untuk scan, gunakan **OCR halaman ini** atau **OCR semua halaman kosong**, kemudian koreksi hasil dan centang bahwa teks sudah diperiksa.
4. **Draf resume** — tulis naskah manual atau jalankan model lokal. Kandidat AI dapat ditinjau bersama kutipan sumber sebelum diterapkan sebagai revisi baru.
5. **Ekspor** — unduh Word dari revisi tersimpan. Peta sumber kandidat tersedia bila draf memakai hasil AI. Periksa halaman hasilnya di Word desktop.

Dalam editor, gunakan `## Judul bagian`, `### Subbagian`, dan `- Poin`. Pisahkan paragraf dengan baris kosong. Huruf dan nomor heading dibuat otomatis. Riwayat revisi dapat dipulihkan sebagai revisi baru.

## OCR dan AI lokal

OCR membutuhkan Tesseract dengan paket bahasa Indonesia (`ind`). Aplikasi mendeteksi Tesseract dari PATH, lokasi Windows yang umum, atau variabel `TESSERACT_CMD`. Bahasa yang ditampilkan adalah bahasa yang terpasang. Rotasi dipilih sebelum OCR. Hasil foto yang melengkung atau buram perlu koreksi manual. [Panduan Tesseract](https://tesseract-ocr.github.io/tessdoc/Installation.html)

Untuk AI, pasang Ollama dan unduh model lokal. Kandidat awal pengujian RAM 8 GB adalah `qwen3:1.7b`.

```powershell
ollama pull qwen3:1.7b
```

Jalankan Ollama, buka panel AI di tab Draf resume, lalu klik **Periksa model lokal**. Pilih model dan panjang ringkasan. Aplikasi memproses satu potongan sumber pada satu waktu, dengan konteks 4096 token dan checkpoint tiap hasil. Kualitas ringkasan serta kecepatan perlu diukur pada laptop pengguna. [Ollama](https://ollama.com/download) · [Model contoh](https://ollama.com/library/qwen3:1.7b)

Pembatalan menunggu permintaan AI aktif selesai. Jika aplikasi berhenti mendadak, pekerjaan yang tidak memperbarui checkpoint selama 10 menit ditandai terhenti saat layanan pekerjaan dimuat kembali. Kandidat yang sudah tersimpan dapat dilanjutkan. Setelah sumber diubah, buat generasi baru agar bukti sesuai dengan teks terkini.

## Data dan batas draf

Data berada di folder `AcademicgentData` dalam direktori pengguna. Folder ini berisi `projects.sqlite3` dan `sources/` dengan PDF asli berdasarkan checksum. Untuk cadangan lengkap, tutup aplikasi lalu salin seluruh folder. Lokasi dapat diubah melalui `ACADEMICGENT_DATA_DIR` sebelum aplikasi dijalankan. Proyek dari P1 dimigrasikan saat dibuka.

Draf ini memakai satu PDF aktif per proyek, maksimal 50 MB dan 100 halaman. Sumber asli disimpan, sedangkan urutan baca dan koreksi teks disimpan di database. Penggantian PDF membuat referensi kandidat lama ditandai perlu ditinjau. Sumber penuh dan berkas tugas berada pada perangkat pengguna.

Peta sumber menunjukkan hubungan kandidat AI dengan potongan halaman. Pemeriksaan kutipan membuktikan keberadaan teks pendukung dalam potongan sumber. Pengguna tetap meninjau kesesuaian makna ringkasan. Pemformatan resume mengikuti preset yang disalin ke proyek.

## Verifikasi pengembang

```powershell
.venv\Scripts\python -m unittest discover -s tests -v
```

Delapan pengujian otomatis lulus, mencakup alur antarmuka, migrasi P1, konflik revisi, urutan halaman, PDF rusak, validasi bukti, ekspor Word, dan kelanjutan job setelah kegagalan layanan. Pengujian integrasi AI memakai server lokal dengan respons terkontrol. Validasi model sungguhan di laptop pengguna dan pemeriksaan Microsoft Word desktop masih dijadwalkan. Lihat [hasil verifikasi dan batas draf](docs/STATUS_DRAF.md).

## Mulai membaca

| Dokumen | Isi |
| --- | --- |
| [Status draf](docs/STATUS_DRAF.md) | Fitur yang tersedia, hasil uji, batas versi, dan langkah mencoba di laptop |
| [Arsitektur](docs/ARSITEKTUR.md) | Komponen lokal, pilihan teknologi, penyimpanan, pemrosesan AI, ekspor, dan pemulihan pekerjaan |
| [Alur pengguna](docs/ALUR_PENGGUNA.md) | Resume PDF, makalah, parafrase, Mendeley, artikel jurnal, skripsi, dan perapian Word |
| [Kontrak data](docs/KONTRAK_DATA.md) | Struktur proyek, halaman sumber, bukti, draf, sitasi, versi, dan hasil ekspor |
| [Template dan sumber](docs/TEMPLATE_DAN_SUMBER.md) | Temuan dari SINTA, Scholar, ResearchGate, jurnal penerbit, APA, dan IEEE |
| [Roadmap dan uji](docs/ROADMAP_DAN_UJI.md) | Tahap implementasi beserta syarat kelulusan setiap tahap |
| [Preset resume](templates/presets/resume-v0.1.json) | Format awal yang diturunkan dari contoh pengguna |
| [Preset makalah kuliah](templates/presets/makalah-kuliah-v0.1.json) | Aturan A4, Times New Roman, margin 4/3/3/3 cm, dan spasi 1,5 |

## Keputusan awal

- Antarmuka berbahasa Indonesia melalui browser lokal. Python dan Streamlit dipilih untuk implementasi pertama.
- Target awal Windows pada laptop i3 generasi ke-13, RAM 8 GB, dan SSD 512 GB. Model dan kapasitas konteks ditentukan melalui uji perangkat. Upgrade RAM dicatat sebagai opsi.
- Proyek dan draf tersimpan di SQLite serta folder data aplikasi lokal. Profil mahasiswa diisi ketika aplikasi pertama dijalankan.
- Ollama menjalankan satu model lokal dan satu pekerjaan generasi pada satu waktu. Pengguna dapat menyunting serta mengekspor teks ketika layanan AI sedang tidak tersedia.
- Format dokumen berasal dari preset yang berversi. Pemilihan gaya sitasi dan aturan tata letak dicatat sebagai dua pengaturan proyek.
- Referensi tersimpan sebagai CSL-JSON. Pandoc citeproc direncanakan saat fitur sitasi masuk, lalu RIS menjadi jalur pemindahan referensi ke Mendeley.
- Format resume awal mengikuti contoh pengguna. APA, IEEE, dan template jurnal adalah calon preset tambahan yang memerlukan validasi masing-masing.

```mermaid
flowchart TD
    A[Proyek dan preset] --> B[Bahan sumber]
    B --> C{Teks sudah ditinjau}
    C -->|Perlu perbaikan| D[Urutan halaman dan OCR]
    D --> B
    C -->|Siap| E[Kerangka dan draf per bagian]
    E --> F[Tinjau isi serta sitasi]
    F --> G{Pemeriksaan ekspor}
    G -->|Perlu revisi| E
    G -->|Selesai| H[Word dan paket referensi]
```

## Alur yang tersedia

Pengguna dapat menyimpan proyek, membaca dan mengoreksi bahan PDF, menyusun naskah, meninjau kandidat AI, serta mengunduh Word yang mengikuti contoh resume.

## Batas keputusan yang masih terbuka

Model AI, kecepatan generasi, dan ukuran konteks menunggu pengukuran di laptop. Preset skripsi Sistem Informasi IPI memerlukan pedoman program studi yang berlaku. Katalog template jurnal mencatat tingkat verifikasi sumber dan tanggal pemeriksaan. Target kompatibilitas akhir adalah Word desktop pada perangkat pengguna.

Repositori publik ini menyimpan rancangan dan preset generik. Penyimpanan profil, berkas kuliah, hasil ekstraksi, dan dokumen tugas dirancang di direktori data aplikasi pada laptop.
