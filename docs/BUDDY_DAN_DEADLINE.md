# Buddy dan deadline

Panduan draf 0.4 • 7 November 2026

Buddy memakai enam foto meme dari pengguna. Ia mengikuti proses Academicgent dan menampilkan pop-up tugas yang sudah dimasukkan ke daftar deadline.

## Enam status

| Kondisi | Foto | Contoh pemicu |
| --- | --- | --- |
| Sedang bekerja | Monyet **Proses verifikasi** | Membaca PDF, menjalankan OCR, atau menyusun kandidat resume melalui Ollama |
| Proses selesai | Monyet **Verifikasi berhasil** | Revisi tersimpan, kandidat selesai, atau tugas ditandai selesai |
| Ada kesalahan | Monyet **Verifikasi gagal** | Pembacaan bahan atau proses AI gagal |
| Fokus, rencana, dan koreksi | **Ijin kompe** | Menyusun langkah kerja, memeriksa struktur, menyimpan koreksi halaman, atau menunggu pekerjaan |
| Meminta jawaban/tinjauan | **Jarvis** dengan status **Jarvis bertanya** | Memilih bantuan yang dibutuhkan atau mengingatkan agar kandidat ditinjau |
| Pengingat tugas | **Deadline sudah dekat, kid** | Waktu pengingat tiba atau deadline sudah lewat |

Foto ditampilkan utuh sesuai rasio aslinya. Judul dan pesan status ditulis di luar foto agar tetap terbaca. **Verifikasi berhasil** menandakan proses berhasil; label ini tidak mengesahkan kebenaran isi akademik. Peta aset ada di [assets/buddy](../assets/buddy/README.md).

## Menjalankan buddy

1. Pasang Python 3.11 atau lebih baru, lalu jalankan `setup.bat` dari folder proyek. Dependensi termasuk Pillow dipasang pada tahap ini.
2. Jalankan `start.bat` untuk membuka aplikasi browser dan buddy desktop.
3. Untuk buddy desktop saja, jalankan `start_buddy.bat`. Tombol **Buka aplikasi** membuka browser dan menjalankan server lokal bila belum aktif.

Jika muncul pesan Tcl/Tk, buka **Modify** pada installer Python Windows, aktifkan dukungan Tcl/Tk, lalu coba kembali. Pengujian tampilan desktop saat ini dilakukan melalui Tk di Linux/Xvfb; instalasi dan tampilan Windows perlu dicoba di laptop target.

Buddy desktop berupa foto kecil yang bergerak perlahan. Seret foto untuk memindahkan, klik untuk menampilkan pesan, dan klik dua kali untuk membuka aplikasi. Klik kanan foto untuk membuka menu jeda gerakan, jeda pengingat, selalu di atas, dan keluar. Membuka launcher dua kali tidak membuat dua buddy untuk folder data yang sama. Gelembung pengingat menyediakan tombol tunda, selesai, dan tutup. Pada Windows, area di sekitar foto menggunakan latar transparan; foto meme aslinya tetap berbentuk persegi panjang.

Buddy browser muncul di sudut kanan bawah dan dapat dikecilkan. Pengaturan untuk menyembunyikannya dan mematikan animasi ringan tersedia di tab **Tugas & buddy → Pengaturan buddy**. Saat buddy desktop aktif, pengingat deadline browser ditahan agar tidak muncul bersamaan. Status proses tetap dapat terlihat di browser.

## Menambah dan mengubah deadline

1. Buka **Tugas & buddy** dan pilih **Tambah tugas baru** pada **Kelola tugas**.
2. Isi nama, tanggal, jam, dan zona waktu **WIB**, **WITA**, atau **WIT**. Gunakan zona waktu deadline tugasmu, terlepas dari zona waktu sistem laptop.
3. Pilih **Mulai ingatkan**. Nilai awal adalah satu hari sebelum deadline. Jadwal berikutnya satu jam sebelum deadline dan saat jatuh tempo; jadwal yang bertepatan tidak digandakan.
4. Tambahkan catatan dan proyek terkait bila diperlukan. Pastikan **Ingatkan tugas ini** dicentang, lalu klik **Simpan tugas**.
5. Untuk mengubah tugas, pilih namanya pada **Kelola tugas**, sunting, lalu simpan. Jika tugas sudah berubah di jendela lain, klik **Muat ulang tugas** sebelum melanjutkan.

Deadline dimasukkan pengguna; versi ini belum mengambil jadwal dari PDF, kalender, atau sistem kampus. Tugas umum dapat disimpan tanpa membuat proyek resume. Tugas selesai disembunyikan dari daftar awal dan dapat dilihat melalui **Tampilkan tugas selesai**.

## Tindakan pada pop-up

| Tombol/pilihan | Hasil |
| --- | --- |
| **Tunda 15 m** | Menunda pengingat ini selama 15 menit; penundaan tersimpan walaupun buddy ditutup dan dibuka kembali |
| **Selesai** di browser maupun desktop | Menandai tugas selesai dan menghentikan pengingat berikutnya untuk tugas tersebut |
| **Tutup pengingat ini** di browser / **Tutup** di desktop | Menutup pesan saat ini; tugas tetap ada dan jadwal pengingat berikutnya tetap berlaku |
| **Jeda semua pengingat 1 jam** / **Jeda pengingat 1 jam** | Menahan seluruh pengingat sementara tanpa menghapus tugas |
| **Aktifkan lagi sekarang** / **Aktifkan pengingat lagi** | Mengakhiri jeda; menu desktop juga mengaktifkan kembali pengingat global |

Untuk mematikan pengingat sebuah tugas, hilangkan centang **Ingatkan tugas ini** lalu simpan. Untuk menghapusnya, buka **Hapus tugas**, centang konfirmasi, lalu klik **Hapus tugas**. Menghapus tugas juga menghapus catatan pengingatnya.

Satu tugas hanya mempunyai satu pengingat tertunda. Bila beberapa jadwal terlewat saat laptop mati, buddy menggabungkannya menjadi satu pesan. Beberapa tugas ditampilkan menurut deadline terdekat; setelah satu pesan ditangani, pesan berikutnya dapat muncul. Pesan tidak terus dibuat ulang pada setiap penyegaran layar.

## Bantuan rencana dan koreksi

Di **Draf resume**, buka **Buddy bantu merencanakan dan mengoreksi**, lalu klik **Buddy, bantu aku**. Jarvis meminta pilihan **Susun langkah kerja** atau **Periksa draf**. Setelah **Jalankan pilihan**, foto beralih ke **Ijin kompe** dan hasil muncul di panel.

Bantuan ini memakai aturan lokal untuk langkah kerja dan struktur dasar, seperti identitas yang kosong, judul bagian, halaman yang belum diperiksa, serta penanda isi sementara. Penilaian makna, angka, dan rujukan tetap dilakukan terhadap sumber. Pembuatan kandidat resume oleh model berlangsung melalui panel Ollama yang terpisah.

## Kapan pengingat berjalan

- Buddy desktop memeriksa jadwal sekitar setiap tiga detik selama prosesnya berjalan. Browser boleh ditutup.
- Tanpa buddy desktop, buddy browser memeriksa jadwal selama sesi aplikasi aktif dan tampilan buddy diaktifkan.
- Laptop mati atau tidur tidak menampilkan pop-up. Jadwal yang terlewat diperiksa setelah perangkat dan buddy aktif kembali. Pastikan jam perangkat benar.
- Menutup buddy melalui menu menghentikan proses desktop. Belum ada startup otomatis saat masuk Windows atau layanan Windows yang tetap berjalan setelah buddy keluar.

Versi ini menampilkan foto meme yang bergerak perlahan dan dapat digeser; gerakannya berupa perpindahan gambar, belum berupa animasi karakter dengan kaki. Belum ada installer `.exe`.

## Data dan percobaan pertama

Tugas dan pengaturan tersimpan dalam `projects.sqlite3` di folder `AcademicgentData` milik pengguna. Bila menggunakan `ACADEMICGENT_DATA_DIR`, aplikasi dan buddy harus memakai lokasi yang sama. Untuk membuat cadangan, keluar dari buddy, hentikan server Streamlit, lalu salin seluruh folder data. Menutup tab browser saja belum menghentikan server.

Untuk mencoba, buat tugas contoh dengan deadline beberapa menit lagi dan pengingat satu jam sebelumnya. Karena waktu pengingat awal sudah lewat, pop-up muncul pada pemeriksaan berikutnya. Coba tunda, selesaikan tugas, kecilkan buddy, dan tutup browser sambil membiarkan buddy desktop berjalan. Hapus tugas contoh setelah selesai. Rangkuman pengujian tersedia pada [status draf](STATUS_DRAF.md).
