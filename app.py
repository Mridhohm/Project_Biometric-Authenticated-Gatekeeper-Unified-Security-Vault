r"""
Krypt Vault - Sistem Brankas Bukti Forensik Siber & Dokumen Intelijen
=====================================================================

Alur aplikasi:
  1. GATE_01 Kunci perangkat keras : HANYA USB flash drive D:\ (GetDriveTypeW + psutil), tanpa fallback
                                     virtual. Tanpa D:\ -> layar CRITICAL_SECURITY_HALT merah penuh.
  2. GATE_02 Identitas & biometrik : login saja (username + passkey + pemindai wajah). Kredensial,
                                     PBKDF2 verifier + salt, dan template wajah AES-128-EAX dibaca dari
                                     D:\.bagus_vault_auth\operators.db. Jika D:\ kosong (0 operator) ->
                                     layar satu kali INITIALIZE_ROOT_OPERATOR.
  3. GATE_03 Ruang kerja vault     :
       - Enkripsi teks   : Super enkripsi Extended Vigenere (klasik) + AES-256-CBC (modern)
       - Enkripsi berkas : ChaCha20 stream cipher (.krypt.enc)
       - Steganografi    : LSB pada citra PNG
       - Basis data      : penyimpanan ciphertext at-rest di SQLite + audit
       - Ledger aset     : blockchain SHA-256 Proof-of-Work + AES-256-GCM
       - [06] Manajemen Operator : ENROLL_NEW_IDENTITY (khusus operator yang sudah login)
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import secrets
import time
from typing import Optional

import streamlit as st

import config
import database
import ui_theme as ui
from modules import (
    auth_biometric,
    blockchain,
    dongle_guard,
    face_scanner,
    file_crypto,
    steganography,
    super_encryption,
)

st.set_page_config(
    page_title="Krypt Vault — Forensic Security Suite",
    layout="wide",
    initial_sidebar_state="expanded",
)

for _k, _v in {
    "user": None,
    "similarity": None,
    "page": "Ringkasan",
    "dongle_sig": None,
    "session_dongle_id": None,
    "last_auth_sim": None,
    "last_auth_msg": None,
    "li_last_auto_id": None,
    "li_bad_cred_sig": None,
    "li_cred_seen_sig": None,
    "li_last_log_ts": 0.0,
}.items():
    st.session_state.setdefault(_k, _v)

ui.inject_theme()
ui.init_logs()
# NOTE: no database.init_db() here - databases are opened only after GATE_01 confirms D:\.

PAGES = [
    "Ringkasan",
    "Enkripsi Teks",
    "Enkripsi Berkas",
    "Steganografi",
    "Basis Data",
    "Ledger Aset",
    "Manajemen Operator",
    "Kunci Perangkat",
    "Log Aktivitas",
]


# =========================================================================== #
# Helpers
# =========================================================================== #
def _short(path: Optional[str], n: int = 42) -> str:
    if not path:
        return "-"
    return path if len(path) <= n else "..." + path[-(n - 3):]


def _navigate(target_page: str) -> None:
    st.session_state.page = target_page


def _format_bytes(num: int) -> str:
    if num < 1024:
        return f"{num} B"
    if num < 1024 * 1024:
        return f"{num / 1024:.1f} KB"
    return f"{num / (1024 * 1024):.2f} MB"


def _safe_download_name(name: object, fallback: str = "vault_file.bin") -> str:
    """Sanitize a filename for Windows SaveFileDialog and browser downloads."""
    base = re.split(r"[\\/]+", str(name or ""))[-1]
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", base).strip(" .")
    return cleaned or fallback


def _password_strength(pw: str) -> tuple[float, str, str]:
    if not pw:
        return 0.0, "warn", ""
    score = 0
    if len(pw) >= 8:
        score += 30
    if len(pw) >= 12:
        score += 20
    if re.search(r"[a-z]", pw):
        score += 15
    if re.search(r"[A-Z]", pw):
        score += 15
    if re.search(r"\d", pw):
        score += 10
    if re.search(r"[^A-Za-z0-9]", pw):
        score += 10
    if score >= 80 and len(pw) >= 8 and re.search(r"[A-Za-z]", pw) and re.search(r"\d", pw):
        return float(score), "ok", ""
    if score >= 55:
        return float(score), "info", ""
    return float(score), "bad", ""


def _clear_identity_session(*, drop_user: bool = True) -> None:
    """Clear volatile identity state and cached live face snapshots."""
    if drop_user:
        st.session_state.user = None
        st.session_state.similarity = None
        st.session_state.session_dongle_id = None
    st.session_state.last_auth_sim = None
    st.session_state.last_auth_msg = None
    st.session_state.li_last_auto_id = None
    st.session_state.li_bad_cred_sig = None
    st.session_state.li_cred_seen_sig = None
    st.session_state.li_last_log_ts = 0.0
    face_scanner.clear_live_cache("li")
    face_scanner.clear_live_cache("rg")


def _capture_face(
    key: str,
    *,
    mode: str = "login",
    ready: bool = True,
    similarity: Optional[float] = None,
    status_note: str = "",
) -> tuple[Optional[bytes], Optional[str]]:
    """Acquire face image via continuous live HUD scanner or uploaded file."""
    source_mode = st.segmented_control(
        "Sumber citra wajah",
        ["Pindai Live", "Unggah foto"],
        default="Pindai Live",
        key=f"{key}_mode",
    ) or "Pindai Live"
    if source_mode == "Pindai Live":
        return face_scanner.render_live_face_scanner(
            key,
            mode=mode,
            ready=ready,
            similarity=similarity,
            status_note=status_note,
            threshold=auth_biometric.MATCH_THRESHOLD,
        )
    face_scanner.clear_live_cache(key)
    up = st.file_uploader("Foto wajah (PNG/JPG)", type=["png", "jpg", "jpeg"], key=f"{key}_up")
    return (up.getvalue() if up else None), None


def _active_dongle_status() -> dongle_guard.DongleStatus:
    return dongle_guard.scan_for_dongle()


def _render_topbar(status: dongle_guard.DongleStatus, show_brand: bool = True) -> None:
    """Persistent application bar: brand or breadcrumb, hardware key status, and the activity log."""
    logs_count = len(st.session_state.get("kv_logs", []))

    c_left, c_stat, c_log = st.columns([2, 2.2, 0.9], vertical_alignment="center")
    with c_left:
        if show_brand:
            ui.brand()
        else:
            ui.crumb("Vault", st.session_state.page)
    with c_stat:
        if status.valid:
            ui.status("Kunci aktif", "ok", status.label or "USB")
        else:
            ui.status("Menunggu kunci USB", "warn")
    with c_log:
        with st.popover(f"Log ({logs_count})", use_container_width=True):
            st.markdown("**Telemetri aktivitas terbaru**")
            ui.render_log(limit=25)
            if st.button("Bersihkan log", key="top_clear_logs", use_container_width=True):
                st.session_state.kv_logs = []
                ui.log("SYSTEM", "Riwayat log sesi dibersihkan", level="INFO")
                st.rerun()


@st.fragment(run_every=2)
def _dongle_watch(expected_id: Optional[str], user: Optional[str] = None) -> None:
    """Re-probe D:\\ every 2 s; invalidate the session the moment the stick is pulled or swapped."""
    status = _active_dongle_status()
    if not status.valid or status.dongle_id != expected_id or (user and not auth_biometric.validate_session(user)):
        ui.log("DONGLE", "USB D:\\ dicabut / berubah - sesi diinvalidasi dan vault dikunci", level="CRIT")
        _clear_identity_session()
        st.rerun(scope="app")


# =========================================================================== #
# Interactive Dialogs (Modals)
# =========================================================================== #
@st.dialog("Dekripsi Cepat Laporan Rahasia")
def _modal_decrypt_message(msg: dict) -> None:
    st.markdown(
        f"**Rekaman #{msg['id']} — {html.escape(msg['title'])}**  \n"
        + ui.chip(msg["algorithm"], "info")
        + ui.chip(msg["created_at"]),
        unsafe_allow_html=True,
    )
    st.code(msg["ciphertext"][:180] + ("..." if len(msg["ciphertext"]) > 180 else ""), language=None)
    vk = st.text_input("Kunci Vigenere (Lapisan 1)", type="password", key=f"mdl_vk_{msg['id']}")
    ak = st.text_input("Passphrase AES-256 (Lapisan 2)", type="password", key=f"mdl_ak_{msg['id']}")
    if st.button("Buka Ciphertext", type="primary", use_container_width=True, key=f"mdl_go_{msg['id']}"):
        try:
            out = super_encryption.super_decrypt_detailed(msg["ciphertext"], vk, ak)
            ui.log("TEXT", f"Laporan #{msg['id']} didekripsi via inspektor", ui.sha256_hex(out["plaintext"]), "OK")
            st.success("Dekripsi dua lapis berhasil.")
            st.text_area("Plaintext asli", out["plaintext"], height=150, key=f"mdl_pt_{msg['id']}")
        except Exception:
            ui.log("TEXT", f"Gagal mendekripsi laporan #{msg['id']}", level="CRIT")
            st.error("Kunci Vigenere atau Passphrase AES-256 salah.")


@st.dialog("Inspeksi Blok & Dekripsi Metadata")
def _modal_inspect_block(blk: blockchain.Block, is_ok: bool) -> None:
    st.markdown(
        f"**Blok #{blk.index} — {html.escape(blk.asset_name)}** "
        + ui.chip("Valid PoW" if is_ok else "Integritas Rusak", "ok" if is_ok else "bad"),
        unsafe_allow_html=True,
    )
    ui.kv_grid([
        ("Timestamp", blk.timestamp),
        ("Nonce PoW", str(blk.nonce)),
        ("Current Hash", blk.current_hash),
        ("Previous Hash", blk.previous_hash),
    ])
    st.divider()
    st.markdown("**Metadata Terenkripsi (AES-256-GCM)**")
    try:
        dec = blockchain.decrypt_metadata(blk)
        st.json(dec)
        ui.log("LEDGER", f"Metadata blok #{blk.index} didekripsi & diverifikasi AES-GCM", blk.current_hash, "OK")
    except Exception as exc:
        st.error(f"Tag autentikasi AES-256-GCM gagal: {exc}")


# =========================================================================== #
# Gate 1 - Strict hardware lock: USB flash drive D:\ (no virtual fallback)
# =========================================================================== #
_LOCKDOWN_CSS = """
<style>
section[data-testid="stSidebar"], [data-testid="stExpandSidebarButton"],
[data-testid="collapsedControl"] { display: none !important; }
.stApp {
  background: radial-gradient(ellipse 90% 60% at 50% 30%, #3A0009 0%, #14000A 55%, #050002 100%) !important;
}
.stApp::before { background: #FF1F3D !important; height: 4px !important; }
.kv-halt {
  min-height: 62vh; display: flex; flex-direction: column; align-items: center; justify-content: center;
  text-align: center; padding: 36px 20px; border: 2px solid #FF1F3D;
  background: repeating-linear-gradient(0deg, rgba(255, 31, 61, 0.05) 0 2px, transparent 2px 4px), rgba(20, 0, 6, 0.88);
  box-shadow: 0 0 70px rgba(255, 31, 61, 0.35) inset, 0 0 40px rgba(255, 31, 61, 0.25);
  clip-path: polygon(0 0, calc(100% - 22px) 0, 100% 22px, 100% 100%, 22px 100%, 0 calc(100% - 22px));
}
.kv-halt-ic { color: #FF1F3D; animation: kv-halt-blink 1.1s steps(2, start) infinite; }
.kv-halt-tag {
  font-family: var(--f-mono); color: #FF8A99; font-size: 0.86rem; font-weight: 600;
  letter-spacing: 0.14em; margin-top: 14px; text-transform: uppercase;
}
.kv-halt-code {
  font-family: var(--f-mono); color: #FF1F3D; font-weight: 700; letter-spacing: 0.04em;
  font-size: clamp(1.15rem, 2.6vw, 2.1rem); margin: 10px 0 6px; word-break: break-word;
  text-shadow: 0 0 18px rgba(255, 31, 61, 0.85);
}
@keyframes kv-halt-blink { to { visibility: hidden; } }
@media (prefers-reduced-motion: reduce) { .kv-halt-ic { animation: none; } }
</style>
"""


@st.fragment(run_every=2)
def _lockdown_monitor(halt_code: Optional[str]) -> None:
    """Re-probe D:\\ every 2 s; reopen the app as soon as the halt condition changes."""
    live = dongle_guard.scan_for_dongle()
    if live.valid or live.halt_code != halt_code:
        st.rerun(scope="app")


def screen_lockdown(status: dongle_guard.DongleStatus) -> None:
    """GATE_01 full-screen Crimson Red Lockscreen. Nothing else is rendered."""
    st.markdown(_LOCKDOWN_CSS, unsafe_allow_html=True)
    banner = status.banner or config.HALT_BANNER_DRIVE_MISSING
    st.markdown(
        "<div class='kv-halt'>"
        f"<div class='kv-halt-ic'>{ui.icon('lock', 64)}</div>"
        "<div class='kv-halt-tag'>GATE_01 // HARDWARE_LOCK</div>"
        f"<div class='kv-halt-code'>{html.escape(banner)}</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    _lockdown_monitor(status.halt_code)

    st.write("")
    if st.button("Pindai Ulang D:\\", type="primary", use_container_width=True, key="halt_rescan"):
        st.rerun()


@st.fragment(run_every=2)
def _gate_watch(expected_id: Optional[str]) -> None:
    """Pre-login watcher: return to the lockscreen immediately if D:\\ disappears or changes."""
    live = dongle_guard.scan_for_dongle()
    if not live.valid or live.dongle_id != expected_id:
        _clear_identity_session()
        st.rerun(scope="app")


def _drive_chips(status: dongle_guard.DongleStatus) -> None:
    st.markdown(
        ui.chip(f"Kunci: {status.label or '-'}", "ok", icon_name="usb")
        + ui.chip(f"Drive: {status.path or 'D:'} ({status.drive_type or '-'})", "info")
        + ui.chip(f"Serial: {status.volume_serial or '-'}")
        + ui.chip(f"Brankas: {_short(status.auth_dir, 32)}"),
        unsafe_allow_html=True,
    )


def _handle_drive_loss(context: str) -> None:
    ui.log("DONGLE", f"USB D:\\ hilang saat {context} - sesi diinvalidasi", level="CRIT")
    _clear_identity_session()
    st.rerun()


# =========================================================================== #
# Gate 2a - One-time bootstrap (D:\ has zero operators)
# =========================================================================== #
def screen_bootstrap(status: dongle_guard.DongleStatus) -> None:
    _gate_watch(status.dongle_id)
    _render_topbar(status, show_brand=True)
    ui.steps(2)
    ui.page_header(
        "Gerbang Keamanan 02 // BOOTSTRAP",
        "INITIALIZE_ROOT_OPERATOR",
        icon_name="key",
    )
    _drive_chips(status)
    st.write("")

    c1, c2 = st.columns([1, 1.15], gap="large")
    with c1:
        with st.container(border=True):
            st.markdown("### Identitas Operator Root")
            bu = st.text_input("Nama pengguna (3-32 karakter: a-z, 0-9, _ . -)", key="boot_user")
            bp = st.text_input("Kata sandi (minimal 8 karakter, huruf + angka)", type="password", key="boot_pw")
            s_pct, s_kind, _ = _password_strength(bp)
            ui.meter("Kekuatan Kata Sandi", s_pct, kind=s_kind)
            bp2 = st.text_input("Ulangi kata sandi", type="password", key="boot_pw2")
    with c2:
        with st.container(border=True):
            st.markdown("### Template Wajah Root")
            bface, _ = _capture_face("boot", mode="register", ready=True)

    if st.button("INITIALIZE_ROOT_OPERATOR", type="primary", use_container_width=True, key="boot_submit"):
        if bp != bp2:
            st.error("Kedua kata sandi tidak sama.")
        elif not (bu and bp and bface):
            st.warning("Lengkapi nama pengguna, kata sandi, dan citra wajah.")
        else:
            with st.status("Menginisialisasi D:\\ dan menyegel template biometrik...", expanded=True) as st_box:
                res = auth_biometric.register_user(bu.strip().lower(), bp, bface, bootstrap=True)
                if res.drive_missing:
                    _handle_drive_loss("inisialisasi root")
                ui.log("AUTH", f"INITIALIZE_ROOT_OPERATOR {bu}: {res.message}", ui.sha256_hex(bface),
                       "OK" if res.success else "WARN")
                if res.success:
                    st_box.update(label="Operator root terdaftar di D:\\", state="complete", expanded=False)
                    face_scanner.clear_live_cache("boot")
                    st.toast("Operator root dibuat. Setup awal ditutup permanen - silakan login.")
                    st.rerun()
                st_box.update(label="Inisialisasi ditolak", state="error", expanded=False)
                st.error(res.message)


# =========================================================================== #
# Gate 2b - Operator login ONLY (no public enrollment)
# =========================================================================== #
def screen_identity(status: dongle_guard.DongleStatus) -> None:
    _gate_watch(status.dongle_id)
    _render_topbar(status, show_brand=True)
    ui.steps(2)
    ui.page_header(
        "Gerbang Keamanan 02",
        "Login operator",
        icon_name="user",
    )
    _drive_chips(status)
    st.write("")

    def _login_success(res: auth_biometric.AuthResult, digest: str) -> None:
        _clear_identity_session(drop_user=False)
        ui.log("AUTH", f"Login berhasil: {res.username} (kemiripan {res.similarity:.1%})", digest, "OK")
        st.session_state.user = res.username
        st.session_state.similarity = res.similarity
        st.session_state.session_dongle_id = status.dongle_id
        st.session_state.page = "Ringkasan"
        st.toast(f"Selamat datang, {res.username}. Vault terbuka.")
        st.rerun()

    def _verify_operator_login(
        username: str,
        password: str,
        face_bytes: bytes,
        *,
        silent_fail: bool = False,
        cred_sig: Optional[str] = None,
    ) -> None:
        digest = ui.sha256_hex(face_bytes)
        if silent_fail:
            res = auth_biometric.authenticate_user(username.strip().lower(), password, face_bytes)
            if res.drive_missing:
                _handle_drive_loss("verifikasi login")
            if res.success:
                _login_success(res, digest)
            st.session_state.last_auth_sim = res.similarity
            if res.similarity is None:
                st.session_state.last_auth_msg = res.message
                if cred_sig:
                    st.session_state.li_bad_cred_sig = cred_sig
            else:
                st.session_state.last_auth_msg = (
                    f"Kemiripan {res.similarity:.1%} (minimum {auth_biometric.MATCH_THRESHOLD:.0%})"
                )
                st.session_state.li_bad_cred_sig = None
            now_ts = time.monotonic()
            if now_ts - float(st.session_state.get("li_last_log_ts") or 0.0) >= 4.0:
                ui.log("AUTH", f"Login ditolak untuk {username}: {res.message}", digest, "CRIT")
                st.session_state.li_last_log_ts = now_ts
            st.rerun()

        with st.status("Memverifikasi dua faktor terhadap brankas D:\\...", expanded=True) as st_box:
            st.write("Membaca verifier dari D:\\ & menghitung PBKDF2-HMAC-SHA256 (600.000 iterasi)...")
            res = auth_biometric.authenticate_user(username.strip().lower(), password, face_bytes)
            if res.drive_missing:
                _handle_drive_loss("verifikasi login")
            if res.success:
                st.write("Mendekripsi template AES-128-EAX dari D:\\ & mencocokkan wajah...")
                st_box.update(label="Autentikasi berhasil", state="complete", expanded=False)
                _login_success(res, digest)
            st_box.update(label="Verifikasi ditolak", state="error", expanded=False)
            st.session_state.last_auth_sim = res.similarity
            st.session_state.last_auth_msg = res.message
            st.session_state.li_bad_cred_sig = cred_sig if (res.similarity is None and cred_sig) else None
            ui.log("AUTH", f"Login ditolak untuk {username}: {res.message}", digest, "CRIT")
            st.session_state.li_last_log_ts = time.monotonic()
            sim_note = (
                f" (Kemiripan wajah: {res.similarity:.1%}, minimum {auth_biometric.MATCH_THRESHOLD:.0%})"
                if res.similarity is not None
                else ""
            )
            st.error(res.message + sim_note)

    c1, c2 = st.columns([1, 1.15], gap="large")
    with c1:
        with st.container(border=True):
            st.markdown("### Faktor 1 — Kredensial")
            user = st.text_input("Nama pengguna", key="li_user", placeholder="contoh: analis_01")
            pw = st.text_input("Passkey", type="password", key="li_pw", placeholder="Masukkan kata sandi")
            cred_sig = (
                hashlib.sha256(f"{user.strip().lower()}\x00{pw}".encode("utf-8")).hexdigest()[:16]
                if (user and pw)
                else None
            )
            if cred_sig != st.session_state.get("li_cred_seen_sig"):
                st.session_state.li_cred_seen_sig = cred_sig
                st.session_state.li_bad_cred_sig = None
                st.session_state.last_auth_msg = None
                st.session_state.last_auth_sim = None

            if st.session_state.get("last_auth_sim") is not None:
                sim_val = float(st.session_state.last_auth_sim)
                ui.meter(
                    "Skor Kemiripan Wajah Live",
                    sim_val * 100.0,
                    threshold_pct=auth_biometric.MATCH_THRESHOLD * 100.0,
                    kind="ok" if sim_val >= auth_biometric.MATCH_THRESHOLD else "bad",
                    subtitle=f"Ambang batas sistem: {auth_biometric.MATCH_THRESHOLD:.0%} (garis penanda)",
                )
            elif st.session_state.get("last_auth_msg") and cred_sig == st.session_state.get("li_bad_cred_sig"):
                st.error(st.session_state.last_auth_msg)
    with c2:
        with st.container(border=True):
            st.markdown("### Faktor 2 — Pemindai Wajah Optik")
            face, capture_id = _capture_face(
                "li",
                mode="login",
                ready=bool(user and pw),
                similarity=st.session_state.get("last_auth_sim"),
                status_note=st.session_state.get("last_auth_msg") or "",
            )

    is_manual_hud = bool(capture_id and capture_id.startswith("m-"))
    cred_blocked = bool(cred_sig and st.session_state.get("li_bad_cred_sig") == cred_sig)
    auto_triggered = bool(
        capture_id
        and face
        and user
        and pw
        and capture_id != st.session_state.get("li_last_auto_id")
        and (is_manual_hud or not cred_blocked)
    )
    if auto_triggered:
        st.session_state.li_last_auto_id = capture_id
        _verify_operator_login(user, pw, face, silent_fail=not is_manual_hud, cred_sig=cred_sig)
    elif st.button("Verifikasi dan Masuk ke Vault", type="primary", use_container_width=True, key="li_submit"):
        if not (user and pw and face):
            st.warning("Lengkapi nama pengguna, passkey, dan citra wajah terlebih dahulu.")
        else:
            _verify_operator_login(user, pw, face, silent_fail=False, cred_sig=cred_sig)


# =========================================================================== #
# Workspace Pages (Gate 3)
# =========================================================================== #
def page_overview(user: str, status: dongle_guard.DongleStatus) -> None:
    blockchain.ensure_genesis()
    stats = database.get_user_stats(user)
    report = blockchain.verify_chain()
    ui.page_header(
        "Pusat Kendali",
        f"Selamat datang, {user}",
        icon_name="shield",
    )

    m = st.columns(4)
    m[0].metric("Laporan Rahasia", stats["secret_messages"])
    m[1].metric("Berkas ChaCha20", stats["encrypted_files"])
    m[2].metric("Blok Ledger PoW", stats["ledger_blocks"])
    m[3].metric("Integritas Rantai", "Valid" if report.valid else "Terganggu")

    if not report.valid:
        st.error(f"Ledger terdeteksi dimanipulasi ({len(report.issues)} temuan). Buka Ledger Aset untuk inspeksi.")

    st.write("")
    st.markdown("### Akses Cepat Modul")
    qa_cols = st.columns(4)
    quick_items = [
        ("Enkripsi Teks", "Super enkripsi", "text"),
        ("Enkripsi Berkas", "Stream ChaCha20", "file"),
        ("Steganografi", "Sisip citra PNG", "image"),
        ("Ledger Aset", "Blockchain PoW", "blocks"),
    ]
    for col, (target_page, heading, ic) in zip(qa_cols, quick_items):
        with col:
            with st.container(border=True):
                ui.module_head(ic, heading)
                st.button(
                    "Buka modul",
                    key=f"qa_{target_page}",
                    on_click=_navigate,
                    args=(target_page,),
                    use_container_width=True,
                )

    st.write("")
    with st.container(border=True):
        st.markdown("### Telemetri Sesi Aktif")
        sim_str = f"{st.session_state.similarity:.1%}" if st.session_state.similarity is not None else "-"
        ui.kv_grid([
            ("Operator", user),
            ("Skor Biometrik", sim_str),
            ("Kunci Aktif", status.label or "-"),
            ("ID Dongle", (status.dongle_id or "-")[:18]),
            ("Volume Serial", status.volume_serial or "-"),
            ("Waktu Verifikasi", f"{report.elapsed_ms:.1f} ms"),
        ])


def page_text(user: str) -> None:
    ui.page_header(
        "Kriteria 3 — Pesan Rahasia",
        "Super enkripsi teks (Klasik + Modern)",
        icon_name="text",
    )
    has_res = "text_result" in st.session_state and st.session_state.text_result is not None
    ui.pipeline([
        ("1. Plaintext", "Input UTF-8", True),
        ("2. Extended Vigenere", "Mod-256 Klasik", has_res),
        ("3. AES-256-CBC", "Salt + IV Acak", has_res),
        ("4. SQLite Ciphertext", "At-Rest Vault", has_res),
    ])

    msgs = database.list_secret_messages(user)
    t_enc, t_dec, t_list = st.tabs(["Enkripsi & Simpan", "Dekripsi Manual", f"Arsip Laporan ({len(msgs)})"])

    with t_enc:
        with st.form("enc_text"):
            title = st.text_input("Judul laporan")
            plain = st.text_area("Isi laporan rahasia", height=145)
            c1, c2 = st.columns(2)
            vk = c1.text_input("Kunci Vigenere (Lapisan 1)", type="password")
            ak = c2.text_input("Passphrase AES-256 (Lapisan 2)", type="password")
            go = st.form_submit_button("Enkripsi dan Simpan ke Vault", type="primary")
        if go:
            if not (title and plain and vk and ak):
                st.warning("Semua kolom wajib diisi.")
            else:
                with st.status("Menjalankan super enkripsi dua lapis...", expanded=False) as s_box:
                    res = super_encryption.super_encrypt_detailed(plain, vk, ak)
                    mid = database.insert_secret_message(user, title, res["token"], super_encryption.ALGORITHM_ID)
                    ui.log("TEXT", f"Laporan #{mid} '{title}' dienkripsi", ui.sha256_hex(res["token"]), "OK")
                    st.session_state.text_result = res
                    s_box.update(label=f"Laporan #{mid} tersimpan sebagai ciphertext", state="complete")
                st.toast(f"Laporan #{mid} berhasil diamankan.")

        res = st.session_state.get("text_result")
        if res:
            with st.container(border=True):
                st.markdown("### Inspeksi Hasil Per Lapisan")
                st.markdown("**Lapisan 1 — Extended Vigenere (Base64)**")
                st.code(res["vigenere_b64"], language=None, wrap_lines=True)
                st.markdown("**Lapisan 2 — Parameter & Ciphertext AES-256-CBC**")
                ui.kv_grid([
                    ("Salt", res["salt_hex"]),
                    ("IV", res["iv_hex"]),
                    ("AES Ciphertext", res["aes_ciphertext_hex"][:96] + "..."),
                ])
                st.markdown("**Token Final (Tersimpan di SQLite)**")
                st.code(res["token"], language=None, wrap_lines=True)

    with t_dec:
        src = st.segmented_control("Sumber ciphertext", ["Pilih dari Arsip", "Tempel Token"], default="Pilih dari Arsip", key="tdec_src") or "Pilih dari Arsip"
        token = ""
        if src == "Pilih dari Arsip":
            if msgs:
                opts = {f"#{m['id']} — {m['title']}": m for m in msgs}
                token = opts[st.selectbox("Pilih laporan", list(opts), key="tdec_sel")]["ciphertext"]
                st.code(token, language=None, wrap_lines=True)
            else:
                st.info("Arsip masih kosong.")
        else:
            token = st.text_area("Tempel token Base64", height=110, key="tdec_paste")
        c1, c2 = st.columns(2)
        vk = c1.text_input("Kunci Vigenere", type="password", key="dvk")
        ak = c2.text_input("Passphrase AES-256", type="password", key="dak")
        if st.button("Dekripsi Token", type="primary", key="tdec_go"):
            try:
                out = super_encryption.super_decrypt_detailed(token.strip(), vk, ak)
                ui.log("TEXT", "Dekripsi laporan berhasil", ui.sha256_hex(out["plaintext"]), "OK")
                st.toast("Dekripsi berhasil.")
                st.markdown("**Hasil Lapisan Tengah (Masih Terenkripsi Vigenere)**")
                st.code(out["vigenere_b64"], language=None, wrap_lines=True)
                st.markdown("**Plaintext Asli**")
                st.text_area("Plaintext", out["plaintext"], height=140, label_visibility="collapsed")
            except Exception as exc:
                ui.log("TEXT", f"Dekripsi gagal: {exc}", level="CRIT")
                st.error("Dekripsi gagal. Periksa kembali kedua kunci atau keutuhan token.")

    with t_list:
        if not msgs:
            st.info("Belum ada laporan tersimpan di vault.")
        for m in msgs:
            with st.container(border=True):
                a, b, c = st.columns([4.2, 1.3, 0.9], vertical_alignment="center")
                a.markdown(
                    f"**#{m['id']} — {html.escape(m['title'])}**  \n"
                    + ui.chip(m["algorithm"], "info")
                    + ui.chip(m["created_at"]),
                    unsafe_allow_html=True,
                )
                if b.button("Dekripsi", key=f"openm{m['id']}", type="primary", use_container_width=True):
                    _modal_decrypt_message(m)
                if c.button("Hapus", key=f"delm{m['id']}", use_container_width=True):
                    database.delete_secret_message(m["id"], user)
                    ui.log("TEXT", f"Laporan #{m['id']} dihapus dari arsip", level="WARN")
                    st.toast(f"Laporan #{m['id']} dihapus.")
                    st.rerun()


def page_files(user: str) -> None:
    ui.page_header(
        "Kriteria 4 — Berkas Biner",
        "Enkripsi berkas (ChaCha20 Stream Cipher)",
        icon_name="file",
    )
    has_fr = "file_result" in st.session_state and st.session_state.file_result is not None
    ui.pipeline([
        ("1. Berkas Asli", "Raw Bytes", True),
        ("2. SHA-256 Checksum", "Sidik Jari", has_fr),
        ("3. ChaCha20 Cipher", "256-bit Stream", has_fr),
        ("4. Paket .krypt.enc", "Mandiri + Vault", has_fr),
    ])

    files = database.list_encrypted_files(user)
    t_enc, t_dec, t_vault = st.tabs(["Enkripsi Berkas", "Buka .krypt.enc", f"Arsip Vault ({len(files)})"])

    with t_enc:
        up = st.file_uploader("Pilih atau seret berkas untuk diamankan", key="fe_up")
        if up is not None:
            raw_preview = up.getvalue()
            with st.container(border=True):
                st.markdown("**Pratinjau Inspeksi Berkas (Pra-Enkripsi)**")
                ui.kv_grid([
                    ("Nama Berkas", up.name),
                    ("Ukuran", f"{_format_bytes(len(raw_preview))} ({len(raw_preview):,} byte)"),
                    ("Tipe MIME", up.type or "application/octet-stream"),
                    ("SHA-256 Asli", ui.sha256_hex(raw_preview)),
                ])
        pw = st.text_input("Passphrase Enkripsi Berkas", type="password", key="fe_pw")
        if st.button("Enkripsi & Segel Berkas", type="primary", disabled=up is None, key="fe_go"):
            if not pw:
                st.warning("Passphrase wajib diisi.")
            else:
                with st.status("Menjalankan ChaCha20 Stream Cipher...", expanded=False) as s_box:
                    raw = up.getvalue()
                    bundle = file_crypto.encrypt_file_bytes(raw, pw)
                    pkg = file_crypto.pack_krypt_envelope(bundle, up.name, up.type)
                    stored = f"{secrets.token_hex(16)}.enc"
                    config.ensure_storage()
                    (config.FILES_DIR / stored).write_bytes(bundle.ciphertext)
                    database.insert_encrypted_file(
                        owner=user, original_name=up.name, stored_name=stored, mime_type=up.type,
                        size_bytes=len(raw), sha256_plain=bundle.sha256_plain, kdf_salt=bundle.kdf_salt,
                        nonce=bundle.nonce, algorithm=bundle.algorithm,
                    )
                    ui.log("FILE", f"Berkas '{up.name}' ({len(raw)} B) dienkripsi", bundle.sha256_plain, "OK")
                    st.session_state.file_result = (up.name, len(raw), bundle, pkg)
                    s_box.update(label=f"'{up.name}' disegel ke paket .krypt.enc", state="complete")
                st.toast(f"'{up.name}' berhasil dienkripsi.")

        fr = st.session_state.get("file_result")
        if fr:
            name, size, bundle, pkg = fr
            with st.container(border=True):
                st.success(f"'{name}' selesai dienkripsi dan tersimpan di arsip vault.")
                ui.kv_grid([
                    ("Algoritma", bundle.algorithm),
                    ("Ukuran Asli", f"{_format_bytes(size)} ({size:,} byte)"),
                    ("SHA-256 Plaintext", bundle.sha256_plain),
                    ("KDF Salt", bundle.kdf_salt),
                    ("Nonce 96-bit", bundle.nonce),
                    ("Pratinjau Ciphertext", bundle.ciphertext[:32].hex() + "..."),
                ])
                st.write("")
                st.download_button(
                    f"Unduh {name}.krypt.enc",
                    pkg,
                    file_name=_safe_download_name(f"{name}.krypt.enc", "encrypted.krypt.enc"),
                    mime="application/octet-stream",
                    key="fe_dl",
                    on_click="ignore",
                    type="primary",
                )

    with t_dec:
        enc = st.file_uploader("Unggah berkas .krypt.enc", type=["enc"], key="fd_up")
        pw = st.text_input("Passphrase Dekripsi", type="password", key="fd_pw")
        if st.button("Buka & Verifikasi .krypt.enc", type="primary", disabled=enc is None, key="fd_go"):
            try:
                plain, meta = file_crypto.unpack_krypt_envelope(enc.getvalue(), pw)
                st.session_state.file_dec = (plain, meta)
                ui.log("FILE", f"Berkas '{meta['original_name']}' didekripsi, SHA-256 cocok", meta["sha256_plain"], "OK")
                st.toast(f"'{meta['original_name']}' siap diunduh.")
            except Exception as exc:
                st.session_state.file_dec = None
                ui.log("FILE", f"Dekripsi berkas gagal: {exc}", level="CRIT")
                st.error("Dekripsi gagal. Passphrase salah atau berkas dimanipulasi.")
        fd = st.session_state.get("file_dec")
        if fd:
            plain, meta = fd
            st.success(f"Integritas SHA-256 terverifikasi: {meta['original_name']} ({_format_bytes(len(plain))}).")
            st.download_button(
                f"Unduh {meta['original_name']}",
                plain,
                file_name=_safe_download_name(meta.get("original_name"), "decrypted_file.bin"),
                mime=meta.get("mime_type") or "application/octet-stream",
                key="fd_dl",
                on_click="ignore",
                type="primary",
            )

    with t_vault:
        if not files:
            st.info("Arsip berkas di vault masih kosong.")
        for f in files:
            with st.container(border=True):
                st.markdown(
                    f"**#{f['id']} — {html.escape(f['original_name'])}**  \n"
                    + ui.chip(_format_bytes(f["size_bytes"]), "info")
                    + ui.chip(f"sha256:{f['sha256_plain'][:12]}")
                    + ui.chip(f["created_at"]),
                    unsafe_allow_html=True,
                )
                c1, c2, c3 = st.columns([3, 1, 1])
                pw_v = c1.text_input("Passphrase", type="password", key=f"vpw{f['id']}", label_visibility="collapsed", placeholder="Masukkan passphrase berkas")
                if c2.button("Dekripsi", key=f"vdec{f['id']}", use_container_width=True):
                    try:
                        ct = (config.FILES_DIR / f["stored_name"]).read_bytes()
                        plain = file_crypto.decrypt_file_bytes(ct, pw_v, f["kdf_salt"], f["nonce"], f["sha256_plain"])
                        st.session_state[f"vault_plain_{f['id']}"] = plain
                        ui.log("FILE", f"Arsip berkas #{f['id']} didekripsi", f["sha256_plain"], "OK")
                        st.toast(f"'{f['original_name']}' didekripsi.")
                    except Exception:
                        st.error("Passphrase salah atau checksum SHA-256 tidak cocok.")
                if c3.button("Hapus", key=f"vdel{f['id']}", use_container_width=True):
                    try:
                        (config.FILES_DIR / f["stored_name"]).unlink(missing_ok=True)
                    except OSError:
                        pass
                    database.delete_encrypted_file(f["id"], user)
                    ui.log("FILE", f"Arsip berkas #{f['id']} dihapus", level="WARN")
                    st.toast("Berkas dihapus dari vault.")
                    st.rerun()
                plain = st.session_state.get(f"vault_plain_{f['id']}")
                if plain is not None:
                    st.download_button(
                        f"Unduh {f['original_name']}",
                        plain,
                        file_name=_safe_download_name(f.get("original_name"), "vault_file.bin"),
                        mime=f["mime_type"] or "application/octet-stream",
                        key=f"vdl{f['id']}",
                        on_click="ignore",
                        type="primary",
                    )


def page_stego() -> None:
    ui.page_header(
        "Kriteria 6 — Steganografi Citra",
        "Penyisipan pesan LSB pada citra PNG",
        icon_name="image",
    )
    t_in, t_out = st.tabs(["Sisipkan Pesan (Encode)", "Ekstrak Pesan (Decode)"])

    with t_in:
        c1, c2 = st.columns([1.1, 1], gap="large")
        with c1:
            cover = st.file_uploader("Pilih citra sampul (PNG, BMP, JPG)", type=["png", "bmp", "jpg", "jpeg"], key="sg_cover")
            msg = st.text_area("Pesan rahasia yang akan disisipkan", height=130, key="sg_msg")
            pw = st.text_input("Passphrase tambahan (opsional)", type="password", key="sg_pw")
        with c2:
            with st.container(border=True):
                st.markdown("### Meter Kapasitas LSB")
                if cover:
                    cover_bytes = cover.getvalue()
                    cap = max(1, steganography.calculate_capacity(cover_bytes))
                    overhead = 80 if pw else 32
                    used = len(msg.encode("utf-8")) + overhead if msg else 0
                    pct = (used / cap) * 100.0
                    kind = "bad" if pct > 95 else ("warn" if pct > 75 else "ok")
                    ui.meter(
                        "Utilisasi Kanal RGB",
                        pct,
                        kind=kind,
                        subtitle=f"Terpakai ~{used:,} byte dari kapasitas {cap:,} byte ({cover.name})",
                    )
                    st.image(cover_bytes, caption="Pratinjau citra sampul", use_container_width=True)

        if st.button("Sisipkan Pesan ke Citra PNG", type="primary", disabled=cover is None, key="sg_go"):
            if not msg.strip():
                st.warning("Pesan rahasia tidak boleh kosong.")
            else:
                try:
                    out = steganography.embed_message_lsb(cover.getvalue(), msg, pw or None)
                    st.session_state.stego_out = (cover.getvalue(), out, cover.name)
                    ui.log("STEGO", f"{len(msg.encode())} byte disisipkan ke '{cover.name}'", ui.sha256_hex(out), "OK")
                    st.toast("Pesan berhasil disisipkan ke citra PNG lossless.")
                except Exception as exc:
                    st.error(f"Gagal menyisipkan pesan: {exc}")

        so = st.session_state.get("stego_out")
        if so:
            with st.container(border=True):
                st.markdown("### Perbandingan Visual Asli vs Stego")
                a, b = st.columns(2)
                a.image(so[0], caption=f"Citra Asli ({_format_bytes(len(so[0]))})", use_container_width=True)
                b.image(so[1], caption=f"Citra Stego PNG ({_format_bytes(len(so[1]))})", use_container_width=True)
                st.download_button(
                    "Unduh Citra Stego (krypt_stego.png)",
                    so[1],
                    file_name="krypt_stego.png",
                    mime="image/png",
                    key="sg_dl",
                    on_click="ignore",
                    type="primary",
                )

    with t_out:
        img = st.file_uploader("Unggah citra stego (PNG/BMP)", type=["png", "bmp"], key="sg_ext")
        pw_out = st.text_input("Passphrase (jika dipakai saat penyisipan)", type="password", key="sg_ext_pw")
        if st.button("Ekstrak Pesan Rahasia", type="primary", disabled=img is None, key="sg_ext_go"):
            try:
                text = steganography.extract_message_lsb(img.getvalue(), pw_out or None)
                ui.log("STEGO", f"Pesan diekstrak ({len(text)} karakter)", ui.sha256_hex(text), "OK")
                st.toast("Pesan tersembunyi berhasil diekstrak.")
                st.text_area("Pesan Tersembunyi", text, height=150)
            except Exception as exc:
                st.error(f"Gagal mengekstrak pesan: {exc}")


def page_database(user: str) -> None:
    ui.page_header(
        "Kriteria 5 — Basis Data Terenkripsi",
        "Audit enkripsi at-rest SQLite",
        icon_name="database",
    )
    raw = database.get_raw_records_for_inspection(user)
    t_raw, t_probe, t_compare = st.tabs(["Isi Mentah Tabel", "Uji Pencarian Byte (vault.db)", "Komparasi Ciphertext vs Plaintext"])

    with t_raw:
        for name in ("users", "secret_messages", "encrypted_files", "blockchain_ledger"):
            with st.container(border=True):
                st.markdown(f"**Tabel `{name}`** — {len(raw[name])} baris")
                if raw[name]:
                    st.dataframe(raw[name], use_container_width=True, hide_index=True)
                else:
                    st.caption("Belum ada rekaman pada tabel ini.")

    with t_probe:
        st.write(
            "Masukkan kata atau potongan kalimat rahasia yang pernah Anda simpan. Sistem akan memindai berkas biner "
            "`vault.db` secara langsung untuk membuktikan tidak ada plaintext rahasia yang bocor di disk."
        )
        needle = st.text_input("Kata kunci pencarian byte mentah", key="db_needle")
        if st.button("Pindai Berkas vault.db", type="primary", key="db_scan_go") and needle:
            blob = config.DB_PATH.read_bytes()
            found = needle.encode("utf-8") in blob
            ui.log("DB", f"Pencarian plaintext '{needle}' di vault.db: {'DITEMUKAN' if found else 'aman (nihil)'}", level="WARN" if found else "OK")
            if found:
                st.warning("String ditemukan (kemungkinan berasal dari kolom non-rahasia seperti judul laporan atau username).")
            else:
                st.success(f"Tidak ditemukan dalam {len(blob):,} byte `vault.db`. Seluruh isi rahasia tersimpan terenkripsi.")
            st.markdown("**Cuplikan 256 byte header `vault.db` (hex)**")
            st.code(blob[:256].hex(" "), language=None, wrap_lines=True)

    with t_compare:
        msgs = raw["secret_messages"]
        if not msgs:
            st.info("Belum ada laporan terenkripsi untuk dibandingkan.")
        else:
            opts = {f"#{m['id']} — {m['title']}": m for m in msgs}
            m = opts[st.selectbox("Pilih rekaman basis data", list(opts), key="dbc_sel")]
            c1, c2 = st.columns(2)
            vk = c1.text_input("Kunci Vigenere", type="password", key="dbvk")
            ak = c2.text_input("Passphrase AES-256", type="password", key="dbak")
            a, b = st.columns(2, gap="large")
            with a:
                with st.container(border=True):
                    st.markdown("### Tersimpan di Disk (Ciphertext)")
                    st.code(m["ciphertext"], language=None, wrap_lines=True)
            with b:
                with st.container(border=True):
                    st.markdown("### Hasil Dekripsi Memori")
                    if vk and ak:
                        try:
                            st.write(super_encryption.super_decrypt(m["ciphertext"], vk, ak))
                        except Exception:
                            st.error("Kunci salah atau token tidak valid.")
                    else:
                        st.caption("Masukkan kedua kunci di atas untuk membandingkan isi plaintext.")


def page_ledger(user: str) -> None:
    blockchain.ensure_genesis()
    ui.page_header(
        "Kriteria 7 — Ledger Blockchain",
        "Pencatatan aset penting & Proof-of-Work",
        icon_name="blocks",
    )
    report = blockchain.verify_chain()
    c1, c2, c3 = st.columns([2.2, 1, 1], vertical_alignment="center")
    with c1:
        if report.valid:
            st.markdown(
                ui.chip(f"Rantai Valid — {report.blocks_checked} blok diverifikasi ({report.elapsed_ms:.1f} ms)", "ok", dot=True),
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                ui.chip(f"Manipulasi Terdeteksi — {len(report.issues)} temuan", "bad", dot=True),
                unsafe_allow_html=True,
            )
    if c2.button("Verifikasi Rantai", use_container_width=True, key="bc_verify"):
        ui.log("LEDGER", f"Verifikasi rantai: valid={report.valid}", level="OK" if report.valid else "CRIT")
        st.toast("Audit rantai selesai." if report.valid else "Temuan integritas terdeteksi!")
        st.rerun()
    c3.download_button(
        "Ekspor JSON",
        blockchain.export_chain_json(),
        file_name="krypt_ledger.json",
        mime="application/json",
        key="bc_dl",
        on_click="ignore",
        use_container_width=True,
    )

    if not report.valid:
        for i in report.issues:
            st.error(f"Blok #{i.index} ({i.kind}): {i.detail}")

    chain = blockchain.get_chain()
    t_add, t_chain, t_lab = st.tabs(["Tambang & Catat Aset", f"Penjelajah Blok ({len(chain)})", "Lab Uji Manipulasi"])

    with t_add:
        with st.form("mine_form"):
            a1, a2 = st.columns(2)
            kind = a1.selectbox("Kategori aset", blockchain.ASSET_TYPES)
            name = a2.text_input("Nama / kode aset")
            desc = st.text_area("Detail / koordinat / sertifikat aset (dienkripsi AES-256-GCM)", height=105)
            go = st.form_submit_button("Tambang Blok PoW & Catat", type="primary")
        if go:
            if not name:
                st.warning("Nama aset wajib diisi.")
            else:
                with st.status("Menambang Proof-of-Work SHA-256...", expanded=False) as s_box:
                    r = blockchain.add_asset(name, kind, {"keterangan": desc, "jenis": kind}, owner=user)
                    ui.log("LEDGER", f"Blok #{r.block.index} ditambang ({r.attempts} hash)", r.block.current_hash, "OK")
                    s_box.update(
                        label=f"Blok #{r.block.index} tercatat (Nonce {r.block.nonce}, {r.attempts} percobaan dalam {r.elapsed_ms:.1f} ms)",
                        state="complete",
                    )
                st.toast(f"Blok #{r.block.index} berhasil ditambahkan ke rantai.")
                st.code(r.block.current_hash, language=None)

    with t_chain:
        for blk in reversed(chain):
            ok = report.block_status.get(blk.index) == "OK"
            with st.container(border=True):
                h_l, h_r = st.columns([3.5, 1.3], vertical_alignment="center")
                h_l.markdown(
                    f"**Blok #{blk.index} — {html.escape(blk.asset_name)}** "
                    + ui.chip("Terverifikasi PoW" if ok else "Rusak", "ok" if ok else "bad")
                    + ui.chip(f"Nonce {blk.nonce}"),
                    unsafe_allow_html=True,
                )
                if h_r.button("Inspeksi & Dekripsi", key=f"bd{blk.index}", type="primary", use_container_width=True):
                    _modal_inspect_block(blk, ok)
                ui.kv_grid([
                    ("Waktu UTC", blk.timestamp),
                    ("Hash Blok", blk.current_hash),
                    ("Hash Sebelumnya", blk.previous_hash),
                    ("Payload AES-GCM", blk.encrypted_asset_metadata[:72] + "..."),
                ])

    with t_lab:
        st.write(
            "Simulasikan penyerang yang mengubah atau menghapus data langsung di SQLite, lalu amati "
            "bagaimana hash berantai, AES-GCM, dan anchor HMAC mendeteksinya seketika."
        )
        l1, l2 = st.columns(2)
        idx = l1.selectbox("Target Blok", [b.index for b in chain], key="tamper_idx")
        mode = l2.selectbox("Skenario Serangan", list(blockchain.TAMPER_MODES), format_func=lambda k: blockchain.TAMPER_MODES[k], key="tamper_mode")
        b1, b2 = st.columns(2)
        if b1.button("Jalankan Simulasi Serangan", type="primary", use_container_width=True, key="tamper_run"):
            msg = blockchain.simulate_tampering(int(idx), mode)
            ui.log("LEDGER", f"Simulasi serangan blok #{idx}: {msg}", level="CRIT")
            st.toast(f"Serangan dijalankan pada Blok #{idx}.")
            st.rerun()
        if b2.button("Pulihkan / Reset ke Genesis", use_container_width=True, key="tamper_reset"):
            blockchain.reset_ledger()
            ui.log("LEDGER", "Ledger di-reset bersih ke Blok Genesis #0", level="WARN")
            st.toast("Ledger dipulihkan ke Genesis #0.")
            st.rerun()


def page_hardware(status: dongle_guard.DongleStatus) -> None:
    ui.page_header(
        "Kriteria 1 — Manajemen Perangkat",
        "Kunci perangkat keras D:\\",
        icon_name="key",
    )
    c1, c2 = st.columns([1.25, 1], gap="large")
    with c1:
        with st.container(border=True):
            st.markdown("### Detail Kunci Aktif")
            ui.kv_grid([
                ("Drive", status.path or "-"),
                ("Tipe Drive", status.drive_type or "-"),
                ("Volume Serial", status.volume_serial or "-"),
                ("Label Token", status.label or "-"),
                ("ID Sesi Kunci", status.dongle_id or "-"),
                ("Diterbitkan", status.issued_at or "-"),
                ("Kedaluwarsa", status.expires_at or "Tidak pernah"),
                ("Algoritma", "HMAC-SHA256 (HKDF) + ikatan serial volume"),
            ])
    with c2:
        with st.container(border=True):
            st.markdown("### Brankas Kredensial di D:\\")
            ui.kv_grid([
                ("Direktori", str(config.auth_dir())),
                ("Basis Data", config.AUTH_DB_FILENAME),
                ("Master Secret", config.MASTER_SECRET_FILENAME),
                ("Token HMAC", config.DONGLE_FILENAME),
                ("Operator", str(database.count_operators())),
            ])
            st.divider()
            if st.button("Kunci Vault Sekarang", use_container_width=True, key="hw_lock"):
                ui.log("AUTH", "Vault dikunci manual dari halaman Kunci Perangkat", level="INFO")
                _clear_identity_session()
                st.rerun()


def page_operators(user: str, status: dongle_guard.DongleStatus) -> None:
    """[06] MANAJEMEN OPERATOR // ENROLL_NEW_IDENTITY - authenticated sessions only."""
    ui.page_header(
        "[06] MANAJEMEN OPERATOR // ENROLL_NEW_IDENTITY",
        "Manajemen operator",
        icon_name="user",
    )
    roster = database.list_operators()
    t_enroll, t_roster = st.tabs(["ENROLL_NEW_IDENTITY", f"Operator di D:\\ ({len(roster)})"])

    with t_enroll:
        c1, c2 = st.columns([1, 1.15], gap="large")
        with c1:
            with st.container(border=True):
                st.markdown("### Data Operator Baru")
                ru = st.text_input("Nama pengguna (3-32 karakter: a-z, 0-9, _ . -)", key="rg_user")
                rp = st.text_input("Kata sandi (minimal 8 karakter, huruf + angka)", type="password", key="rg_pw")
                s_pct, s_kind, _ = _password_strength(rp)
                ui.meter("Kekuatan Kata Sandi", s_pct, kind=s_kind)
                rp2 = st.text_input("Ulangi kata sandi", type="password", key="rg_pw2")
            with st.container(border=True):
                st.markdown("### Otorisasi Sponsor")
                sp = st.text_input(f"Passkey Anda ({user}) untuk konfirmasi", type="password", key="rg_sponsor_pw")
        with c2:
            with st.container(border=True):
                st.markdown("### Pemindaian Wajah Operator Baru")
                rface, _ = _capture_face("rg", mode="register", ready=True)

        if st.button("Daftarkan Operator ke D:\\", type="primary", use_container_width=True, key="rg_submit"):
            if rp != rp2:
                st.error("Kedua kata sandi tidak sama.")
            elif not (ru and rp and rface and sp):
                st.warning("Lengkapi nama pengguna, kata sandi, foto wajah, dan passkey konfirmasi Anda.")
            else:
                with st.status("Menyegel template biometrik & menulis ke D:\\...", expanded=True) as st_box:
                    res = auth_biometric.register_user(
                        ru.strip().lower(), rp, rface, enrolled_by=user, enroller_password=sp,
                    )
                    if res.drive_missing:
                        _handle_drive_loss("pendaftaran operator")
                    ui.log("AUTH", f"Enroll {ru} oleh {user}: {res.message}", ui.sha256_hex(rface),
                           "OK" if res.success else "WARN")
                    if res.success:
                        st_box.update(label="Operator terdaftar di D:\\", state="complete", expanded=False)
                        face_scanner.clear_live_cache("rg")
                        for k in ("rg_user", "rg_pw", "rg_pw2", "rg_sponsor_pw"):
                            st.session_state.pop(k, None)
                        st.toast(f"Operator '{res.username}' berhasil didaftarkan ke D:\\.")
                        st.rerun()
                    st_box.update(label="Pendaftaran ditolak", state="error", expanded=False)
                    st.error(res.message)

    with t_roster:
        if not roster:
            st.info("Belum ada operator.")
        else:
            st.dataframe(
                [
                    {
                        "Username": r["username"],
                        "Peran": r["role"],
                        "Didaftarkan oleh": r["enrolled_by"] or "(bootstrap)",
                        "Dibuat": r["created_at"],
                        "Login terakhir": r["last_login"] or "-",
                    }
                    for r in roster
                ],
                use_container_width=True,
                hide_index=True,
            )
        st.caption(f"Sumber: {config.auth_db_path()} (verifier, salt & template biometrik tidak ditampilkan).")


def page_logs() -> None:
    ui.page_header(
        "Audit & Telemetri",
        "Log aktivitas kriptografi",
        icon_name="activity",
    )
    c1, c2, c3, c4 = st.columns([1.6, 1.4, 0.8, 0.8], vertical_alignment="bottom")
    lvl = c1.segmented_control("Filter Level", ["Semua", "OK", "WARN", "CRIT"], default="Semua", key="log_lvl") or "Semua"
    q = c2.text_input("Cari kata kunci / modul", placeholder="contoh: AUTH, LEDGER...", key="log_q")
    raw_txt = "\n".join(
        f"{r['time']} [{r['level']}] {r['subsys']} - {r['msg']}" + (f" (sha256:{r['digest']})" if r.get("digest") else "")
        for r in st.session_state.get("kv_logs", [])
    )
    c3.download_button(
        "Ekspor .txt",
        raw_txt or "-",
        file_name="krypt_vault_audit.txt",
        mime="text/plain",
        key="log_dl",
        on_click="ignore",
        use_container_width=True,
    )
    if c4.button("Bersihkan", use_container_width=True, key="log_clear"):
        st.session_state.kv_logs = []
        ui.log("SYSTEM", "Riwayat log dibersihkan oleh operator", level="INFO")
        st.rerun()
    ui.render_log(level_filter=lvl, query=q)


# =========================================================================== #
# Router
# =========================================================================== #
def main() -> None:
    # ---- GATE_01: strict USB D:\ check before ANY login screen or DB access ---- #
    status = dongle_guard.scan_for_dongle()
    sig = (status.valid, status.dongle_id, status.halt_code)
    if st.session_state.dongle_sig != sig:
        st.session_state.dongle_sig = sig
        ui.log(
            "DONGLE",
            f"USB D:\\ terverifikasi ({status.label})" if status.valid else f"{status.banner} - {status.message}",
            status.dongle_id,
            "OK" if status.valid else "CRIT",
        )

    if not status.valid:
        _clear_identity_session()
        screen_lockdown(status)
        return

    # ---- D:\ present: databases may be opened from here on ---------------- #
    try:
        database.init_db()
        bootstrap_required = database.is_bootstrap_required()
    except config.DongleDriveMissing:
        _clear_identity_session()
        st.rerun()

    if bootstrap_required:
        _clear_identity_session()
        screen_bootstrap(status)
        return
    if not st.session_state.user:
        screen_identity(status)
        return

    # ---- GATE_03: session must stay bound to the same physical D:\ ---------- #
    user = st.session_state.user
    if st.session_state.get("session_dongle_id") != status.dongle_id or not auth_biometric.validate_session(user):
        ui.log("DONGLE", "Sesi tidak lagi terikat ke USB D:\\ yang sama - sesi diinvalidasi", level="CRIT")
        _clear_identity_session()
        st.rerun()
    _dongle_watch(status.dongle_id, user)

    if st.session_state.get("page") not in PAGES:
        st.session_state.page = "Ringkasan"

    with st.sidebar:
        ui.brand()
        st.write("")
        page = st.radio("Navigasi", PAGES, key="page", label_visibility="collapsed")
        st.divider()
        sim_txt = f"Kecocokan wajah {st.session_state.similarity:.0%}" if st.session_state.similarity is not None else ""
        ui.operator(user, sim_txt)
        st.write("")
        if st.button("Kunci & Keluar", use_container_width=True, key="sb_logout"):
            ui.log("AUTH", f"Operator '{user}' mengunci sesi", level="INFO")
            _clear_identity_session()
            st.toast("Sesi dikunci.")
            st.rerun()

    _render_topbar(status, show_brand=False)

    try:
        if page == "Ringkasan":
            page_overview(user, status)
        elif page == "Enkripsi Teks":
            page_text(user)
        elif page == "Enkripsi Berkas":
            page_files(user)
        elif page == "Steganografi":
            page_stego()
        elif page == "Basis Data":
            page_database(user)
        elif page == "Ledger Aset":
            page_ledger(user)
        elif page == "Manajemen Operator":
            page_operators(user, status)
        elif page == "Kunci Perangkat":
            page_hardware(status)
        else:
            page_logs()
    except config.DongleDriveMissing:
        _handle_drive_loss(f"membuka halaman '{page}'")


main()
