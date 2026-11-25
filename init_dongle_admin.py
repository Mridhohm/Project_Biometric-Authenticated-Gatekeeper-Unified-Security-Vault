"""
Krypt Vault - CLI Root Operator Bootstrap on USB Drive D:\\
==========================================================

Enrolls the first root operator directly onto ``D:\\.bagus_vault_auth\\operators.db``
(and provisions ``D:\\.bagus_vault_auth\\.geovault_dongle`` + ``.master_secret``)
when ``D:\\`` is empty (0 registered operators).

Once at least one operator exists on ``D:\\``, this bootstrap utility refuses
to run; subsequent operators must be enrolled from inside an authenticated
dashboard session (``[06] MANAJEMEN OPERATOR // ENROLL_NEW_IDENTITY``).

Usage::

    python init_dongle_admin.py --username admin_root --password "RootPassword123!"
    python init_dongle_admin.py --username admin_root --password "RootPassword123!" --face path/to/face.png
"""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path
from typing import Optional

import config
import database
from modules import auth_biometric, dongle_guard


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Initialize the first Root Operator directly on USB drive D:\\ (.bagus_vault_auth)."
    )
    parser.add_argument("--username", "-u", required=True, help="Root operator username (3-32 lowercase chars).")
    parser.add_argument("--password", "-p", help="Root operator password (prompted securely if omitted).")
    parser.add_argument(
        "--face", "-f",
        help="Path to a PNG/JPG face image (if omitted, generates a deterministic optical reference frame).",
    )
    args = parser.parse_args(argv)

    probe = config.probe_dongle_drive(deep=True)
    if not probe.mounted:
        print(f"{config.HALT_BANNER_DRIVE_MISSING}\n[ERROR] {probe.reason}", file=sys.stderr)
        return 1

    if not database.is_bootstrap_required():
        print(
            "[DENIED] INITIALIZE_ROOT_OPERATOR is permanently closed: USB drive D:\\ already has "
            f"{database.count_operators()} registered operator(s).",
            file=sys.stderr,
        )
        return 1

    password = args.password or getpass.getpass("Root operator passkey: ")
    if args.face:
        face_bytes = Path(args.face).read_bytes()
    else:
        face_bytes = auth_biometric.generate_optical_face_sample(args.username.strip().lower(), seed_variant=0)

    res = auth_biometric.register_user(args.username, password, face_bytes, bootstrap=True)
    if not res.success:
        print(f"[FAILED] {res.message}", file=sys.stderr)
        return 1

    status = dongle_guard.scan_for_dongle()
    print(f"[OK] {res.message}")
    print(f"     Auth DB      : {config.auth_db_path()}")
    print(f"     Master Secret: {config.master_secret_path()}")
    print(f"     Dongle Token : {config.dongle_token_path()} (Serial: {status.volume_serial})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
