"""
Krypt Vault (GeoVault) - SQLite persistence layer
=================================================

Two physically separated databases
----------------------------------
1. **Operator credential vault - on the USB flash drive** ``D:\\``::

       D:\\.bagus_vault_auth\\operators.db
           users      username, PBKDF2-HMAC-SHA256 verifier + salt,
                      AES-128-EAX face template (bio_nonce | bio_ciphertext | bio_tag)
           auth_meta  key/value (bootstrap timestamp, ...)

   Nothing that identifies or authenticates an operator is stored on the
   workstation. Pull the stick and there is nothing local to attack.

2. **Payload vault - on the workstation** ``storage/vault.db``::

       secret_messages    Vigenere + AES-256-CBC super-encrypted tokens
       encrypted_files    ChaCha20 file metadata (ciphertext lives on disk)
       blockchain_ledger  PoW blocks with AES-GCM encrypted asset metadata
       app_meta           Key/value store (e.g. the HMAC-signed ledger tip anchor)

Design rules
------------
* **No plaintext secrets are ever written.** Every helper receives data that
  has already been hashed or encrypted by a crypto module and stores it verbatim.
* **No database operation runs without ``D:\\``.** Both connection factories call
  :func:`config.require_dongle_drive` and raise :class:`config.DongleDriveMissing`
  when the USB drive is absent.
* All SQL is parameterised; each call opens a short-lived connection, which is
  the safest pattern for Streamlit's multi-threaded script runner.
"""

from __future__ import annotations

import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Callable, Iterator, Optional

import config


class BootstrapClosedError(PermissionError):
    """INITIALIZE_ROOT_OPERATOR was attempted although D:\\ already has an operator."""


class EnrollmentDenied(PermissionError):
    """An enrollment was attempted without a valid, enrolled operator as sponsor."""


# =========================================================================== #
# Schemas
# =========================================================================== #
AUTH_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    username         TEXT    NOT NULL UNIQUE,      -- always lower-case
    password_hash    TEXT    NOT NULL,             -- hex verifier: PBKDF2-HMAC-SHA256 -> HKDF
    salt             TEXT    NOT NULL,             -- hex, 16 random bytes
    kdf_iterations   INTEGER NOT NULL,
    bio_nonce        BLOB    NOT NULL,             -- AES-128-EAX nonce (16 bytes)
    bio_ciphertext   BLOB    NOT NULL,             -- AES-128-EAX ciphertext of the 128x128 face vector
    bio_tag          BLOB    NOT NULL,             -- AES-128-EAX authentication tag (16 bytes)
    bio_algorithm    TEXT    NOT NULL,
    role             TEXT    NOT NULL DEFAULT 'operator' CHECK (role IN ('root', 'operator')),
    enrolled_by      TEXT,                         -- NULL only for the bootstrap root operator
    failed_attempts  INTEGER NOT NULL DEFAULT 0,
    locked_until     REAL    NOT NULL DEFAULT 0,   -- unix epoch seconds
    created_at       TEXT    NOT NULL,
    last_login       TEXT
);

CREATE TABLE IF NOT EXISTS auth_meta (
    key    TEXT PRIMARY KEY,
    value  TEXT NOT NULL
);
"""

# Payload tables intentionally carry no FOREIGN KEY to ``users``: operators
# live in a different database file on a different (removable) volume.
_SECRET_MESSAGES_DDL = """
CREATE TABLE IF NOT EXISTS {name} (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    owner       TEXT NOT NULL,                     -- operator username on D:\\
    title       TEXT NOT NULL,
    ciphertext  TEXT NOT NULL,                     -- super-encrypted token (Vigenere + AES-256-CBC)
    algorithm   TEXT NOT NULL,
    created_at  TEXT NOT NULL
)"""

_ENCRYPTED_FILES_DDL = """
CREATE TABLE IF NOT EXISTS {name} (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    owner          TEXT    NOT NULL,               -- operator username on D:\\
    original_name  TEXT    NOT NULL,
    stored_name    TEXT    NOT NULL UNIQUE,        -- random file name inside storage/files
    mime_type      TEXT,
    size_bytes     INTEGER NOT NULL,
    sha256_plain   TEXT    NOT NULL,               -- integrity check after decryption
    kdf_salt       TEXT    NOT NULL,               -- hex
    nonce          TEXT    NOT NULL,               -- hex
    algorithm      TEXT    NOT NULL,
    created_at     TEXT    NOT NULL
)"""

_SECRET_MESSAGES_COLS = "id, owner, title, ciphertext, algorithm, created_at"
_ENCRYPTED_FILES_COLS = ("id, owner, original_name, stored_name, mime_type, size_bytes, "
                         "sha256_plain, kdf_salt, nonce, algorithm, created_at")

VAULT_SCHEMA = (
    _SECRET_MESSAGES_DDL.format(name="secret_messages") + ";\n"
    + _ENCRYPTED_FILES_DDL.format(name="encrypted_files") + ";\n"
    + """
CREATE TABLE IF NOT EXISTS blockchain_ledger (
    block_index               INTEGER PRIMARY KEY,
    timestamp                 TEXT    NOT NULL,
    asset_name                TEXT    NOT NULL,
    encrypted_asset_metadata  TEXT    NOT NULL,    -- base64(AES-256-GCM nonce|tag|ciphertext)
    previous_hash             TEXT    NOT NULL,
    nonce                     INTEGER NOT NULL,
    current_hash              TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS app_meta (
    key    TEXT PRIMARY KEY,
    value  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_secret_messages_owner ON secret_messages(owner);
CREATE INDEX IF NOT EXISTS idx_encrypted_files_owner ON encrypted_files(owner);
"""
)


# =========================================================================== #
# Shared helpers
# =========================================================================== #
def utc_now_iso() -> str:
    """ISO-8601 UTC timestamp with second precision."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@contextmanager
def _transaction_on(connect: Callable[[], sqlite3.Connection], immediate: bool = True) -> Iterator[sqlite3.Connection]:
    """``BEGIN IMMEDIATE`` grabs the write lock up-front, serialising concurrent writers."""
    conn = connect()
    try:
        conn.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
        yield conn
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()


def _fetchone_on(connect: Callable[[], sqlite3.Connection], sql: str, params: tuple = ()) -> Optional[dict]:
    conn = connect()
    try:
        row = conn.execute(sql, params).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def _fetchall_on(connect: Callable[[], sqlite3.Connection], sql: str, params: tuple = ()) -> list[dict]:
    conn = connect()
    try:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


def _execute_on(connect: Callable[[], sqlite3.Connection], sql: str, params: tuple = ()) -> int:
    """Run a single write statement; returns ``lastrowid`` (or rowcount for UPDATE/DELETE)."""
    with _transaction_on(connect) as conn:
        cur = conn.execute(sql, params)
        return cur.lastrowid if sql.lstrip().upper().startswith("INSERT") else cur.rowcount


# =========================================================================== #
# 1) Operator credential vault on USB drive D:\
# =========================================================================== #
_AUTH_READY: set[tuple[str, Optional[str]]] = set()


def get_auth_connection() -> sqlite3.Connection:
    """
    Open ``D:\\.bagus_vault_auth\\operators.db``.

    Raises :class:`config.DongleDriveMissing` if the USB drive is not mounted.
    The schema is created lazily, once per physical stick (volume serial).
    """
    config.ensure_auth_dir()
    path = config.auth_db_path()
    conn = sqlite3.connect(path, timeout=15, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA synchronous = FULL")  # removable media: flush every commit
    ready_key = (str(path), config.get_volume_serial(config.DONGLE_DRIVE_ROOT))
    if ready_key not in _AUTH_READY:
        conn.executescript(AUTH_SCHEMA)
        _AUTH_READY.add(ready_key)
    return conn


def auth_transaction(immediate: bool = True):
    return _transaction_on(get_auth_connection, immediate)


def init_auth_db() -> None:
    """Create the operator tables on ``D:\\`` (idempotent)."""
    conn = get_auth_connection()
    try:
        conn.executescript(AUTH_SCHEMA)
    finally:
        conn.close()


def count_operators() -> int:
    row = _fetchone_on(get_auth_connection, "SELECT COUNT(*) AS c FROM users")
    return int(row["c"]) if row else 0


def is_bootstrap_required() -> bool:
    """True while ``D:\\`` holds zero operators (INITIALIZE_ROOT_OPERATOR is allowed)."""
    return count_operators() == 0


def get_operator(username: str) -> Optional[dict]:
    return _fetchone_on(get_auth_connection, "SELECT * FROM users WHERE username = ?", (username,))


def operator_exists(username: str) -> bool:
    return _fetchone_on(get_auth_connection, "SELECT 1 AS x FROM users WHERE username = ?", (username,)) is not None


def create_operator(
    username: str,
    password_hash: str,
    salt: str,
    kdf_iterations: int,
    bio_nonce: bytes,
    bio_ciphertext: bytes,
    bio_tag: bytes,
    bio_algorithm: str,
    *,
    bootstrap: bool = False,
    enrolled_by: Optional[str] = None,
) -> int:
    """
    Insert a new operator on ``D:\\`` atomically.

    * ``bootstrap=True``  - allowed only while the vault is empty; creates the ``root`` operator.
    * otherwise           - ``enrolled_by`` must name an operator that already exists on ``D:\\``.

    Both checks run inside the same ``BEGIN IMMEDIATE`` transaction as the
    INSERT, so two concurrent sessions can never both "bootstrap" the stick.
    Raises :class:`BootstrapClosedError`, :class:`EnrollmentDenied` or
    ``sqlite3.IntegrityError`` (duplicate username).
    """
    if bootstrap == bool(enrolled_by):
        raise EnrollmentDenied("Specify exactly one of bootstrap=True or enrolled_by=<operator>.")

    with auth_transaction() as conn:
        count = int(conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"])
        if bootstrap:
            if count > 0:
                raise BootstrapClosedError("D:\\ already has an operator - initial setup is permanently closed.")
            role, sponsor = "root", None
        else:
            sponsor_row = conn.execute("SELECT 1 FROM users WHERE username = ?", (enrolled_by,)).fetchone()
            if sponsor_row is None:
                raise EnrollmentDenied("Enrolling operator is not registered on D:\\.")
            role, sponsor = "operator", enrolled_by

        cur = conn.execute(
            """INSERT INTO users (username, password_hash, salt, kdf_iterations,
                                  bio_nonce, bio_ciphertext, bio_tag, bio_algorithm,
                                  role, enrolled_by, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (username, password_hash, salt, kdf_iterations,
             sqlite3.Binary(bio_nonce), sqlite3.Binary(bio_ciphertext), sqlite3.Binary(bio_tag),
             bio_algorithm, role, sponsor, utc_now_iso()),
        )
        if bootstrap:
            conn.execute(
                "INSERT INTO auth_meta (key, value) VALUES ('bootstrapped_at', ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (utc_now_iso(),),
            )
        return int(cur.lastrowid)


def list_operators() -> list[dict]:
    """Public operator roster (no verifier, salt or biometric material)."""
    return _fetchall_on(
        get_auth_connection,
        "SELECT username, role, enrolled_by, created_at, last_login FROM users ORDER BY id ASC",
    )


def record_login_failure(username: str, max_attempts: int, lockout_seconds: int) -> int:
    """Increment the failure counter on D:\\; lock the account when the limit is hit."""
    with auth_transaction() as conn:
        row = conn.execute("SELECT failed_attempts FROM users WHERE username = ?", (username,)).fetchone()
        if row is None:
            return 0
        attempts = row["failed_attempts"] + 1
        locked_until = 0.0
        if attempts >= max_attempts:
            locked_until = time.time() + lockout_seconds
            attempts = 0  # reset counter after applying the lock
        conn.execute(
            "UPDATE users SET failed_attempts = ?, locked_until = ? WHERE username = ?",
            (attempts, locked_until, username),
        )
        return attempts


def record_login_success(username: str) -> None:
    _execute_on(
        get_auth_connection,
        "UPDATE users SET failed_attempts = 0, locked_until = 0, last_login = ? WHERE username = ?",
        (utc_now_iso(), username),
    )


def wipe_operators() -> int:
    """Delete every operator on D:\\ (factory reset; re-opens INITIALIZE_ROOT_OPERATOR)."""
    with auth_transaction() as conn:
        n = conn.execute("DELETE FROM users").rowcount
        conn.execute("DELETE FROM auth_meta")
        return n


# Backwards-compatible names used by older call sites.
count_users = count_operators
get_user = get_operator
user_exists = operator_exists


# =========================================================================== #
# 2) Payload vault on the workstation (storage/vault.db)
# =========================================================================== #
def get_connection() -> sqlite3.Connection:
    """
    Open ``storage/vault.db`` in autocommit mode (``isolation_level=None``).
    Refuses to open while ``D:\\`` is absent (no database operations without the dongle).
    """
    config.require_dongle_drive()
    config.ensure_storage()
    conn = sqlite3.connect(config.DB_PATH, timeout=15, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def transaction(immediate: bool = True):
    return _transaction_on(get_connection, immediate)


def _fetchone(sql: str, params: tuple = ()) -> Optional[dict]:
    return _fetchone_on(get_connection, sql, params)


def _fetchall(sql: str, params: tuple = ()) -> list[dict]:
    return _fetchall_on(get_connection, sql, params)


def _execute(sql: str, params: tuple = ()) -> int:
    return _execute_on(get_connection, sql, params)


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)).fetchone() is not None


def _references_users(conn: sqlite3.Connection, table: str) -> bool:
    return any(row["table"] == "users" for row in conn.execute(f"PRAGMA foreign_key_list({table})").fetchall())


def _migrate_legacy_vault(conn: sqlite3.Connection) -> None:
    """
    One-time migration from the pre-refactor layout:

    * rebuild ``secret_messages`` / ``encrypted_files`` without the
      ``REFERENCES users(username)`` foreign key (operators now live on D:\\), and
    * drop the legacy local ``users`` table so no password verifier or face
      template remains on the workstation.
    """
    needs_rebuild = [
        (table, ddl, cols)
        for table, ddl, cols in (
            ("secret_messages", _SECRET_MESSAGES_DDL, _SECRET_MESSAGES_COLS),
            ("encrypted_files", _ENCRYPTED_FILES_DDL, _ENCRYPTED_FILES_COLS),
        )
        if _table_exists(conn, table) and _references_users(conn, table)
    ]
    has_legacy_users = _table_exists(conn, "users")
    if not needs_rebuild and not has_legacy_users:
        return

    conn.execute("PRAGMA foreign_keys = OFF")
    try:
        conn.execute("BEGIN IMMEDIATE")
        try:
            for table, ddl, cols in needs_rebuild:
                tmp = f"{table}__rebuild"
                conn.execute(f"DROP TABLE IF EXISTS {tmp}")
                conn.execute(ddl.format(name=tmp))
                conn.execute(f"INSERT INTO {tmp} ({cols}) SELECT {cols} FROM {table}")
                conn.execute(f"DROP TABLE {table}")
                conn.execute(f"ALTER TABLE {tmp} RENAME TO {table}")
            if has_legacy_users:
                conn.execute("DROP TABLE users")
            conn.execute("COMMIT")
        except BaseException:
            conn.execute("ROLLBACK")
            raise
    finally:
        conn.execute("PRAGMA foreign_keys = ON")


def init_db() -> None:
    """Create/migrate the local payload tables (idempotent). Requires D:\\."""
    conn = get_connection()
    try:
        _migrate_legacy_vault(conn)
        conn.executescript(VAULT_SCHEMA)
    finally:
        conn.close()


# --------------------------------------------------------------------------- #
# secret_messages  (ciphertext produced by modules.super_encryption)
# --------------------------------------------------------------------------- #
def insert_secret_message(owner: str, title: str, ciphertext: str, algorithm: str) -> int:
    return _execute(
        "INSERT INTO secret_messages (owner, title, ciphertext, algorithm, created_at) VALUES (?, ?, ?, ?, ?)",
        (owner, title, ciphertext, algorithm, utc_now_iso()),
    )


def list_secret_messages(owner: str) -> list[dict]:
    return _fetchall("SELECT * FROM secret_messages WHERE owner = ? ORDER BY id DESC", (owner,))


def get_secret_message(message_id: int, owner: str) -> Optional[dict]:
    return _fetchone("SELECT * FROM secret_messages WHERE id = ? AND owner = ?", (message_id, owner))


def delete_secret_message(message_id: int, owner: str) -> bool:
    return _execute("DELETE FROM secret_messages WHERE id = ? AND owner = ?", (message_id, owner)) > 0


# --------------------------------------------------------------------------- #
# encrypted_files  (ciphertext produced by modules.file_crypto)
# --------------------------------------------------------------------------- #
def insert_encrypted_file(
    owner: str,
    original_name: str,
    stored_name: str,
    mime_type: Optional[str],
    size_bytes: int,
    sha256_plain: str,
    kdf_salt: str,
    nonce: str,
    algorithm: str,
) -> int:
    return _execute(
        """INSERT INTO encrypted_files (owner, original_name, stored_name, mime_type, size_bytes,
                                        sha256_plain, kdf_salt, nonce, algorithm, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (owner, original_name, stored_name, mime_type, size_bytes,
         sha256_plain, kdf_salt, nonce, algorithm, utc_now_iso()),
    )


def list_encrypted_files(owner: str) -> list[dict]:
    return _fetchall("SELECT * FROM encrypted_files WHERE owner = ? ORDER BY id DESC", (owner,))


def get_encrypted_file(file_id: int, owner: str) -> Optional[dict]:
    return _fetchone("SELECT * FROM encrypted_files WHERE id = ? AND owner = ?", (file_id, owner))


def delete_encrypted_file(file_id: int, owner: str) -> bool:
    return _execute("DELETE FROM encrypted_files WHERE id = ? AND owner = ?", (file_id, owner)) > 0


# --------------------------------------------------------------------------- #
# blockchain_ledger
# --------------------------------------------------------------------------- #
_BLOCK_COLUMNS = ("block_index", "timestamp", "asset_name", "encrypted_asset_metadata",
                  "previous_hash", "nonce", "current_hash")


def _row_to_block(row: Optional[sqlite3.Row | dict]) -> Optional[dict]:
    """Map the DB column ``block_index`` to the public field name ``index``."""
    if row is None:
        return None
    data = dict(row)
    data["index"] = data.pop("block_index")
    return data


def get_all_blocks() -> list[dict]:
    return [_row_to_block(r) for r in _fetchall("SELECT * FROM blockchain_ledger ORDER BY block_index ASC")]


def get_last_block() -> Optional[dict]:
    return _row_to_block(_fetchone("SELECT * FROM blockchain_ledger ORDER BY block_index DESC LIMIT 1"))


def count_blocks() -> int:
    row = _fetchone("SELECT COUNT(*) AS n FROM blockchain_ledger")
    return int(row["n"]) if row else 0


def append_block_atomic(
    builder: Callable[[Optional[dict]], Optional[tuple[dict, dict[str, str]]]],
) -> Optional[dict]:
    """
    Append a block inside a single ``BEGIN IMMEDIATE`` transaction.

    ``builder(last_block)`` receives the current chain tip (or ``None``) and
    must return ``(block_dict, meta_updates)`` - or ``None`` to abort without
    writing. Holding the write lock while building guarantees that two
    sessions can never mine on top of the same parent block.
    """
    with transaction() as conn:
        last = _row_to_block(
            conn.execute("SELECT * FROM blockchain_ledger ORDER BY block_index DESC LIMIT 1").fetchone()
        )
        built = builder(last)
        if built is None:
            return None
        block, meta_updates = built
        conn.execute(
            f"INSERT INTO blockchain_ledger ({', '.join(_BLOCK_COLUMNS)}) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (block["index"], block["timestamp"], block["asset_name"], block["encrypted_asset_metadata"],
             block["previous_hash"], block["nonce"], block["current_hash"]),
        )
        for key, value in meta_updates.items():
            conn.execute(
                "INSERT INTO app_meta (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )
        return block


def overwrite_block(block: dict) -> None:
    """
    Raw UPDATE of a block row **bypassing all validation**.
    Used only by the blockchain *Tamper Lab* demo to simulate an attacker.
    """
    _execute(
        """UPDATE blockchain_ledger
           SET timestamp = ?, asset_name = ?, encrypted_asset_metadata = ?,
               previous_hash = ?, nonce = ?, current_hash = ?
           WHERE block_index = ?""",
        (block["timestamp"], block["asset_name"], block["encrypted_asset_metadata"],
         block["previous_hash"], block["nonce"], block["current_hash"], block["index"]),
    )


def delete_block(index: int) -> bool:
    """Raw DELETE of a block (Tamper Lab demo only)."""
    return _execute("DELETE FROM blockchain_ledger WHERE block_index = ?", (index,)) > 0


def clear_ledger(meta_keys: tuple[str, ...] = ()) -> None:
    """Delete every block and the given meta keys (ledger reset)."""
    with transaction() as conn:
        conn.execute("DELETE FROM blockchain_ledger")
        for key in meta_keys:
            conn.execute("DELETE FROM app_meta WHERE key = ?", (key,))


# --------------------------------------------------------------------------- #
# app_meta
# --------------------------------------------------------------------------- #
def get_meta(key: str) -> Optional[str]:
    row = _fetchone("SELECT value FROM app_meta WHERE key = ?", (key,))
    return row["value"] if row else None


def set_meta(key: str, value: str) -> None:
    _execute(
        "INSERT INTO app_meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )


# --------------------------------------------------------------------------- #
# Dashboard statistics
# --------------------------------------------------------------------------- #
def get_user_stats(owner: str) -> dict[str, Any]:
    msgs = _fetchone("SELECT COUNT(*) AS n FROM secret_messages WHERE owner = ?", (owner,))
    files = _fetchone("SELECT COUNT(*) AS n, COALESCE(SUM(size_bytes), 0) AS total "
                      "FROM encrypted_files WHERE owner = ?", (owner,))
    return {
        "secret_messages": int(msgs["n"]) if msgs else 0,
        "encrypted_files": int(files["n"]) if files else 0,
        "encrypted_bytes": int(files["total"]) if files else 0,
        "ledger_blocks": count_blocks(),
    }


# --------------------------------------------------------------------------- #
# Raw Ciphertext Database Inspection (Forensic Audit)
# --------------------------------------------------------------------------- #
def get_raw_records_for_inspection(owner: str) -> dict[str, list[dict]]:
    """Raw at-rest rows: ``users`` comes from D:\\, the rest from storage/vault.db."""
    users_raw = _fetchall_on(
        get_auth_connection,
        "SELECT id, username, password_hash, salt, kdf_iterations, hex(bio_nonce) AS bio_nonce_hex, "
        "hex(bio_ciphertext) AS bio_ciphertext_hex, hex(bio_tag) AS bio_tag_hex, bio_algorithm, role, "
        "enrolled_by, created_at FROM users WHERE username = ?",
        (owner,),
    )
    messages_raw = _fetchall(
        "SELECT id, title, ciphertext, algorithm, created_at FROM secret_messages WHERE owner = ? ORDER BY id DESC",
        (owner,),
    )
    files_raw = _fetchall(
        "SELECT id, original_name, stored_name, size_bytes, sha256_plain, kdf_salt, nonce, algorithm, created_at "
        "FROM encrypted_files WHERE owner = ? ORDER BY id DESC",
        (owner,),
    )
    blocks_raw = _fetchall(
        "SELECT block_index, timestamp, asset_name, encrypted_asset_metadata, previous_hash, nonce, current_hash "
        "FROM blockchain_ledger ORDER BY block_index ASC"
    )
    return {
        "users": users_raw,
        "secret_messages": messages_raw,
        "encrypted_files": files_raw,
        "blockchain_ledger": blocks_raw,
    }
