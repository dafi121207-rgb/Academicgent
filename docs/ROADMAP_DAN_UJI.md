# Roadmap dan kriteria pengujian

Rencana per 6 November 2026. Waktu pengerjaan ditentukan setelah setiap tahap diuji. Perangkat target awal adalah Windows, i3 generasi ke-13, RAM 8 GB, dan SSD 512 GB.

## Urutan implementasi

| Tahap | Deliverable | Syarat selesai |
| --- | --- | --- |
| P0 Rancangan | Dokumen arsitektur, flow, kontrak data, riset template, dan preset awal | Tautan internal, spesifikasi JSON, dan konsistensi antarbagian diperiksa serta tersimpan di GitHub |
| P1 Ekspor resume | Form identitas, judul, editor bagian, penyimpanan proyek, ekspor DOCX | Resume pendek dan panjang sesuai preset, bisa dibuka di Word, lalu proyek dapat dibuka kembali |
| P2 Bahan PDF | Unggah, pratinjau, ekstraksi, urutan halaman, OCR pilihan, koreksi teks | Kasus PDF teracak dan scan menghasilkan teks serta locator yang dikonfirmasi pengguna |
| P3 AI lokal | Ollama, generasi per bagian, kandidat revisi, checkpoint | Proses dapat selesai, dibatalkan, dan dilanjutkan pada laptop target dengan bukti sumber tetap terhubung |
| P4 Referensi | CSL-JSON, RIS, metadata DOI, APA 7, alur Mendeley | Uji sitasi dan impor RIS lolos, penanda dapat diganti menjadi sitasi aktif melalui Mendeley Cite |
| P5 Makalah dan parafrase | Kerangka makalah, editor antarbab, perbandingan parafrase | Rujukan, angka, dan makna penting dapat diperiksa, revisi aman diterapkan |
| P6 Artikel jurnal | Preset jurnal pertama yang dipilih pengguna, lalu IEEE atau APA paper | Berkas template resmi diperiksa dan contoh hasil lolos layout serta aturan penerbit |
| P7 Skripsi dan Word lama | Preset prodi, penggabungan bab, daftar isi, perapian salinan | Pedoman berlaku terkonfirmasi dan fitur Word yang didukung lulus fixture preservasi |

P1 dan persiapan P2 bisa dikerjakan sebelum laptop tiba. P3 membutuhkan pengujian perangkat untuk menetapkan model dan ukuran bahan. Makalah dengan teks yang sudah tersedia dapat memakai kemampuan ekspor sebelum generasi AI siap.

## Kasus uji yang harus disiapkan

| Area | Kasus | Hasil yang diharapkan |
| --- | --- | --- |
| Identitas | NIM berawalan nol, nama dan dosen panjang | Nilai diperlakukan sebagai teks dan tetap terbaca di tabel |
| Struktur resume | Satu bagian, banyak bagian, judul dua baris | Penomoran dinamis dan heading melekat pada paragraf berikutnya |
| Word | Isi pendek dan panjang hingga beberapa halaman | Margin, styles, header, footer, nomor halaman, dan simbol benar |
| Sumber | PDF halaman acak, nomor Romawi, halaman tanpa nomor, nomor berulang | Posisi file, label cetak, dan urutan baca tersimpan terpisah |
| Scan | Halaman miring, teks kecil, satu gambar berisi dua halaman | Halaman bermasalah ditandai dan bisa diperbaiki atau dikecualikan pengguna |
| Ekstraksi | Tabel, dua kolom, rumus, superscript | Isi yang sulit dipastikan meminta tinjauan, sumber visual tersedia |
| Kegagalan input | PDF rusak, terproteksi, terlalu besar, atau decompression berlebihan | Pesan tindakan jelas dan proyek sebelumnya dapat dibuka |
| AI | JSON gagal, ID bukti palsu, keluaran terpotong, perubahan angka | Validasi menemukan masalah dan menyimpan kandidat untuk diperbaiki |
| Provenance | Teks OCR dan urutan halaman diubah sesudah draf dibuat | Hasil terdampak ditandai perlu tinjau dan tetap terkait versi asal |
| Referensi | Nama tunggal, penulis lembaga, tahun kosong, DOI ganda | Data tidak dipaksa mengarang nilai, duplikat ditinjau pengguna |
| Gaya sitasi | Penulis dan tahun sama, kutipan naratif, multi-sumber, locator | Keluaran dibandingkan dengan contoh otoritatif serta Mendeley Cite |
| IEEE | Kutipan disisipkan di awal setelah draf selesai | Seluruh nomor dan bibliografi dihitung ulang secara konsisten |
| Mendeley | RIS berisi buku, artikel, nama beraksen, halaman, DOI | Metadata impor cocok, setiap penanda punya petunjuk pemasangan |
| Pemulihan | Browser refresh, proses aplikasi berhenti, model berhenti | Draf tersimpan dapat dipulihkan dan job terhenti bisa dilanjutkan |
| Konflik | Dua tab menyimpan revisi sama, klik generasi dua kali | Tidak ada kehilangan revisi atau pekerjaan berat ganda |
| Penyimpanan | Disk penuh, rename gagal, crash di tengah ekspor | Berkas final hanya diumumkan setelah lengkap dan revisi sebelumnya tersedia |
| Cadangan | Backup lalu restore ke direktori baru | Database, sumber, draf, dan checksum cocok |
| Word lama | Tabel, gambar, field, komentar, sitasi, track changes | Perubahan hanya diterapkan pada elemen dengan dukungan yang teruji |

Fixture otomatis memakai teks sintetis atau dokumen yang izinnya sesuai. Bahan kuliah pengguna digunakan untuk uji lokal. Pengujian mencakup perilaku yang paling berisiko kehilangan data dan perubahan dokumen.

## Pemeriksaan format Word

Setiap preset menjalani pemeriksaan OOXML untuk ukuran kertas, margin, font efektif, heading, dan field. Pemeriksaan visual dilakukan pada semua halaman hasil render. Word desktop kemudian digunakan untuk memeriksa pergantian halaman, font terpasang, daftar isi, dan fungsi sitasi yang relevan. Versi Word, renderer, serta font dicatat dalam hasil uji.

Editor di browser menampilkan struktur dan isi. Pratinjau PDF memperlihatkan layout hasil ekspor. Perubahan isi yang besar mengharuskan render ulang sebelum versi ditandai sudah ditinjau.

## Pengukuran setelah laptop tersedia

| Ukuran | Cara mencatat | Pengaruh keputusan |
| --- | --- | --- |
| RAM saat aplikasi diam dan saat generasi | Bandingkan sebelum serta selama pekerjaan | Tetapkan model dan batas konteks |
| Waktu sampai keluaran pertama | Gunakan bahan dan prompt uji yang sama | Nilai kenyamanan interaksi |
| Waktu menyelesaikan satu subbagian | Uji teks pendek serta panjang dengan sumber sama | Tetapkan ukuran chunk dan timeout |
| Kualitas Bahasa Indonesia | Cek makna, istilah, angka, dan cakupan sumber | Pilih model berdasarkan hasil tugas nyata |
| Waktu OCR per halaman | Bandingkan scan baik dan scan sulit | Tetapkan resolusi dan ukuran batch |
| Keberhasilan format dan sitasi | Gunakan fixture tetap | Tentukan kesiapan fitur untuk penggunaan tugas |

Hasil RAM 8 GB menjadi baseline. Jika perangkat ditingkatkan ke 16 GB, pengujian yang sama diulang untuk menentukan keuntungan yang benar-benar diperoleh. Konfigurasi awal yang direncanakan tercantum pada [arsitektur](ARSITEKTUR.md).

## Pekerjaan berikutnya

Implementasikan P1 dengan preset resume 0.1. Gunakan data sintetis untuk pengujian awal, lalu bandingkan hasil dengan contoh resume pengguna. Setelah ekspor lolos, implementasikan P2 menggunakan PDF Bab 12 saat bahan tersedia pada perangkat. Setup Ollama dan pemilihan model dilakukan pada P3.

## Keputusan yang masih perlu bukti

- Nomor model laptop, OS terpasang, konfigurasi RAM, dan hasil pengukuran performa.
- Pedoman skripsi Sistem Informasi IPI yang berlaku.
- Jurnal tujuan pertama dan template Word resminya.
- Detail makalah seperti cover, daftar isi, serta penomoran halaman awal.
- Pemroses dan versi dependensi yang lolos uji Word serta Mendeley pada perangkat pengguna.

## Pemeriksaan paket rancangan

Paket P0 diperiksa untuk kelengkapan file, sintaks JSON, tautan relatif Markdown, konsistensi angka preset dengan tabel acuan, serta keberadaan seluruh alur yang diminta. Diagram ditulis dalam Mermaid agar dapat dirender langsung oleh GitHub. Keberhasilan push diperiksa melalui commit dan tree repositori.
