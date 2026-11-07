# Status draf Academicgent 0.4

Draf 0.4 per 7 November 2026 menambahkan chat Ollama dan tampilan pet foto bergerak. Draf 0.3 menambahkan buddy dan pengingat deadline pada alur resume draf 0.2. Arsitektur makalah, parafrase, referensi, artikel jurnal, skripsi, dan perapian Word tetap tersedia sebagai rencana pengembangan.

## Kemampuan yang tersedia

- Membuat proyek dan menyimpan identitas, naskah, serta riwayat revisi di laptop.
- Membaca satu PDF aktif per proyek, maksimal 50 MB dan 100 halaman.
- Menampilkan halaman, mengubah urutan baca, memilih halaman, serta memberi label nomor buku.
- Mengekstrak teks PDF atau menjalankan OCR lokal dengan Tesseract, lalu mengoreksi hasil per halaman.
- Menghubungkan Ollama lokal, menyusun kandidat per potongan sumber, dan memeriksa kutipan bukti.
- Menyimpan progres per bagian, membatalkan generasi, dan melanjutkan pekerjaan yang terputus.
- Meninjau serta menerapkan kandidat sebagai revisi baru. Revisi lama dapat dipulihkan.
- Mengekspor Word, teks, JSON revisi, serta peta sumber kandidat. Format Word menggunakan preset resume contoh pengguna.
- Menampilkan enam foto meme sesuai status proses, keberhasilan, kesalahan, fokus, pertanyaan, atau deadline. Foto pengguna ditampilkan utuh dan proporsional.
- Menjalankan buddy pada browser dan sebagai jendela desktop yang dapat diseret, dikecilkan, serta diatur agar selalu di atas jendela lain.
- Menambah, mengubah, menyelesaikan, dan menghapus tugas dengan deadline WIB/WITA/WIT, keterkaitan proyek pilihan, serta catatan.
- Menampilkan pengingat otomatis, menundanya 15 menit, menutup satu pengingat, dan menjeda seluruh pengingat satu jam. Jadwal dan tindakan pengingat bertahan setelah proses dibuka kembali.
- Memberi langkah kerja dan pemeriksaan struktur dasar melalui panel bantuan buddy di tab Draf resume.

## Verifikasi draf 0.3

| Pemeriksaan | Hasil pada 7 November 2026 |
| --- | --- |
| Suite otomatis | 16 pengujian lulus melalui `python -m unittest discover -s tests -v`, termasuk regresi alur resume |
| Buddy dan jadwal | Enam status, transisi job AI, zona waktu, jadwal bertahap, pencegahan pengingat ganda, pemulihan pengingat terlewat, jeda, penundaan setelah restart, dan penyelesaian lulus |
| Perubahan tugas | Penyimpanan, pembatalan notifikasi lama saat tugas diubah, penolakan perubahan dari revisi usang, serta pengingat nonaktif lulus |
| Alur antarmuka | Tiga alur Streamlit AppTest lulus: PDF hingga kandidat dan pemulihan revisi; tugas dan buddy; teks belum tersimpan saat model tidak tersedia. Ketiganya juga lulus setelah label tombol browser menjadi **Selesai** |
| Browser nyata | Alur tugas/pengingat dan tampilan buddy diperiksa pada 1440 × 1000 dan 390 × 844. Tombol **Selesai** terbaca utuh, buddy tidak meluap secara horizontal, dan tidak tercatat kesalahan browser pada pemeriksaan |
| Buddy desktop | Tk pada Linux dengan layar virtual: pop-up deadline, Tunda 15 m, Sudah selesai, mode kecil, jeda satu jam, dan pencegahan instance ganda diperiksa |

Uji otomatis berjalan di Linux dengan Python 3.12. Respons AI adalah fixture dari server lokal, sehingga hasilnya menguji integrasi dan penyimpanan. Uji browser dilakukan pada dua ukuran viewport; uji Tk menggunakan Linux/Xvfb. Keduanya belum membuktikan perilaku di Windows atau perangkat pengguna. Rincian pemakaian ada pada [Buddy dan deadline](BUDDY_DAN_DEADLINE.md).

## Catatan verifikasi draf 0.2

Catatan berikut berasal dari pengujian alur resume sebelumnya dan bukan pengukuran baru draf 0.3. Delapan uji otomatis ini menjadi bagian dari suite yang diperluas pada 0.3.

| Pemeriksaan | Hasil |
| --- | --- |
| Uji otomatis | 8 pengujian lulus melalui `python -m unittest discover -s tests -v` |
| Alur antarmuka | Identitas → PDF → koreksi label → urutan → editor → kandidat → ekspor → pemulihan revisi lulus dengan Streamlit AppTest |
| Editor saat AI tidak tersedia | Teks yang belum disimpan tetap terbawa saat proyek dibuat; kegagalan koneksi AI tidak menghilangkan editor dan unduhan |
| Riwayat dan konflik | Revisi lama dipertahankan; tab dengan revisi usang ditolak saat menyimpan |
| API AI | Server HTTP lokal dengan respons terkontrol menguji kegagalan, checkpoint, dan kelanjutan tanpa mengulang bagian selesai |
| PDF scan contoh pengguna | Terdeteksi 19 halaman tanpa teks asli; satu halaman berhasil melalui OCR bahasa Inggris yang tersedia pada lingkungan uji |
| Word | Contoh pendek 1 halaman dan panjang 3 halaman dirender serta diperiksa; heading, identitas, margin, bullet, serta nomor halaman terbaca |

Uji 0.2 dilakukan di Linux dengan Python 3.12. Respons AI pada pengujian otomatis adalah fixture, sehingga hasil ini menguji alur integrasi dan penyimpanan, bukan kualitas ringkasan dari model sungguhan. Microsoft Word di Windows masih perlu diperiksa di laptop target.

## Batas yang perlu diketahui

Pengingat desktop bekerja selama proses buddy berjalan dan laptop aktif. Menutup browser tidak menghentikan buddy desktop, tetapi laptop mati atau tidur tidak dapat menampilkan pengingat. Saat perangkat aktif dan buddy berjalan kembali, jadwal yang terlewat diperiksa. Satu tugas mempunyai paling banyak satu pengingat tertunda; beberapa jadwal yang terlewat tidak ditumpuk menjadi banyak pop-up. Jam perangkat perlu benar. Saat buddy desktop aktif, pengingat browser ditahan agar tidak muncul bersamaan.

Belum ada startup otomatis saat masuk Windows atau layanan latar Windows. Pet bergerak dengan memindahkan foto, tanpa animasi karakter berjalan. `start.bat` membuka aplikasi dan buddy; `start_buddy.bat` membuka buddy saja. Bantuan rencana dan koreksi memakai aturan struktur lokal, bukan pemeriksaan kebenaran isi oleh LLM. Label meme **Verifikasi berhasil** berarti suatu proses berhasil, bukan pengesahan isi akademik. Kompatibilitas buddy/Tk di Windows masih perlu dicoba pada laptop target.

OCR belum otomatis memperbaiki foto buku yang melengkung, tabel, atau rumus. Setiap halaman terpilih harus diperiksa sebelum generasi. Kutipan bukti yang cocok hanya membuktikan bahwa teks tersebut terdapat pada sumber; kesetiaan makna ringkasan tetap ditinjau pengguna. Kandidat disusun per potongan, sehingga beberapa heading atau gagasan dapat berulang dan perlu dirapikan di editor.

Model Ollama sungguhan, penggunaan RAM, dan kecepatan pada i3 generasi ke-13/RAM 8 GB belum diukur. `qwen3:1.7b` adalah kandidat uji awal. Instalasi Python, Tesseract, dan Ollama masih dilakukan terpisah. Belum ada installer `.exe`.

Versi ini belum menyediakan sitasi APA/IEEE otomatis, impor RIS ke Mendeley, field Mendeley Cite aktif, penelusuran jurnal, makalah antarbab, atau skripsi lengkap. Pratinjau PDF dalam aplikasi adalah pratinjau bahan sumber. Pratinjau hasil ekspor masih diperiksa dengan membuka Word.

Saat satu job AI berjalan, job baru ditolak. OCR batch berjalan berurutan pada sesi antarmuka dan menyimpan setiap halaman selesai. Setelah aplikasi berhenti mendadak, job AI yang tidak memperbarui progres selama 10 menit ditandai dapat dilanjutkan. Proyek baru tidak menerapkan kandidat secara otomatis.

## Percobaan pertama di laptop

1. Unduh ZIP repositori, ekstrak, pasang Python, lalu jalankan `setup.bat` dan `start.bat` sesuai README. Pastikan aplikasi dan buddy desktop terbuka.
2. Buat proyek kecil, isi identitas dan dua bagian resume manual, lalu buka hasil Word.
3. Pasang Tesseract beserta bahasa Indonesia. Unggah PDF bab, periksa label, urutan, dan OCR dua halaman terlebih dahulu.
4. Pasang Ollama dan model kandidat. Buat ringkasan dari dua halaman yang sudah diperiksa, lalu bandingkan setiap paragraf dengan sumbernya.
5. Jika hasil sesuai, lanjutkan halaman lain. Catat waktu generasi, penggunaan RAM, kualitas OCR, dan perubahan format di Word.
6. Buat tugas contoh di **Tugas & buddy** dengan deadline beberapa menit lagi, zona waktu yang benar, dan **Mulai ingatkan: 1 jam sebelumnya**. Karena waktu pengingat awal sudah lewat, pop-up muncul pada pemeriksaan berikutnya. Coba **Tunda 15 m**, **Sudah selesai**, mode kecil, dan menu buddy. Coba tutup browser sambil membiarkan buddy desktop aktif. Hapus tugas contoh setelah pengujian.
7. Pada **Draf resume**, coba **Buddy, bantu aku** untuk melihat langkah kerja dan pemeriksaan struktur. Tetap bandingkan isi dengan sumber.

Untuk cadangan lengkap, tutup buddy melalui klik kanan foto lalu **Keluar dari buddy** dan hentikan server Streamlit, lalu salin seluruh folder `AcademicgentData`. Menutup tab browser saja belum menghentikan aplikasi. Repositori publik berisi kode, dokumentasi, preset generik, fixture sintetis, dan enam aset meme yang diberikan pengguna; data proyek serta tugas disimpan terpisah pada perangkat.
