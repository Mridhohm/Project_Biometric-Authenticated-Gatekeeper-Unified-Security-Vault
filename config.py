"""
Krypt Vault (GeoVault) - Central configuration & key hierarchy
==============================================================

This module is the single source of truth for filesystem paths, the strict
hardware-dongle location and the application's key hierarchy.

Strict hardware dongle (no virtual fallback)
--------------------------------------------
The vault is bound to ONE physical location: the removable USB flash drive
mounted as ``D:\\``. There is **no** ``virtual_usb`` folder, no environment
override and no Plug-and-Play fallback. :func:`probe_dongle_drive` verifies

  1. ``GetDriveTypeW("D:\\")`` reports ``DRIVE_REMOVABLE`` (USB flash drive),
  2. ``D:\\`` is not the Windows system drive,
  3. ``os.path.exists("D:\\")`` (media present and accessible),
  4. ``psutil.disk_partitions()`` lists ``D:\\`` as an active partition, and
  5. the root directory can actually be read.

Operator credential vault (on the USB drive)
--------------------------------------------
::

    D:\\.bagus_vault_auth\\
        operators.db       SQLite: username, PBKDF2 verifier + salt,
                           AES-128-EAX face template (nonce | ciphertext | tag)
        .master_secret     256-bit root of the HKDF key hierarchy (hidden)
        .geovault_dongle   HMAC-SHA256 token bound to the D:\\ volume serial (hidden)

Key hierarchy
-------------
::

                 D:\\.bagus_vault_auth\\.master_secret
                                 |
                     HKDF-SHA256 (salt = HKDF_SALT)
          +-----------------+----+-------------+-------------------+
          |                 |                  |                   |
   dongle/hmac-sha256  auth/password-pepper  ledger/aes-256-gcm  ledger/anchor-hmac
   (dongle_guard)      (auth_biometric)      (blockchain)        (blockchain)

Because the master secret only lives on the USB drive, unplugging ``D:\\``
makes every key in the hierarchy underivable: the workstation alone cannot
verify a password, decrypt a face template or unseal ledger metadata.
"""

from __future__ import annotations

import ctypes
import os
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from Crypto.Hash import SHA256
from Crypto.Protocol.KDF import HKDF

# --------------------------------------------------------------------------- #
# Local workstation paths (ciphertext-only payload storage)
# --------------------------------------------------------------------------- #
BASE_DIR: Path = Path(__file__).resolve().parent
STORAGE_DIR: Path = Path(os.environ.get("GEOVAULT_STORAGE_DIR", BASE_DIR / "storage"))
DB_PATH: Path = STORAGE_DIR / "vault.db"
LEDGER_JSON_PATH: Path = STORAGE_DIR / "ledger.json"
FILES_DIR: Path = STORAGE_DIR / "files"  # ChaCha20 encrypted document blobs
#: Pre-refactor location of the master secret. Read ONCE (one-way migration to
#: D:\) so existing ledger blocks stay decryptable; never written again.
LEGACY_MASTER_SECRET_FILE: Path = STORAGE_DIR / ".master_secret"

# --------------------------------------------------------------------------- #
# Strict hardware dongle: USB flash drive D:\
# --------------------------------------------------------------------------- #
DONGLE_DRIVE_LETTER: str = "D"
DONGLE_DRIVE_ROOT: Path = Path(f"{DONGLE_DRIVE_LETTER}:\\")

DRIVE_UNKNOWN = 0
DRIVE_NO_ROOT_DIR = 1
DRIVE_REMOVABLE = 2
DRIVE_FIXED = 3
#: Only removable USB flash drives are accepted. (Some USB SSD enclosures
#: report DRIVE_FIXED; add DRIVE_FIXED here only if your stick does that.)
DONGLE_ACCEPTED_DRIVE_TYPES: tuple[int, ...] = (DRIVE_REMOVABLE,)
DRIVE_TYPE_NAMES: dict[int, str] = {
    0: "UNKNOWN",
    1: "NOT_MOUNTED",
    2: "REMOVABLE_USB",
    3: "FIXED_DISK",
    4: "NETWORK",
    5: "CDROM",
    6: "RAMDISK",
}

AUTH_DIR_NAME: str = ".bagus_vault_auth"
AUTH_DB_FILENAME: str = "operators.db"
MASTER_SECRET_FILENAME: str = ".master_secret"
DONGLE_FILENAME: str = ".geovault_dongle"

HALT_BANNER_DRIVE_MISSING: str = "// CRITICAL_SECURITY_HALT: USB DRIVE (D:) NOT DETECTED"

# --------------------------------------------------------------------------- #
# Misc settings
# --------------------------------------------------------------------------- #
#: Blockchain Proof-of-Work difficulty (number of leading hex zeros).
POW_DIFFICULTY: int = 2

# --------------------------------------------------------------------------- #
# Key-derivation purposes (domain separation labels)
# --------------------------------------------------------------------------- #
HKDF_SALT: bytes = b"GeoVault/v1/key-hierarchy"
PURPOSE_DONGLE_HMAC = "dongle/hmac-sha256"
PURPOSE_PASSWORD_PEPPER = "auth/password-pepper"
PURPOSE_LEDGER_AES = "ledger/aes-256-gcm"
PURPOSE_LEDGER_ANCHOR = "ledger/anchor-hmac"

_FILE_ATTRIBUTE_HIDDEN = 0x02
_FILE_ATTRIBUTE_NORMAL = 0x80


class DongleDriveMissing(RuntimeError):
    """Raised when a protected operation is attempted while USB drive D:\\ is absent."""


@dataclass(frozen=True)
class DriveProbe:
    """Result of a physical presence check of the dongle drive."""

    mounted: bool
    root: str
    drive_type: int
    drive_type_name: str
    volume_serial: Optional[str]
    reason: str


# --------------------------------------------------------------------------- #
# Path helpers (functions, so the whole tree follows DONGLE_DRIVE_ROOT)
# --------------------------------------------------------------------------- #
def auth_dir() -> Path:
    """``D:\\.bagus_vault_auth``"""
    return DONGLE_DRIVE_ROOT / AUTH_DIR_NAME


def auth_db_path() -> Path:
    """``D:\\.bagus_vault_auth\\operators.db``"""
    return auth_dir() / AUTH_DB_FILENAME


def master_secret_path() -> Path:
    """``D:\\.bagus_vault_auth\\.master_secret``"""
    return auth_dir() / MASTER_SECRET_FILENAME


def dongle_token_path() -> Path:
    """``D:\\.bagus_vault_auth\\.geovault_dongle``"""
    return auth_dir() / DONGLE_FILENAME


# --------------------------------------------------------------------------- #
# Windows drive primitives
# --------------------------------------------------------------------------- #
def get_drive_type(root: str) -> int:
    """``GetDriveTypeW`` for ``root`` (e.g. ``"D:\\\\"``); 0 when unavailable."""
    if os.name != "nt":
        return DRIVE_UNKNOWN
    try:
        return int(ctypes.windll.kernel32.GetDriveTypeW(ctypes.c_wchar_p(root)))  # type: ignore[attr-defined]
    except Exception:
        return DRIVE_UNKNOWN


def get_volume_serial(path: str | os.PathLike) -> Optional[str]:
    """Volume serial number of the drive holding ``path`` (Windows only)."""
    if os.name != "nt":
        return None
    drive, _ = os.path.splitdrive(os.path.abspath(os.fspath(path)))
    if not drive or drive.startswith("\\\\"):  # UNC/network paths are not bound
        return None
    serial = ctypes.c_uint32(0)
    ok = ctypes.windll.kernel32.GetVolumeInformationW(  # type: ignore[attr-defined]
        ctypes.c_wchar_p(drive + "\\"), None, 0, ctypes.byref(serial), None, None, None, 0
    )
    return f"{serial.value:08X}" if ok else None


def set_hidden(path: Path) -> None:
    """Mark a file/directory hidden on Windows (the leading dot hides it on POSIX)."""
    if os.name == "nt":
        try:
            ctypes.windll.kernel32.SetFileAttributesW(str(path), _FILE_ATTRIBUTE_HIDDEN)  # type: ignore[attr-defined]
        except Exception:
            pass


def clear_attributes(path: Path) -> None:
    """Reset attributes so a hidden file can be overwritten or deleted on Windows."""
    if os.name == "nt":
        try:
            ctypes.windll.kernel32.SetFileAttributesW(str(path), _FILE_ATTRIBUTE_NORMAL)  # type: ignore[attr-defined]
        except Exception:
            pass


def _psutil_lists_mount(root: str) -> bool:
    """True when ``psutil.disk_partitions()`` reports ``root`` as a mounted partition."""
    try:
        import psutil

        partitions = psutil.disk_partitions(all=False)
    except Exception:
        return False
    target = os.path.normcase(root.rstrip("\\/"))
    return any(os.path.normcase((p.mountpoint or "").rstrip("\\/")) == target for p in partitions)


def probe_dongle_drive(deep: bool = True) -> DriveProbe:
    """
    Strictly verify that the USB flash drive ``D:\\`` is physically mounted.

    ``deep=False`` skips the (slower) psutil enumeration and directory listing;
    it is used on hot paths such as every key derivation, while the gatekeeper
    always performs the deep probe.
    """
    root = str(DONGLE_DRIVE_ROOT)
    if os.name != "nt":
        return DriveProbe(False, root, DRIVE_UNKNOWN, "UNSUPPORTED_OS", None,
                          "The D:\\ USB dongle lock is only supported on Windows.")

    dtype = get_drive_type(root)
    dname = DRIVE_TYPE_NAMES.get(dtype, f"TYPE_{dtype}")

    def _fail(reason: str) -> DriveProbe:
        return DriveProbe(False, root, dtype, dname, None, reason)

    if dtype in (DRIVE_UNKNOWN, DRIVE_NO_ROOT_DIR):
        return _fail("No drive is mounted at D:\\.")
    if dtype not in DONGLE_ACCEPTED_DRIVE_TYPES:
        return _fail(f"D:\\ is reported as {dname}, not a removable USB flash drive.")
    system_drive = os.environ.get("SystemDrive", "C:").rstrip("\\/").upper()
    if system_drive == root.rstrip("\\/").upper():
        return _fail("D:\\ is the Windows system drive and cannot act as a hardware dongle.")
    if not os.path.exists(root):
        return _fail("D:\\ is a USB slot without readable media (stick removed?).")
    if deep:
        if not _psutil_lists_mount(root):
            return _fail("psutil.disk_partitions() does not list D:\\ as an active partition.")
        try:
            os.listdir(root)
        except OSError as exc:
            return _fail(f"D:\\ is mounted but not readable: {exc}")

    return DriveProbe(True, root, dtype, dname, get_volume_serial(root),
                      "USB flash drive D:\\ is mounted and accessible.")


def is_dongle_drive_mounted(deep: bool = False) -> bool:
    return probe_dongle_drive(deep=deep).mounted


def require_dongle_drive() -> Path:
    """Return ``D:\\`` or raise :class:`DongleDriveMissing`. Guards every protected operation."""
    if not is_dongle_drive_mounted(deep=False):
        raise DongleDriveMissing(HALT_BANNER_DRIVE_MISSING)
    return DONGLE_DRIVE_ROOT


def ensure_storage() -> None:
    """Create the local (workstation) storage directories if they do not exist yet."""
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    FILES_DIR.mkdir(parents=True, exist_ok=True)


def ensure_auth_dir() -> Path:
    """Create the hidden ``D:\\.bagus_vault_auth`` directory on the USB drive."""
    require_dongle_drive()
    directory = auth_dir()
    if not directory.is_dir():
        directory.mkdir(parents=True, exist_ok=True)
        set_hidden(directory)
    return directory


# --------------------------------------------------------------------------- #
# Master secret (lives ONLY on D:\)
# --------------------------------------------------------------------------- #
_SECRET_CACHE: dict[tuple[str, Optional[str]], bytes] = {}


def _parse_secret(raw: str) -> bytes:
    """Accept a hex string (preferred) or fall back to raw UTF-8 bytes."""
    raw = raw.strip()
    try:
        return bytes.fromhex(raw)
    except ValueError:
        return raw.encode("utf-8")


def _provision_master_secret(path: Path) -> None:
    """
    Create ``D:\\.bagus_vault_auth\\.master_secret`` exactly once.

    If a pre-refactor ``storage/.master_secret`` exists, its value is carried
    over so ledger blocks sealed before the refactor remain decryptable.
    Otherwise a fresh 256-bit CSPRNG secret is generated.
    """
    material = secrets.token_bytes(32).hex()
    if LEGACY_MASTER_SECRET_FILE.is_file():
        try:
            legacy = LEGACY_MASTER_SECRET_FILE.read_text(encoding="utf-8").strip()
            if len(_parse_secret(legacy)) >= 16:
                material = legacy
        except OSError:
            pass
    try:
        # O_EXCL avoids a race where two sessions generate different secrets.
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(material)
    set_hidden(path)


def get_master_secret() -> bytes:
    """
    Return the master secret stored on the USB drive ``D:\\``.

    Raises :class:`DongleDriveMissing` when ``D:\\`` is not mounted. The value is
    cached per volume serial, so swapping in a different stick as ``D:\\``
    never reuses the previous stick's secret.

    .. warning::
       Losing the USB drive (or this file) makes every password verifier, face
       template and ledger ciphertext unrecoverable. Keep an offline backup.
    """
    require_dongle_drive()
    path = master_secret_path()
    cache_key = (str(path), get_volume_serial(DONGLE_DRIVE_ROOT))
    cached = _SECRET_CACHE.get(cache_key)
    if cached is not None and path.is_file():
        return cached

    ensure_auth_dir()
    if not path.is_file():
        _provision_master_secret(path)
    secret = _parse_secret(path.read_text(encoding="utf-8"))
    if len(secret) < 16:
        raise RuntimeError(f"{path} is corrupted (secret too short).")
    _SECRET_CACHE[cache_key] = secret
    return secret


def clear_secret_cache() -> None:
    _SECRET_CACHE.clear()


def derive_subkey(purpose: str, length: int = 32) -> bytes:
    """
    Derive a domain-separated sub-key from the D:\\ master secret with HKDF-SHA256.

    :param purpose: One of the ``PURPOSE_*`` labels (or a new unique label).
    :param length:  Key length in bytes (16 = AES-128, 32 = AES-256/ChaCha20).
    """
    return HKDF(
        master=get_master_secret(),
        key_len=length,
        salt=HKDF_SALT,
        hashmod=SHA256,
        context=purpose.encode("utf-8"),
    )
