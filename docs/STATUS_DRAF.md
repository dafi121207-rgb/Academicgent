# Status draf Academicgent 0.2

Draf implementasi selesai pada 7 November 2026 untuk alur resume. Arsitektur makalah, parafrase, referensi, artikel jurnal, skripsi, dan perapian Word tetap tersedia sebagai rencana pengembangan.

## Kemampuan yang tersedia

- Membuat proyek dan menyimpan identitas, naskah, serta riwayat revisi di laptop.
- Membaca satu PDF aktif per proyek, maksimal 50 MB dan 100 halaman.
- Menampilkan halaman, mengubah urutan baca, memilih halaman, serta memberi label nomor buku.
- Mengekstrak teks PDF atau menjalankan OCR lokal dengan Tesseract, lalu mengoreksi hasil per halaman.
- Menghubungkan Ollama lokal, menyusun kandidat per potongan sumber, dan memeriksa kutipan bukti.
- Menyimpan progres per bagian, membatalkan generasi, dan melanjutkan pekerjaan yang terputus.
- Meninjau serta menerapkan kandidat sebagai revisi baru. Revisi lama dapat dipulihkan.
- Mengekspor Word, teks, JSON revisi, serta peta sumber kandidat. Format Word menggunakan preset resume contoh pengguna.

## Verifikasi

| Pemeriksaan | Hasil |
| --- | --- |
| Uji otomatis | 8 pengujian lulus melalui `python -m unittest discover -s tests -v` |
| Alur antarmuka | Identitas → PDF → koreksi label → urutan → editor → kandidat → ekspor → pemulihan revisi lulus dengan Streamlit AppTest |
| Editor saat AI tidak tersedia | Teks yang belum disimpan tetap terbawa saat proyek dibuat; kegagalan koneksi AI tidak menghilangkan editor dan unduhan |
| Riwayat dan konflik | Revisi lama dipertahankan; tab dengan revisi usang ditolak saat menyimpan |
| API AI | Server HTTP lokal dengan respons terkontrol menguji kegagalan, checkpoint, dan kelanjutan tanpa mengulang bagian selesai |
| PDF scan contoh pengguna | Terdeteksi 19 halaman tanpa teks asli; satu halaman berhasil melalui OCR bahasa Inggris yang tersedia pada lingkungan uji |
| Word | Contoh pendek 1 halaman dan panjang 3 halaman dirender serta diperiksa; heading, identitas, margin, bullet, serta nomor halaman terbaca |

Uji dilakukan di Linux dengan Python 3.12. Respons AI pada pengujian otomatis adalah fixture, sehingga hasil ini menguji alur integrasi dan penyimpanan, bukan kualitas ringkasan dari model sungguhan. AppTest menguji interaksi komponen; tampilan browser dan Microsoft Word di Windows perlu diperiksa di laptop target.

## Batas yang perlu diketahui

OCR belum otomatis memperbaiki foto buku yang melengkung, tabel, atau rumus. Setiap halaman terpilih harus diperiksa sebelum generasi. Kutipan bukti yang cocok hanya membuktikan bahwa teks tersebut terdapat pada sumber; kesetiaan makna ringkasan tetap ditinjau pengguna. Kandidat disusun per potongan, sehingga beberapa heading atau gagasan dapat berulang dan perlu dirapikan di editor.

Model Ollama sungguhan, penggunaan RAM, dan kecepatan pada i3 generasi ke-13/RAM 8 GB belum diukur. `qwen3:1.7b` adalah kandidat uji awal. Instalasi Python, Tesseract, dan Ollama masih dilakukan terpisah. Belum ada installer `.exe`.

Versi ini belum menyediakan sitasi APA/IEEE otomatis, impor RIS ke Mendeley, field Mendeley Cite aktif, penelusuran jurnal, makalah antarbab, atau skripsi lengkap. Pratinjau PDF dalam aplikasi adalah pratinjau bahan sumber. Pratinjau hasil ekspor masih diperiksa dengan membuka Word.

Saat satu job AI berjalan, job baru ditolak. OCR batch berjalan berurutan pada sesi antarmuka dan menyimpan setiap halaman selesai. Setelah aplikasi berhenti mendadak, job AI yang tidak memperbarui progres selama 10 menit ditandai dapat dilanjutkan. Proyek baru tidak menerapkan kandidat secara otomatis.

## Percobaan pertama di laptop

1. Unduh ZIP repositori, ekstrak, pasang Python, lalu jalankan `setup.bat` dan `start.bat` sesuai README.
2. Buat proyek kecil, isi identitas dan dua bagian resume manual, lalu buka hasil Word.
3. Pasang Tesseract beserta bahasa Indonesia. Unggah PDF bab, periksa label, urutan, dan OCR dua halaman terlebih dahulu.
4. Pasang Ollama dan model kandidat. Buat ringkasan dari dua halaman yang sudah diperiksa, lalu bandingkan setiap paragraf dengan sumbernya.
5. Jika hasil sesuai, lanjutkan halaman lain. Catat waktu generasi, penggunaan RAM, kualitas OCR, dan perubahan format di Word.

Cadangan lengkap dibuat dengan menutup aplikasi dan menyalin folder `AcademicgentData`. Repositori publik hanya berisi kode, dokumentasi, preset generik, dan fixture sintetis.
