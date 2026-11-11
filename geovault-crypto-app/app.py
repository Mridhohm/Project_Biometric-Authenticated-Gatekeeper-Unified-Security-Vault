"""
Krypt Vault: Sistem Pengamanan Bukti Forensik Siber & Dokumen Intelijen Strategis
================================================================================

Biometric-Authenticated Gatekeeper & Unified Security Vault
Forensic & Intelligence Evidence Security Architecture:
  1. [GATE_01] Hardware USB Dongle Intercept (HMAC-SHA256 Token Validation)
  2. [GATE_02] Optical Facial Recognition (PIL 128x128 SHA-256 + AES-128-EAX) & PBKDF2-SHA256
  3. [GATE_03] Forensic Evidence & Intelligence Operations Subsystems:
     - [01] LAPORAN INTELIJEN (Super Enkripsi Teks: Vigenère + AES-256-CBC)
     - [02] BERKAS BARANG BUKTI (Enkripsi File: ChaCha20 Stream Cipher)
     - [03] CITRA FORENSIK STEGANOGRAFI (LSB PNG Image Steganography)
     - [04] INSPEKSI BASIS DATA (Encrypted SQLite At-Rest vs Decrypted View)
     - [05] CHAIN OF CUSTODY LEDGER (Blockchain Asset Integrity & PoW)\n"""

from __future__ import annotations

import base64
import html
import io
import secrets
import time
from typing import Optional

import streamlit as st
from PIL import Image

import config
import database
import ui_cyberpunk
from modules import (
    auth_biometric,
    blockchain,
    dongle_guard,
    file_crypto,
    steganography,
    super_encryption,
)

# --------------------------------------------------------------------------- #
# Bootstrap & Page Setup
# --------------------------------------------------------------------------- #
st.set_page_config(
    page_title="Krypt Vault | Forensic & Intelligence Evidence Security",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

ui_cyberpunk.inject_cyberpunk_css()
ui_cyberpunk.init_cli_logs()
database.init_db()

if "authenticated_user" not in st.session_state:
    st.session_state.authenticated_user = None
if "auth_similarity" not in st.session_state:
    st.session_state.auth_similarity = None
if "custom_dongle_path" not in st.session_state:
    st.session_state.custom_dongle_path = ""
if "last_logged_dongle_state" not in st.session_state:
    st.session_state.last_logged_dongle_state = None
if "active_nav_tab" not in st.session_state:
    st.session_state.active_nav_tab = "📊 Dashboard"


# --------------------------------------------------------------------------- #
# Top HUD Navigation & Gatekeeper Badges (Used in Gate 01 & 02)
# --------------------------------------------------------------------------- #
def render_hud_topbar(current_step: int, dongle_mounted: bool = True) -> None:
    dongle_color = "#10B981" if dongle_mounted else "#EF4444"
    dongle_bg = "rgba(16, 185, 129, 0.12)" if dongle_mounted else "rgba(239, 68, 68, 0.12)"
    dongle_label = "● HARDWARE KEY: TERHUBUNG" if dongle_mounted else "● HARDWARE KEY: TERPUTUS"

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #0F172A 0%, #111827 100%);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px;
            padding: 16px 22px;
            margin-bottom: 16px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            align-items: center;
            gap: 14px;
        ">
            <div>
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 2px;">
                    <span style="font-size: 1.4rem; font-weight: 800; color: #F8FAFC; letter-spacing: -0.02em;">
                        ⚡ KRYPT VAULT
                    </span>
                    <span style="
                        background: rgba(14, 165, 233, 0.15);
                        color: #38BDF8;
                        border: 1px solid rgba(14, 165, 233, 0.3);
                        padding: 2px 10px;
                        border-radius: 9999px;
                        font-size: 0.72rem;
                        font-weight: 700;
                    ">FORENSIC SECURITY SUITE</span>
                </div>
                <div style="
                    color: #94A3B8;
                    font-size: 0.8rem;
                ">Sistem Pengamanan Bukti Forensik Siber &amp; Dokumen Intelijen Strategis</div>
            </div>
            <div style="display: flex; flex-wrap: wrap; align-items: center; gap: 10px;">
                <span style="
                    background: {dongle_bg};
                    color: {dongle_color};
                    border: 1px solid {dongle_color};
                    padding: 5px 12px;
                    border-radius: 9999px;
                    font-size: 0.78rem;
                    font-weight: 700;
                ">{dongle_label}</span>
                <span style="
                    background: rgba(14, 165, 233, 0.1);
                    color: #38BDF8;
                    border: 1px solid rgba(14, 165, 233, 0.25);
                    padding: 5px 12px;
                    border-radius: 9999px;
                    font-size: 0.78rem;
                    font-weight: 600;
                ">CIPHER: AES-256 / CHACHA20 / SHA-256 / LSB</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    steps = [
        (1, "GATE 01", "HARDWARE DONGLE USB", "HMAC-SHA256 Token"),
        (2, "GATE 02", "BIOMETRIK & KREDENSIAL", "PBKDF2 + AES-128-EAX"),
        (3, "GATE 03", "BRANKAS BUKTI FORENSIK", "Super Enc & Ledger Core"),
    ]
    cols = st.columns(3)
    for col, (num, tag, title, desc) in zip(cols, steps):
        if num < current_step:
            border = "rgba(16, 185, 129, 0.5)"
            bg = "linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, #111827 100%)"
            badge = "<span style='color:#10B981; font-weight:700;'>● SELESAI / CLEARED</span>"
        elif num == current_step:
            border = "rgba(14, 165, 233, 0.8)"
            bg = "linear-gradient(135deg, rgba(14, 165, 233, 0.12) 0%, #111827 100%)"
            badge = "<span style='color:#38BDF8; font-weight:700;'>⚡ VERIFIKASI AKTIF</span>"
        else:
            border = "rgba(255, 255, 255, 0.06)"
            bg = "#0B0F19"
            badge = "<span style='color:#64748B; font-weight:600;'>🔒 TERKUNCI / STANDBY</span>"

        with col:
            st.markdown(
                f"""
                <div style="
                    background: {bg};
                    border: 1px solid {border};
                    border-radius: 10px;
                    padding: 10px 14px;
                    margin-bottom: 14px;
                ">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:2px; font-size:11px;">
                        <span style="color:#94A3B8; font-weight:700;">{tag}</span>
                        {badge}
                    </div>
                    <div style="font-size:12.5px; color:#F8FAFC; font-weight:700;">{title}</div>
                    <div style="font-size:10.5px; color:#64748B;">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# --------------------------------------------------------------------------- #
# GATE 01: Hardware Dongle Intercept & High-Impact Crimson Red Lockscreen
# --------------------------------------------------------------------------- #
def render_dongle_lock_screen(status: dongle_guard.DongleStatus) -> None:
    render_hud_topbar(current_step=1, dongle_mounted=False)

    st.markdown(
        """
        <div style="
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.08) 0%, #111827 100%);
            border: 1px solid rgba(239, 68, 68, 0.35);
            border-left: 5px solid #EF4444;
            border-radius: 12px;
            padding: 20px 24px;
            margin-bottom: 20px;
        ">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                <div style="font-size:1.25rem; font-weight:700; color:#EF4444; display:flex; align-items:center; gap:8px;">
                    <span>🔒</span> GERBANG 1: PEMERIKSAAN KUNCI HARDWARE USB
                </div>
                <span style="
                    background: rgba(239,68,68,0.18);
                    color:#EF4444;
                    border:1px solid rgba(239,68,68,0.4);
                    padding:3px 12px;
                    border-radius:9999px;
                    font-size:0.75rem;
                    font-weight:700;
                ">SISTEM TERKUNCI</span>
            </div>
            <div style="color:#CBD5E1; font-size:0.92rem; line-height:1.5;">
                Aplikasi <strong>Krypt Vault</strong> dilindungi oleh otentikasi perangkat keras fisik.
                Pilih salah satu metode di bawah ini untuk membuka akses:
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_demo, col_phys = st.columns([1, 1.2])

    with col_demo:
        st.markdown(
            """
            <div style="background:#131B2E; border:1px solid rgba(16,185,129,0.3); border-radius:12px; padding:18px; margin-bottom:12px;">
                <div style="font-size:1.05rem; font-weight:700; color:#10B981; margin-bottom:6px;">
                    🚀 OPSI A: MASUK CEPAT / MODE DEMO
                </div>
                <div style="color:#94A3B8; font-size:0.86rem; line-height:1.5;">
                    Gunakan opsi ini jika Anda ingin langsung mendemonstrasikan atau menguji seluruh fitur brankas kriptografi tanpa harus mencari dan mencolokkan flashdisk fisik.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("🟢 BUKA AKSES MODE DEMO (1-CLICK MASUK)", type="primary", use_container_width=True):
            res = dongle_guard.mount_virtual_dongle(label="Demo Forensic Hardware Key")
            ui_cyberpunk.log_cli("DONGLE_GUARD", f"Virtual dongle mounted: {res.path}", level="OK")
            st.session_state.last_logged_dongle_state = None
            st.rerun()

    with col_phys:
        all_drives = dongle_guard.list_all_drives_for_provisioning()
        usb_drives = [d for d in all_drives if d.get("is_usb")]

        st.markdown(
            """
            <div style="background:#131B2E; border:1px solid rgba(14,165,233,0.3); border-radius:12px; padding:18px; margin-bottom:12px;">
                <div style="font-size:1.05rem; font-weight:700; color:#38BDF8; margin-bottom:6px;">
                    🔌 OPSI B: FLASHDISK USB FISIK (OTORISASI NYATA)
                </div>
                <div style="color:#94A3B8; font-size:0.86rem; line-height:1.5;">
                    Tancapkan flashdisk USB fisik Anda ke port laptop. Sistem akan mengunci nomor seri fisik partisi Windows dengan tanda tangan HMAC-SHA256.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if usb_drives:
            st.success(f"🟢 Terdeteksi {len(usb_drives)} Flashdisk USB di port komputer:")
            for u in usb_drives:
                st.markdown(f"- **Drive `{u['drive']}`** ({u['type_name']}) — Serial: `{u['volume_serial']}`")

            target_usb = st.selectbox(
                "Pilih Flashdisk Untuk Diinisialisasi Sebagai Kunci",
                [u["drive"] for u in usb_drives],
                key="target_usb_sel",
            )
            lbl = st.text_input("Label Kunci Hardware", value="Analis Forensik Hardware Key", key="usb_lbl_input")
            if st.button("🔑 INISIALISASI FLASHDISK INI SEBAGAI HARDWARE KEY", use_container_width=True):
                ok, msg = dongle_guard.provision_drive(target_usb, label=lbl)
                if ok:
                    ui_cyberpunk.log_cli("DONGLE_GUARD", f"Physical USB provisioned: {target_usb}", level="OK")
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
        else:
            st.info("⚠️ Belum ada flashdisk USB removable yang terpasang.")
            st.caption("Colokkan flashdisk Anda ke port USB laptop, lalu klik tombol Pindai Ulang di bawah.")

        if st.button("🔄 PINDAI ULANG PORT USB (RE-SCAN)", use_container_width=True):
            ui_cyberpunk.log_cli("DONGLE_GUARD", "Re-scanning USB ports", level="INFO")
            st.session_state.last_logged_dongle_state = None
            st.rerun()

    with st.expander("💻 Log Telemetri Kriptografi & Terminal TTY", expanded=False):
        ui_cyberpunk.render_cli_console("GATE_01 // HARDWARE DONGLE INTERCEPT TELEMETRY")


# --------------------------------------------------------------------------- #
# GATE 02: Realtime Optical Face Scanner & Cryptographic Handshake
# --------------------------------------------------------------------------- #
def _capture_optical_face_auto(username: str, simulate_mismatch: bool = False) -> bytes:
    """
    Realtime automatic optical face frame capture:
    Attempts direct camera grab; smoothly falls back to deterministic optical frame.
    Runs a sleek modern scanning sequence.
    """
    status_box = st.empty()
    progress_bar = st.progress(0)

    stages = [
        (0.20, "Inisialisasi Sensor Optik // Mengunci Apertur..."),
        (0.40, "Memetakan Centroid // Memproyeksikan Retikel 128x128..."),
        (0.65, "Mengekstraksi Gradien Wajah & Deskriptor pHash/dHash..."),
        (0.85, "Menghitung SHA-256 Digest Matriks Piksel Grayscale..."),
        (1.00, "Menyegel Vektor Biometrik dengan AES-128-EAX..."),
    ]

    for p, txt in stages:
        progress_bar.progress(int(p * 100))
        status_box.markdown(
            f"<div style='color:#38BDF8; font-size:13px; padding:8px 14px; border-left:3px solid #0EA5E9; background:#111827; border-radius:6px; margin:6px 0;'>"
            f"⚡ [SENSOR OPTIK] {txt} ({int(p*100)}%)</div>",
            unsafe_allow_html=True,
        )
        time.sleep(0.3)

    progress_bar.empty()
    status_box.empty()

    # Attempt hardware capture via OpenCV if camera is ready
    captured_bytes: Optional[bytes] = None
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            for _ in range(5):
                ret, frame = cap.read()
            cap.release()
            if ret and frame is not None:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(rgb_frame)
                buf = io.BytesIO()
                pil_img.save(buf, format="PNG")
                captured_bytes = buf.getvalue()
    except Exception:
        captured_bytes = None

    if captured_bytes is None:
        seed = 999 if simulate_mismatch else 0
        captured_bytes = auth_biometric.generate_optical_face_sample(username, seed_variant=seed)

    return captured_bytes


def render_auth_screen(dongle: dongle_guard.DongleStatus) -> None:
    render_hud_topbar(current_step=2, dongle_mounted=True)

    mount_display = dongle.path or "Removable USB"
    if len(mount_display) > 40:
        mount_display = "..." + mount_display[-35:]

    st.markdown(
        f"""
        <div style="
            background: #111827;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 10px;
            padding: 12px 18px;
            margin-bottom: 16px;
            display: flex;
            flex-wrap: wrap;
            gap: 16px;
            align-items: center;
            font-size: 0.85rem;
        ">
            <div>🔑 <strong>Kunci Hardware:</strong> <span style="color:#10B981; font-weight:600;">{dongle.label or 'Valid Hardware Key'}</span></div>
            <div>📍 <strong>Mount:</strong> <code style="color:#38BDF8;">{mount_display}</code></div>
            <div>🧬 <strong>Pipeline:</strong> <span style="color:#94A3B8;">PBKDF2 (600k iter) + PIL 128x128 + AES-128-EAX</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_login, tab_register = st.tabs([
        "🔑 [01] OTORISASI OPERATOR (LOGIN)",
        "📝 [02] REGISTRASI OPERATOR BARU",
    ])

    with tab_login:
        st.info("💡 **Akun Default Pengujian**: Username: `analyst_01` | Passkey: `KryptVault2026!` (Siap langsung digunakan)")
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown("#### FAKTOR 01 // KREDENSIAL PBKDF2-SHA256")
            login_user = st.text_input("Operator Identifier (Username)", key="login_username", value="analyst_01")
            login_pw = st.text_input("Passkey Otorisasi", type="password", key="login_password", value="KryptVault2026!")
            st.caption(
                "Kunci diturunkan melalui **PBKDF2-HMAC-SHA256 (600.000 iterasi)** + 16-byte random salt + "
                "**HKDF-SHA256** domain separation (`auth/verifier` & `auth/biometric-key`)."
            )
            sim_mismatch = st.checkbox("🧪 DEV_DEMO: Simulasikan Wajah Tidak Cocok / Penyusup (Demo Dosen)", key="sim_mismatch_login")

        with c2:
            st.markdown("#### FAKTOR 02 // REALTIME OPTICAL SCANNER")
            ui_cyberpunk.render_optical_scanner_hud("login_cam_hud", height=240)
            scan_mode = st.radio("Metode Akuisisi Wajah", ["Pindai Sensor Optik / Kamera", "Unggah Citra Wajah (.PNG / .JPG)"], horizontal=True, key="login_face_mode")
            uploaded_face = None
            if scan_mode == "Unggah Citra Wajah (.PNG / .JPG)":
                uploaded_face = st.file_uploader("Pilih Berkas Foto Wajah", type=["png", "jpg", "jpeg"], key="face_upload_login")

        c_submit, c_back = st.columns([3, 1])
        with c_submit:
            if st.button("⚡ OTORISASI AKSES OPERATOR (VERIFIKASI 2FA)", type="primary", use_container_width=True):
                if not login_user or not login_pw:
                    st.warning("Masukkan Operator Identifier dan Passkey sebelum inisialisasi.")
                else:
                    user_norm = login_user.strip().lower()
                    with st.spinner("MEMVERIFIKASI KREDENSIAL PBKDF2 & DEKRIPSI VEKTOR BIOMETRIK AES-128-EAX..."):
                        if uploaded_face is not None:
                            face_bytes = uploaded_face.getvalue()
                        else:
                            face_bytes = _capture_optical_face_auto(user_norm, simulate_mismatch=sim_mismatch)
                        img_digest = ui_cyberpunk.sha256_hex(face_bytes)

                        ui_cyberpunk.log_cli(
                            "FACE_AUTH",
                            f"Optical scan captured ({len(face_bytes)} B) — Unsealing AES-128-EAX template for '{user_norm}'",
                            digest=img_digest,
                            level="INFO",
                        )
                        res = auth_biometric.authenticate_user(user_norm, login_pw, face_bytes)

                    if res.success:
                        ui_cyberpunk.log_cli(
                            "FACE_AUTH",
                            f"Optical face verification GRANTED for '{res.username}' (similarity={res.similarity:.1%})",
                            digest=img_digest,
                            level="OK",
                        )
                        st.session_state.authenticated_user = res.username
                        st.session_state.auth_similarity = res.similarity
                        st.session_state.active_nav_tab = "📊 Dashboard"
                        st.rerun()
                    else:
                        sim_txt = f" (Skor Kemiripan: {res.similarity:.1%})" if res.similarity is not None else ""
                        ui_cyberpunk.log_cli(
                            "FACE_AUTH",
                            f"Optical verification REJECTED for '{user_norm}': {res.message}{sim_txt}",
                            digest=img_digest,
                            level="CRIT",
                        )
                        st.error(f"❌ {res.message}{sim_txt}")

        with c_back:
            if st.button("⬅️ Ganti Kunci USB", use_container_width=True):
                dongle_guard.unmount_virtual_dongle()
                st.session_state.last_logged_dongle_state = None
                st.rerun()

    with tab_register:
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown("#### LANGKAH 1 // PEMBUATAN IDENTITAS OPERATOR")
            reg_user = st.text_input("Username Baru (3-32 karakter, a-z0-9_.-)", key="reg_username", placeholder="analyst_02")
            reg_pw = st.text_input("Passkey Otorisasi (min. 8 karakter, huruf & angka)", type="password", key="reg_pw")
            reg_pw2 = st.text_input("Konfirmasi Passkey", type="password", key="reg_pw2")
        with c2:
            st.markdown("#### LANGKAH 2 // PENDAFTARAN BIOMETRIK WAJAH")
            ui_cyberpunk.render_optical_scanner_hud("reg_cam_hud", height=240)
            reg_scan_mode = st.radio("Metode Akuisisi", ["Pindai Sensor Optik / Kamera", "Unggah Citra Wajah"], horizontal=True, key="reg_face_mode")
            reg_face_upload = None
            if reg_scan_mode == "Unggah Citra Wajah":
                reg_face_upload = st.file_uploader("Unggah Foto Wajah", type=["png", "jpg", "jpeg"], key="reg_face_up")
            st.caption(
                "Citra dinormalisasi ke matriks grayscale `128x128` via `PIL`, dihitung SHA-256 pixel digest, "
                "dan disegel dalam database dengan enkripsi terautentikasi **AES-128-EAX**."
            )

        if st.button("📝 DAFTARKAN IDENTITAS BARU (ENROLL BIOMETRIC)", type="primary", use_container_width=True):
            if reg_pw != reg_pw2:
                st.error("Konfirmasi passkey tidak cocok.")
            elif not reg_user or not reg_pw:
                st.warning("Lengkapi Username dan Passkey.")
            else:
                user_norm = reg_user.strip().lower()
                with st.spinner("MENYIMPAN KREDENSIAL PBKDF2 & MENYEGEL BIOMETRIK DENGAN AES-128-EAX..."):
                    if reg_face_upload is not None:
                        face_bytes = reg_face_upload.getvalue()
                    else:
                        face_bytes = _capture_optical_face_auto(user_norm, simulate_mismatch=False)
                    img_digest = ui_cyberpunk.sha256_hex(face_bytes)
                    res = auth_biometric.register_user(user_norm, reg_pw, face_bytes)

                if res.success:
                    ui_cyberpunk.log_cli(
                        "FACE_AUTH",
                        f"Enrolled operator '{res.username}' — 128x128 biometric vector sealed via AES-128-EAX",
                        digest=img_digest,
                        level="OK",
                    )
                    st.success(f"✅ {res.message}")
                else:
                    ui_cyberpunk.log_cli("FACE_AUTH", f"Enrollment error: {res.message}", digest=img_digest, level="WARN")
                    st.error(f"❌ {res.message}")

    with st.expander("💻 Log Telemetri Kriptografi & Terminal TTY", expanded=False):
        ui_cyberpunk.render_cli_console("GATE_02 // OPTICAL BIOMETRIC & PBKDF2-SHA256 TELEMETRY STREAM")


# --------------------------------------------------------------------------- #
# Top Persistent App Header (Authenticated Mode)
# --------------------------------------------------------------------------- #
def render_app_header(username: str, dongle: dongle_guard.DongleStatus) -> None:
    mount_info = dongle.path or "USB Key"
    if len(mount_info) > 30:
        mount_info = "..." + mount_info[-25:]

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #0F172A 0%, #111827 100%);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 14px 20px;
            margin-bottom: 12px;
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.25);
        ">
            <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 1.4rem; font-weight: 800; color: #F8FAFC; letter-spacing: -0.02em;">
                    ⚡ KRYPT VAULT
                </span>
                <span style="
                    background: rgba(14, 165, 233, 0.15);
                    color: #38BDF8;
                    border: 1px solid rgba(14, 165, 233, 0.3);
                    padding: 2px 10px;
                    border-radius: 9999px;
                    font-size: 0.72rem;
                    font-weight: 700;
                ">FORENSIC SECURITY SUITE</span>
            </div>
            <div style="display: flex; flex-wrap: wrap; align-items: center; gap: 10px;">
                <span style="
                    background: rgba(16, 185, 129, 0.12);
                    color: #10B981;
                    border: 1px solid rgba(16, 185, 129, 0.35);
                    padding: 5px 12px;
                    border-radius: 9999px;
                    font-size: 0.78rem;
                    font-weight: 600;
                ">🔑 {html.escape(dongle.label or 'Hardware Key')} ({html.escape(mount_info)})</span>
                <span style="
                    background: rgba(56, 189, 248, 0.12);
                    color: #38BDF8;
                    border: 1px solid rgba(56, 189, 248, 0.35);
                    padding: 5px 12px;
                    border-radius: 9999px;
                    font-size: 0.78rem;
                    font-weight: 600;
                ">👤 {username.upper()}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------- #
# TAB 00: Interactive Dashboard Hub
# --------------------------------------------------------------------------- #
def render_dashboard_hub(username: str, dongle: dongle_guard.DongleStatus) -> None:
    blockchain.ensure_genesis()
    stats = database.get_user_stats(username)
    report = blockchain.verify_chain()

    # 4 Top Telemetry Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("⛓️ BLOK BLOCKCHAIN", stats["ledger_blocks"], help="Total blok bukti digital pada SQLite ledger")
    m2.metric("🛡️ INTEGRITAS LEDGER", "VALID (100%)" if report.valid else "TERKOMPROMI!", help="Status verifikasi hash SHA-256 dan Proof-of-Work")
    m3.metric("📝 LAPORAN SUPER ENKRIPSI", stats["secret_messages"], help="Jumlah dokumen teks dengan proteksi Vigenère + AES-256")
    m4.metric("📁 BERKAS BUKTI CHACHA20", stats["encrypted_files"], help="Jumlah berkas terenkripsi mandiri .krypt.enc")

    if not report.valid:
        st.error(
            f"🚨 **[PERINGATAN INTEGRITAS LEDGER]** Terdeteksi {len(report.issues)} pelanggaran hash pada blockchain! "
            "Klik kartu **Blockchain Ledger** di bawah untuk melakukan audit detail."
        )

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    st.markdown("### 🎛️ PUSAT NAVIGASI & KONTROL BUKTI KRIPTOGRAFI")
    st.caption("Pilih modul di bawah ini untuk mengakses fungsionalitas enkripsi, steganografi, dan audit:")

    # Row 1: 3 Cards
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            """
            <div class="kv-feature-card">
                <div>
                    <div class="kv-card-icon">📝</div>
                    <div class="kv-card-title">Super Enkripsi Teks</div>
                    <div class="kv-card-badge">KLASIK + MODERN</div>
                    <div class="kv-card-desc">
                        Dua lapis proteksi: Substitusi Polialfabetik Extended Vigenère Cipher dilapisi AES-256-CBC dengan random IV &amp; PKCS#7 padding.
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("🚀 Buka Modul Teks", key="btn_open_super_enc", use_container_width=True, type="primary"):
            st.session_state.active_nav_tab = "📝 Super Enkripsi Teks"
            st.rerun()

    with c2:
        st.markdown(
            """
            <div class="kv-feature-card">
                <div>
                    <div class="kv-card-icon">📁</div>
                    <div class="kv-card-title">Enkripsi Berkas Dokumen</div>
                    <div class="kv-card-badge">CHACHA20 STREAM CIPHER</div>
                    <div class="kv-card-desc">
                        Enkripsi biner berkecepatan tinggi untuk dokumen (PDF, DOCX, ZIP) menggunakan ChaCha20 dan dibungkus menjadi paket mandiri .krypt.enc.
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("🚀 Buka Modul Berkas", key="btn_open_file_crypto", use_container_width=True, type="primary"):
            st.session_state.active_nav_tab = "📁 Enkripsi Berkas (ChaCha20)"
            st.rerun()

    with c3:
        st.markdown(
            """
            <div class="kv-feature-card">
                <div>
                    <div class="kv-card-icon">🖼️</div>
                    <div class="kv-card-title">Steganografi Citra</div>
                    <div class="kv-card-badge">LSB PNG LOSSLESS</div>
                    <div class="kv-card-desc">
                        Penyisipan dan ekstraksi pesan atau koordinat rahasia secara kasat mata ke dalam Least Significant Bit (LSB) channel RGB citra PNG.
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("🚀 Buka Steganografi", key="btn_open_stego", use_container_width=True, type="primary"):
            st.session_state.active_nav_tab = "🖼️ Steganografi Citra (LSB)"
            st.rerun()

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Row 2: 3 Cards
    c4, c5, c6 = st.columns(3)
    with c4:
        st.markdown(
            """
            <div class="kv-feature-card">
                <div>
                    <div class="kv-card-icon">🔍</div>
                    <div class="kv-card-title">Inspeksi Basis Data SQLite</div>
                    <div class="kv-card-badge">AT-REST ENCRYPTION</div>
                    <div class="kv-card-desc">
                        Audit forensik independen: membuktikan bahwa seluruh data sensitif tersimpan dalam format Ciphertext saat at-rest di storage/vault.db.
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("🚀 Buka Inspeksi Database", key="btn_open_db_inspect", use_container_width=True, type="primary"):
            st.session_state.active_nav_tab = "🔍 Inspeksi Database SQLite"
            st.rerun()

    with c5:
        st.markdown(
            """
            <div class="kv-feature-card">
                <div>
                    <div class="kv-card-icon">⛓️</div>
                    <div class="kv-card-title">Blockchain Chain-of-Custody</div>
                    <div class="kv-card-badge">SHA-256 POW + AES-GCM</div>
                    <div class="kv-card-desc">
                        Buku besar bukti digital tidak dapat diubah (Immutable Ledger) dengan penambangan Proof-of-Work SHA-256 (prefix '00') &amp; segel AES-256-GCM.
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("🚀 Buka Blockchain Ledger", key="btn_open_blockchain", use_container_width=True, type="primary"):
            st.session_state.active_nav_tab = "⛓️ Blockchain Ledger (PoW)"
            st.rerun()

    with c6:
        st.markdown(
            """
            <div class="kv-feature-card">
                <div>
                    <div class="kv-card-icon">🔑</div>
                    <div class="kv-card-title">Hardware Dongle USB</div>
                    <div class="kv-card-badge">HMAC-SHA256 TOKEN</div>
                    <div class="kv-card-desc">
                        Manajemen flashdisk USB otorisasi, penandatanganan token HMAC-SHA256, pengikatan Volume Serial fisik Windows, dan status gatekeeper.
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("🚀 Kelola Kunci USB", key="btn_open_dongle_mgr", use_container_width=True, type="primary"):
            st.session_state.active_nav_tab = "🔑 Pengaturan Kunci USB"
            st.rerun()

    # Spesifikasi Ringkas Modul
    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)
    with st.expander("🛡️ Tabel Pemetaan 7 Kriteria Kriptografi Pak Bagus (UPN 'Veteran' Yogyakarta)"):
        st.markdown(
            """
            | No | Kriteria Tugas Akhir | Implementasi Teknis Krypt Vault | Algoritma Utama |
            | :--- | :--- | :--- | :--- |
            | **1** | **Login Biometric & Dongle Hardware** | Sistem terkunci total hingga USB fisik ber-token HMAC-SHA256 terdeteksi | `HMAC-SHA256` + Win32 Volume Serial |
            | **2** | **Login Menggunakan Algoritma Kriptografi** | Autentikasi 2FA: Kredensial PBKDF2 (600k iter) + Vektor Wajah 128x128 disegel AES-128-EAX | `PBKDF2-HMAC-SHA256` + `AES-128-EAX` |
            | **3** | **Super Enkripsi Teks (Klasik + Modern)** | Enkripsi pesan berjenjang: Lapisan 1 Vigenère Cipher $\\rightarrow$ Lapisan 2 AES-256-CBC | `Extended Vigenère` + `AES-256-CBC` |
            | **4** | **Enkripsi File (Beda dari Teks)** | Aliran biner file dokumen/arsip dikunci dengan stream cipher kecepatan tinggi | `ChaCha20 Stream` (256-bit key) |
            | **5** | **Enkripsi Basis Data (At-Rest)** | Seluruh kolom sensitif SQLite `vault.db` tersimpan dalam format ciphertext saat di disk | `Ciphertext At-Rest` + Dual-View Audit |
            | **6** | **Steganografi Citra** | Menyisipkan pesan ke bit terkecil RGB citra PNG lossless dengan delimiter `<<<END>>>` | `LSB (Least Significant Bit)` |
            | **7** | **Blockchain Sederhana Aset Penting** | Rantai blok ledger bukti digital dengan Proof-of-Work & segel AES-256-GCM | `SHA-256 PoW ('00')` + `AES-256-GCM` |
            """
        )


# --------------------------------------------------------------------------- #
# TAB 06: Hardware Dongle Settings & Telemetry
# --------------------------------------------------------------------------- #
def render_usb_settings_tab(dongle: dongle_guard.DongleStatus) -> None:
    st.subheader("🔑 PENGATURAN & TELEMETRI KUNCI HARDWARE DONGLE USB")
    st.caption(
        "Krypt Vault menggunakan tanda tangan digital HMAC-SHA256 yang diikat dengan nomor seri fisik partisi Windows. "
        "Pada halaman ini Anda dapat memeriksa status kunci, memformat flashdisk USB baru, atau mengaktifkan mode simulasi."
    )

    all_drives = dongle_guard.list_all_drives_for_provisioning()
    usb_drives = [d for d in all_drives if d.get("is_usb")]

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 💾 Status Kunci Aktif Saat Ini")
        st.json({
            "dongle_label": dongle.label,
            "dongle_id": dongle.dongle_id,
            "mount_path": dongle.path,
            "volume_serial": dongle.volume_serial or "UNBOUND_VIRTUAL",
            "auth_algorithm": "HMAC-SHA256 (HKDF domain: dongle/hmac-sha256)",
            "anti_cloning_protection": "Volume Serial Hardware Binding",
        })

    with c2:
        st.markdown("#### ⚡ Kontrol Kunci & Pengujian")
        if st.button("🔄 Pindai Ulang Port USB", type="primary", use_container_width=True):
            ui_cyberpunk.log_cli("DONGLE_GUARD", "Manual re-scan requested by operator", level="INFO")
            st.session_state.last_logged_dongle_state = None
            st.rerun()

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        v_mounted = dongle_guard.is_virtual_dongle_mounted()
        if v_mounted:
            st.success("🟢 Mode Kunci: **VIRTUAL DONGLE (TERPASANG)**")
            if st.button("🔴 Cabut Kunci Virtual (Simulasikan USB Dicabut)", use_container_width=True):
                dongle_guard.unmount_virtual_dongle()
                ui_cyberpunk.log_cli("DONGLE_GUARD", "Virtual dongle hot-unplugged", level="CRIT")
                st.session_state.last_logged_dongle_state = None
                st.rerun()
        else:
            st.info("ℹ️ Mode Kunci: **FLASHDISK FISIK / DRIVE PORT**")
            if st.button("🟢 Pasang Kunci Virtual Tambahan", use_container_width=True):
                dongle_guard.mount_virtual_dongle()
                ui_cyberpunk.log_cli("DONGLE_GUARD", "Virtual dongle mounted", level="OK")
                st.session_state.last_logged_dongle_state = None
                st.rerun()

    st.markdown("---")
    st.markdown("#### 🔌 Inisialisasi Flashdisk USB Fisik Baru")
    if usb_drives:
        st.success(f"Terdeteksi {len(usb_drives)} Flashdisk Removable USB:")
        for u in usb_drives:
            st.markdown(f"- **Drive `{u['drive']}`** ({u['type_name']}) — Volume Serial: `{u['volume_serial']}`")

        target_usb = st.selectbox("Pilih Drive USB", [u["drive"] for u in usb_drives], key="prov_usb_sel")
        lbl = st.text_input("Label Kunci", value="Analis Forensik Hardware Key", key="prov_lbl_in")
        if st.button("🔑 Inisialisasi Token HMAC-SHA256 Pada Flashdisk Ini", type="primary"):
            ok, msg = dongle_guard.provision_drive(target_usb, label=lbl)
            if ok:
                st.success(msg)
                ui_cyberpunk.log_cli("DONGLE_GUARD", f"Provisioned {target_usb}", level="OK")
                st.rerun()
            else:
                st.error(msg)
    else:
        st.info("Tidak ada flashdisk USB removable yang terpasang saat ini.")


# --------------------------------------------------------------------------- #
# TAB 01: [01] LAPORAN INTELIJEN (Super Enkripsi Teks: Vigenère + AES-256-CBC)
# --------------------------------------------------------------------------- #
def render_super_encryption_tab(username: str) -> None:
    st.subheader("📝 [01] LAPORAN INTELIJEN // SUPER ENKRIPSI TEKS (VIGENÈRE + AES-256-CBC)")
    st.caption(
        "Dua lapis proteksi: Substitusi Polialfabetik Klasik (Extended Vigenère modulo 256) "
        "dilapisi Enkripsi Simetris Modern AES-256-CBC dengan padding PKCS#7."
    )

    tab_enc, tab_dec = st.tabs([
        "🔒 [01] ENKRIPSI DISPATCH INTELIJEN",
        "🔓 [02] DEKRIPSI DISPATCH INTELIJEN",
    ])

    with tab_enc:
        with st.form("super_enc_form"):
            title = st.text_input("Judul / Sandi Dokumen Intelijen", placeholder="LAPORAN_OPERASI_SANGKURIANG_07")
            plaintext = st.text_area(
                "Isi Laporan Rahasia / Koordinat Intelijen",
                height=130,
                placeholder="Target teridentifikasi pada koordinat -6.2088, 106.8456. Titik ekstraksi aman di safehouse B-2.",
            )
            c1, c2 = st.columns(2)
            vig_key = c1.text_input("Kunci Vigenère (Lapisan 1)", type="password", key="vkey_in")
            aes_pass = c2.text_input("Passphrase AES-256-CBC (Lapisan 2)", type="password", key="aeskey_in")
            submitted = st.form_submit_button("🔒 JALANKAN SUPER ENKRIPSI (VIGENÈRE -> AES-256-CBC)", type="primary")

        if submitted:
            if not (title and plaintext and vig_key and aes_pass):
                st.warning("Semua kolom (Judul, Plaintext, Kunci Vigenère, Passphrase AES) wajib diisi.")
            else:
                try:
                    res = super_encryption.super_encrypt_detailed(plaintext, vig_key, aes_pass)
                    token = res["token"]
                    database.insert_secret_message(username, title, token, super_encryption.ALGORITHM_ID)

                    ui_cyberpunk.log_cli(
                        "SUPER_ENC",
                        f"Super-encrypted intel dispatch '{title}' — Token size: {len(token)} chars",
                        digest=ui_cyberpunk.sha256_hex(token),
                        level="OK",
                    )
                    st.success("✅ **[SUKSES]** Laporan Intelijen berhasil di-super-enkripsi dan disimpan di database!")

                    # Live Telemetry Preview for Class Demonstration
                    st.markdown("#### 🔬 TELEMETRI HASIL DUA LAPIS ENKRIPSI:")
                    p1, p2 = st.columns(2)
                    with p1:
                        st.markdown("**[TAHAP 1: CIPHERTEXT VIGENÈRE (BASE64 & HEX)]**")
                        st.code(f"Base64: {res['vigenere_b64']}\nHex:    {res['vigenere_hex'][:64]}...")
                    with p2:
                        st.markdown("**[TAHAP 2: AES-256-CBC PARAMETERS]**")
                        st.code(
                            f"Salt (16B): {res['salt_hex']}\n"
                            f"IV (16B):   {res['iv_hex']}\n"
                            f"AES CT:     {res['aes_ciphertext_hex'][:64]}..."
                        )

                    st.markdown("**[TOKEN TERKONSOLIDASI (DISIMPAN DI SQLITE)]**")
                    st.code(token)
                except Exception as exc:
                    ui_cyberpunk.log_cli("SUPER_ENC", f"Encryption error: {exc}", level="CRIT")
                    st.error(f"Gagal melakukan enkripsi: {exc}")

    with tab_dec:
        st.markdown("#### 🔓 DEKRIPSI DAN PEMULIHAN LAPORAN INTELIJEN")
        source_mode = st.radio("Pilih Sumber Ciphertext", ["Pilih Dari Arsip Database SQLite", "Input Token Base64 Manual"], horizontal=True)

        target_token = ""
        target_title = ""
        if source_mode == "Pilih Dari Arsip Database SQLite":
            saved_msgs = database.list_secret_messages(username)
            if not saved_msgs:
                st.info("Belum ada laporan intelijen tersimpan di database.")
            else:
                msg_options = {f"[{m['id']:03d}] {m['title']} ({m['created_at']})": m for m in saved_msgs}
                chosen_label = st.selectbox("Pilih Arsip Laporan", list(msg_options.keys()))
                chosen_msg = msg_options[chosen_label]
                target_token = chosen_msg["ciphertext"]
                target_title = chosen_msg["title"]
                st.caption(f"Ciphertext Token Terpilih: `{target_token[:64]}...`")
        else:
            target_token = st.text_area("Tempelkan Token Base64 Ciphertext", height=100)
            target_title = "Manual Token Input"

        d1, d2 = st.columns(2)
        dec_vig = d1.text_input("Kunci Vigenère Pemulih", type="password", key="vkey_dec")
        dec_aes = d2.text_input("Passphrase AES-256-CBC", type="password", key="aeskey_dec")

        if st.button("🔓 JALANKAN DEKRIPSI (AES-256-CBC -> REVERSE VIGENÈRE)", type="primary"):
            if not (target_token and dec_vig and dec_aes):
                st.warning("Lengkapi Ciphertext Token, Kunci Vigenère, dan Passphrase AES.")
            else:
                try:
                    res_dec = super_encryption.super_decrypt_detailed(target_token, dec_vig, dec_aes)
                    ui_cyberpunk.log_cli(
                        "SUPER_ENC",
                        f"Successfully decrypted intel dispatch '{target_title}'",
                        digest=ui_cyberpunk.sha256_hex(res_dec["plaintext"]),
                        level="OK",
                    )
                    st.success("✅ **[OTORISASI SUKSES]** Dua lapis enkripsi berhasil dibuka!")
                    st.markdown("#### 📄 HASIL DEKRIPSI DUA TAHAP:")
                    r1, r2 = st.columns(2)
                    with r1:
                        st.markdown("**[TAHAP 1: TEKS VIGENÈRE DIPULIHKAN DARI AES-256]**")
                        st.code(res_dec["vigenere_b64"])
                    with r2:
                        st.markdown("**[TAHAP 2: PLAINTEXT ASLI TERBUKA (REVERSE VIGENÈRE)]**")
                        st.text_area("Plaintext Rahasia", value=res_dec["plaintext"], height=120)
                except Exception as exc:
                    ui_cyberpunk.log_cli("SUPER_ENC", f"Decryption failure: {exc}", level="CRIT")
                    st.error(f"❌ Dekripsi gagal: Kunci Vigenère atau Passphrase AES salah, atau ciphertext rusak! ({exc})")


# --------------------------------------------------------------------------- #
# TAB 02: [02] BERKAS BARANG BUKTI (Enkripsi File: ChaCha20 Stream Cipher)
# --------------------------------------------------------------------------- #
def render_file_crypto_tab(username: str) -> None:
    st.subheader("📁 [02] BERKAS BARANG BUKTI // ENKRIPSI DOKUMEN FORENSIK (CHACHA20)")
    st.caption(
        "Enkripsi stream cipher kecepatan tinggi ChaCha20 untuk barang bukti dokumen (PDF, DOCX, TXT, CSV, JPG, ZIP). "
        "Menghasilkan berkas terenkripsi mandiri berformat `.krypt.enc` yang memuat verifikasi integritas SHA-256."
    )

    tab_enc, tab_dec = st.tabs([
        "🔐 [01] ENKRIPSI BERKAS BARANG BUKTI",
        "🔓 [02] DEKRIPSI BERKAS (.KRYPT.ENC / ARSIP VAULT)",
    ])

    with tab_enc:
        uploaded = st.file_uploader(
            "Unggah Berkas Barang Bukti Forensik (PDF, DOCX, TXT, CSV, JPG, PNG, ZIP, KML)",
            key="file_enc_uploader",
        )
        passphrase = st.text_input("Passphrase Enkripsi ChaCha20", type="password", key="file_enc_pw")

        if st.button("🔐 ENKRIPSI DOKUMEN DENGAN CHACHA20", type="primary", disabled=uploaded is None):
            if not passphrase:
                st.warning("Masukkan passphrase enkripsi.")
            else:
                raw_bytes = uploaded.getvalue()
                with st.spinner("MENGEKSEKUSI STREAM CIPHER CHACHA20 & MEMBUNGKUS .KRYPT.ENC..."):
                    bundle = file_crypto.encrypt_file_bytes(raw_bytes, passphrase)
                    package_bytes = file_crypto.pack_krypt_envelope(bundle, uploaded.name, uploaded.type)

                    # Persist ciphertext blob & metadata
                    stored_name = f"{secrets.token_hex(16)}.enc"
                    config.ensure_storage()
                    (config.FILES_DIR / stored_name).write_bytes(bundle.ciphertext)
                    database.insert_encrypted_file(
                        owner=username,
                        original_name=uploaded.name,
                        stored_name=stored_name,
                        mime_type=uploaded.type,
                        size_bytes=len(raw_bytes),
                        sha256_plain=bundle.sha256_plain,
                        kdf_salt=bundle.kdf_salt,
                        nonce=bundle.nonce,
                        algorithm=bundle.algorithm,
                    )

                    ui_cyberpunk.log_cli(
                        "CHACHA20",
                        f"Encrypted evidence '{uploaded.name}' ({len(raw_bytes)} B) -> Nonce: {bundle.nonce}",
                        digest=bundle.sha256_plain,
                        level="OK",
                    )
                    st.success(f"✅ Dokumen **{uploaded.name}** berhasil dienkripsi dengan ChaCha20!")

                    c_meta1, c_meta2 = st.columns(2)
                    with c_meta1:
                        st.json({
                            "original_name": uploaded.name,
                            "algorithm": bundle.algorithm,
                            "sha256_plain": bundle.sha256_plain,
                            "size_bytes": len(raw_bytes),
                        })
                    with c_meta2:
                        st.json({
                            "kdf_salt": bundle.kdf_salt,
                            "nonce": bundle.nonce,
                            "envelope_package_size": len(package_bytes),
                            "kdf_iterations": 200_000,
                        })

                    enc_filename = f"{uploaded.name}.krypt.enc"
                    st.download_button(
                        f"⬇️ UNDUH BERKAS TERENKRIPSI ({enc_filename})",
                        data=package_bytes,
                        file_name=enc_filename,
                        mime="application/octet-stream",
                        use_container_width=True,
                    )

    with tab_dec:
        st.markdown("#### 🔓 DEKRIPSI DAN PEMULIHAN BERKAS BUKTI FORENSIK")
        dec_mode = st.radio("Metode Masukan Berkas", ["Unggah Berkas .krypt.enc Mandiri", "Pilih Dari Arsip Database SQLite"], horizontal=True)

        if dec_mode.startswith("Unggah"):
            enc_file_in = st.file_uploader("Unggah Berkas Terenkripsi (.krypt.enc / .bagus.enc)", type=["enc"], key="standalone_enc_in")
            dec_pw = st.text_input("Passphrase Dekripsi ChaCha20", type="password", key="dec_pw_standalone")
            if st.button("🔓 DEKRIPSI PAKET MANDIRI", type="primary", disabled=enc_file_in is None):
                if not dec_pw:
                    st.warning("Masukkan passphrase dekripsi.")
                else:
                    try:
                        plain_bytes, meta = file_crypto.unpack_bagus_envelope(enc_file_in.getvalue(), dec_pw)
                        ui_cyberpunk.log_cli(
                            "CHACHA20",
                            f"Decrypted standalone package '{meta['original_name']}' — SHA-256 verified",
                            digest=meta["sha256_plain"],
                            level="OK",
                        )
                        st.success(f"✅ Berkas **{meta['original_name']}** berhasil dipulihkan dan diverifikasi integritas SHA-256!")
                        st.download_button(
                            f"⬇️ UNDUH DOKUMEN PULIH ({meta['original_name']})",
                            data=plain_bytes,
                            file_name=meta["original_name"],
                            mime=meta.get("mime_type", "application/octet-stream"),
                            use_container_width=True,
                        )
                    except Exception as exc:
                        ui_cyberpunk.log_cli("CHACHA20", f"Decryption error: {exc}", level="CRIT")
                        st.error(f"❌ Gagal mendekripsi: {exc}")
        else:
            files = database.list_encrypted_files(username)
            if not files:
                st.info("Belum ada berkas terenkripsi dalam arsip vault.")
            else:
                for f in files:
                    with st.expander(f"📦 [{f['id']:03d}] {f['original_name']} ({f['size_bytes']} B // {f['created_at']})"):
                        st.caption(f"SHA-256: `{f['sha256_plain']}` | Nonce: `{f['nonce']}`")
                        vdec_pw = st.text_input("Passphrase Dekripsi", type="password", key=f"vdec_{f['id']}")
                        if st.button(f"🔓 DEKRIPSI {f['original_name']}", key=f"btn_vdec_{f['id']}"):
                            try:
                                cipher_bytes = (config.FILES_DIR / f["stored_name"]).read_bytes()
                                plain = file_crypto.decrypt_file_bytes(
                                    cipher_bytes, vdec_pw, f["kdf_salt"], f["nonce"], f["sha256_plain"]
                                )
                                ui_cyberpunk.log_cli(
                                    "CHACHA20",
                                    f"Decrypted vault file #{f['id']} ('{f['original_name']}')",
                                    digest=f["sha256_plain"],
                                    level="OK",
                                )
                                st.success("Integritas SHA-256 valid! Berkas siap diunduh:")
                                st.download_button(
                                    f"⬇️ UNDUH {f['original_name']}",
                                    data=plain,
                                    file_name=f["original_name"],
                                    mime=f["mime_type"] or "application/octet-stream",
                                    key=f"dl_vault_{f['id']}",
                                )
                            except Exception as exc:
                                ui_cyberpunk.log_cli("CHACHA20", f"Vault decrypt failed: {exc}", level="CRIT")
                                st.error(str(exc))


# --------------------------------------------------------------------------- #
# TAB 03: [03] CITRA FORENSIK STEGANOGRAFI (LSB PNG Image Steganography)
# --------------------------------------------------------------------------- #
def render_steganography_tab() -> None:
    st.subheader("🖼️ [03] CITRA FORENSIK STEGANOGRAFI // LSB PNG EMBEDDING & EXTRACTION")
    st.caption(
        "Penyisipan pesan rahasia / koordinat ekstraksi ke dalam bit terkecil (Least Significant Bit) "
        "komponen warna RGB citra PNG lossless dengan pembatas terminal `<<<END>>>`."
    )

    tab_embed, tab_extract = st.tabs([
        "📥 [01] EMBED BUKTI INTELIJEN (LSB INJECTION)",
        "📤 [02] EKSTRAK BUKTI TERSEMBUNYI (LSB EXTRACTION)",
    ])

    with tab_embed:
        cover_file = st.file_uploader("Unggah Citra Sampul (Cover Image - PNG / BMP)", type=["png", "bmp"], key="stego_cover_in")
        secret_text = st.text_area(
            "Pesan / Koordinat Rahasia Yang Akan Disisipkan",
            height=110,
            placeholder="[TOP SECRET] Target bergerak menuju safehouse perbatasan. Sandi kontak: PHOENIX-99.",
        )
        stego_pass = st.text_input("Passphrase Enkripsi Steganografi (Opsional)", type="password", key="stego_pw_in")

        if cover_file is not None:
            cover_bytes = cover_file.getvalue()
            capacity = steganography.calculate_capacity(cover_bytes)
            st.info(f"Kapasitas Maksimal Muatan Citra: **{capacity:,} Bytes** ({capacity / 1024:.1f} KB)")

        if st.button("✨ SISIPKAN PESAN KE BIT LSB CITRA", type="primary", disabled=cover_file is None):
            if not secret_text.strip():
                st.warning("Tuliskan pesan rahasia yang akan disisipkan.")
            else:
                cover_bytes = cover_file.getvalue()
                try:
                    with st.spinner("MENYISIPKAN BIT KE DALAM PIXEL CITRA DENGAN PEMBATAS <<<END>>>..."):
                        out_png = steganography.embed_message_lsb(cover_bytes, secret_text, stego_pass or None)
                    out_digest = ui_cyberpunk.sha256_hex(out_png)

                    ui_cyberpunk.log_cli(
                        "LSB_STEGO",
                        f"Embedded {len(secret_text.encode('utf-8'))} bytes into '{cover_file.name}'",
                        digest=out_digest,
                        level="OK",
                    )
                    st.success("✅ Pesan rahasia berhasil disisipkan secara kasat mata ke dalam LSB citra PNG!")

                    col_prev1, col_prev2 = st.columns(2)
                    with col_prev1:
                        st.markdown("**Citra Sampul Asli:**")
                        st.image(cover_bytes, use_container_width=True)
                    with col_prev2:
                        st.markdown("**Citra Stego (Memuat Pesan Tersembunyi):**")
                        st.image(out_png, use_container_width=True)

                    st.download_button(
                        "⬇️ UNDUH CITRA STEGANOGRAFI (krypt_forensic_stego.png)",
                        data=out_png,
                        file_name="krypt_forensic_stego.png",
                        mime="image/png",
                        use_container_width=True,
                    )
                except Exception as exc:
                    ui_cyberpunk.log_cli("LSB_STEGO", f"Embed error: {exc}", level="CRIT")
                    st.error(f"Gagal menyisipkan steganografi: {exc}")

    with tab_extract:
        stego_in = st.file_uploader("Unggah Citra Steganografi (.PNG)", type=["png"], key="stego_extract_in")
        ext_pass = st.text_input("Passphrase Dekripsi (Jika Disisipkan Menggunakan Passphrase)", type="password", key="stego_ext_pw")

        if st.button("🔍 EKSTRAK PESAN DARI CITRA LSB", type="primary", disabled=stego_in is None):
            stego_bytes = stego_in.getvalue()
            try:
                with st.spinner("MEMINDAI BIT LSB CITRA HINGGA DELIMITER <<<END>>>..."):
                    recovered_msg = steganography.extract_message_lsb(stego_bytes, ext_pass or None)
                ui_cyberpunk.log_cli(
                    "LSB_STEGO",
                    f"Extracted payload from '{stego_in.name}' ({len(recovered_msg)} chars)",
                    digest=ui_cyberpunk.sha256_hex(recovered_msg),
                    level="OK",
                )
                st.success("✅ **[EKSTRAKSI SUKSES]** Pesan rahasia berhasil dipulihkan dari citra!")
                st.text_area("Pesan Rahasia Terbaca:", value=recovered_msg, height=130)
            except Exception as exc:
                ui_cyberpunk.log_cli("LSB_STEGO", f"Extraction error: {exc}", level="CRIT")
                st.error(f"❌ Gagal mengekstrak pesan: {exc}")


# --------------------------------------------------------------------------- #
# TAB 04: [04] INSPEKSI BASIS DATA (Encrypted SQLite At-Rest vs Decrypted View)
# --------------------------------------------------------------------------- #
def render_database_inspection_tab(username: str) -> None:
    st.subheader("🔍 [04] INSPEKSI BASIS DATA // AT-REST ENCRYPTED SQLITE VS DECRYPTED VIEW")
    st.caption(
        "Audit Forensik Independen: Membuktikan bahwa seluruh kolom kredensial, berkas, dan laporan "
        "tersimpan dalam bentuk Ciphertext / BLOB terenkripsi pada basis data `vault.db` saat at-rest."
    )

    raw_data = database.get_raw_records_for_inspection(username)

    view_mode = st.radio(
        "Pilih Mode Tampilan Audit",
        ["Komparasi Side-by-Side (Ciphertext At-Rest vs Decrypted)", "Dump Mentah Tabel SQLite"],
        horizontal=True,
    )

    if view_mode == "Komparasi Side-by-Side (Ciphertext At-Rest vs Decrypted)":
        c_left, c_right = st.columns(2)
        with c_left:
            st.markdown("#### 🔒 RAW SQLITE CIPHERTEXT (AT-REST)")
            st.caption("Data mentah yang tersimpan di disk `storage/vault.db` (tidak terbaca tanpa kunci).")

            st.markdown("**1. Tabel `users` (Biometrik Wajah & Hash)**")
            if raw_data["users"]:
                u = raw_data["users"][0]
                st.code(
                    f"username:       {u['username']}\n"
                    f"password_hash:  {u['password_hash'][:40]}...\n"
                    f"password_salt:  {u['password_salt']}\n"
                    f"bio_template:   {u['bio_template_hex'][:40]}... (AES-128-EAX BLOB)\n"
                    f"bio_algorithm:  {u['bio_algorithm']}"
                )

            st.markdown("**2. Tabel `secret_messages` (Super Encryption Ciphertext)**")
            if raw_data["secret_messages"]:
                m = raw_data["secret_messages"][0]
                st.code(
                    f"title:      {m['title']}\n"
                    f"ciphertext: {m['ciphertext'][:70]}...\n"
                    f"algorithm:  {m['algorithm']}"
                )
            else:
                st.write("Belum ada rekaman laporan intelijen.")

            st.markdown("**3. Tabel `encrypted_files` (ChaCha20 Stream Metadata)**")
            if raw_data["encrypted_files"]:
                f = raw_data["encrypted_files"][0]
                st.code(
                    f"stored_name:  {f['stored_name']}\n"
                    f"sha256_plain: {f['sha256_plain']}\n"
                    f"nonce:        {f['nonce']}\n"
                    f"kdf_salt:     {f['kdf_salt']}"
                )
            else:
                st.write("Belum ada rekaman berkas barang bukti.")

        with c_right:
            st.markdown("#### 🔓 AUTHENTICATED DECRYPTED FORENSIC VIEW")
            st.caption("Hasil komputasi saat operator terautentikasi memasukkan kunci yang sah.")

            st.markdown("**1. Profil Operator Terverifikasi**")
            st.code(
                f"Operator:        {username.upper()}\n"
                f"Status:          AUTHENTICATED_ONLINE\n"
                f"Face Vector:     UNSEALED // AES-128-EAX AUTHTAG_VALID\n"
                f"Session Mode:    FORENSIC_EXAMINER"
            )

            st.markdown("**2. Dekripsi Laporan Intelijen Terkini**")
            if raw_data["secret_messages"]:
                st.info("Buka tab **[01] LAPORAN INTELIJEN** untuk mendekripsi token Base64 di sebelah kiri menggunakan kunci Vigenère & passphrase.")
            else:
                st.write("Tidak ada rekaman untuk didekripsi.")

            st.markdown("**3. Integritas Dokumen Bukti Forensik**")
            if raw_data["encrypted_files"]:
                f = raw_data["encrypted_files"][0]
                st.success(
                    f"Berkas Asli: `{f['original_name']}`\n"
                    f"Algoritma:   ChaCha20-Stream (PBKDF2 200k iter)\n"
                    f"Verifikasi:  Plaintext SHA-256 Checksum Embedded"
                )
    else:
        st.markdown("#### 📦 DATA MENTAH TABEL BASIS DATA SQLITE")
        t_user, t_msg, t_file, t_chain = st.tabs(["users", "secret_messages", "encrypted_files", "blockchain_ledger"])
        with t_user:
            st.dataframe(raw_data["users"], use_container_width=True)
        with t_msg:
            st.dataframe(raw_data["secret_messages"], use_container_width=True)
        with t_file:
            st.dataframe(raw_data["encrypted_files"], use_container_width=True)
        with t_chain:
            st.dataframe(raw_data["blockchain_ledger"], use_container_width=True)


# --------------------------------------------------------------------------- #
# TAB 05: [05] CHAIN OF CUSTODY LEDGER (Blockchain Asset Integrity & PoW)
# --------------------------------------------------------------------------- #
def render_blockchain_tab(username: str) -> None:
    blockchain.ensure_genesis()
    st.subheader("⛓️ [05] CHAIN OF CUSTODY LEDGER // BLOCKCHAIN BUKTI FORENSIK & POW")
    st.caption(
        "Buku besar tidak dapat diubah (Immutable Ledger) untuk mencatat rantai serah terima bukti digital. "
        "Setiap aset disegel dengan **AES-256-GCM**, ditambang dengan **Proof-of-Work SHA-256 (prefix '00')**, "
        "dan dipatok dengan tanda tangan **HMAC Chain-Tip Anchor**."
    )

    c_audit, c_export = st.columns([2, 1])
    with c_audit:
        if st.button("🔍 VERIFY_CHAIN_INTEGRITY // AUDIT HASH KESELURUHAN", type="primary", use_container_width=True):
            rep = blockchain.verify_chain()
            st.session_state["last_verification"] = rep
            tip_hash = blockchain.get_chain()[-1].current_hash if blockchain.get_chain() else "NONE"
            ui_cyberpunk.log_cli(
                "POW_LEDGER",
                f"Chain audit finished: valid={rep.valid} | blocks={rep.blocks_checked} | elapsed={rep.elapsed_ms:.2f}ms",
                digest=tip_hash,
                level="OK" if rep.valid else "CRIT",
            )
    with c_export:
        st.download_button(
            "⬇️ EKSPOR LEDGER KE JSON",
            data=blockchain.export_chain_json(),
            file_name="krypt_vault_chain_of_custody.json",
            mime="application/json",
            use_container_width=True,
        )

    report: blockchain.VerificationReport = st.session_state.get("last_verification") or blockchain.verify_chain()
    if report.valid:
        st.success(
            f"✅ **[INTEGRITAS RANTAI VALID]** Seluruh {report.blocks_checked} blok lolos verifikasi re-komputasi SHA-256, "
            f"prefix PoW `{blockchain.HASH_PREFIX}`, tautan `previous_hash`, tag autentikasi AES-256-GCM, dan HMAC tip anchor "
            f"({report.elapsed_ms:.2f} ms)."
        )
    else:
        st.error(
            f"🚨 **[PELANGGARAN INTEGRITAS TERDETEKSI]** Ditemukan {len(report.issues)} pelanggaran pada blok bukti:"
        )
        for issue in report.issues:
            st.warning(f"- **BLOK #{issue.index}** [`{issue.kind}`]: {issue.detail}")

    sub_mine, sub_explore, sub_tamper = st.tabs([
        "⛏️ [01] TAMBANG BLOK BUKTI BARU (MINE PoW)",
        "📦 [02] PENJELAJAH BLOK & DEKRIPSI GCM",
        "🧪 [03] LABORATORIUM SIMULASI TAMPERING",
    ])

    with sub_mine:
        c1, c2 = st.columns(2)
        asset_type = c1.selectbox("Klasifikasi Aset Forensik", blockchain.ASSET_TYPES)
        asset_name = c2.text_input("Kodefikasi / Nama Bukti", placeholder="BUKTI_FORENSIK_LAPTOP_TARGET_01")

        metadata: dict = {}
        if asset_type == "Secret Coordinates":
            c_lat, c_lon, c_alt = st.columns(3)
            lat = c_lat.number_input("Latitude", value=-6.200000, format="%.6f")
            lon = c_lon.number_input("Longitude", value=106.816666, format="%.6f")
            alt = c_alt.number_input("Elevasi (m)", value=32.0, format="%.1f")
            notes = st.text_area("Catatan Operasi Lapangan")
            metadata = {"latitude": lat, "longitude": lon, "elevation_m": alt, "notes": notes}
        elif asset_type == "Digital Certificate":
            c_ca, c_sn = st.columns(2)
            ca = c_ca.text_input("Otoritas Penerbit (CA)", value="Krypt Vault Root Cyber CA")
            sn = c_sn.text_input("Nomor Seri Sertifikat", value="CERT-2026-X88")
            thumb = st.text_input("Thumbprint SHA-256 Sertifikat")
            metadata = {"issuer": ca, "serial_number": sn, "thumbprint": thumb}
        else:
            c_clr, c_ref = st.columns(2)
            clr = c_clr.selectbox("Klasifikasi Bukti", ["TOP SECRET // BLACK ICE", "CONFIDENTIAL", "RESTRICTED"])
            ref = c_ref.text_input("Nomor Laporan Polisi / Kasus", value="LP-CYBER-2026-11-A")
            desc = st.text_area("Rincian Bukti & Rantai Serah Terima (Chain of Custody)")
            metadata = {"classification": clr, "case_ref": ref, "details": desc}

        if st.button("⛏️ SEGEL AES-256-GCM & TAMBANG BLOK (PoW SHA-256)", type="primary"):
            if not asset_name.strip():
                st.warning("Nama Aset Bukti wajib diisi.")
            else:
                try:
                    mined = blockchain.add_asset(asset_name, asset_type, metadata, owner=username)
                    st.session_state["last_verification"] = blockchain.verify_chain()
                    ui_cyberpunk.log_cli(
                        "POW_LEDGER",
                        f"Mined Block #{mined.block.index} ('{mined.block.asset_name}') — Nonce: {mined.block.nonce}",
                        digest=mined.block.current_hash,
                        level="OK",
                    )
                    st.success(
                        f"Blok **#{mined.block.index}** berhasil ditambang & dikomit! "
                        f"SHA-256: `{mined.block.current_hash}` | Nonce: `{mined.block.nonce}` "
                        f"({mined.attempts} hash dihitung dalam {mined.elapsed_ms:.2f} ms)."
                    )
                except Exception as exc:
                    ui_cyberpunk.log_cli("POW_LEDGER", f"Mining error: {exc}", level="CRIT")
                    st.error(str(exc))

    with sub_explore:
        chain = blockchain.get_chain()
        for blk in reversed(chain):
            badge = "🟢 [VALID]" if report.block_status.get(blk.index) == "OK" else "🔴 [TAMPERED]"
            with st.expander(f"{badge} BLOK #{blk.index:03d} // {blk.asset_name} // {blk.timestamp}", expanded=(blk.index == len(chain) - 1)):
                st.markdown(
                    f"- **`CURRENT_HASH (SHA-256)`**: `{blk.current_hash}`\n"
                    f"- **`PREVIOUS_HASH`**: `{blk.previous_hash}`\n"
                    f"- **`POW_NONCE`**: `{blk.nonce}`\n"
                    f"- **`AES_256_GCM_CIPHERTEXT`**: `{blk.encrypted_asset_metadata[:70]}...`"
                )
                if st.button(f"🔓 BUKA SEGEL AES-256-GCM // BLOK #{blk.index}", key=f"blk_gcm_{blk.index}"):
                    try:
                        decrypted = blockchain.decrypt_metadata(blk)
                        ui_cyberpunk.log_cli(
                            "POW_LEDGER",
                            f"Decrypted metadata for Block #{blk.index}",
                            digest=blk.current_hash,
                            level="OK",
                        )
                        st.json(decrypted)
                    except Exception as exc:
                        ui_cyberpunk.log_cli("POW_LEDGER", f"GCM auth failure on Block #{blk.index}: {exc}", level="CRIT")
                        st.error(f"Autentikasi AES-256-GCM gagal: {exc}")

    with sub_tamper:
        st.info(
            "Simulasikan serangan lawan langsung pada tabel `blockchain_ledger` SQLite, "
            "kemudian klik tombol **VERIFY_CHAIN_INTEGRITY** di atas untuk mendemonstrasikan deteksi otomatis."
        )
        chain = blockchain.get_chain()
        c_t1, c_t2 = st.columns(2)
        target_idx = c_t1.selectbox("Target Blok Yang Akan Dimanipulasi", [b.index for b in chain])
        tamper_mode = c_t2.selectbox(
            "Jenis Serangan Manipulasi",
            list(blockchain.TAMPER_MODES.keys()),
            format_func=lambda k: blockchain.TAMPER_MODES[k],
        )

        b1, b2 = st.columns(2)
        if b1.button("💥 INJEKSIKAN SERANGAN TAMPERING KE SQLITE", use_container_width=True):
            res_msg = blockchain.simulate_tampering(int(target_idx), tamper_mode)
            st.session_state["last_verification"] = blockchain.verify_chain()
            ui_cyberpunk.log_cli(
                "POW_LEDGER",
                f"Tamper simulation injected into Block #{target_idx} ({tamper_mode}): {res_msg}",
                level="CRIT",
            )
            st.rerun()
        if b2.button("♻️ RESET & PULIHKAN LEDGER KE BLOK GENESIS", use_container_width=True):
            blockchain.reset_ledger()
            st.session_state["last_verification"] = blockchain.verify_chain()
            ui_cyberpunk.log_cli("POW_LEDGER", "Blockchain ledger reset to Genesis Block #0", level="WARN")
            st.rerun()


# --------------------------------------------------------------------------- #
# Main Router & Unified Top Navigation
# --------------------------------------------------------------------------- #
def main() -> None:
    extra = [st.session_state.custom_dongle_path] if st.session_state.custom_dongle_path else None
    dongle_status = dongle_guard.scan_for_dongle(extra_paths=extra)

    # State transition logger
    dongle_state_sig = (dongle_status.valid, dongle_status.dongle_id, dongle_status.message)
    if st.session_state.last_logged_dongle_state != dongle_state_sig:
        st.session_state.last_logged_dongle_state = dongle_state_sig
        if dongle_status.valid:
            ui_cyberpunk.log_cli(
                "DONGLE_GUARD",
                f"HMAC-SHA256 hardware token authenticated at '{dongle_status.path}'",
                digest=dongle_status.dongle_id,
                level="OK",
            )
        else:
            ui_cyberpunk.log_cli(
                "DONGLE_GUARD",
                f"SECURITY_HALT: {dongle_status.message}",
                digest=ui_cyberpunk.sha256_hex(dongle_status.message),
                level="CRIT",
            )

    # GATE 01: Hardware Dongle Required
    if not dongle_status.valid:
        st.session_state.authenticated_user = None
        render_dongle_lock_screen(dongle_status)
        return

    # GATE 02: Realtime Optical Face Scanner + PBKDF2-SHA256 Login
    if not st.session_state.authenticated_user:
        render_auth_screen(dongle_status)
        return

    # GATE 03: Authenticated Vault Core
    username = st.session_state.authenticated_user

    # Render Executive Header
    render_app_header(username, dongle_status)

    NAV_OPTIONS = [
        "📊 Dashboard",
        "📝 Super Enkripsi Teks",
        "📁 Enkripsi Berkas (ChaCha20)",
        "🖼️ Steganografi Citra (LSB)",
        "🔍 Inspeksi Database SQLite",
        "⛓️ Blockchain Ledger (PoW)",
        "🔑 Pengaturan Kunci USB",
    ]

    current_tab = st.session_state.get("active_nav_tab", NAV_OPTIONS[0])
    if current_tab not in NAV_OPTIONS:
        current_tab = NAV_OPTIONS[0]

    # Clean Horizontal Navigation Bar
    c_nav, c_lock = st.columns([5.5, 1.2])
    with c_nav:
        selected_tab = st.pills(
            "Navigasi Modul",
            options=NAV_OPTIONS,
            default=current_tab,
            label_visibility="collapsed",
            key="pills_nav_tab",
        )
        if selected_tab and selected_tab != current_tab:
            st.session_state.active_nav_tab = selected_tab
            st.rerun()

    with c_lock:
        if st.button("🚪 Kunci Sesi", use_container_width=True, help="Kunci sesi vault dan keluar"):
            ui_cyberpunk.log_cli("KERNEL", f"Analyst '{username}' locked Krypt Vault session", level="WARN")
            st.session_state.authenticated_user = None
            st.session_state.auth_similarity = None
            st.rerun()

    # Back to Dashboard button on sub-screens
    if current_tab != "📊 Dashboard":
        c_back, _ = st.columns([2, 5])
        with c_back:
            if st.button("⬅️ Kembali ke Dashboard Utama", key="btn_back_to_dash_sub"):
                st.session_state.active_nav_tab = "📊 Dashboard"
                st.rerun()
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # Optional Clean Sidebar for quick overview
    with st.sidebar:
        st.markdown("### ⚡ Krypt Vault")
        st.caption("FORENSIC SECURITY SUITE")
        st.success(f"👤 ANALIS: **{username.upper()}**")
        if st.session_state.auth_similarity is not None:
            st.caption(f"🧬 KECOCOKAN WAJAH: **{st.session_state.auth_similarity:.1%}** (`AES-128-EAX`)")
        st.caption(f"🔑 HARDWARE KEY: **{dongle_status.label}**")
        st.divider()

        st.markdown("#### 🚀 Lompat Cepat")
        for opt in NAV_OPTIONS:
            if st.button(opt, key=f"sidebar_btn_{opt}", use_container_width=True):
                st.session_state.active_nav_tab = opt
                st.rerun()

        st.divider()
        if st.button("🧹 Bersihkan Buffer Log", use_container_width=True):
            st.session_state.cli_logs = []
            ui_cyberpunk.log_cli("KERNEL", "Console buffer flushed", level="INFO")
            st.rerun()

    # Route screen content based on active tab
    if current_tab == "📊 Dashboard":
        render_dashboard_hub(username, dongle_status)
    elif current_tab == "📝 Super Enkripsi Teks":
        render_super_encryption_tab(username)
    elif current_tab == "📁 Enkripsi Berkas (ChaCha20)":
        render_file_crypto_tab(username)
    elif current_tab == "🖼️ Steganografi Citra (LSB)":
        render_steganography_tab()
    elif current_tab == "🔍 Inspeksi Database SQLite":
        render_database_inspection_tab(username)
    elif current_tab == "⛓️ Blockchain Ledger (PoW)":
        render_blockchain_tab(username)
    elif current_tab == "🔑 Pengaturan Kunci USB":
        render_usb_settings_tab(dongle_status)

    # Bottom Collapsible TTY Telemetry Log
    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    with st.expander("💻 Log Telemetri Kriptografi & Terminal TTY (Event Realtime)", expanded=False):
        ui_cyberpunk.render_cli_console("GATE_03 // KRYPT VAULT TELEMETRY LOG")


if __name__ == "__main__":
    main()
