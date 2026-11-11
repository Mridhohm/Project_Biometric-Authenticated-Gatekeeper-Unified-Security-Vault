# Krypt Vault — Biometric-Authenticated Gatekeeper & Unified Security Vault
> **Sistem Brankas Bukti Forensik Siber & Dokumen Intelijen Strategis**  
> **Tugas Akhir Mata Kuliah Kriptografi — UPN "Veteran" Yogyakarta**  
> **Dosen Pengampu: Bagus Mahardika, S.Kom., M.T.**

---

## Repositori Utama
Seluruh kode sumber aplikasi, dokumentasi laporan akhir, dan suite pengujian otomatis tersimpan di dalam folder:
[`geovault-crypto-app/`](./geovault-crypto-app/)

## Panduan Eksekusi 1-Klik
Cukup jalankan berkas peluncur:
- **Windows Launcher**: `JALANKAN_KRYPT_VAULT.bat`
- **Reset Pabrik (Fresh)**: `RESET_DATA_FRESH.bat`

Atau melalui terminal:
1. Masuk ke direktori aplikasi:
   ```bash
   cd geovault-crypto-app
   ```
2. Pasang dependensi:
   ```bash
   pip install -r requirements.txt
   ```
3. Jalankan suite pengujian otomatis (7/7 Kriteria Lulus):
   ```bash
   python tests/test_crypto_modules.py
   ```
4. Jalankan aplikasi desktop:
   ```bash
   python run_desktop.py
   ```

## Luaran Laporan Akhir (Deliverables)
- **Dokumen Word (.docx)**: [`geovault-crypto-app/docs/LAPORAN_AKHIR_KRIPTOGRAFI.docx`](./geovault-crypto-app/docs/LAPORAN_AKHIR_KRIPTOGRAFI.docx)
- **Dokumen Markdown (.md)**: [`geovault-crypto-app/docs/LAPORAN_AKHIR_KRIPTOGRAFI.md`](./geovault-crypto-app/docs/LAPORAN_AKHIR_KRIPTOGRAFI.md)
