"""
Krypt Vault - Reset to Fresh State Utility
==========================================
Mengembalikan basis data payload lokal (dan brankas kredensial di USB D:\\
jika terpasang) ke kondisi awal pabrik (fresh 0 data).
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
    config.ensure_storage()

    if config.FILES_DIR.exists():
        for f in config.FILES_DIR.glob("*.enc"):
            try:
                f.unlink()
            except OSError:
                pass

    if config.is_dongle_drive_mounted(deep=True):
        database.init_db()
        with database.transaction() as conn:
            conn.execute("DELETE FROM secret_messages")
            conn.execute("DELETE FROM encrypted_files")
            conn.execute("DELETE FROM blockchain_ledger")
        blockchain.ensure_genesis()

        database.init_auth_db()
        database.wipe_operators()
        token = config.dongle_token_path()
        if token.exists():
            config.clear_attributes(token)
            token.unlink(missing_ok=True)
        print("[OK] Brankas D:\\ dan storage lokal berhasil di-reset ke kondisi FRESH (0 operator)!")
    else:
        print("[WARN] USB D:\\ tidak terpasang. Hanya berkas ciphertext lokal yang dibersihkan.")


if __name__ == "__main__":
    reset_to_fresh()
