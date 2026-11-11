"""
Krypt Vault - Sistem Brankas Bukti Forensik Siber & Dokumen Intelijen
=====================================================================

Alur aplikasi:
  1. Kunci perangkat keras  : flashdisk USB berisi token .krypt_dongle (HMAC-SHA256 + volume serial)
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
import secrets

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
ui.inject_theme()
ui.init_logs()
database.init_db()

for _k, _v in {
    "user": None,
    "similarity": None,
    "page": "Ringkasan",
    "dongle_sig": None,
}.items():
    st.session_state.setdefault(_k, _v)

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
def _short(path: str | None, n: int = 42) -> str:
    if not path:
        return "-"
    return path if len(path) <= n else "..." + path[-(n - 3):]


def _capture_face(key: str) -> bytes | None:
    """Real face acquisition: webcam snapshot or uploaded photo."""
    mode = st.radio(
        "Sumber citra wajah",
        ["Kamera", "Unggah foto"],
        horizontal=True,
        key=f"{key}_mode",
    )
    if mode == "Kamera":
        shot = st.camera_input("Posisikan wajah di tengah bingkai, lalu ambil foto", key=f"{key}_cam")
        return shot.getvalue() if shot else None
    up = st.file_uploader("Foto wajah (PNG/JPG)", type=["png", "jpg", "jpeg"], key=f"{key}_up")
    return up.getvalue() if up else None


@st.fragment(run_every=4)
def _dongle_watch(expected_id: str | None) -> None:
    """Re-scan the USB bus every few seconds; lock the app if the key is removed."""
    status = dongle_guard.scan_for_dongle()
    if not status.valid or status.dongle_id != expected_id:
        ui.log("DONGLE", "Kunci perangkat keras dicabut - sesi dikunci", level="CRIT")
        st.session_state.user = None
        st.rerun(scope="app")


# =========================================================================== #
# Gate 1 - Hardware key
# =========================================================================== #
def screen_hardware_gate(status: dongle_guard.DongleStatus) -> None:
    ui.brand()
    ui.steps(1)
    ui.page_header(
        "Kontrol akses",
        "Hubungkan kunci perangkat keras",
        "Krypt Vault hanya dapat dibuka ketika flashdisk USB yang telah diinisialisasi terpasang. "
        "Token pada flashdisk ditandatangani HMAC-SHA256 dan diikat ke nomor seri volume, sehingga "
        "salinan token di media lain akan ditolak.",
    )

    if status.failures:
        st.error("Token ditemukan tetapi tidak valid: " + "; ".join(f"{_short(k, 20)} - {v}" for k, v in status.failures.items()))

    drives = dongle_guard.list_all_drives_for_provisioning()
    usb = [d for d in drives if d.get("is_usb")]

    left, right = st.columns([1.35, 1], gap="large")
    with left:
        with st.container(border=True):
            st.markdown("### Flashdisk terdeteksi")
            if usb:
                rows = "".join(
                    f"<tr><td class='mono'>{html.escape(d['drive'])}</td><td>{html.escape(d['type_name'])}</td>"
                    f"<td class='mono'>{html.escape(d['volume_serial'])}</td></tr>"
                    for d in usb
                )
                st.markdown(
                    f"<table class='kv-table'><tr><th>Drive</th><th>Tipe</th><th>Volume serial</th></tr>{rows}</table>",
                    unsafe_allow_html=True,
                )
                st.write("")
                target = st.selectbox("Flashdisk yang akan dijadikan kunci", [d["drive"] for d in usb])
                label = st.text_input("Label kunci", value="Kunci Analis Forensik")
                st.caption("Inisialisasi hanya menambahkan berkas tersembunyi .krypt_dongle. Data lain di flashdisk tidak diubah.")
                if st.button("Inisialisasi sebagai kunci", type="primary", use_container_width=True):
                    ok, msg = dongle_guard.provision_drive(target, label=label)
                    ui.log("DONGLE", msg, level="OK" if ok else "CRIT")
                    (st.success if ok else st.error)(msg)
                    if ok:
                        st.rerun()
            else:
                st.markdown(ui.chip("Tidak ada flashdisk", "warn"), unsafe_allow_html=True)
                st.write(
                    "Pasang flashdisk USB ke komputer. Jika flashdisk sudah pernah diinisialisasi, "
                    "vault akan langsung terbuka setelah dipindai."
                )
            if st.button("Pindai ulang port USB", use_container_width=True):
                st.rerun()

    with right:
        with st.container(border=True):
            st.markdown("### Cara kerja verifikasi")
            st.markdown(
                "1. Aplikasi memindai seluruh drive bertipe *removable*.\n"
                "2. Berkas `.krypt_dongle` dibaca dan field-nya dikanonikalisasi.\n"
                "3. Tag HMAC-SHA256 dihitung ulang dengan kunci turunan HKDF dan dibandingkan secara constant-time.\n"
                "4. Nomor seri volume dicocokkan untuk mencegah kloning token.\n"
                "5. Saat flashdisk dicabut, sesi terkunci otomatis dalam beberapa detik."
            )
        with st.expander("Mode presentasi tanpa flashdisk"):
            st.caption(
                "Membuat token virtual di folder lokal virtual_usb. Hanya untuk demonstrasi ketika port USB tidak tersedia."
            )
            if st.button("Aktifkan token virtual", use_container_width=True):
                dongle_guard.mount_virtual_dongle(label="Token Virtual Presentasi")
                ui.log("DONGLE", "Token virtual diaktifkan", level="WARN")
                st.rerun()

    with st.expander("Log aktivitas"):
        ui.render_log()


# =========================================================================== #
# Gate 2 - Identity & biometrics
# =========================================================================== #
def screen_identity(status: dongle_guard.DongleStatus) -> None:
    _dongle_watch(status.dongle_id)
    ui.brand()
    ui.steps(2)
    ui.page_header(
        "Autentikasi dua faktor",
        "Verifikasi identitas operator",
        "Faktor pengetahuan diverifikasi dengan PBKDF2-HMAC-SHA256 (600.000 iterasi). "
        "Faktor biometrik dibandingkan dengan template wajah yang tersimpan terenkripsi AES-128-EAX; "
        "kunci dekripsinya hanya dapat diturunkan dari kata sandi yang benar.",
    )
    st.markdown(
        ui.chip(f"Kunci: {status.label or '-'}", "ok") + ui.chip(f"Lokasi: {_short(status.path, 30)}"),
        unsafe_allow_html=True,
    )
    st.write("")

    tab_in, tab_up = st.tabs(["Masuk", "Daftarkan operator baru"])

    with tab_in:
        if database.count_users() == 0:
            st.info("Belum ada operator terdaftar. Buka tab 'Daftarkan operator baru' untuk mendaftarkan akun pertama.")
        c1, c2 = st.columns([1, 1.1], gap="large")
        with c1:
            with st.container(border=True):
                st.markdown("### Faktor 1 - Kredensial")
                user = st.text_input("Nama pengguna", key="li_user")
                pw = st.text_input("Kata sandi", type="password", key="li_pw")
        with c2:
            with st.container(border=True):
                st.markdown("### Faktor 2 - Wajah")
                face = _capture_face("li")
                st.caption(f"Posisikan wajah menghadap kamera. Sistem menggunakan penyelarasan spasial multi-skala (ambang batas: {auth_biometric.MATCH_THRESHOLD:.0%}).")
        if st.button("Verifikasi dan masuk", type="primary", use_container_width=True):
            if not (user and pw and face):
                st.warning("Isi nama pengguna, kata sandi, dan ambil citra wajah terlebih dahulu.")
            else:
                with st.spinner("Menurunkan kunci PBKDF2 dan membuka template biometrik..."):
                    res = auth_biometric.authenticate_user(user.strip().lower(), pw, face)
                digest = ui.sha256_hex(face)
                if res.success:
                    ui.log("AUTH", f"Login berhasil: {res.username} (kemiripan {res.similarity:.1%})", digest, "OK")
                    st.session_state.user = res.username
                    st.session_state.similarity = res.similarity
                    st.session_state.page = "Ringkasan"
                    st.rerun()
                else:
                    sim = f" Skor kemiripan wajah: {res.similarity:.1%} (ambang batas: {auth_biometric.MATCH_THRESHOLD:.0%})." if res.similarity is not None else ""
                    ui.log("AUTH", f"Login ditolak untuk {user}: {res.message}", digest, "CRIT")
                    st.error(res.message + sim)

    with tab_up:
        c1, c2 = st.columns([1, 1.1], gap="large")
        with c1:
            with st.container(border=True):
                st.markdown("### Data operator")
                ru = st.text_input("Nama pengguna (3-32 karakter: a-z, 0-9, _ . -)", key="rg_user")
                rp = st.text_input("Kata sandi (minimal 8 karakter, huruf dan angka)", type="password", key="rg_pw")
                rp2 = st.text_input("Ulangi kata sandi", type="password", key="rg_pw2")
        with c2:
            with st.container(border=True):
                st.markdown("### Pendaftaran wajah")
                rface = _capture_face("rg")
                st.caption("Posisikan wajah di depan kamera. Algoritma penyelarasan multi-skala mentolerir pergeseran wajar posisi duduk.")
        if st.button("Daftarkan operator", type="primary", use_container_width=True):
            if rp != rp2:
                st.error("Kedua kata sandi tidak sama.")
            elif not (ru and rp and rface):
                st.warning("Lengkapi data operator dan citra wajah.")
            else:
                with st.spinner("Membuat verifier PBKDF2 dan menyegel template wajah..."):
                    res = auth_biometric.register_user(ru.strip().lower(), rp, rface)
                ui.log("AUTH", f"Registrasi {ru}: {res.message}", ui.sha256_hex(rface), "OK" if res.success else "WARN")
                (st.success if res.success else st.error)(res.message + (" Silakan masuk melalui tab Masuk." if res.success else ""))


# =========================================================================== #
# Workspace pages
# =========================================================================== #
def page_overview(user: str, status: dongle_guard.DongleStatus) -> None:
    blockchain.ensure_genesis()
    stats = database.get_user_stats(user)
    report = blockchain.verify_chain()
    ui.page_header("Ruang kerja", f"Selamat datang, {user}", "Ringkasan kondisi vault dan status setiap mekanisme kriptografi.")

    m = st.columns(4)
    m[0].metric("Laporan terenkripsi", stats["secret_messages"])
    m[1].metric("Berkas terenkripsi", stats["encrypted_files"])
    m[2].metric("Blok ledger", stats["ledger_blocks"])
    m[3].metric("Integritas ledger", "Valid" if report.valid else "Rusak")

    if not report.valid:
        st.error(f"Ledger terdeteksi dimanipulasi ({len(report.issues)} temuan). Buka halaman Ledger Aset untuk audit.")

    st.write("")
    c1, c2 = st.columns([1.6, 1], gap="large")
    with c1:
        with st.container(border=True):
            st.markdown("### Pemetaan kriteria tugas akhir")
            rows = [
                ("Login biometrik dan dongle", "Token HMAC-SHA256 pada flashdisk + verifikasi wajah", "Kunci Perangkat"),
                ("Login dengan algoritma kriptografi", "PBKDF2-HMAC-SHA256, HKDF, AES-128-EAX", "Halaman masuk"),
                ("Super enkripsi teks", "Extended Vigenere + AES-256-CBC", "Enkripsi Teks"),
                ("Enkripsi berkas (algoritma berbeda)", "ChaCha20 stream cipher", "Enkripsi Berkas"),
                ("Enkripsi basis data", "Ciphertext at-rest di SQLite", "Basis Data"),
                ("Steganografi gambar", "LSB pada kanal RGB PNG", "Steganografi"),
                ("Blockchain aset penting", "SHA-256 Proof-of-Work + AES-256-GCM", "Ledger Aset"),
            ]
            body = "".join(f"<tr><td>{a}</td><td class='mono'>{b}</td><td>{c}</td></tr>" for a, b, c in rows)
            st.markdown(
                f"<table class='kv-table'><tr><th>Kriteria</th><th>Implementasi</th><th>Halaman</th></tr>{body}</table>",
                unsafe_allow_html=True,
            )
    with c2:
        with st.container(border=True):
            st.markdown("### Sesi aktif")
            ui.kv_grid([
                ("Operator", user),
                ("Kemiripan wajah", f"{st.session_state.similarity:.1%}" if st.session_state.similarity is not None else "-"),
                ("Kunci", status.label or "-"),
                ("ID kunci", (status.dongle_id or "-")[:16]),
                ("Volume serial", status.volume_serial or "virtual"),
            ])


def page_text(user: str) -> None:
    ui.page_header(
        "Kriteria 3",
        "Super enkripsi teks",
        "Lapisan pertama mengenkripsi plaintext dengan Extended Vigenere (modulo 256). Hasilnya dienkripsi lagi "
        "dengan AES-256-CBC menggunakan kunci PBKDF2, salt dan IV acak, serta padding PKCS#7.",
    )
    t_enc, t_dec, t_list = st.tabs(["Enkripsi", "Dekripsi", "Arsip"])

    with t_enc:
        with st.form("enc_text"):
            title = st.text_input("Judul laporan")
            plain = st.text_area("Isi laporan", height=150)
            c1, c2 = st.columns(2)
            vk = c1.text_input("Kunci Vigenere (lapisan 1)", type="password")
            ak = c2.text_input("Passphrase AES-256 (lapisan 2)", type="password")
            go = st.form_submit_button("Enkripsi dan simpan", type="primary")
        if go:
            if not (title and plain and vk and ak):
                st.warning("Semua kolom wajib diisi.")
            else:
                res = super_encryption.super_encrypt_detailed(plain, vk, ak)
                mid = database.insert_secret_message(user, title, res["token"], super_encryption.ALGORITHM_ID)
                ui.log("TEXT", f"Laporan #{mid} '{title}' dienkripsi", ui.sha256_hex(res["token"]), "OK")
                st.session_state.text_result = res
                st.success(f"Laporan tersimpan sebagai rekaman #{mid}.")
        res = st.session_state.get("text_result")
        if res:
            with st.container(border=True):
                st.markdown("### Hasil per lapisan")
                st.markdown("**Lapisan 1 - Vigenere (Base64)**")
                st.code(res["vigenere_b64"], language=None, wrap_lines=True)
                st.markdown("**Lapisan 2 - AES-256-CBC**")
                ui.kv_grid([("Salt", res["salt_hex"]), ("IV", res["iv_hex"]), ("Ciphertext", res["aes_ciphertext_hex"][:96] + "...")])
                st.markdown("**Token akhir (disimpan di basis data)**")
                st.code(res["token"], language=None, wrap_lines=True)

    with t_dec:
        msgs = database.list_secret_messages(user)
        src = st.radio("Sumber ciphertext", ["Arsip", "Tempel token"], horizontal=True)
        token = ""
        if src == "Arsip":
            if msgs:
                opts = {f"#{m['id']} - {m['title']}": m for m in msgs}
                token = opts[st.selectbox("Pilih laporan", list(opts))]["ciphertext"]
                st.code(token, language=None, wrap_lines=True)
            else:
                st.info("Arsip masih kosong.")
        else:
            token = st.text_area("Token Base64", height=110)
        c1, c2 = st.columns(2)
        vk = c1.text_input("Kunci Vigenere", type="password", key="dvk")
        ak = c2.text_input("Passphrase AES-256", type="password", key="dak")
        if st.button("Dekripsi", type="primary"):
            try:
                out = super_encryption.super_decrypt_detailed(token.strip(), vk, ak)
                ui.log("TEXT", "Dekripsi laporan berhasil", ui.sha256_hex(out["plaintext"]), "OK")
                st.markdown("**Setelah membuka AES-256-CBC (masih tersandi Vigenere)**")
                st.code(out["vigenere_b64"], language=None, wrap_lines=True)
                st.markdown("**Plaintext**")
                st.text_area("Plaintext", out["plaintext"], height=140, label_visibility="collapsed")
            except Exception as exc:
                ui.log("TEXT", f"Dekripsi gagal: {exc}", level="CRIT")
                st.error("Dekripsi gagal. Kunci salah atau token rusak.")

    with t_list:
        msgs = database.list_secret_messages(user)
        if not msgs:
            st.info("Belum ada laporan.")
        for m in msgs:
            with st.container(border=True):
                a, b = st.columns([5, 1])
                a.markdown(f"**#{m['id']} - {html.escape(m['title'])}**  \n<span class='kv-chip'>{m['algorithm']}</span> {m['created_at']}", unsafe_allow_html=True)
                if b.button("Hapus", key=f"delm{m['id']}"):
                    database.delete_secret_message(m["id"], user)
                    ui.log("TEXT", f"Laporan #{m['id']} dihapus", level="WARN")
                    st.rerun()


def page_files(user: str) -> None:
    ui.page_header(
        "Kriteria 4",
        "Enkripsi berkas",
        "Berkas dienkripsi sebagai aliran byte dengan ChaCha20 (kunci 256-bit dari PBKDF2, nonce 96-bit). "
        "Hash SHA-256 plaintext disimpan untuk memverifikasi integritas setelah dekripsi.",
    )
    t_enc, t_dec, t_vault = st.tabs(["Enkripsi", "Dekripsi berkas .krypt.enc", "Arsip vault"])

    with t_enc:
        up = st.file_uploader("Pilih berkas", key="fe_up")
        pw = st.text_input("Passphrase", type="password", key="fe_pw")
        if st.button("Enkripsi berkas", type="primary", disabled=up is None):
            if not pw:
                st.warning("Passphrase wajib diisi.")
            else:
                raw = up.getvalue()
                bundle = file_crypto.encrypt_file_bytes(raw, pw)
                pkg = file_crypto.pack_bagus_envelope(bundle, up.name, up.type)
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
        fr = st.session_state.get("file_result")
        if fr:
            name, size, bundle, pkg = fr
            with st.container(border=True):
                st.success(f"'{name}' berhasil dienkripsi dan disimpan di arsip vault.")
                ui.kv_grid([
                    ("Algoritma", bundle.algorithm), ("Ukuran asli", f"{size} byte"),
                    ("SHA-256 plaintext", bundle.sha256_plain), ("Salt", bundle.kdf_salt), ("Nonce", bundle.nonce),
                    ("Pratinjau ciphertext", bundle.ciphertext[:32].hex() + "..."),
                ])
                st.write("")
                st.download_button(f"Unduh {name}.krypt.enc", pkg, file_name=f"{name}.krypt.enc", type="primary")

    with t_dec:
        enc = st.file_uploader("Berkas .krypt.enc", type=["enc"], key="fd_up")
        pw = st.text_input("Passphrase", type="password", key="fd_pw")
        if st.button("Dekripsi berkas", type="primary", disabled=enc is None):
            try:
                plain, meta = file_crypto.unpack_bagus_envelope(enc.getvalue(), pw)
                st.session_state.file_dec = (plain, meta)
                ui.log("FILE", f"Berkas '{meta['original_name']}' didekripsi, SHA-256 cocok", meta["sha256_plain"], "OK")
            except Exception as exc:
                st.session_state.file_dec = None
                ui.log("FILE", f"Dekripsi gagal: {exc}", level="CRIT")
                st.error("Dekripsi gagal. Passphrase salah atau berkas rusak.")
        fd = st.session_state.get("file_dec")
        if fd:
            plain, meta = fd
            st.success(f"Integritas terverifikasi: {meta['original_name']} ({len(plain)} byte).")
            st.download_button(f"Unduh {meta['original_name']}", plain, file_name=meta["original_name"], type="primary")

    with t_vault:
        files = database.list_encrypted_files(user)
        if not files:
            st.info("Arsip berkas masih kosong.")
        for f in files:
            with st.container(border=True):
                st.markdown(f"**#{f['id']} - {html.escape(f['original_name'])}**  \n{f['size_bytes']} byte, {f['created_at']}")
                c1, c2, c3 = st.columns([3, 1, 1])
                pw = c1.text_input("Passphrase", type="password", key=f"vpw{f['id']}", label_visibility="collapsed", placeholder="Passphrase")
                if c2.button("Dekripsi", key=f"vdec{f['id']}", use_container_width=True):
                    try:
                        ct = (config.FILES_DIR / f["stored_name"]).read_bytes()
                        plain = file_crypto.decrypt_file_bytes(ct, pw, f["kdf_salt"], f["nonce"], f["sha256_plain"])
                        st.session_state[f"vault_plain_{f['id']}"] = plain
                        ui.log("FILE", f"Arsip #{f['id']} didekripsi", f["sha256_plain"], "OK")
                    except Exception:
                        st.error("Passphrase salah atau integritas gagal.")
                if c3.button("Hapus", key=f"vdel{f['id']}", use_container_width=True):
                    try:
                        (config.FILES_DIR / f["stored_name"]).unlink(missing_ok=True)
                    except OSError:
                        pass
                    database.delete_encrypted_file(f["id"], user)
                    ui.log("FILE", f"Arsip #{f['id']} dihapus", level="WARN")
                    st.rerun()
                plain = st.session_state.get(f"vault_plain_{f['id']}")
                if plain is not None:
                    st.download_button(f"Unduh {f['original_name']}", plain, file_name=f["original_name"],
                                       mime=f["mime_type"] or "application/octet-stream", key=f"vdl{f['id']}")


def page_stego() -> None:
    ui.page_header(
        "Kriteria 6",
        "Steganografi citra",
        "Pesan disisipkan ke bit paling tidak signifikan (LSB) kanal R, G, B setiap piksel dan diakhiri penanda. "
        "Hasil selalu disimpan sebagai PNG agar tidak rusak oleh kompresi. Passphrase opsional mengenkripsi pesan sebelum disisipkan.",
    )
    t_in, t_out = st.tabs(["Sisipkan pesan", "Ekstrak pesan"])

    with t_in:
        cover = st.file_uploader("Citra sampul (PNG, BMP, JPG)", type=["png", "bmp", "jpg", "jpeg"], key="sg_cover")
        msg = st.text_area("Pesan rahasia", height=120)
        pw = st.text_input("Passphrase (opsional)", type="password", key="sg_pw")
        if cover:
            st.caption(f"Kapasitas maksimum: {steganography.calculate_capacity(cover.getvalue()):,} byte")
        if st.button("Sisipkan", type="primary", disabled=cover is None):
            if not msg.strip():
                st.warning("Pesan tidak boleh kosong.")
            else:
                try:
                    out = steganography.embed_message_lsb(cover.getvalue(), msg, pw or None)
                    st.session_state.stego_out = (cover.getvalue(), out)
                    ui.log("STEGO", f"{len(msg.encode())} byte disisipkan ke '{cover.name}'", ui.sha256_hex(out), "OK")
                except Exception as exc:
                    st.error(f"Gagal menyisipkan: {exc}")
        so = st.session_state.get("stego_out")
        if so:
            a, b = st.columns(2)
            a.image(so[0], caption="Citra asli", use_container_width=True)
            b.image(so[1], caption="Citra stego (berisi pesan)", use_container_width=True)
            st.download_button("Unduh citra stego (PNG)", so[1], file_name="krypt_stego.png", mime="image/png", type="primary")

    with t_out:
        img = st.file_uploader("Citra stego (PNG)", type=["png", "bmp"], key="sg_ext")
        pw = st.text_input("Passphrase (jika dipakai saat menyisipkan)", type="password", key="sg_ext_pw")
        if st.button("Ekstrak", type="primary", disabled=img is None):
            try:
                text = steganography.extract_message_lsb(img.getvalue(), pw or None)
                ui.log("STEGO", f"Pesan diekstrak ({len(text)} karakter)", ui.sha256_hex(text), "OK")
                st.text_area("Pesan tersembunyi", text, height=140)
            except Exception as exc:
                st.error(f"Tidak ada pesan valid atau passphrase salah: {exc}")


def page_database(user: str) -> None:
    ui.page_header(
        "Kriteria 5",
        "Audit enkripsi basis data",
        "Semua data sensitif disimpan di storage/vault.db dalam bentuk ciphertext, hash, atau BLOB terenkripsi. "
        "Halaman ini menampilkan isi mentah tabel dan menyediakan uji pencarian langsung pada berkas basis data.",
    )
    raw = database.get_raw_records_for_inspection(user)
    t_raw, t_probe, t_compare = st.tabs(["Isi mentah tabel", "Uji pencarian plaintext", "Dekripsi rekaman"])

    with t_raw:
        for name in ("users", "secret_messages", "encrypted_files", "blockchain_ledger"):
            st.markdown(f"**Tabel `{name}`** - {len(raw[name])} baris")
            if raw[name]:
                st.dataframe(raw[name], use_container_width=True, hide_index=True)

    with t_probe:
        st.write(
            "Masukkan potongan teks yang pernah Anda enkripsi (misalnya isi laporan). Aplikasi akan membaca berkas "
            "vault.db byte demi byte dan mencari teks tersebut. Jika enkripsi at-rest berjalan, isi laporan tidak akan ditemukan."
        )
        needle = st.text_input("Teks yang dicari")
        if st.button("Cari di vault.db", type="primary") and needle:
            blob = config.DB_PATH.read_bytes()
            found = needle.encode("utf-8") in blob
            ui.log("DB", f"Pencarian plaintext di vault.db: {'DITEMUKAN' if found else 'tidak ditemukan'}", level="WARN" if found else "OK")
            if found:
                st.warning("Teks ditemukan di berkas basis data. Kemungkinan teks ini adalah kolom non-rahasia seperti judul atau nama pengguna.")
            else:
                st.success(f"Teks tidak ditemukan dalam {len(blob):,} byte vault.db. Data tersimpan dalam bentuk terenkripsi.")
            st.markdown("**Cuplikan 256 byte pertama vault.db (hex)**")
            st.code(blob[:256].hex(" "), language=None, wrap_lines=True)

    with t_compare:
        msgs = raw["secret_messages"]
        if not msgs:
            st.info("Belum ada laporan terenkripsi.")
        else:
            opts = {f"#{m['id']} - {m['title']}": m for m in msgs}
            m = opts[st.selectbox("Rekaman", list(opts))]
            c1, c2 = st.columns(2)
            vk = c1.text_input("Kunci Vigenere", type="password", key="dbvk")
            ak = c2.text_input("Passphrase AES-256", type="password", key="dbak")
            a, b = st.columns(2, gap="large")
            with a:
                with st.container(border=True):
                    st.markdown("### Tersimpan di disk")
                    st.code(m["ciphertext"], language=None, wrap_lines=True)
            with b:
                with st.container(border=True):
                    st.markdown("### Setelah didekripsi")
                    if vk and ak:
                        try:
                            st.write(super_encryption.super_decrypt(m["ciphertext"], vk, ak))
                        except Exception:
                            st.error("Kunci salah.")
                    else:
                        st.caption("Masukkan kedua kunci untuk melihat plaintext.")


def page_ledger(user: str) -> None:
    blockchain.ensure_genesis()
    ui.page_header(
        "Kriteria 7",
        "Ledger aset penting",
        f"Setiap aset dicatat sebagai blok yang metadatanya dienkripsi AES-256-GCM, ditautkan ke hash blok sebelumnya, "
        f"dan ditambang dengan Proof-of-Work SHA-256 (hash harus diawali '{blockchain.HASH_PREFIX}').",
    )
    report = blockchain.verify_chain()
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        if report.valid:
            st.markdown(ui.chip(f"Rantai valid - {report.blocks_checked} blok diverifikasi", "ok"), unsafe_allow_html=True)
        else:
            st.markdown(ui.chip(f"Rantai rusak - {len(report.issues)} temuan", "bad"), unsafe_allow_html=True)
    if c2.button("Verifikasi ulang", use_container_width=True):
        ui.log("LEDGER", f"Verifikasi rantai: valid={report.valid}", level="OK" if report.valid else "CRIT")
        st.rerun()
    c3.download_button("Ekspor JSON", blockchain.export_chain_json(), file_name="krypt_ledger.json", use_container_width=True)
    if not report.valid:
        for i in report.issues:
            st.error(f"Blok #{i.index} - {i.kind}: {i.detail}")

    t_add, t_chain, t_lab = st.tabs(["Catat aset", "Rantai blok", "Uji manipulasi"])

    with t_add:
        with st.form("mine"):
            a1, a2 = st.columns(2)
            kind = a1.selectbox("Jenis aset", blockchain.ASSET_TYPES)
            name = a2.text_input("Nama aset")
            desc = st.text_area("Keterangan / isi aset (akan dienkripsi)", height=100)
            go = st.form_submit_button("Tambang dan catat blok", type="primary")
        if go:
            if not name:
                st.warning("Nama aset wajib diisi.")
            else:
                with st.spinner("Menambang Proof-of-Work..."):
                    r = blockchain.add_asset(name, kind, {"keterangan": desc, "jenis": kind}, owner=user)
                ui.log("LEDGER", f"Blok #{r.block.index} ditambang ({r.attempts} percobaan)", r.block.current_hash, "OK")
                st.success(f"Blok #{r.block.index} tercatat. Nonce {r.block.nonce}, {r.attempts} hash dalam {r.elapsed_ms:.1f} ms.")
                st.code(r.block.current_hash, language=None)

    with t_chain:
        for blk in reversed(blockchain.get_chain()):
            ok = report.block_status.get(blk.index) == "OK"
            with st.container(border=True):
                st.markdown(
                    f"**Blok #{blk.index} - {html.escape(blk.asset_name)}** "
                    + ui.chip("valid" if ok else "rusak", "ok" if ok else "bad"),
                    unsafe_allow_html=True,
                )
                ui.kv_grid([
                    ("Waktu", blk.timestamp), ("Hash", blk.current_hash), ("Hash sebelumnya", blk.previous_hash),
                    ("Nonce", str(blk.nonce)), ("Metadata (AES-GCM)", blk.encrypted_asset_metadata[:80] + "..."),
                ])
                if st.button("Dekripsi metadata", key=f"bd{blk.index}"):
                    try:
                        st.json(blockchain.decrypt_metadata(blk))
                    except Exception as exc:
                        st.error(f"Tag autentikasi AES-GCM gagal: {exc}")

    with t_lab:
        st.write("Simulasikan penyerang yang mengubah tabel ledger langsung di SQLite, lalu lihat deteksinya di bagian atas halaman.")
        chain = blockchain.get_chain()
        l1, l2 = st.columns(2)
        idx = l1.selectbox("Blok target", [b.index for b in chain])
        mode = l2.selectbox("Jenis serangan", list(blockchain.TAMPER_MODES), format_func=lambda k: blockchain.TAMPER_MODES[k])
        b1, b2 = st.columns(2)
        if b1.button("Jalankan serangan", use_container_width=True):
            msg = blockchain.simulate_tampering(int(idx), mode)
            ui.log("LEDGER", f"Simulasi serangan blok #{idx}: {msg}", level="CRIT")
            st.rerun()
        if b2.button("Reset ledger", use_container_width=True):
            blockchain.reset_ledger()
            ui.log("LEDGER", "Ledger di-reset ke blok genesis", level="WARN")
            st.rerun()


def page_hardware(status: dongle_guard.DongleStatus) -> None:
    ui.page_header(
        "Kriteria 1",
        "Kunci perangkat keras",
        "Status token yang sedang membuka vault, serta inisialisasi flashdisk tambahan.",
    )
    c1, c2 = st.columns([1.3, 1], gap="large")
    with c1:
        with st.container(border=True):
            st.markdown("### Token aktif")
            ui.kv_grid([
                ("Label", status.label or "-"), ("ID", status.dongle_id or "-"), ("Lokasi", status.path or "-"),
                ("Volume serial", status.volume_serial or "tidak terikat (virtual)"),
                ("Diterbitkan", status.issued_at or "-"), ("Kedaluwarsa", status.expires_at or "tidak ada"),
                ("Algoritma", "HMAC-SHA256, kunci HKDF 'dongle/hmac-sha256'"),
            ])
    with c2:
        with st.container(border=True):
            st.markdown("### Flashdisk lain")
            usb = [d for d in dongle_guard.list_all_drives_for_provisioning() if d.get("is_usb")]
            if usb:
                target = st.selectbox("Drive", [d["drive"] for d in usb])
                if st.button("Inisialisasi sebagai kunci", type="primary", use_container_width=True):
                    ok, msg = dongle_guard.provision_drive(target)
                    ui.log("DONGLE", msg, level="OK" if ok else "CRIT")
                    (st.success if ok else st.error)(msg)
            else:
                st.caption("Tidak ada flashdisk removable yang terpasang.")
            if dongle_guard.is_virtual_dongle_mounted():
                st.divider()
                if st.button("Nonaktifkan token virtual", use_container_width=True):
                    dongle_guard.unmount_virtual_dongle()
                    st.rerun()


# =========================================================================== #
# Router
# =========================================================================== #
def main() -> None:
    status = dongle_guard.scan_for_dongle()
    sig = (status.valid, status.dongle_id)
    if st.session_state.dongle_sig != sig:
        st.session_state.dongle_sig = sig
        ui.log("DONGLE", f"Token valid di {status.path}" if status.valid else status.message,
               status.dongle_id, "OK" if status.valid else "WARN")

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
        page = st.radio("Navigasi", PAGES, index=PAGES.index(st.session_state.page), label_visibility="collapsed")
        st.session_state.page = page
        st.divider()
        st.markdown(ui.chip("Kunci terpasang", "ok") + ui.chip(user, "info"), unsafe_allow_html=True)
        st.write("")
        if st.button("Keluar", use_container_width=True):
            ui.log("AUTH", f"{user} keluar", level="INFO")
            st.session_state.user = None
            st.rerun()

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
        ui.page_header("Audit", "Log aktivitas", "Catatan seluruh operasi kriptografi pada sesi ini.")
        ui.render_log()


main()
