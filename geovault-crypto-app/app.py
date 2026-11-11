"""
Krypt Vault - Sistem Brankas Bukti Forensik Siber & Dokumen Intelijen
=====================================================================

Alur aplikasi:
  1. Kunci perangkat keras  : flashdisk USB (.krypt_dongle HMAC-SHA256 + volume serial,
                              atau otorisasi serial Plug-and-Play USB fisik)
  2. Identitas & biometrik  : PBKDF2-HMAC-SHA256 + template wajah 128x128 disegel AES-128-EAX
  3. Ruang kerja vault      :
       - Enkripsi teks   : Super enkripsi Extended Vigenere (klasik) + AES-256-CBC (modern)
       - Enkripsi berkas : ChaCha20 stream cipher (.krypt.enc)
       - Steganografi    : LSB pada citra PNG
       - Basis data      : penyimpanan ciphertext at-rest di SQLite + audit
       - Ledger aset     : blockchain SHA-256 Proof-of-Work + AES-256-GCM
"""

from __future__ import annotations

import html
import json
import re
import secrets
from typing import Optional

import streamlit as st

import config
import database
import ui_theme as ui
from modules import (
    auth_biometric,
    blockchain,
    dongle_guard,
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
    "pnp_usb_serial": None,
    "kv_theme": "dark",
    "last_auth_sim": None,
    "last_usb_snapshot": None,
}.items():
    st.session_state.setdefault(_k, _v)

ui.inject_theme()
ui.init_logs()
database.init_db()

PAGES = [
    "Ringkasan",
    "Enkripsi Teks",
    "Enkripsi Berkas",
    "Steganografi",
    "Basis Data",
    "Ledger Aset",
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


def _format_bytes(num: int) -> str:
    if num < 1024:
        return f"{num} B"
    if num < 1024 * 1024:
        return f"{num / 1024:.1f} KB"
    return f"{num / (1024 * 1024):.2f} MB"


def _password_strength(pw: str) -> tuple[float, str, str]:
    if not pw:
        return 0.0, "warn", "Masukkan minimal 8 karakter dengan huruf dan angka."
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
        return float(score), "ok", "Kuat - memenuhi kebijakan kompleksitas kata sandi."
    if score >= 55:
        return float(score), "info", "Cukup - tambahkan huruf kapital/simbol untuk keamanan ekstra."
    return float(score), "bad", "Lemah - gunakan minimal 8 karakter campuran huruf dan angka."


def _capture_face(key: str) -> Optional[bytes]:
    """Real face acquisition: webcam snapshot or uploaded photo."""
    mode = st.segmented_control(
        "Sumber citra wajah",
        ["Kamera", "Unggah foto"],
        default="Kamera",
        key=f"{key}_mode",
    ) or "Kamera"
    if mode == "Kamera":
        shot = st.camera_input("Posisikan wajah di tengah bingkai, lalu ambil foto", key=f"{key}_cam")
        return shot.getvalue() if shot else None
    up = st.file_uploader("Foto wajah (PNG/JPG)", type=["png", "jpg", "jpeg"], key=f"{key}_up")
    return up.getvalue() if up else None


def _active_dongle_status() -> dongle_guard.DongleStatus:
    return dongle_guard.scan_for_dongle(pnp_volume_serial=st.session_state.get("pnp_usb_serial"))


def _render_topbar(status: dongle_guard.DongleStatus, show_brand: bool = True) -> None:
    """Persistent application bar with hardware status badge, log popover, and theme toggle."""
    theme_mode = ui.get_theme()
    next_label = "Mode Terang" if theme_mode == "dark" else "Mode Gelap"
    logs_count = len(st.session_state.get("kv_logs", []))

    c_left, c_stat, c_log, c_theme = st.columns([2.1, 1.8, 0.75, 0.85], vertical_alignment="center")
    with c_left:
        if show_brand:
            ui.brand()
        else:
            st.markdown(
                ui.chip(f"Halaman: {st.session_state.page}", "info", icon_name="shield"),
                unsafe_allow_html=True,
            )
    with c_stat:
        if status.valid:
            st.markdown(
                ui.chip(f"Dongle Aktif: {status.label or 'USB'}", "ok", dot=True),
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                ui.chip("Gate 01 Terkunci: Menunggu USB", "warn", dot=True),
                unsafe_allow_html=True,
            )
    with c_log:
        with st.popover(f"Log ({logs_count})", use_container_width=True):
            st.markdown("**Telemetri Aktivitas Terbaru**")
            ui.render_log(limit=25)
            if st.button("Bersihkan log", key="top_clear_logs", use_container_width=True):
                st.session_state.kv_logs = []
                ui.log("SYSTEM", "Riwayat log sesi dibersihkan", level="INFO")
                st.rerun()
    with c_theme:
        if st.button(next_label, key="top_theme_toggle", use_container_width=True):
            ui.toggle_theme()
            st.rerun()


@st.fragment(run_every=4)
def _dongle_watch(expected_id: Optional[str]) -> None:
    """Re-scan the USB bus periodically; lock the app automatically if the key is removed."""
    status = _active_dongle_status()
    if not status.valid or status.dongle_id != expected_id:
        ui.log("DONGLE", "Kunci perangkat keras dicabut - sesi dikunci otomatis", level="CRIT")
        st.session_state.user = None
        st.session_state.pnp_usb_serial = None
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
# Gate 1 - Hardware key
# =========================================================================== #
@st.fragment(run_every=3)
def _usb_live_monitor(known_usb_drives: tuple[str, ...], active_pnp: Optional[str]) -> None:
    """Auto-detect USB insertion/removal without requiring manual reload."""
    live_status = dongle_guard.scan_for_dongle(pnp_volume_serial=active_pnp)
    if live_status.valid:
        st.rerun(scope="app")
    usb_now = tuple(d["drive"] for d in dongle_guard.list_all_drives_for_provisioning() if d.get("is_usb"))
    if usb_now != known_usb_drives:
        st.rerun(scope="app")


def screen_hardware_gate(status: dongle_guard.DongleStatus) -> None:
    _render_topbar(status, show_brand=True)
    ui.steps(1)
    ui.page_header(
        "Gerbang Keamanan 01",
        "Hubungkan kunci perangkat keras",
        "Krypt Vault mensyaratkan kunci USB fisik yang terverifikasi HMAC-SHA256 atau otorisasi serial volume "
        "sebelum akses operator dibuka. Saat perangkat dilepas, sesi akan terkunci otomatis.",
        icon_name="usb",
    )

    if status.failures:
        st.error(
            "Token ditemukan namun verifikasi HMAC gagal: "
            + "; ".join(f"{_short(k, 24)} ({v})" for k, v in status.failures.items())
        )

    drives = dongle_guard.list_all_drives_for_provisioning()
    usb = [d for d in drives if d.get("is_usb")]
    _usb_live_monitor(tuple(d["drive"] for d in usb), st.session_state.get("pnp_usb_serial"))

    left, right = st.columns([1.45, 1], gap="large")
    with left:
        with st.container(border=True):
            h1, h2 = st.columns([2.2, 1], vertical_alignment="center")
            h1.markdown("### Pemindai Bus USB & Partisi")
            if h2.button("Pindai Ulang", use_container_width=True, key="g1_rescan"):
                st.rerun()

            diag = dongle_guard.get_usb_diagnostics(st.session_state.get("pnp_usb_serial"))
            rows_html = []
            for row in diag:
                badge = ui.chip(
                    row["hmac_challenge"],
                    row.get("state_kind", "standby"),
                    dot=row["is_valid"],
                )
                rows_html.append(
                    f"<tr><td class='mono'>{html.escape(row['mount'])}</td>"
                    f"<td>{html.escape(row['type'])}</td>"
                    f"<td class='mono'>{html.escape(row['volume_serial'])}</td>"
                    f"<td>{badge}</td></tr>"
                )
            st.markdown(
                "<table class='kv-table'><tr><th>Drive / Lokasi</th><th>Kategori</th>"
                f"<th>Serial</th><th>Status Autentikasi</th></tr>{''.join(rows_html)}</table>",
                unsafe_allow_html=True,
            )

            st.write("")
            if usb:
                st.success(f"Terdeteksi {len(usb)} drive USB removable siap digunakan.")
                c_sel, c_lbl = st.columns(2)
                target = c_sel.selectbox("Pilih USB Flash Drive", [d["drive"] for d in usb], key="g1_usb_sel")
                label = c_lbl.text_input("Label Kunci", value="Krypt Analis Key", key="g1_usb_lbl")
                b_perm, b_pnp = st.columns(2)
                if b_perm.button("Tulis Token Permanen (.krypt_dongle)", type="primary", use_container_width=True):
                    ok, msg = dongle_guard.provision_drive(target, label=label)
                    ui.log("DONGLE", msg, level="OK" if ok else "CRIT")
                    if ok:
                        st.toast("Token USB HMAC-SHA256 berhasil dibuat.")
                        st.rerun()
                    else:
                        st.error(msg)
                if b_pnp.button("Otorisasi Plug-and-Play (Tanpa File)", use_container_width=True):
                    res = dongle_guard.authorize_physical_usb(target)
                    if res.valid:
                        st.session_state.pnp_usb_serial = res.volume_serial
                        ui.log("DONGLE", res.message, res.dongle_id, "OK")
                        st.toast("USB fisik diotorisasi lewat HMAC serial volume.")
                        st.rerun()
                    else:
                        st.error(res.message)
            else:
                st.markdown(ui.chip("Belum ada USB flash drive terpasang", "warn"), unsafe_allow_html=True)
                st.caption(
                    "Colokkan USB flash drive ke port komputer. Pemindai otomatis mendeteksi drive baru setiap 3 detik; "
                    "drive C:\\ sistem lokal selalu dikecualikan."
                )

    with right:
        with st.container(border=True):
            st.markdown("### Token Virtual (Demo Offline)")
            st.caption(
                "Tidak membawa flashdisk? Gunakan token HMAC-SHA256 virtual di folder lokal `virtual_usb` "
                "untuk demonstrasi dan presentasi."
            )
            if st.button("Aktifkan Token Virtual", type="primary", use_container_width=True, key="g1_virtual"):
                dongle_guard.mount_virtual_dongle(label="Token Virtual Presentasi")
                ui.log("DONGLE", "Token virtual presentasi diaktifkan", level="WARN")
                st.toast("Token virtual aktif. Melanjutkan ke Gerbang 02...")
                st.rerun()

        with st.container(border=True):
            st.markdown("### Mekanisme Perlindungan")
            st.markdown(
                "1. **Anti-Kloning Volume**: Token `.krypt_dongle` diikat ke serial hardware USB.\n"
                "2. **Integritas HMAC-SHA256**: Perubahan 1 karakter pada token langsung ditolak.\n"
                "3. **Plug-and-Play Opsional**: Otorisasi serial runtime tanpa menulis berkas ke flashdisk.\n"
                "4. **Auto-Lock**: Mencabut USB otomatis mengunci sesi aktif."
            )


# =========================================================================== #
# Gate 2 - Identity & biometrics
# =========================================================================== #
def screen_identity(status: dongle_guard.DongleStatus) -> None:
    _dongle_watch(status.dongle_id)
    _render_topbar(status, show_brand=True)
    ui.steps(2)
    ui.page_header(
        "Gerbang Keamanan 02",
        "Verifikasi identitas dan biometrik",
        "Kombinasi faktor pengetahuan (PBKDF2-HMAC-SHA256, 600.000 iterasi) dan faktor wajah (matriks optik 128x128 "
        "terenkripsi AES-128-EAX yang hanya bisa dibuka menggunakan kunci turunan kata sandi).",
        icon_name="user",
    )

    chips = (
        ui.chip(f"Kunci: {status.label or '-'}", "ok", icon_name="usb")
        + ui.chip(f"Serial: {status.volume_serial or 'virtual'}", "info")
        + ui.chip(f"Lokasi: {_short(status.path, 28)}")
    )
    c_chips, c_sw = st.columns([3.5, 1], vertical_alignment="center")
    c_chips.markdown(chips, unsafe_allow_html=True)
    if c_sw.button("Ganti / Cabut Kunci", use_container_width=True, key="g2_unmount"):
        st.session_state.pnp_usb_serial = None
        if dongle_guard.is_virtual_dongle_mounted():
            dongle_guard.unmount_virtual_dongle()
        st.rerun()

    st.write("")
    tab_in, tab_up = st.tabs(["Masuk Operator", "Daftarkan Operator Baru"])

    with tab_in:
        if database.count_users() == 0:
            st.info("Belum ada operator terdaftar. Silakan buka tab 'Daftarkan Operator Baru' untuk membuat akun pertama.")
        c1, c2 = st.columns([1, 1.15], gap="large")
        with c1:
            with st.container(border=True):
                st.markdown("### Faktor 1 — Kredensial")
                user = st.text_input("Nama pengguna", key="li_user", placeholder="contoh: analis_01")
                pw = st.text_input("Kata sandi", type="password", key="li_pw", placeholder="Masukkan kata sandi")
                if st.session_state.get("last_auth_sim") is not None:
                    sim_val = float(st.session_state.last_auth_sim)
                    ui.meter(
                        "Skor Kemiripan Wajah Terakhir",
                        sim_val * 100.0,
                        threshold_pct=auth_biometric.MATCH_THRESHOLD * 100.0,
                        kind="ok" if sim_val >= auth_biometric.MATCH_THRESHOLD else "bad",
                        subtitle=f"Ambang batas sistem: {auth_biometric.MATCH_THRESHOLD:.0%} (garis penanda)",
                    )
        with c2:
            with st.container(border=True):
                st.markdown("### Faktor 2 — Biometrik Wajah")
                face = _capture_face("li")
                st.caption(
                    f"Penyelarasan spasial multi-skala toleran terhadap pergeseran alami (ambang batas: "
                    f"{auth_biometric.MATCH_THRESHOLD:.0%})."
                )

        if st.button("Verifikasi dan Masuk ke Vault", type="primary", use_container_width=True, key="li_submit"):
            if not (user and pw and face):
                st.warning("Lengkapi nama pengguna, kata sandi, dan citra wajah terlebih dahulu.")
            else:
                with st.status("Memverifikasi dua faktor autentikasi...", expanded=True) as st_box:
                    st.write("Menghitung PBKDF2-HMAC-SHA256 (600.000 iterasi)...")
                    res = auth_biometric.authenticate_user(user.strip().lower(), pw, face)
                    digest = ui.sha256_hex(face)
                    if res.success:
                        st.write("Mendekripsi template AES-128-EAX & mencocokkan wajah...")
                        st_box.update(label="Autentikasi berhasil", state="complete", expanded=False)
                        st.session_state.last_auth_sim = None
                        ui.log("AUTH", f"Login berhasil: {res.username} (kemiripan {res.similarity:.1%})", digest, "OK")
                        st.session_state.user = res.username
                        st.session_state.similarity = res.similarity
                        st.session_state.page = "Ringkasan"
                        st.toast(f"Selamat datang, {res.username}. Vault terbuka.")
                        st.rerun()
                    else:
                        st_box.update(label="Verifikasi ditolak", state="error", expanded=False)
                        st.session_state.last_auth_sim = res.similarity
                        ui.log("AUTH", f"Login ditolak untuk {user}: {res.message}", digest, "CRIT")
                        sim_note = (
                            f" (Kemiripan wajah: {res.similarity:.1%}, minimum {auth_biometric.MATCH_THRESHOLD:.0%})"
                            if res.similarity is not None
                            else ""
                        )
                        st.error(res.message + sim_note)

    with tab_up:
        c1, c2 = st.columns([1, 1.15], gap="large")
        with c1:
            with st.container(border=True):
                st.markdown("### Data Operator Baru")
                ru = st.text_input("Nama pengguna (3-32 karakter: a-z, 0-9, _ . -)", key="rg_user")
                rp = st.text_input("Kata sandi (minimal 8 karakter, huruf + angka)", type="password", key="rg_pw")
                s_pct, s_kind, s_msg = _password_strength(rp)
                ui.meter("Kekuatan Kata Sandi", s_pct, kind=s_kind, subtitle=s_msg)
                rp2 = st.text_input("Ulangi kata sandi", type="password", key="rg_pw2")
        with c2:
            with st.container(border=True):
                st.markdown("### Pendaftaran Template Wajah")
                rface = _capture_face("rg")
                st.caption("Pastikan pencahayaan merata dan wajah berada di tengah bingkai kamera/foto.")

        if st.button("Daftarkan Operator", type="primary", use_container_width=True, key="rg_submit"):
            if rp != rp2:
                st.error("Kedua kata sandi tidak sama.")
            elif not (ru and rp and rface):
                st.warning("Lengkapi nama pengguna, kata sandi, dan foto wajah.")
            else:
                with st.status("Mendaftarkan identitas & menyegel template biometrik...", expanded=True) as st_box:
                    res = auth_biometric.register_user(ru.strip().lower(), rp, rface)
                    digest = ui.sha256_hex(rface)
                    ui.log("AUTH", f"Registrasi {ru}: {res.message}", digest, "OK" if res.success else "WARN")
                    if res.success:
                        st_box.update(label="Operator terdaftar", state="complete", expanded=False)
                        st.toast("Pendaftaran operator berhasil. Silakan masuk di tab Masuk Operator.")
                        st.success(res.message + " Silakan masuk melalui tab Masuk Operator.")
                    else:
                        st_box.update(label="Pendaftaran ditolak", state="error", expanded=False)
                        st.error(res.message)


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
        "Ringkasan real-time brankas, akses cepat modul kriptografi, dan audit status ketujuh kriteria.",
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
        ("Enkripsi Teks", "Super Enkripsi", "Extended Vigenere + AES-256-CBC untuk catatan rahasia."),
        ("Enkripsi Berkas", "Stream ChaCha20", "Segel berkas biner ke amplop mandiri .krypt.enc."),
        ("Steganografi", "Sisip Citra PNG", "Sembunyikan teks rahasia ke bit LSB kanal RGB."),
        ("Ledger Aset", "Blockchain PoW", "Catat aset kritis dengan AES-GCM & hash berantai."),
    ]
    for col, (target_page, heading, desc) in zip(qa_cols, quick_items):
        with col:
            with st.container(border=True):
                st.markdown(f"**{heading}**")
                st.caption(desc)
                if st.button("Buka modul", key=f"qa_{target_page}", use_container_width=True):
                    st.session_state.page = target_page
                    st.rerun()

    st.write("")
    c1, c2 = st.columns([1.6, 1], gap="large")
    with c1:
        with st.container(border=True):
            st.markdown("### Pemetaan 7 Kriteria Kriptografi")
            rows = [
                ("1. Login biometrik & dongle", "HMAC-SHA256 / Serial USB + Wajah 128x128", "Kunci Perangkat"),
                ("2. Login algoritma kriptografi", "PBKDF2-HMAC-SHA256 (600k) + AES-128-EAX", "Gerbang Masuk"),
                ("3. Super enkripsi teks", "Extended Vigenere (Mod 256) + AES-256-CBC", "Enkripsi Teks"),
                ("4. Enkripsi berkas berbeda", "ChaCha20 Stream Cipher + SHA-256 (.krypt.enc)", "Enkripsi Berkas"),
                ("5. Enkripsi basis data", "Ciphertext / BLOB / Hash at-rest di SQLite", "Basis Data"),
                ("6. Steganografi gambar", "LSB 24-bit RGB + PNG Lossless + Passphrase", "Steganografi"),
                ("7. Blockchain aset penting", "SHA-256 PoW ('00') + AES-256-GCM + Anchor", "Ledger Aset"),
            ]
            body = "".join(f"<tr><td>{a}</td><td class='mono'>{b}</td><td>{c}</td></tr>" for a, b, c in rows)
            st.markdown(
                f"<table class='kv-table'><tr><th>Kriteria</th><th>Algoritma</th><th>Modul</th></tr>{body}</table>",
                unsafe_allow_html=True,
            )
    with c2:
        with st.container(border=True):
            st.markdown("### Telemetri Sesi Aktif")
            sim_str = f"{st.session_state.similarity:.1%}" if st.session_state.similarity is not None else "-"
            ui.kv_grid([
                ("Operator", user),
                ("Skor Biometrik", sim_str),
                ("Kunci Aktif", status.label or "-"),
                ("ID Dongle", (status.dongle_id or "-")[:18]),
                ("Volume Serial", status.volume_serial or "virtual"),
                ("Waktu Verifikasi", f"{report.elapsed_ms:.1f} ms"),
            ])


def page_text(user: str) -> None:
    ui.page_header(
        "Kriteria 3 — Pesan Rahasia",
        "Super enkripsi teks (Klasik + Modern)",
        "Teks dienkripsi dua tahap berurutan: Extended Vigenere (modulo 256) lalu AES-256-CBC dengan kunci turunan PBKDF2, "
        "salt dan IV acak, serta padding PKCS#7 sebelum disimpan ke SQLite.",
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
        "Berkas biner dienkripsi aliran byte dengan ChaCha20 (kunci 256-bit PBKDF2 + nonce 96-bit) dan dibungkus menjadi "
        "paket mandiri `.krypt.enc` berisi metadata serta hash SHA-256 untuk cek integritas otomatis.",
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
                st.download_button(f"Unduh {name}.krypt.enc", pkg, file_name=f"{name}.krypt.enc", type="primary")

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
            st.download_button(f"Unduh {meta['original_name']}", plain, file_name=meta["original_name"], type="primary")

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
                        file_name=f["original_name"],
                        mime=f["mime_type"] or "application/octet-stream",
                        key=f"vdl{f['id']}",
                        type="primary",
                    )


def page_stego() -> None:
    ui.page_header(
        "Kriteria 6 — Steganografi Citra",
        "Penyisipan pesan LSB pada citra PNG",
        "Pesan disembunyikan ke Least Significant Bit (LSB) kanal RGB tanpa mengubah tampilan kasat mata, "
        "dan dapat dilindungi passphrase enkripsi tambahan sebelum disisipkan.",
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
                else:
                    st.caption("Unggah citra sampul untuk menghitung kapasitas penyisipan piksel LSB secara otomatis.")

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
                st.download_button("Unduh Citra Stego (krypt_stego.png)", so[1], file_name="krypt_stego.png", mime="image/png", type="primary")

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
        "Seluruh payload rahasia di `storage/vault.db` disimpan dalam bentuk hash verifier, BLOB AES-128-EAX, "
        "ciphertext Vigenere+AES, dan tag AES-256-GCM sehingga tidak terbaca sebagai plaintext.",
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
        f"Setiap aset ditambang menggunakan SHA-256 Proof-of-Work (awalan '{blockchain.HASH_PREFIX}'), "
        "metadatanya disegel AES-256-GCM, serta dijaga oleh jangkar tip HMAC-SHA256.",
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
    c3.download_button("Ekspor JSON", blockchain.export_chain_json(), file_name="krypt_ledger.json", use_container_width=True)

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
        "Kunci perangkat keras aktif",
        "Pantau informasi dongle aktif, inisialisasi USB cadangan, atau alihkan mode token.",
        icon_name="key",
    )
    c1, c2 = st.columns([1.25, 1], gap="large")
    with c1:
        with st.container(border=True):
            st.markdown("### Detail Token Aktif")
            mode_label = (
                "USB Plug-and-Play (Serial Runtime HMAC)"
                if (status.dongle_id or "").startswith("PNP-")
                else ("Token Virtual Presentasi" if not status.volume_serial else "Token Permanen (.krypt_dongle)")
            )
            ui.kv_grid([
                ("Label", status.label or "-"),
                ("Mode", mode_label),
                ("ID Kunci", status.dongle_id or "-"),
                ("Lokasi", status.path or "-"),
                ("Volume Serial", status.volume_serial or "tidak terikat (virtual)"),
                ("Diterbitkan", status.issued_at or "-"),
                ("Algoritma", "HMAC-SHA256, kunci turunan HKDF"),
            ])
    with c2:
        with st.container(border=True):
            st.markdown("### Inisialisasi Flashdisk Tambahan")
            usb = [d for d in dongle_guard.list_all_drives_for_provisioning() if d.get("is_usb")]
            if usb:
                target = st.selectbox("Pilih USB", [d["drive"] for d in usb], key="hw_add_sel")
                if st.button("Inisialisasi (.krypt_dongle)", type="primary", use_container_width=True, key="hw_add_go"):
                    ok, msg = dongle_guard.provision_drive(target)
                    ui.log("DONGLE", msg, level="OK" if ok else "CRIT")
                    (st.success if ok else st.error)(msg)
            else:
                st.caption("Tidak ada flashdisk removable tambahan yang terpasang.")

            if st.session_state.get("pnp_usb_serial") or dongle_guard.is_virtual_dongle_mounted():
                st.divider()
                if st.button("Nonaktifkan Kunci Sementara & Kunci Vault", use_container_width=True, key="hw_drop"):
                    st.session_state.pnp_usb_serial = None
                    if dongle_guard.is_virtual_dongle_mounted():
                        dongle_guard.unmount_virtual_dongle()
                    st.session_state.user = None
                    st.rerun()


def page_logs() -> None:
    ui.page_header(
        "Audit & Telemetri",
        "Log aktivitas kriptografi",
        "Catatan real-time operasi autentikasi, enkripsi, dan verifikasi integritas pada sesi aktif.",
        icon_name="activity",
    )
    c1, c2, c3, c4 = st.columns([1.6, 1.4, 0.8, 0.8], vertical_alignment="bottom")
    lvl = c1.segmented_control("Filter Level", ["Semua", "OK", "WARN", "CRIT"], default="Semua", key="log_lvl") or "Semua"
    q = c2.text_input("Cari kata kunci / modul", placeholder="contoh: AUTH, LEDGER...", key="log_q")
    raw_txt = "\n".join(
        f"{r['time']} [{r['level']}] {r['subsys']} - {r['msg']}" + (f" (sha256:{r['digest']})" if r.get("digest") else "")
        for r in st.session_state.get("kv_logs", [])
    )
    c3.download_button("Ekspor .txt", raw_txt or "-", file_name="krypt_vault_audit.txt", use_container_width=True)
    if c4.button("Bersihkan", use_container_width=True, key="log_clear"):
        st.session_state.kv_logs = []
        ui.log("SYSTEM", "Riwayat log dibersihkan oleh operator", level="INFO")
        st.rerun()
    ui.render_log(level_filter=lvl, query=q)


# =========================================================================== #
# Router
# =========================================================================== #
def main() -> None:
    status = _active_dongle_status()
    sig = (status.valid, status.dongle_id)
    if st.session_state.dongle_sig != sig:
        st.session_state.dongle_sig = sig
        ui.log(
            "DONGLE",
            f"Token valid di {status.path}" if status.valid else status.message,
            status.dongle_id,
            "OK" if status.valid else "WARN",
        )

    if not status.valid:
        st.session_state.user = None
        screen_hardware_gate(status)
        return
    if not st.session_state.user:
        screen_identity(status)
        return

    user = st.session_state.user
    _dongle_watch(status.dongle_id)

    with st.sidebar:
        ui.brand()
        st.write("")
        page = st.radio("Navigasi", PAGES, index=PAGES.index(st.session_state.page), label_visibility="collapsed")
        st.session_state.page = page
        st.divider()
        sim_txt = f" | Wajah {st.session_state.similarity:.0%}" if st.session_state.similarity is not None else ""
        st.markdown(
            ui.chip(f"{user}{sim_txt}", "info", icon_name="user")
            + ui.chip(status.label or "USB Aktif", "ok", dot=True),
            unsafe_allow_html=True,
        )
        st.write("")
        if st.button("Kunci & Keluar", use_container_width=True, key="sb_logout"):
            ui.log("AUTH", f"Operator '{user}' mengunci sesi", level="INFO")
            st.session_state.user = None
            st.toast("Sesi dikunci.")
            st.rerun()

    _render_topbar(status, show_brand=False)

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
    elif page == "Kunci Perangkat":
        page_hardware(status)
    else:
        page_logs()


main()
