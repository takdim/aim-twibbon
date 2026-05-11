# Product Requirements Document (PRD)
# Website Twibbon — Berbasis Flask

**Versi:** 1.0  
**Tanggal:** 11 Mei 2026  
**Status:** Draft  

---

## 1. Ringkasan Eksekutif

Website Twibbon adalah platform web yang memungkinkan pengguna mengunggah foto profil mereka, memilih frame/bingkai twibbon, dan mengunduh hasil gabungan sebagai satu gambar. Platform ini dibangun menggunakan **Flask (Python)** sebagai backend, dengan antarmuka yang intuitif dan responsif.

---

## 2. Latar Belakang & Tujuan

### 2.1 Latar Belakang
Twibbon telah menjadi medium populer untuk kampanye, perayaan, dan solidaritas di media sosial. Banyak organisasi, komunitas, dan individu membutuhkan cara mudah untuk membuat dan mendistribusikan twibbon tanpa keahlian desain grafis.

### 2.2 Tujuan Produk
- Memudahkan pengguna menggabungkan foto profil dengan frame kampanye.
- Menyediakan platform bagi admin/kreator untuk mengelola koleksi frame twibbon.
- Menghasilkan gambar twibbon berkualitas tinggi yang siap digunakan di media sosial.

---

## 3. Target Pengguna

| Segmen | Deskripsi |
|---|---|
| **End User** | Siapa pun yang ingin membuat twibbon — mahasiswa, pegawai, komunitas, dll. |
| **Admin / Kreator** | Organisasi atau individu yang membuat dan mengelola frame twibbon. |

---

## 4. Fitur Utama (Feature List)

### 4.1 Fitur untuk End User

#### F-01 · Pilih Frame Twibbon
- Menampilkan galeri frame twibbon yang tersedia.
- Filter berdasarkan kategori (nasional, kampus, komunitas, dll.).
- Pratinjau frame sebelum digunakan.

#### F-02 · Unggah Foto
- Pengguna mengunggah foto dari perangkat lokal.
- Format yang didukung: JPG, PNG, WEBP.
- Batas ukuran file: maksimal 5 MB.
- Pratinjau foto setelah diunggah.

#### F-03 · Editor Twibbon
- Overlay foto pengguna dengan frame yang dipilih secara real-time di browser.
- Kemampuan mengatur posisi dan ukuran foto (pan & zoom).
- Pratinjau hasil akhir sebelum diunduh.

#### F-04 · Unduh Hasil
- Mengunduh gambar hasil gabungan dalam format PNG atau JPG.
- Resolusi output: minimal 1000×1000 px (untuk kebutuhan media sosial).
- Nama file otomatis (contoh: `twibbon_[nama_frame]_[timestamp].png`).

#### F-05 · Bagikan Langsung
- Tombol salin tautan pratinjau hasil.
- Tombol berbagi langsung ke WhatsApp dan media sosial lain (opsional).

---

### 4.2 Fitur untuk Admin

#### F-06 · Manajemen Frame
- Upload frame twibbon baru (format PNG dengan transparansi/alpha channel).
- Edit metadata frame: nama, deskripsi, kategori, tanggal aktif/kedaluwarsa.
- Hapus atau nonaktifkan frame.

#### F-07 · Dashboard Admin
- Statistik jumlah unduhan per frame.
- Total pengunjung dan pengguna aktif.
- Frame terpopuler.

#### F-08 · Manajemen Kategori
- Tambah, edit, dan hapus kategori frame.

---

## 5. Spesifikasi Teknis

### 5.1 Stack Teknologi

| Layer | Teknologi |
|---|---|
| **Backend** | Python 3.11+, Flask 3.x |
| **Image Processing** | Pillow (PIL) |
| **Database** | SQLite (development) / PostgreSQL (production) |
| **ORM** | SQLAlchemy / Flask-SQLAlchemy |
| **Frontend** | HTML5, CSS3, JavaScript (Vanilla atau Alpine.js) |
| **File Storage** | Lokal (development) / AWS S3 atau Cloudinary (production) |
| **Autentikasi Admin** | Flask-Login |
| **Form Handling** | Flask-WTF |

### 5.2 Arsitektur Aplikasi

```
twibbon-app/
├── app/
│   ├── __init__.py           # Flask app factory
│   ├── config.py             # Konfigurasi environment
│   ├── models/
│   │   ├── frame.py          # Model Frame
│   │   └── user.py           # Model Admin User
│   ├── routes/
│   │   ├── main.py           # Rute publik (pilih frame, upload, download)
│   │   └── admin.py          # Rute admin (CRUD frame, dashboard)
│   ├── services/
│   │   └── image_processor.py  # Logika overlay gambar (Pillow)
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── uploads/          # Penyimpanan frame & hasil sementara
│   └── templates/
│       ├── base.html
│       ├── index.html        # Halaman utama / galeri frame
│       ├── editor.html       # Halaman editor twibbon
│       └── admin/
│           ├── dashboard.html
│           └── frames.html
├── migrations/
├── tests/
├── requirements.txt
├── run.py
└── .env
```

### 5.3 Endpoint API (Flask Routes)

| Method | Endpoint | Deskripsi |
|---|---|---|
| `GET` | `/` | Halaman utama — galeri frame |
| `GET` | `/frame/<id>` | Detail & editor frame |
| `POST` | `/upload` | Upload foto pengguna |
| `POST` | `/generate` | Proses overlay, kembalikan URL hasil |
| `GET` | `/download/<token>` | Unduh gambar hasil |
| `GET` | `/admin/` | Dashboard admin |
| `GET/POST` | `/admin/frames` | Daftar & tambah frame |
| `POST` | `/admin/frames/<id>/delete` | Hapus frame |
| `GET/POST` | `/admin/login` | Login admin |
| `GET` | `/admin/logout` | Logout admin |

### 5.4 Logika Image Processing (Pillow)

```python
# Contoh alur proses overlay
def generate_twibbon(user_photo_path, frame_path, output_path):
    base = Image.open(user_photo_path).convert("RGBA")
    frame = Image.open(frame_path).convert("RGBA")

    # Resize foto pengguna ke ukuran frame
    base = base.resize(frame.size, Image.LANCZOS)

    # Tempel frame di atas foto
    combined = Image.alpha_composite(base, frame)

    # Simpan hasil
    combined.convert("RGB").save(output_path, "PNG", quality=95)
```

---

## 6. Alur Pengguna (User Flow)

```
[Buka Website]
      ↓
[Lihat Galeri Frame] → [Pilih Frame]
      ↓
[Upload Foto Profil]
      ↓
[Editor: Atur Posisi Foto]
      ↓
[Klik "Buat Twibbon"]
      ↓
[Server: Proses Overlay via Pillow]
      ↓
[Pratinjau Hasil]
      ↓
[Unduh / Bagikan]
```

---

## 7. Persyaratan Non-Fungsional

| Kategori | Persyaratan |
|---|---|
| **Performa** | Proses overlay selesai dalam < 3 detik untuk gambar ≤ 5 MB |
| **Ketersediaan** | Uptime minimal 99% (production) |
| **Keamanan** | Validasi tipe file, sanitasi nama file, batas ukuran upload |
| **Responsivitas** | Tampil baik di mobile (min. 375px) dan desktop |
| **Aksesibilitas** | Kontras warna memenuhi standar WCAG AA |
| **Skalabilitas** | Mendukung minimal 100 pengguna bersamaan |

---

## 8. Keamanan

- File upload divalidasi tipe MIME (bukan hanya ekstensi).
- Nama file di-*sanitize* menggunakan `werkzeug.utils.secure_filename`.
- File hasil bersifat sementara dan dihapus otomatis setelah diunduh atau setelah X menit.
- Halaman admin dilindungi autentikasi Flask-Login.
- CSRF protection via Flask-WTF pada semua form.
- Variabel sensitif (secret key, DB URI) disimpan di `.env`, tidak di-*commit* ke repo.

---

## 9. Batasan & Asumsi

- **Batasan:** Tidak ada fitur registrasi pengguna publik; semua orang dapat langsung menggunakan tanpa login.
- **Batasan:** Satu sesi hanya menyimpan satu foto pengguna.
- **Asumsi:** Frame twibbon selalu berformat PNG dengan alpha channel (transparansi).
- **Asumsi:** Semua frame memiliki aspek rasio 1:1 (persegi).

---

## 10. Rencana Pengembangan (Milestone)

| Milestone | Deskripsi | Estimasi |
|---|---|---|
| **M1 — Setup & Core** | Setup Flask, DB, model Frame, upload & proses gambar dasar | 1 minggu |
| **M2 — Frontend** | Halaman galeri, editor (pratinjau real-time), unduh | 1 minggu |
| **M3 — Admin Panel** | CRUD frame, kategori, dashboard statistik | 1 minggu |
| **M4 — QA & Deploy** | Testing, optimasi, deployment ke server (VPS/Railway/Fly.io) | 1 minggu |

---

## 11. Kriteria Keberhasilan (Success Metrics)

- Pengguna dapat membuat dan mengunduh twibbon dalam < 2 menit.
- Tingkat error pada proses generate gambar < 1%.
- Admin dapat menambah frame baru tanpa bantuan developer.
- Waktu muat halaman utama < 2 detik.

---

## 12. Di Luar Cakupan (Out of Scope)

- Aplikasi mobile native (iOS/Android).
- Editor foto lanjutan (filter, teks, stiker).
- Fitur komunitas / komentar.
- Pembayaran / monetisasi frame premium (bisa jadi fase berikutnya).

---

*Dokumen ini dapat direvisi sesuai perkembangan kebutuhan. Perubahan signifikan harus didiskusikan bersama tim sebelum implementasi.*
