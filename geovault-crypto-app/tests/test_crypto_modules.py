"""
B.A.G.U.S. Vault - Comprehensive Cryptographic Verification Test Suite
=====================================================================
Mata Kuliah: Kriptografi (UPN "Veteran" Yogyakarta)
Dosen Pengampu: Pak Bagus

Pengujian Otomatis 7 Kriteria Tugas Akhir:
  1. [KRITERIA 1] Hardware Dongle Intercept & HMAC-SHA256 Signature
  2. [KRITERIA 2] Optical Facial Biometric (PIL 128x128) + PBKDF2-SHA256 & AES-128-EAX
  3. [KRITERIA 3] Super Enkripsi Teks (Extended Vigenere Modulo 256 + AES-256-CBC)
  4. [KRITERIA 4] Enkripsi File Biner (ChaCha20 Stream Cipher & .bagus.enc Envelope)
  5. [KRITERIA 5] Enkripsi Basis Data At-Rest (Zero-Plaintext SQLite Verification)
  6. [KRITERIA 6] Steganografi Citra PNG LSB (Least Significant Bit + <<<END>>>)
  7. [KRITERIA 7] Blockchain PoW SHA-256 ('00' Prefix) & AES-256-GCM Asset Custody
"""

from __future__ import annotations

import io
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import unittest
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=ResourceWarning)

# Setup paths
APP_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_DIR))

import config
import database
from modules import (
    auth_biometric,
    blockchain,
    dongle_guard,
    file_crypto,
    steganography,
    super_encryption,
)
from PIL import Image


class TestBAGUSVaultCryptography(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create an isolated temporary test storage directory
        cls.test_dir = tempfile.mkdtemp(prefix="bagus_vault_test_")
        cls.orig_storage_dir = config.STORAGE_DIR
        cls.orig_db_path = config.DB_PATH
        cls.orig_ledger_json = config.LEDGER_JSON_PATH
        cls.orig_files_dir = config.FILES_DIR

        config.STORAGE_DIR = Path(cls.test_dir)
        config.DB_PATH = config.STORAGE_DIR / "vault.db"
        config.LEDGER_JSON_PATH = config.STORAGE_DIR / "ledger.json"
        config.FILES_DIR = config.STORAGE_DIR / "files"
        config.ensure_storage()

        database.init_db()

    @classmethod
    def tearDownClass(cls):
        # Restore paths and clean up temporary directory
        config.STORAGE_DIR = cls.orig_storage_dir
        config.DB_PATH = cls.orig_db_path
        config.LEDGER_JSON_PATH = cls.orig_ledger_json
        config.FILES_DIR = cls.orig_files_dir
        try:
            shutil.rmtree(cls.test_dir, ignore_errors=True)
        except Exception:
            pass

    # ----------------------------------------------------------------------- #
    # 1. KRITERIA 1: Hardware Dongle Intercept & HMAC-SHA256 Token
    # ----------------------------------------------------------------------- #
    def test_01_dongle_hmac_and_guard(self):
        """Uji validasi tanda tangan HMAC-SHA256 dan proteksi gatekeeper dongle."""
        # 1. Pastikan virtual dongle dapat di-mount
        mount_res = dongle_guard.mount_virtual_dongle(label="Operator Forensic Key #01")
        self.assertTrue(dongle_guard.is_virtual_dongle_mounted())
        self.assertTrue(Path(mount_res.path).exists())

        # 2. Pindai keberadaan dongle (harus valid)
        status = dongle_guard.scan_for_dongle()
        self.assertTrue(status.valid)
        self.assertIn("HMAC-SHA256 OK", status.message)
        self.assertEqual(status.label, "Operator Forensic Key #01")

        # 3. Uji deteksi pemalsuan token (Tampered Token Payload)
        dongle_file = Path(mount_res.path) / config.DONGLE_FILENAME
        with open(dongle_file, "r", encoding="utf-8") as f:
            token_data = json.load(f)

        # Ubah isi token tanpa memperbarui tanda tangan HMAC
        token_data["label"] = "FORGED_MALICIOUS_KEY"
        if os.name == "nt":
            import ctypes
            try:
                ctypes.windll.kernel32.SetFileAttributesW(str(dongle_file), 0x80)  # FILE_ATTRIBUTE_NORMAL
            except Exception:
                pass
        with open(dongle_file, "w", encoding="utf-8") as f:
            json.dump(token_data, f)

        # Pindai ulang: Harus DITOLAK karena HMAC tidak cocok!
        forged_status = dongle_guard.scan_for_dongle()
        self.assertFalse(forged_status.valid)
        self.assertTrue(
            "forged" in forged_status.message.lower()
            or "mismatch" in forged_status.message.lower()
            or "failed" in forged_status.message.lower()
        )

        # 4. Unmount virtual dongle (Simulasikan pencabutan USB)
        dongle_guard.unmount_virtual_dongle()
        self.assertFalse(dongle_guard.is_virtual_dongle_mounted())

        unmounted_status = dongle_guard.scan_for_dongle()
        self.assertFalse(unmounted_status.valid)

    # ----------------------------------------------------------------------- #
    # 2. KRITERIA 2: Biometric Authentication & Cryptographic Handshake
    # ----------------------------------------------------------------------- #
    def test_02_biometric_face_and_pbkdf2_login(self):
        """Uji pendaftaran & login: PBKDF2-SHA256 (600k iterasi) + PIL 128x128 + AES-128-EAX."""
        username = "analyst_test_01"
        passkey = "CyberVault#2026!"

        # Buat citra wajah sintetis operator uji
        face_sample = auth_biometric.generate_optical_face_sample(username, seed_variant=0)

        # Pendaftaran akun
        reg_res = auth_biometric.register_user(username, passkey, face_sample)
        self.assertTrue(reg_res.success)
        self.assertIn("sealed with AES-128-EAX", reg_res.message)

        # Autentikasi dengan wajah asli dan passkey benar (Harus Berhasil, similarity = 100%)
        auth_ok = auth_biometric.authenticate_user(username, passkey, face_sample)
        self.assertTrue(auth_ok.success)
        self.assertIsNotNone(auth_ok.similarity)
        self.assertGreaterEqual(auth_ok.similarity, auth_biometric.MATCH_THRESHOLD)

        # Autentikasi dengan wajah asli yang bergeser posisi (Simulasi gerak wajar kepala 10px)
        with Image.open(io.BytesIO(face_sample)) as img:
            shifted = Image.new("L", (128, 128), color=30)
            shifted.paste(img, (8, 6))
            buf = io.BytesIO()
            shifted.save(buf, format="PNG")
            shifted_sample = buf.getvalue()
        auth_shifted = auth_biometric.authenticate_user(username, passkey, shifted_sample)
        self.assertTrue(auth_shifted.success, f"Shifted face failed: {auth_shifted.message}")
        self.assertGreaterEqual(auth_shifted.similarity, auth_biometric.MATCH_THRESHOLD)

        # Autentikasi dengan wajah penyusup / tidak cocok (Harus Ditolak, similarity < MATCH_THRESHOLD)
        intruder_face = auth_biometric.generate_optical_face_sample(username, seed_variant=888)
        auth_intruder = auth_biometric.authenticate_user(username, passkey, intruder_face)
        self.assertFalse(auth_intruder.success)
        self.assertLess(auth_intruder.similarity, auth_biometric.MATCH_THRESHOLD)

        # Autentikasi dengan passkey salah (Harus Ditolak)
        auth_wrong_pw = auth_biometric.authenticate_user(username, "WrongPassword#999", face_sample)
        self.assertFalse(auth_wrong_pw.success)

    # ----------------------------------------------------------------------- #
    # 3. KRITERIA 3: Super Enkripsi Teks (Vigenère + AES-256-CBC)
    # ----------------------------------------------------------------------- #
    def test_03_super_encryption_cascade(self):
        """Uji super enkripsi dua lapis: Extended Vigenère (klasik) + AES-256-CBC (modern)."""
        plaintext = "RAHASIA NEGARA: Koordinat Safehouse -7.7828, 110.3670. Kode: KASUARI-09."
        vig_key = "KUNCI_VIGENERE_SUPER_RAHASIA"
        aes_pass = "AES-Passphrase-256-Bit-Military!"

        # Enkripsi super
        res = super_encryption.super_encrypt_detailed(plaintext, vig_key, aes_pass)
        token = res["token"]

        self.assertIn("vigenere_b64", res)
        self.assertIn("salt_hex", res)
        self.assertIn("iv_hex", res)
        self.assertIn("aes_ciphertext_hex", res)

        # Dekripsi dengan kunci yang benar
        dec_res = super_encryption.super_decrypt_detailed(token, vig_key, aes_pass)
        self.assertEqual(dec_res["plaintext"], plaintext)

        # Dekripsi dengan Kunci Vigenère salah (harus gagal memulihkan plaintext)
        dec_wrong_vig = super_encryption.super_decrypt_detailed(token, "WRONG_KEY", aes_pass)
        self.assertNotEqual(dec_wrong_vig["plaintext"], plaintext)

        # Dekripsi dengan Passphrase AES salah (harus melempar exception padding/MAC error)
        with self.assertRaises(Exception):
            super_encryption.super_decrypt_detailed(token, vig_key, "WrongAesPassphrase!")

    # ----------------------------------------------------------------------- #
    # 4. KRITERIA 4: Enkripsi File Biner (ChaCha20 Stream Cipher)
    # ----------------------------------------------------------------------- #
    def test_04_chacha20_file_encryption(self):
        """Uji enkripsi file dokumen biner menggunakan ChaCha20 Stream Cipher dan amplop .bagus.enc."""
        file_content = b"%PDF-1.7 BUKTI FORENSIK DIGITAL CYBER-CRIME CORPO-LEAK DATASET 0xDEADBEEF"
        passphrase = "ChaCha20-HighSpeed-StreamKey!"
        orig_filename = "bukti_kasus_01.pdf"
        mime_type = "application/pdf"

        # Enkripsi byte stream file
        bundle = file_crypto.encrypt_file_bytes(file_content, passphrase)
        self.assertEqual(bundle.algorithm, "ChaCha20-Stream")
        self.assertNotEqual(bundle.ciphertext, file_content)

        # Kemas dalam amplop mandiri .bagus.enc
        package_bytes = file_crypto.pack_bagus_envelope(bundle, orig_filename, mime_type)
        self.assertTrue(package_bytes.startswith(file_crypto.MAGIC_HEADER))

        # Dekripsi paket .bagus.enc mandiri
        recovered_bytes, meta = file_crypto.unpack_bagus_envelope(package_bytes, passphrase)
        self.assertEqual(recovered_bytes, file_content)
        self.assertEqual(meta["original_name"], orig_filename)
        self.assertEqual(meta["sha256_plain"], bundle.sha256_plain)

        # Dekripsi dengan passphrase salah (harus gagal verifikasi integritas SHA-256)
        with self.assertRaises(Exception):
            file_crypto.unpack_bagus_envelope(package_bytes, "WrongPassphrase123!")

    # ----------------------------------------------------------------------- #
    # 5. KRITERIA 5: Enkripsi Basis Data At-Rest (Zero-Plaintext)
    # ----------------------------------------------------------------------- #
    def test_05_database_at_rest_encryption(self):
        """Audit basis data: Buktikan bahwa SQLite hanya menyimpan ciphertext/hash/BLOB saat at-rest."""
        # Simpan pesan super enkripsi
        enc_intel = super_encryption.super_encrypt_detailed(
            "Target berada di pelabuhan sektor 4.", "VIGKEY", "AESPWRule!"
        )
        database.insert_secret_message(
            owner="analyst_test_01",
            title="INFILTRASI_PELABUHAN",
            ciphertext=enc_intel["token"],
            algorithm=super_encryption.ALGORITHM_ID,
        )

        # Hubungkan langsung ke file SQLite vault.db secara independen (Direct SQLite Audit)
        conn = sqlite3.connect(str(config.DB_PATH))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Audit tabel users: Tidak ada password mentah
        user_row = cur.execute("SELECT * FROM users WHERE username = ?", ("analyst_test_01",)).fetchone()
        self.assertIsNotNone(user_row)
        self.assertNotIn("CyberVault#2026!", user_row["password_hash"])
        self.assertIsInstance(user_row["bio_template"], bytes)  # BLOB AES-128-EAX

        # Audit tabel secret_messages: Tidak ada plaintext pesan
        msg_row = cur.execute("SELECT * FROM secret_messages WHERE title = ?", ("INFILTRASI_PELABUHAN",)).fetchone()
        self.assertIsNotNone(msg_row)
        self.assertNotIn("pelabuhan sektor 4", msg_row["ciphertext"])
        # Pastikan tersimpan dalam token Base64 yang memuat ciphertext hex
        import base64
        decoded_raw = base64.b64decode(msg_row["ciphertext"].encode("ascii"))
        token_json = json.loads(decoded_raw)
        self.assertIn("ct", token_json)
        self.assertNotIn("pelabuhan sektor 4", str(token_json))

        conn.close()

    # ----------------------------------------------------------------------- #
    # 6. KRITERIA 6: Steganografi Citra PNG LSB (Least Significant Bit)
    # ----------------------------------------------------------------------- #
    def test_06_steganography_lsb(self):
        """Uji penyisipan pesan ke dalam LSB channel RGB citra PNG lossless dengan pembatas <<<END>>>."""
        # Buat citra cover sintetis PNG 120x120 piksel RGB
        cover_img = Image.new("RGB", (120, 120), color=(45, 80, 120))
        cover_buf = io.BytesIO()
        cover_img.save(cover_buf, format="PNG")
        cover_bytes = cover_buf.getvalue()

        secret_text = "DROP POINT: Gudang A-12. Waktu pertemuan 02:00 UTC."

        # 1. Uji penyisipan mode Plaintext RAW
        stego_png = steganography.embed_message_lsb(cover_bytes, secret_text)
        self.assertNotEqual(stego_png, cover_bytes)

        recovered_text = steganography.extract_message_lsb(stego_png)
        self.assertEqual(recovered_text, secret_text)

        # 2. Uji penyisipan mode Enkripsi dengan Passphrase
        stego_pass = "StegoPass#2026!"
        stego_enc_png = steganography.embed_message_lsb(cover_bytes, secret_text, passphrase=stego_pass)

        # Ekstraksi dengan passphrase yang benar
        rec_enc_text = steganography.extract_message_lsb(stego_enc_png, passphrase=stego_pass)
        self.assertEqual(rec_enc_text, secret_text)

        # Ekstraksi dengan passphrase salah (harus gagal)
        with self.assertRaises(ValueError):
            steganography.extract_message_lsb(stego_enc_png, passphrase="WrongStegoPass!")

    # ----------------------------------------------------------------------- #
    # 7. KRITERIA 7: Blockchain Sederhana Proof-of-Work ('00') & Integritas Aset
    # ----------------------------------------------------------------------- #
    def test_07_blockchain_pow_and_integrity(self):
        """Uji blockchain PoW SHA-256 ('00'), segel AES-256-GCM, auto-sync ledger.json, & tamper detection."""
        # Pastikan Genesis Block #0 ada
        blockchain.ensure_genesis()

        # Tambang aset penting baru
        asset_meta = {"classification": "TOP SECRET", "coordinate": "-6.1754, 106.8272", "agent": "007"}
        mined_res = blockchain.add_asset(
            asset_name="DOKUMEN_SANGKURIANG_ALPHA",
            asset_type="High-Value Record",
            metadata=asset_meta,
            owner="analyst_test_01",
        )

        block = mined_res.block
        self.assertTrue(block.current_hash.startswith("00"), "Hash blok harus memenuhi PoW prefix '00'")
        self.assertGreater(block.nonce, 0)

        # Verifikasi seluruh rantai ledger
        report = blockchain.verify_chain()
        self.assertTrue(report.valid)
        self.assertEqual(len(report.issues), 0)

        # Pastikan berkas storage/ledger.json otomatis tersinkronisasi
        self.assertTrue(config.LEDGER_JSON_PATH.exists())
        with open(config.LEDGER_JSON_PATH, "r", encoding="utf-8") as f:
            ledger_data = json.load(f)
        self.assertGreaterEqual(len(ledger_data), 2)  # Genesis + Blok #1

        # Uji Dekripsi metadata berotentikasi AES-256-GCM
        decrypted_meta = blockchain.decrypt_metadata(block)
        self.assertEqual(decrypted_meta["data"]["classification"], "TOP SECRET")

        # Uji Tamper Lab: Simulasikan manipulasi nama aset langsung di database
        blockchain.simulate_tampering(block.index, "edit_data")

        # Verifikasi ulang rantai: Harus mendeteksi TAMPER!
        tamper_report = blockchain.verify_chain()
        self.assertFalse(tamper_report.valid)
        self.assertGreater(len(tamper_report.issues), 0)
        self.assertEqual(tamper_report.issues[0].kind, "HASH_MISMATCH")


if __name__ == "__main__":
    unittest.main(verbosity=2)
