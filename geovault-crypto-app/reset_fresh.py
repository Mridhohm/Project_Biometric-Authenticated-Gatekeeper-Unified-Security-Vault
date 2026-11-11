"""
Krypt Vault - Reset to Fresh State Utility
==========================================
Mengembalikan basis data, penyimpanan berkas terenkripsi,
dan token virtual ke kondisi awal pabrik (fresh 0 data).
"""

from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import config
import database
from modules import blockchain


def reset_to_fresh() -> None:
    print("[*] Mengembalikan Krypt Vault ke kondisi awal (Fresh State)...")

    # 1. Pastikan direktori storage ada
    config.ensure_storage()

    # 2. Inisialisasi struktur tabel database jika belum ada
    database.init_db()

    # 3. Bersihkan tabel database
    with database.transaction() as conn:
        conn.execute("DELETE FROM users")
        conn.execute("DELETE FROM secret_messages")
        conn.execute("DELETE FROM encrypted_files")
        conn.execute("DELETE FROM blockchain_ledger")

    # 4. Buat blok genesis awal (#0)
    blockchain.ensure_genesis()

    # 5. Bersihkan berkas terenkripsi lama di storage/files
    if config.FILES_DIR.exists():
        for f in config.FILES_DIR.glob("*.enc"):
            try:
                f.unlink()
            except OSError:
                pass

    # 6. Bersihkan virtual USB jika ada
    if config.DEFAULT_FALLBACK_DONGLE_DIR.exists():
        for f in config.DEFAULT_FALLBACK_DONGLE_DIR.glob("*"):
            if f.is_file():
                try:
                    f.unlink()
                except OSError:
                    pass

    print("[OK] Krypt Vault berhasil di-reset ke kondisi FRESH!")
    print("     - Operator terdaftar : 0 (siap registrasi baru)")
    print("     - Berkas terenkripsi : 0")
    print("     - Laporan rahasia    : 0")
    print("     - Blockchain Ledger  : 1 (Blok Genesis #0)")
    print("     - Kunci Virtual USB  : Kosong (siap demonstrasi Gate 01)")


if __name__ == "__main__":
    reset_to_fresh()
