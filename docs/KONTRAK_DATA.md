# Kontrak data Academicgent

Versi rancangan 0.1, dengan kontrak implementasi buddy draf 0.3 ditambahkan pada 7 November 2026. Bagian rancangan menjadi dasar model Python dan validasi pada saat implementasi. Semua contoh menggunakan identitas dan materi sintetis.

## Kontrak implementasi buddy 0.3

Empat tabel berikut sudah dibuat oleh `storage.connect()` pada database proyek yang sama. Tabel proyek dan revisi lama tetap dipertahankan.

| Tabel | Kolom utama | Aturan implementasi |
| --- | --- | --- |
| `tasks` | `id`, `title`, `note`, `project_id`, `due_at`, `timezone`, `lead_minutes`, `completed`, `reminders_enabled`, `next_reminder_at`, `revision`, `updated_at` | Judul wajib maksimal 160 karakter, catatan maksimal 2.000; proyek opsional; edit/hapus memakai revisi yang dibaca |
| `task_notifications` | `id`, `task_id`, `task_revision`, `status`, `not_before`, `created_at` | Status `pending`, `acknowledged`, atau `cancelled`; indeks unik membatasi satu `pending` per tugas; penghapusan tugas menghapus notifikasinya |
| `buddy_events` | `id`, `state`, `message`, `project_id`, `expires_at` | Status `working`, `success`, `error`, `focus`, `question`, atau `deadline`; pesan maksimal 500 karakter; event kedaluwarsa dibersihkan saat publikasi event berikutnya |
| `buddy_settings` | `key`, `value` | Nilai JSON untuk visibilitas web, pengingat global, animasi, waktu akhir jeda, heartbeat desktop, dan always-on-top |

`due_at`, `next_reminder_at`, `not_before`, `created_at`, `expires_at`, heartbeat, dan akhir jeda memakai detik Unix UTC. `timezone` menyimpan `WIB`, `WITA`, atau `WIT` untuk input dan tampilan. `updated_at` memakai ISO 8601 UTC; flag boolean pada `tasks` disimpan sebagai 0/1, sedangkan `buddy_settings` memakai boolean JSON. Waktu sistem perangkat menjadi sumber jam scheduler.

Penyimpanan tugas baru menghasilkan UUID dan revisi 1. Perubahan menaikkan revisi serta membatalkan notifikasi `pending` lama. Tindakan terhadap notifikasi memeriksa `task_revision` terhadap revisi tugas saat ini, sehingga pesan lama tidak dapat menyelesaikan tugas yang sudah disunting.

Penundaan mempertahankan notifikasi yang sama dengan `not_before` 15 menit ke depan. Menutup pengingat mengubah status menjadi `acknowledged` dan memilih jadwal berikutnya. Menyelesaikan tugas sekaligus menonaktifkan jadwal berikutnya dan menaikkan revisi tugas. Pengingat global atau per tugas yang dimatikan tidak menghapus tugas.

Data ini dipakai bersama oleh Streamlit dan Tkinter. Transaksi tulis saat pemilihan jadwal menghindari dua scheduler membuat pesan yang berbeda untuk tugas sama. Heartbeat desktop hanya mengarahkan permukaan pop-up; riwayat dan jadwal tetap berada dalam database lokal. Lihat [arsitektur](ARSITEKTUR.md) dan [panduan pengingat](BUDDY_DAN_DEADLINE.md).

## Entitas dan relasi

| Entitas | Field utama | Aturan |
| --- | --- | --- |
| Profile | `id`, `name`, `student_number`, `study_program` | Profil berada di perangkat dan dapat disalin ke proyek |
| Project | `id`, `kind`, `title`, `profile_snapshot`, `preset_snapshot`, `citation_style`, `revision` | Snapshot mengikat identitas dan format untuk proyek tersebut |
| Source | `id`, `project_id`, `path`, `sha256`, `media_type`, `reference_id` | Berkas asli immutable, referensi bibliografi boleh belum tersedia |
| SourcePage | `id`, `source_id`, `pdf_position`, `printed_label`, `text`, `extraction_method`, `text_revision` | Posisi PDF 1-based, nomor cetak berupa string opsional |
| ReadingOrder | `id`, `project_id`, `revision`, `page_ids`, `confirmed_at` | Setiap page ID yang dipilih muncul satu kali dalam urutan |
| Evidence | `id`, `page_id`, `text_revision`, `start`, `end`, `excerpt` | Rentang karakter merujuk teks ekstraksi yang berversi |
| Reference | `id`, `csl`, `metadata_status`, `verification_origin`, `verified_at` | Identitas karya dan bukti isi dicatat terpisah |
| DraftRevision | `id`, `project_id`, `revision`, `blocks`, `reading_order_revision`, `parent_revision` | Revisi tersimpan immutable, proyek menunjuk revisi aktif |
| CitationCluster | `id`, `items`, `mode`, `prefix`, `suffix` | Mengikat satu atau lebih reference ID dan locator ke posisi dalam teks |
| GenerationJob | `id`, `input_revision`, `input_hash`, `model`, `prompt_version`, `status`, `checkpoint` | Hasil hanya dapat diterapkan ke revisi yang masih cocok |
| Export | `id`, `draft_revision`, `preset_hash`, `style_hash`, `renderer_version`, `files`, `review_status` | Hasil dapat ditelusuri ke masukan dan aturan saat dibuat |

## Contoh draf minimal

```json
{
  "schema_version": 1,
  "project_id": "project-demo",
  "kind": "resume",
  "title": "Resume materi pembelajaran",
  "profile_snapshot": {
    "name": "Mahasiswa Contoh",
    "student_number": "00000000000",
    "study_program": "Program Studi Contoh"
  },
  "preset": {"id": "resume", "version": "0.1"},
  "revision": 1,
  "reading_order_revision": 1,
  "blocks": [
    {
      "id": "heading-1",
      "type": "heading",
      "level": 1,
      "text": "Pendahuluan",
      "source_page_ids": ["page-3"]
    },
    {
      "id": "paragraph-1",
      "type": "paragraph",
      "inlines": [
        {"type": "text", "text": "Contoh pernyataan yang akan ditinjau pengguna."}
      ],
      "evidence_ids": ["evidence-1"],
      "support_review": "pending"
    }
  ]
}
```

Penomoran A, B, C dan locator tampilan dihitung saat rendering dari struktur serta daftar halaman. Nilai teks heading menyimpan judul bersih. Blok yang didukung bertambah menurut fase, dimulai dari heading, paragraf, dan daftar, kemudian tabel, gambar, caption, serta persamaan yang diuji.

## Posisi dan bukti sumber

```json
{
  "page": {
    "id": "page-3",
    "source_id": "source-demo",
    "pdf_position": 3,
    "printed_label": "227",
    "text_revision": 1,
    "text": "Contoh teks sumber.",
    "extraction_method": "native",
    "review_status": "confirmed"
  },
  "evidence": {
    "id": "evidence-1",
    "page_id": "page-3",
    "text_revision": 1,
    "start": 0,
    "end": 19,
    "excerpt": "Contoh teks sumber."
  }
}
```

Offset memakai indeks karakter Unicode Python pada teks yang sudah dinormalisasi ke newline LF. Rentang berupa `[start, end)`. `excerpt` harus sama dengan potongan teks tersebut. Teks OCR yang dikoreksi memperoleh `text_revision` baru. Bukti lama masih terkait revisi sebelumnya, dan draf yang bergantung padanya meminta peninjauan.

Urutan visual aplikasi menyimpan `page_ids` terpisah. Jika halaman PDF ketiga adalah halaman buku 227 dan urutan baca pertama, ketiga nilai itu tetap mempunyai arti masing-masing. Bukti dari beberapa halaman disimpan sebagai beberapa record agar pemetaan tetap tepat.

## Referensi dan posisi sitasi

Referensi mengikuti CSL-JSON dengan tipe sumber yang sesuai. Penulis disimpan terstruktur, termasuk `literal` untuk nama lembaga atau nama tunggal yang membutuhkan perlakuan tersebut. Tahun, DOI, judul, penerbit, jurnal, volume, nomor, dan halaman diisi dari metadata yang tersedia. Nilai yang belum diketahui tetap kosong dan ditampilkan untuk pemeriksaan.

```json
{
  "reference": {
    "id": "ref-demo",
    "csl": {
      "id": "ref-demo",
      "type": "book",
      "title": "Bahan latihan sintetis",
      "author": [{"literal": "Tim Contoh"}],
      "issued": {"date-parts": [[2026]]}
    },
    "metadata_status": "user_entered",
    "verification_origin": null,
    "verified_at": null
  },
  "citation_cluster": {
    "id": "c001",
    "mode": "parenthetical",
    "items": [
      {"reference_id": "ref-demo", "label": "page", "locator": "227–229"}
    ],
    "prefix": "",
    "suffix": ""
  },
  "inline": {"type": "citation", "cluster_id": "c001"}
}
```

Kutipan adalah node dalam urutan inline paragraf sehingga posisi, pengelompokan, dan locator tetap tersedia setelah teks diedit. Node teks mendukung penekanan tebal atau miring sesuai kebutuhan renderer. Mode naratif dan parentetik diterjemahkan ke struktur sitasi formatter. Kutipan langsung juga menyimpan bukti dan status pengecekan kecocokan dengan teks sumber.

Status metadata yang direncanakan adalah `user_entered`, `imported_unchecked`, `matched`, dan `needs_review`. Status dukungan klaim adalah `pending`, `confirmed`, dan `insufficient`. Aplikasi mencatat siapa atau langkah apa yang mengubah status dan kapan. Sumber metadata yang cocok tidak otomatis mengubah status dukungan klaim.

Deduplikasi memakai DOI ternormalisasi ketika tersedia. Tanpa DOI, kesamaan judul, tahun, dan penulis hanya mengusulkan penggabungan. Saat pengguna menggabungkan referensi, seluruh citation cluster dipindahkan secara transaksional dan ID lama menyimpan pemetaan ke ID yang dipertahankan.

## Keluaran AI

Model menerima potongan sumber dengan ID eksplisit dan instruksi struktur. Keluaran berisi blok kandidat, ID bukti, serta catatan bagian yang belum memiliki dukungan. Model hanya boleh merujuk ID sumber yang disertakan dalam masukan. Metadata bibliografi dibentuk dari koleksi referensi yang telah dimasukkan pengguna.

Pemeriksaan keluaran meliputi tipe dan field wajib, batas panjang, heading yang valid, ID sumber yang dikenal, serta struktur sitasi. Validasi bentuk diikuti pemeriksaan angka, nama, dan locator. Pemeriksaan dukungan argumen membutuhkan pembandingan dengan sumber pada layar tinjau.

## Kontrak preset

Setiap preset memiliki `schema_version`, `id`, `version`, `status`, `document_kind`, `page`, `typography`, `structure`, `citation`, `provenance`, dan `unresolved`. Ukuran halaman dan margin memakai cm, ukuran huruf dan jarak paragraf memakai pt, dan spasi menggunakan pengali. Nilai `null` menunjukkan pilihan yang masih perlu ditetapkan atau mengikuti proyek.

Preset resume dan makalah yang ada berstatus `draft_spec`. Pengguna dapat mengubah preset pada proyek, dan perubahan disimpan sebagai snapshot lokal dengan asal aturan. Status `validated` baru digunakan setelah kasus uji dokumen pendek dan panjang serta pemeriksaan Word selesai. Tiap ekspor menyimpan snapshot atau checksum yang dapat ditelusuri.

## Pemeriksaan sebelum ekspor

Kesalahan struktural seperti ID sitasi hilang, urutan halaman tidak valid, margin membuat area isi negatif, dan format DOCX rusak harus diselesaikan sebelum ekspor terkait berjalan. Masalah isi seperti sumber belum diperiksa, metadata kurang lengkap, atau pedoman skripsi belum final tampil sebagai daftar pekerjaan yang tersimpan bersama revisi.

Pengguna dapat menyimpan dan mengunduh draf untuk dilanjutkan. Status siap ditinjau hanya diberikan setelah pemeriksaan format serta sumber selesai dan pengguna menandai isi sudah ditinjau. Ekspor yang lebih lama mempertahankan status dan hasil pemeriksaannya sendiri.
