# Krypt Vault — Biometric-Authenticated Gatekeeper & Unified Security Vault

**Sistem Brankas Bukti Forensik Siber & Dokumen Intelijen Strategis**  
**Tugas Akhir Mata Kuliah Kriptografi — Program Studi Informatika**  
**Fakultas Teknik Industri, Universitas Pembangunan Nasional "Veteran" Yogyakarta**  
**Dosen Pengampu: Bagus Mahardika, S.Kom., M.T.**

**Disusun oleh:**  
Muhammad Ridho Hikmatul Maulana (123240218)  
Achmad Daud Ashshidieqiya (123240209)

---

## 1. Ringkasan Eksekutif

Krypt Vault adalah sistem keamanan brankas digital yang menerapkan arsitektur pertahanan tiga gerbang (*3-Gate Defense-in-Depth*) untuk mengamankan bukti forensik digital dan dokumen intelijen sensitif. Aplikasi ini menggabungkan autentikasi berbasis kepemilikan perangkat keras fisik (USB Hardware Dongle), autentikasi biometrik wajah optik dengan penyelarasan spasial multi-skala, kriptografi kunci simetris modern (AES-256-CBC, ChaCha20 Stream Cipher), super enkripsi kaskade (Extended Vigenere 256-byte modulo), steganografi spasial LSB, penyimpanan basis data SQLite *zero-plaintext at-rest*, serta rantai audit bukti forensik yang diikat dengan konsensus blockchain Proof-of-Work (PoW).

Seluruh sistem dirancang menggunakan implementasi murni berbasis pustaka standar dan kriptografi baku tanpa ketergantungan pada layanan cloud pihak ketiga, sehingga dapat dijalankan secara mandiri, lokal, dan portabel.

---

## 2. Pemenuhan 7 Kriteria Kriptografi Tugas Akhir

Sistem ini memenuhi 100% dari 7 kriteria tugas akhir yang disyaratkan:

| No | Kriteria Tugas Akhir | Implementasi Teknis pada Krypt Vault | Status Uji |
| :---: | :--- | :--- | :---: |
| 1 | **Login Biometrik & Intersept Dongle USB** | Gerbang 1 (*Hardware Dongle Intercept*): Memvalidasi tanda tangan HMAC-SHA256 pada berkas `.krypt_dongle` yang diikat ke nomor seri volume fisik USB flashdisk. Sesi terkunci otomatis seketika saat USB dicabut (*live USB bus watcher*). Tersedia mode token virtual lokal untuk demonstrasi tanpa port USB. | LULUS (100%) |
| 2 | **Login Algoritma Kriptografi (Hash / AES)** | Gerbang 2 (*Identity & Biometrics*): Kombinasi PBKDF2-HMAC-SHA256 (600.000 iterasi) untuk faktor pengetahuan, dan enkripsi template biometrik wajah $128 \times 128$ piksel menggunakan AES-128-EAX *authenticated encryption*. Kunci biometrik diturunkan secara dinamis via HKDF dan tidak pernah disimpan dalam basis data. | LULUS (100%) |
| 3 | **Pesan Teks Menggunakan Super Enkripsi** | Super Enkripsi Kaskade Dua Lapis: Lapis pertama menggunakan Extended Vigenere Cipher klasik (substitusi byte-modulo 256 pada seluruh rentang biner ASCII), dilapisi enkripsi modern AES-256-CBC dengan Salt 16-byte, IV CSPRNG 16-byte, dan PKCS#7 padding. Dikemas dalam token Base64 mandiri. | LULUS (100%) |
| 4 | **Pesan Berkas Menggunakan Algoritma Berbeda** | Enkripsi Berkas Biner Terpisah: Berkas biner (PDF, DOCX, ZIP, citra) diamankan menggunakan ChaCha20 Stream Cipher 256-bit (berbeda dari AES pada teks). Menggunakan kunci turunan PBKDF2 200.000 iterasi, nonce acak 12-byte, checksum verifikasi SHA-256, dan dikemas dalam wadah mandiri `.krypt.enc`. | LULUS (100%) |
| 5 | **Pesan Penting Dienkripsi pada Basis Data** | Keamanan At-Rest Zero-Plaintext: Seluruh data sensitif pada SQLite (`storage/vault.db`) disimpan dalam bentuk ciphertext terenkripsi (AES-256-CBC, ChaCha20, AES-128-EAX) dan hash ber-salt. Pemeriksaan biner langsung pada berkas basis data membuktikan tidak ada satu pun teks terbuka yang bocor. | LULUS (100%) |
| 6 | **Pesan Gambar Diamankan dengan Steganografi** | Steganografi Citra Spasial LSB: Pesan rahasia intelijen atau koordinat disisipkan ke dalam Least Significant Bit (LSB) kanal RGB pada citra berformat PNG lossless. Mendukung proteksi lapis ganda via passphrase dan penanda akhir muatan `<<<END>>>` untuk rekonstruksi presisi. | LULUS (100%) |
| 7 | **Aset Penting Diamankan dengan Blockchain** | Ledger Rantai Bukti Forensik: Setiap registrasi barang bukti dicatat ke dalam blok blockchain yang diikat secara kriptografis menggunakan Proof-of-Work SHA-256 (kesulitan target hash diawali `00`). Dilengkapi laboratorium pengujian manipulasi (*Tamper Lab*) untuk membuktikan deteksi instan terhadap pemalsuan riwayat. | LULUS (100%) |

---

## 3. Struktur Direktori Proyek

```text
Project_Biometric-Authenticated-Gatekeeper-Unified-Security-Vault-main/
|-- README.md                        <- Dokumentasi terpadu dan panduan pengujian
|-- geovault-crypto-app/             <- Direktori utama aplikasi Krypt Vault
    |-- .streamlit/config.toml       <- Konfigurasi tema gelap Streamlit
    |-- app.py                       <- Antarmuka utama dan perutean 3-gerbang
    |-- build_exe.bat                <- Skrip kompilasi standalone via PyInstaller
    |-- config.py                    <- Pengaturan jalur penyimpanan dan derivasi HKDF
    |-- database.py                  <- Lapisan abstraksi basis data SQLite
    |-- desktop_launcher.py          <- Peluncur jendela desktop PyWebView mandiri
    |-- generate_dongle.py           <- Utilitas pembuatan dan inspeksi token USB
    |-- KryptVault.spec              <- Spesifikasi build PyInstaller
    |-- requirements.txt             <- Daftar dependensi Python
    |-- reset_fresh.py               <- Utilitas pengembalian ke kondisi fresh
    |-- run_desktop.bat              <- Peluncur batch Windows via desktop_launcher.py
    |-- run_desktop.py               <- Peluncur server dan browser app mode
    |-- ui_theme.py                  <- Tema antarmuka Cyberpunk HUD & mode terang
    |-- modules/                     <- Modul engine kriptografi mandiri
    |   |-- auth_biometric.py        <- Biometrik wajah optik & PBKDF2 + AES-128-EAX
    |   |-- blockchain.py            <- Ledger rantai bukti PoW SHA-256
    |   |-- dongle_guard.py          <- Intersept hardware USB & verifikasi HMAC
    |   |-- file_crypto.py           <- Enkripsi berkas biner ChaCha20
    |   |-- steganography.py         <- Steganografi spasial LSB PNG lossless
    |   |-- super_encryption.py      <- Super enkripsi Extended Vigenere + AES-256-CBC
    |-- storage/                     <- Penyimpanan lokal at-rest terenkripsi
    |   |-- vault.db                 <- Basis data SQLite zero-plaintext
    |   |-- ledger.json              <- Ledger blockchain bukti forensik
    |   |-- files/                   <- Berkas biner terenkripsi (.krypt.enc)
    |-- tests/                       <- Suite pengujian unit otomatis
        |-- test_crypto_modules.py   <- Uji kebenaran matematis 7 kriteria kriptografi
```

---

## 4. Persyaratan Sistem

- **Sistem Operasi**: Windows 10 atau Windows 11 (64-bit disarankan).
- **Python**: Versi 3.10 atau yang lebih baru.
  - Unduh resmi: `https://www.python.org/downloads/`
  - *Penting*: Saat instalasi, pastikan mencentang kotak **"Add Python to PATH"**.
- **Kamera**: Webcam bawaan laptop / USB eksternal (tersedia opsi alternatif unggah foto bila perangkat tidak memiliki webcam).
- **Media Penyimpanan Tambahan**: Flashdisk USB tipe apa pun (tersedia mode token virtual lokal jika tidak membawa USB saat presentasi).

---

## 5. Cara Menjalankan Aplikasi

Tersedia tiga cara untuk menjalankan aplikasi sesuai kenyamanan Anda:

### Cara 1: Batch Launcher Desktop PyWebView (1-Klik via Windows Explorer)
Buka folder `geovault-crypto-app` dan klik ganda berkas:
```text
run_desktop.bat
```
- Skrip ini menjalankan `desktop_launcher.py` untuk mengaktifkan server lokal dan membuka jendela aplikasi desktop mandiri via PyWebView.
- Menutup jendela aplikasi via tombol [X] akan menghentikan proses server secara otomatis.

### Cara 2: Eksekusi Manual melalui Terminal
Buka PowerShell atau Command Prompt pada folder proyek:
```bash
cd geovault-crypto-app
pip install -r requirements.txt
python desktop_launcher.py
```
Atau jalankan antarmuka mode browser app / Streamlit langsung:
```bash
python run_desktop.py
```

### Cara 3: Build Standalone Executable (.exe) dengan PyInstaller
Masuk ke folder `geovault-crypto-app` dan jalankan:
```text
build_exe.bat
```
Hasil kompilasi standalone akan tersimpan di `dist\KryptVault\KryptVault.exe`.

---

## 6. Panduan Pengujian Pertama Kali (Fresh State)

Saat pertama kali dibuka, aplikasi berada dalam kondisi pabrik (*fresh state*):

### Langkah 1: Membuka Gerbang 1 (Hardware Dongle)
1. Tancapkan flashdisk USB ke komputer.
2. Pada layar aplikasi, pilih huruf drive flashdisk Anda (misal: `E:\`), lalu klik tombol **"Inisialisasi sebagai kunci"**.
3. Sistem akan membuat token rahasia `.krypt_dongle` bertanda tangan HMAC-SHA256 tanpa mengubah data lain di flashdisk Anda.
4. *Opsi Tanpa Flashdisk*: Pada panel kanan di bawah "Mode presentasi tanpa flashdisk", klik tombol **"Aktifkan token virtual"**. Layar akan langsung terbuka ke Gerbang 2.

### Langkah 2: Registrasi dan Login Operator (Gerbang 2)
1. Karena belum ada akun terdaftar, buka tab **"Daftarkan operator baru"**.
2. Masukkan nama pengguna (contoh: `analyst_01`), kata sandi (minimal 8 karakter huruf dan angka), dan posisikan wajah menghadap webcam lalu ambil foto (atau unggah berkas foto wajah).
3. Klik tombol **"Daftarkan operator"**. Kunci PBKDF2 diturunkan dan template wajah $128 \times 128$ disegel dengan AES-128-EAX.
4. Pindah ke tab **"Masuk"**, masukkan kredensial yang baru didaftarkan, ambil foto wajah verifikasi, lalu klik **"Verifikasi dan masuk"**.
5. Algoritma penyelarasan spasial multi-skala akan mencocokkan wajah (ambang batas kelulusan $\ge 70\%$). Jika valid, ruang kerja brankas utama langsung terbuka.

### Langkah 3: Menjalankan Fitur Ruang Kerja (Gerbang 3)
Gunakan bilah menu di sebelah kiri untuk mengakses 8 modul kerja:
- **Ringkasan (Overview)**: Status sistem dan rangkuman kriptografi.
- **Super Enkripsi Teks**: Enkripsi kaskade Vigenere + AES-256-CBC.
- **Enkripsi Berkas**: Enkripsi biner dokumen ChaCha20 (.krypt.enc).
- **Steganografi Citra**: Penyisipan teks rahasia ke kanal LSB PNG.
- **Inspeksi Basis Data**: Audit at-rest zero-plaintext pada SQLite.
- **Blockchain Ledger**: Pencatatan bukti PoW & simulasi tamper lab.
- **Pengaturan Kunci USB**: Manajemen dan status drive hardware key.
- **Keluar**: Mengunci sesi kembali ke Gerbang 1.

---

## 7. Skenario Demonstrasi & Presentasi 5 Menit di Hadapan Dosen

Gunakan skenario berikut saat melakukan pengujian dan demonstrasi agar seluruh 7 kriteria terbukti secara runtut dan meyakinkan:

```text
[00:00 - 00:45] Gerbang 1: Hardware Dongle Intercept & Deteksi Cabut USB
[00:45 - 01:45] Gerbang 2: Autentikasi PBKDF2 & Biometrik Wajah Multi-Skala
[01:45 - 02:30] Gerbang 3: Super Enkripsi Teks Kaskade (Vigenere + AES-256)
[02:30 - 03:15] Gerbang 3: Enkripsi Berkas Biner ChaCha20 (.krypt.enc)
[03:15 - 03:45] Gerbang 3: Steganografi Spasial LSB Citra PNG Lossless
[03:45 - 04:15] Gerbang 3: Audit Basis Data SQLite At-Rest Zero-Plaintext
[04:15 - 05:00] Gerbang 3: Ledger Bukti Blockchain PoW & Tamper Lab Attack
```

### Prosedur Demonstrasi Tiap Kriteria:
1. **Pengujian Kriteria 1 (Dongle Guard)**:
   - Tunjukkan layar tertahan di Gerbang 1 saat flashdisk belum terpasang.
   - Tancapkan flashdisk atau aktifkan token virtual; sistem seketika membuka Gerbang 2.
   - *Uji Proteksi Cabut USB*: Saat berada di dalam ruang kerja, cabut flashdisk USB; dalam hitungan 4 detik background watcher akan langsung mengunci paksa sesi kembali ke Gerbang 1.
2. **Pengujian Kriteria 2 (Biometrik Wajah & Toleransi Gerak)**:
   - Lakukan login dengan wajah terdaftar; skor kecocokan mencapai 85%–100% dan sesi terbuka.
   - Coba gunakan foto orang lain atau simulasikan wajah berbeda; sistem menolak akses karena skor kemiripan berada di bawah 60% ($< 70\%$).
3. **Pengujian Kriteria 3 (Super Enkripsi Teks)**:
   - Buka menu Super Enkripsi Teks, masukkan teks rahasia, kunci Vigenere, dan passphrase AES.
   - Tunjukkan hasil dua lapis: transformasi Vigenere byte-modulo 256 dilanjutkan enkripsi AES-256-CBC hingga menghasilkan token Base64.
   - Lakukan dekripsi pada tab dekripsi untuk membuktikan plaintext pulih 100% identik.
4. **Pengujian Kriteria 4 (Enkripsi Berkas Dokumen ChaCha20)**:
   - Jelaskan bahwa enkripsi berkas sengaja menggunakan cipher biner yang berbeda dari teks, yaitu ChaCha20 Stream Cipher 256-bit.
   - Unggah berkas dokumen (PDF atau DOCX), masukkan passphrase, unduh berkas terenkripsi `.krypt.enc`.
   - Lakukan dekripsi berkas tersebut; sistem memvalidasi checksum SHA-256 asli dan berkas dokumen pulih sempurna.
5. **Pengujian Kriteria 5 (Audit Basis Data At-Rest Zero-Plaintext)**:
   - Buka modul Inspeksi Basis Data.
   - Tunjukkan tampilan ciphertext langsung dari berkas fisik `storage/vault.db`: kata sandi hanya berupa intisari hash ber-salt, template biometrik berupa BLOB acak AES-128-EAX, dan seluruh pesan intelijen tersimpan dalam bentuk terenkripsi.
6. **Pengujian Kriteria 6 (Steganografi Citra PNG LSB)**:
   - Buka modul Steganografi Citra, unggah berkas cover PNG, masukkan pesan rahasia dan passphrase.
   - Unduh citra stego yang dihasilkan (secara visual tampak identik dengan aslinya).
   - Ekstrak pesan dari citra stego untuk membuktikan pesan terbaca tepat hingga delimiter `<<<END>>>`.
7. **Pengujian Kriteria 7 (Blockchain Proof-of-Work & Tamper Lab)**:
   - Buka modul Blockchain Ledger, tunjukkan rantai blok yang tertaut dengan hash SHA-256 berawalan `00`.
   - Tambahkan blok barang bukti baru; sistem akan menambang nonce PoW secara real-time.
   - Buka tab "Uji Integritas & Tamper Lab", simulasikan manipulasi isi blok lama; sistem langsung mendeteksi patahnya rantai (*CHAIN_TAMPERED*) dan menandai blok yang korup secara visual.

---

## 8. Cara Mengembalikan Data ke Kondisi Fresh Pabrik

Jika Anda atau penguji telah selesai melakukan demonstrasi dan ingin mengosongkan kembali seluruh akun, riwayat laporan, dan berkas ke kondisi awal, jalankan skrip berikut dari folder `geovault-crypto-app`:
```bash
cd geovault-crypto-app
python reset_fresh.py
```
Tekan tombol `Y` saat diminta konfirmasi. Skrip akan:
- Mengosongkan tabel pengguna dan menghapus template biometrik lama.
- Mengosongkan riwayat berkas terenkripsi dan laporan rahasia.
- Menyetel ulang rantai blockchain kembali ke Blok Genesis #0.
- Membersihkan token virtual, sehingga siap dipakai kembali untuk pengujian baru.

---

## 9. Suite Pengujian Otomatis (Unit Testing)

Krypt Vault dilengkapi suite pengujian otomatis komprehensif yang menguji kebenaran matematis seluruh mekanisme kriptografi secara independen dari antarmuka:

Jalankan perintah berikut pada terminal:
```bash
cd geovault-crypto-app
python -m unittest tests/test_crypto_modules.py
```

### Hasil Pengujian:
```text
Ran 7 tests in 1.917s

OK
```
- `test_01_dongle_hmac_and_guard`: Validasi HMAC-SHA256, deteksi pemalsuan token, dan penguncian sesi unmount.
- `test_02_biometric_face_and_pbkdf2_login`: Verifikasi PBKDF2 600k iterasi, segel AES-128-EAX, toleransi gerak wajar kepala 10px, dan penolakan penyusup.
- `test_03_super_encryption_cascade`: Kebenaran kaskade Extended Vigenere byte-modulo 256 + AES-256-CBC.
- `test_04_chacha20_file_encryption`: Enkripsi berkas ChaCha20, validasi wadah `.krypt.enc`, dan verifikasi checksum SHA-256.
- `test_05_at_rest_zero_plaintext_sqlite`: Audit kebocoran plaintext pada berkas fisik basis data `vault.db`.
- `test_06_lsb_steganography_png`: Penyisipan bit LSB, proteksi passphrase, dan pembacaan delimiter `<<<END>>>`.
- `test_07_blockchain_pow_integrity_and_tamper`: Penambangan PoW target `00`, verifikasi tautan hash, dan deteksi pemalsuan riwayat.
