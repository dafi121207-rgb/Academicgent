# Template dan sumber acuan

Pemeriksaan sumber dilakukan pada 6 November 2026. Katalog ini berisi acuan yang ditemukan, aturan yang dapat diverifikasi, dan pekerjaan yang diperlukan sebelum sebuah preset siap dipakai. Gaya sitasi, tata letak, dan susunan isi dicatat sebagai pengaturan yang dapat berasal dari pedoman berbeda.

## Hasil pemeriksaan tautan pengguna

| Sumber | Temuan | Peran dalam aplikasi |
| --- | --- | --- |
| SINTA | Halaman daftar jurnal menolak pembacaan langsung dengan HTTP 403. Penelusuran menemukan profil Jurnal Algoritma ITG dengan ID 621. | Menemukan jurnal tujuan, lalu membuka panduan dan template di situs penerbit. Status akreditasi harus dicek saat diperlukan. [Daftar jurnal](https://sinta.kemdiktisaintek.go.id/journals) · [Profil Algoritma](https://sinta.kemdiktisaintek.go.id/journals/profile/621) |
| Google Scholar | Halaman penelusuran dapat dibaca sebagian dan menampilkan pesan kegagalan operasi. | Pengguna mencari publikasi, lalu membawa DOI, metadata, atau dokumen yang dapat diakses ke proyek. [Google Scholar](https://scholar.google.com/?hl=id) |
| ResearchGate yang diberikan | Halaman berjudul “Jurnal”, berlabel preprint November 2020, dan mencantumkan DOI `10.31219/osf.io/kr6bc`. Abstrak membahas apologetika. PDF tersedia melalui permintaan kepada penulis. | Identitas publikasi dicatat sebagai temuan penelusuran. Tata letak berkas masih belum dapat diperiksa. [Halaman ResearchGate](https://www.researchgate.net/publication/347027048_Jurnal) |

## Contoh resmi yang ditemukan

### Jurnal Algoritma Institut Teknologi Garut

Relevan sebagai contoh artikel bidang Sistem Informasi dan teknologi. Halaman template menyebut edisi yang berlaku sejak 1 Mei 2024. Panduan penerbit memuat naskah bahasa Indonesia, A4, judul Times New Roman 14 pt, abstrak 100–300 kata, serta sitasi IEEE dengan Mendeley. Struktur inti mencakup pendahuluan, metode, hasil dan diskusi, lalu kesimpulan. [Template jurnal](https://jurnal.itg.ac.id/index.php/algoritma/template) · [Panduan penyerahan](https://jurnal.itg.ac.id/algoritma/about/submissions)

**Status calon preset** — panduan HTML diperiksa. Halaman template yang terbaca menampilkan nama edisi, tetapi tautan unduhan berkas belum berhasil diperoleh. Margin, kolom, styles, dan kesesuaian template dengan panduan memerlukan pemeriksaan DOCX resmi. Kebutuhan jumlah dan umur referensi akan dimasukkan ke preset setelah verifikasi versi template.

### Jurnal Sistem Informasi Universitas Indonesia

Contoh artikel Sistem Informasi berbahasa Inggris. Panduan mencantumkan A4, isi Times New Roman 11 pt, judul 20 pt, maksimal 14 halaman, abstrak maksimal 150 kata, serta APA edisi ke-7. Situs menyediakan tautan `JSI-template-2024-v1.0.docx`. [Panduan penulis](https://jsi.cs.ui.ac.id/index.php/jsi/about/submissions) · [Template Word resmi](https://cs.ui.ac.id/wp-content/uploads/2024/05/JSI-template-2024-v1.0.docx)

**Status calon preset** — panduan dan alamat berkas ditemukan. Pembaca web tidak memproses format biner DOCX sehingga layout belum diuji. Panduan menyebut awal isi 1,9 cm dari atas sekaligus margin 2,5 cm pada semua sisi. Nilai final menunggu inspeksi template dan klarifikasi pedoman terbaru.

### APA Style edisi ke-7

APA menyediakan contoh student paper dan professional paper dalam Word serta PDF. Student paper cocok sebagai pembanding format tugas akademik, dan aturan pengajar dapat menambah persyaratan. [Contoh resmi APA](https://apastyle.apa.org/style-grammar-guidelines/paper-format/sample-papers) · [Contoh student paper Word](https://apastyle.apa.org/style-grammar-guidelines/paper-format/student-paper.docx)

**Status calon preset** — sumber dan tautan Word teridentifikasi. Pemeriksaan file, font, bagian dokumen, dan hasil render menjadi pekerjaan tahap template internasional. Pengguna dapat memilih gaya sitasi APA 7 pada makalah kuliah sambil memakai margin yang ditentukan dosen.

### IEEE

IEEE menyediakan Template Selector untuk memilih format sesuai publikasi tujuan. Katalog Academicgent akan mencatat nama jurnal atau konferensi, versi berkas, dan aturan yang dihasilkan pemilihan tersebut. [Panduan template IEEE](https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/authoring-tools-and-templates/tools-for-ieee-authors/ieee-article-templates/) · [Template Selector](https://template-selector.ieee.org/)

**Status calon preset** — sumber resmi teridentifikasi. Publikasi tujuan belum dipilih, sehingga ukuran huruf, jumlah kolom, dan template berkas masih menunggu pemilihan tersebut.

## Preset awal dari kebutuhan pengguna

### Resume 0.1

Contoh resume Bab 12 yang diberikan pengguna diperiksa melalui struktur DOCX dan pratinjau render. Berikut nilai yang terbaca dari dokumen, dengan ukuran dibulatkan ke dua desimal.

| Elemen | Nilai pada contoh | Keputusan preset awal |
| --- | --- | --- |
| Kertas | A4 portrait | A4 portrait |
| Margin atas, bawah, kiri, kanan | 2,50 / 2,35 / 3,05 / 2,80 cm | Mengikuti nilai contoh |
| Judul | 16 pt, tebal, di tengah | Times New Roman 16 pt |
| Subjudul topik | 10 pt, tebal, di tengah | Times New Roman 10 pt |
| Isi | Times New Roman, ukuran dasar 11 pt, spasi 1,2 | 11 pt, rata kiri-kanan |
| Paragraf isi | Indentasi awal sekitar 0,55 cm, jarak sesudah 6 pt | Mengikuti nilai contoh |
| Judul bagian | 12 pt, tebal, melekat ke paragraf berikutnya | Nomor huruf sesuai jumlah bagian |
| Subbagian | 11,5 pt, tebal | Nomor angka sesuai struktur |
| Identitas | Tabel dua kolom, teks Arial 9 pt | Nama, NIM, prodi, dan dosen sebagai field lokal |
| Header | Arial 8 pt, label resume dan mata kuliah | Label mengikuti proyek |
| Footer | Identitas mahasiswa dan field PAGE | Nomor halaman otomatis |
| Warna | Beberapa styles menyimpan warna biru gelap dan abu-abu | Teks utama dan heading hitam sebagai usulan normalisasi |

Spesifikasi awal ini melengkapi pembacaan sebelumnya dengan ukuran isi 11 pt dan font identitas Arial. Preset mempertahankan susunan contoh, dengan normalisasi warna yang masih dapat diubah saat pratinjau template pertama. Jumlah halaman mengikuti isi. [Spesifikasi preset resume](../templates/presets/resume-v0.1.json)

### Makalah kuliah 0.1

Ketentuan yang pernah diberikan pengguna adalah A4, Times New Roman, judul 14 pt, isi 12 pt, margin atas 4 cm, margin sisi lainnya 3 cm, dan spasi 1,5. Nilai ini menjadi preset terpisah. Struktur cover, daftar isi, penomoran halaman awal, dan detail bab menunggu contoh atau instruksi tugas yang relevan. APA 7 menjadi usulan gaya awal yang dapat diganti sesuai dosen. [Spesifikasi preset makalah](../templates/presets/makalah-kuliah-v0.1.json)

### Skripsi Sistem Informasi IPI

Penelusuran awal menemukan panduan PGSD 2025 dan tesis Teknologi Pendidikan di domain institusi. Pedoman Sistem Informasi yang berlaku perlu diperoleh dari program studi atau pengguna sebelum format skripsi dikunci. Katalog menyimpan status `needs_program_guideline`. [Pedoman PGSD](https://pgsd.institutpendidikan.ac.id/wp-content/uploads/2025/07/Pedoman-Proposal-Skripsi-dan-Jurnal-PGSD-2025.pdf) · [Pedoman tesis Teknologi Pendidikan](https://tekpend.institutpendidikan.ac.id/wp-content/uploads/2024/12/Pedoman-tesis-pascasarjana-tekpend_final-review-dosen-dan-sosialisasi.pdf)

## Cara memvalidasi template baru

1. Catat penerbit, jenis dokumen, publikasi atau program studi tujuan, URL, tanggal akses, versi, dan ketentuan penggunaan berkas.
2. Baca panduan resmi dan periksa DOCX. Catat ukuran halaman, section, styles, font, kolom, header, footer, serta aturan sitasi.
3. Tampilkan konflik aturan dan konfirmasikan sumber yang berlaku sebelum menandai preset siap.
4. Simpan aturan yang terverifikasi sebagai preset dengan nomor versi. Berkas template pihak ketiga ditambahkan ke repositori hanya setelah ketentuan distribusinya diperiksa.
5. Buat dokumen uji pendek dan panjang yang mencakup judul panjang, tabel, gambar, dan sitasi sesuai cakupan preset.
6. Render semua halaman, periksa di Word desktop, lalu catat aplikasi dan versi yang digunakan dalam uji.

Katalog menggunakan status `source_identified`, `guidelines_reviewed`, `file_inspected`, dan `layout_validated`. Preset lokal yang baru disusun berstatus `draft_spec`. Status ini memberi pengguna informasi tentang bagian yang sudah diuji.

## Rujukan teknis

| Kebutuhan | Acuan |
| --- | --- |
| Margin dan section Word | [python-docx sections](https://python-docx.readthedocs.io/en/stable/user/sections.html) |
| Heading dan styles | [python-docx styles](https://python-docx.readthedocs.io/en/stable/user/styles-using.html) |
| Pemformatan referensi | [CSL specification](https://docs.citationstyles.org/en/stable/specification.html) · [Pandoc manual](https://pandoc.org/MANUAL.html) |
| Metadata publikasi | [Crossref API](https://www.crossref.org/documentation/retrieve-metadata/rest-api/) |
| Referensi ke Mendeley | [Impor koleksi](https://static.mendeley.com/md-stitch/releases/live/02-adding-references.e005845c.html) |
| Sitasi aktif di Word | [Mendeley Cite](https://www.mendeley.com/reference-management/mendeley-cite) |

Semua tautan penerbit perlu diperiksa kembali ketika sebuah preset mulai diimplementasikan atau dipakai untuk pengiriman naskah.
