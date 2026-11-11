# 🎯 PANDUAN DEMONSTRASI & PENGUJIAN TUGAS AKHIR KRIPTOGRAFI
## B.A.G.U.S. Vault (*Biometric-Authenticated Gatekeeper & Unified Security Vault*)
**Dosen Pengampu: Pak Bagus | UPN "Veteran" Yogyakarta**

---

## ⏱️ Alur Demonstrasi 5 Menit (Step-by-Step Demo Flow)

Gunakan skenario berikut saat melakukan presentasi di hadapan Pak Bagus agar ke-7 kriteria dapat didemonstrasikan secara runtut, profesional, dan meyakinkan tanpa hambatan teknis.

```text
+---------------------------------------------------------------------------------+
| [00:00 - 00:45] INTRO & GATE 01: Lockscreen Merah & Hardware Dongle Intercept   |
| [00:45 - 01:45] GATE 02: Realtime Face Recognition & Intruder Rejection Demo     |
| [01:45 - 02:30] GATE 03 / SUB-01: Super Enkripsi Teks (Vigenere + AES-256-CBC)  |
| [02:30 - 03:15] GATE 03 / SUB-02: ChaCha20 File Encryption & .bagus.enc Package |
| [03:15 - 03:45] GATE 03 / SUB-03: LSB Image Steganography PNG & Delimiter       |
| [03:45 - 04:15] GATE 03 / SUB-04: At-Rest Database Inspection (Zero-Plaintext)  |
| [04:15 - 05:00] GATE 03 / SUB-05: Blockchain PoW Mining & Tamper Lab Attack     |
+---------------------------------------------------------------------------------+
```

---

### Langkah 1: Membuka Aplikasi & Menunjukkan Gate 01 (Hardware Dongle)
1. Buka terminal dan jalankan:
   ```bash
   streamlit run app.py
   ```
2. **Kondisi Awal (Locked State)**:
   - Tunjukkan kepada Pak Bagus bahwa aplikasi langsung menolak akses dan menampilkan **Layar Merah Crimson (*CRITICAL_SECURITY_HALT*)**.
   - Jelaskan: *"Pak, sistem mengunci total seluruh routing aplikasi karena token `.geovault_dongle` bertanda tangan HMAC-SHA256 belum terdeteksi pada drive sistem."*
   - Tunjukkan tabel **Live USB Diagnostic Telemetry** di layar bawah yang memindai setiap drive letter Windows.
3. **Membuka Gate 01 via Demo Switch**:
   - Buka expander `[ DEV_DEMO: MOUNT / UNMOUNT VIRTUAL DONGLE ]`.
   - Klik tombol **`[ 🟢 MOUNT_VIRTUAL_DONGLE ]`**.
   - Layar otomatis me-refresh dan langsung beralih ke **Gate 02**, membuktikan validasi HMAC-SHA256 sukses dan anti-cloning binding aktif.

---

### Langkah 2: Gate 02 (Realtime Face Recognition & Biometric Authentication)
1. **Pendaftaran Operator Baru**:
   - Buka tab `[02] ENROLL_NEW_IDENTITY (REGISTRASI)`.
   - Masukkan handle: `analyst_01`, passkey: `CyberPass#2026`.
   - Klik **`[ ⚡ INITIALIZE_REALTIME_OPTICAL_SCAN ]`**.
   - Tunjukkan animasi HUD pemindaian optik 2 detik: citra dinormalisasi ke matriks grayscale `128x128` via Pillow, dihitung hash pixel SHA-256, dan template biometrik disegel dalam database dengan **AES-128-EAX**.
2. **Uji Coba Penolakan Penyusup (*Intruder Rejection*)**:
   - Buka tab `[01] AUTHENTICATE_OPERATOR (LOGIN)`.
   - Masukkan identitas `analyst_01` dan passkey `CyberPass#2026`.
   - Centang kotak: **`[ 🧪 DEV_DEMO: Simulasikan Wajah Tidak Cocok / Penyusup ]`**.
   - Klik tombol inisialisasi pemindaian. Sistem akan menampilkan penolakan merah:
     `Authentication failed: similarity did not meet threshold (<80%)`.
3. **Login Wajah Berhasil**:
   - Hilangkan centang simulasi wajah tidak cocok.
   - Klik kembali tombol pemindaian wajah. Sistem memverifikasi kecocokan wajah $\ge 80\%$ dan langsung membuka brankas utama **Gate 03**.

---

### Langkah 3: Gate 03 — Modul 01: Super Enkripsi Teks (Klasik + Modern)
1. Buka menu sidebar: **`[01] LAPORAN INTELIJEN (Super Enkripsi Teks)`**.
2. Masukkan:
   - Judul: `DISPATCH_OPERASI_MERBABU`
   - Isi Plaintext: `Target terkonfirmasi di Safehouse Sektor B. Koordinat -7.7828, 110.3670.`
   - Kunci Vigenère: `KRIPTOKLASIK`
   - Passphrase AES: `ModernAES256Secure!`
3. Klik tombol **`[ 🔒 JALANKAN SUPER ENKRIPSI ]`**.
4. Tunjukkan telemetri live di layar:
   - **Tahap 1**: Hasil substitusi polialfabetik Vigenère byte-modulo 256.
   - **Tahap 2**: Parameter AES-256-CBC (Salt 16B, IV 16B CSPRNG, Ciphertext Hex).
   - **Token Base64**: Format final yang disimpan dalam SQLite.
5. Pindah ke tab **`[02] DEKRIPSI DISPATCH INTELIJEN`**, pilih laporan yang baru disimpan, masukkan kedua kunci, dan klik dekripsi untuk membuktikan pemulihan plaintext asli 100% sempurna.

---

### Langkah 4: Gate 03 — Modul 02: Enkripsi Berkas Dokumen (ChaCha20 Stream Cipher)
1. Buka menu sidebar: **`[02] BERKAS BARANG BUKTI (Enkripsi File ChaCha20)`**.
2. Jelaskan kepada Pak Bagus: *"Pak, untuk file dokumen biner, kami sengaja menggunakan algoritma yang berbeda dari teks, yaitu ChaCha20 Stream Cipher (256-bit key, 12-byte nonce, PBKDF2 200.000 iterasi) yang dikemas dalam format amplop mandiri `.bagus.enc` ber-checksum SHA-256."*
3. Unggah file dokumen sampel (misal: PDF, DOCX, TXT, atau gambar).
4. Masukkan passphrase: `ChaChaPass#2026`, klik **`[ 🔐 ENKRIPSI DOKUMEN ]`**.
5. Unduh file `.bagus.enc` yang dihasilkan.
6. Buka tab Dekripsi, unggah berkas `.bagus.enc`, masukkan passphrase, dan tunjukkan bahwa file asli berhasil dipulihkan lengkap dengan nama asli dan verifikasi kesesuaian checksum SHA-256.

---

### Langkah 5: Gate 03 — Modul 03: Steganografi Citra PNG LSB
1. Buka menu sidebar: **`[03] CITRA FORENSIK STEGANOGRAFI (LSB PNG)`**.
2. Unggah gambar cover PNG.
3. Masukkan pesan tersembunyi: `[TOP SECRET FORENSIC NOTE: ENCRYPTED EXTRACTION POINT 02:00 WIB]`.
4. Masukkan passphrase opsional: `StegoPass#99`.
5. Klik **`[ ✨ SISIPKAN PESAN KE BIT LSB CITRA ]`**.
6. Tunjukkan perbandingan citra asli vs citra stego (keduanya identik secara kasat mata bagi mata manusia).
7. Unduh citra stego, masuk ke tab Ekstraksi, unggah citra tersebut, masukkan passphrase, dan klik **Ekstrak Pesan**. Tunjukkan pembacaan berhenti presisi pada delimiter `<<<END>>>`.

---

### Langkah 6: Gate 03 — Modul 04: Inspeksi Basis Data At-Rest (Zero-Plaintext)
1. Buka menu sidebar: **`[04] INSPEKSI BASIS DATA (Encrypted SQLite At-Rest)`**.
2. Tunjukkan tampilan **Komparasi Side-by-Side**:
   - Kolom Kiri: **Raw SQLite Ciphertext (At-Rest)** di file `storage/vault.db` membuktikan password ber-salt PBKDF2 hash, vektor wajah berupa BLOB terenkripsi AES-128-EAX, laporan intelijen berupa token Base64, dan berkas biner terenkripsi di disk.
   - Kolom Kanan: **Decrypted View** hanya terbuka jika operator memiliki sesi sah.
3. Jelaskan prinsip *Zero-Plaintext Persistence*: bahkan jika file database SQLite dicuri atau dibuka langsung dengan SQLite Browser, tidak ada satu pun rahasia yang bocor.

---

### Langkah 7: Gate 03 — Modul 05: Blockchain Ledger & Tamper Lab
1. Buka menu sidebar: **`[05] CHAIN OF CUSTODY LEDGER (PoW Blockchain)`**.
2. Klik tombol **`[ 🔍 VERIFY_CHAIN_INTEGRITY ]`**. Tunjukkan indikator hijau: `INTEGRITAS RANTAI VALID`.
3. **Menambang Blok Aset Baru**:
   - Buka tab `[01] TAMBANG BLOK BUKTI BARU`.
   - Pilih klasifikasi: `High-Value Record`, masukkan nama: `BUKTI_DIGITAL_LAPTOP_TARGET`.
   - Klik **`[ ⛏️ SEGEL AES-256-GCM & TAMBANG BLOK ]`**.
   - Tunjukkan proses mining SHA-256 Proof-of-Work: nonce bertambah hingga hash blok diawali prefix `"00"`.
4. **Membuktikan Deteksi Tampering (Tamper Lab)**:
   - Buka tab `[03] LABORATORIUM SIMULASI TAMPERING`.
   - Pilih blok yang baru ditambang, pilih jenis manipulasi: `Edit asset_name directly in SQLite (no re-mining)`.
   - Klik **`[ 💥 INJEKSIKAN SERANGAN TAMPERING KE SQLITE ]`**.
   - Tunjukkan banner merah menyala seketika: `🚨 PELANGGARAN INTEGRITAS TERDETEKSI: HASH_MISMATCH!`.
   - Klik tombol **`[ ♻️ RESET & PULIHKAN LEDGER ]`** untuk mengembalikan ledger ke Genesis Block.

---

## 💡 Jawaban Cerdas untuk Pertanyaan Kritis Dosen (Pak Bagus)

### Q1: *"Kenapa Anda menggabungkan Vigenère dengan AES-256? Apakah Vigenère yang klasik masih menambah keamanan?"*
> **Jawaban**:
> *"Secara teori kriptografi modern, AES-256 sendiri sudah sangat kuat. Namun, penggabungan Vigenère (Extended Modulo 256) di depan AES-256 menerapkan prinsip **Defense-in-Depth** dan **Super Encryption**. Vigenère bertindak sebagai tahap pengacakan awal (*pre-whitening / diffusion layer*) yang mengubah pola frekuensi byte teks asli sebelum masuk ke blok cipher AES. Selain itu, implementasi ini memenuhi kriteria akademis tugas akhir yang mensyaratkan perpaduan algoritma klasik dan modern secara simultan."*

### Q2: *"Apa alasan teknis memilih ChaCha20 untuk enkripsi file dan AES untuk teks?"*
> **Jawaban**:
> *"AES adalah Block Cipher yang memproses data dalam blok 16-byte tetap dan membutuhkan padding (PKCS#7). Untuk file dokumen berukuran biner besar (seperti PDF, media, atau database dump), ChaCha20 adalah Stream Cipher 256-bit rancangan Daniel J. Bernstein yang jauh lebih efisien, tidak membutuhkan padding, resisten terhadap serangan timing-cache perangkat keras, dan memproses aliran byte secara sekuensial. Pemisahan ini membuktikan penguasaan dua paradigma kriptografi simetris utama: Block Cipher dan Stream Cipher."*

### Q3: *"Bagaimana Anda mencegah token USB Dongle di-copy paste ke flashdisk lain?"*
> **Jawaban**:
> *"Sistem kami menerapkan **Windows Volume Serial Binding** via Win32 API (`GetVolumeInformationW`). Saat dongle dibuat untuk flashdisk tertentu, nomor seri fisik volume drive tersebut diikatkan secara kanonikal ke dalam payload token dan ditandatangani menggunakan **HMAC-SHA256**. Jika seseorang menyalin file `.geovault_dongle` ke flashdisk lain, nomor seri volume flashdisk baru tidak akan cocok dengan isi token, sehingga sistem langsung membatalkan tanda tangan dan menolak akses (*anti-cloning protection*)."*

### Q4: *"Di mana letak peranan AES-128-EAX pada login biometrik wajah?"*
> **Jawaban**:
> *"Template biometrik wajah tidak boleh disimpan dalam bentuk plaintext karena data biometrik bersifat permanen dan tidak dapat diganti jika bocor. Pada sistem kami, matriks wajah normalisasi 128x128 Grayscale dihitung SHA-256 pixel digest-nya, kemudian disegel menggunakan **AES-128-EAX** (Authenticated Encryption with Associated Data). Kunci enkripsinya diturunkan secara dinamis saat runtime dari passkey operator via HKDF-SHA256 (`auth/biometric-key`) dan tidak pernah disimpan dalam database. AAD (Associated Data) diikatkan pada username operator sehingga template tidak bisa dipindahkan antar akun."*

### Q5: *"Jika PoW-nya hanya prefix '00' (relatif mudah), bukankah penyerang bisa me-remine seluruh rantai jika mereka berhasil membobol database?"*
> **Jawaban**:
> *"Betul Pak, untuk keperluan demonstrasi desktop responsif, difficulty disetel ke prefix 2 karakter hex (`'00'`). Namun, kami mengantisipasi serangan re-mining penuh dengan menambahkan **HMAC Chain-Tip Anchor** yang disimpan di tabel `app_meta`. Anchor ini merupakan tanda tangan `HMAC-SHA256(K_anchor, last_index | last_hash)`. Meskipun penyerang berhasil me-remine seluruh hash dan nonce pada database SQLite, mereka tidak memiliki `K_anchor` (yang diturunkan dari master secret sistem). Akibatnya, chain tip baru akan gagal diverifikasi saat pemeriksaan integritas (`ANCHOR_MISMATCH`)."*
