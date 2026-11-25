"""
Krypt Vault - USB Drive (D:\\) Dongle Provisioning & Inspection Utility
======================================================================

Strictly targets the physical removable USB flash drive mounted at ``D:\\``.
All ``virtual_usb`` local fallback paths have been removed.
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional

import config
import database
from modules import dongle_guard


def run_cli(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify or provision the HMAC-SHA256 hardware token on USB drive D:\\."
    )
    parser.add_argument("--label", "-l", default="Krypt Vault Root Key", help="Token label.")
    parser.add_argument("--overwrite", "-f", action="store_true", help="Overwrite existing token on D:\\.")
    parser.add_argument("--verify", "-v", action="store_true", help="Verify D:\\ dongle status and exit.")
    args = parser.parse_args(argv)

    probe = config.probe_dongle_drive(deep=True)
    if not probe.mounted:
        print(f"{config.HALT_BANNER_DRIVE_MISSING}\n[HALT] {probe.reason}", file=sys.stderr)
        return 1

    if args.verify:
        status = dongle_guard.scan_for_dongle()
        print(f"[{'VALID' if status.valid else 'INVALID'}] {status.message}")
        print(f"  Drive        : {status.path} ({status.drive_type})")
        print(f"  Volume Serial: {status.volume_serial}")
        print(f"  Auth Vault   : {status.auth_dir}")
        print(f"  Operators    : {database.count_operators()}")
        return 0 if status.valid else 1

    try:
        status = dongle_guard.provision_dongle_token(label=args.label, overwrite=args.overwrite)
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    if status.valid:
        print(f"[SUCCESS] Provisioned HMAC-SHA256 token at {config.dongle_token_path()}")
        print(f"  Dongle ID    : {status.dongle_id}")
        print(f"  Volume Serial: {status.volume_serial}")
        return 0
    print(f"[FAILED] {status.message}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(run_cli())
