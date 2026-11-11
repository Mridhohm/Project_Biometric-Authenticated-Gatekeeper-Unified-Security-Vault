"""
Krypt Vault — Executive Dark Cybersecurity Theme & UI Subsystem
==============================================================
Provides high-end, modern dark mode styling, responsive security HUD,
interactive TTY telemetry logs, and cryptographic utility components.
"""

from __future__ import annotations

import html
from datetime import datetime, timezone
from typing import Optional

import streamlit as st
from Crypto.Hash import SHA256

MAX_CLI_LOGS: int = 120


# --------------------------------------------------------------------------- #
# 1. Executive Dark Mode Custom CSS
# --------------------------------------------------------------------------- #
def inject_cyberpunk_css() -> None:
    """Inject clean, modern, executive cybersecurity dark mode theme."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

        :root {
            --bg-base: #0B0F19;
            --bg-surface: #111827;
            --bg-surface-elevated: #1F2937;
            --border-subtle: rgba(255, 255, 255, 0.08);
            --border-focus: #0EA5E9;
            --text-main: #F8FAFC;
            --text-secondary: #94A3B8;
            --text-muted: #64748B;
            --accent-cyan: #0EA5E9;
            --accent-sky: #38BDF8;
            --status-green: #10B981;
            --status-red: #EF4444;
            --status-amber: #F59E0B;
        }

        /* Base Body & App Canvas */
        html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
            background-color: var(--bg-base) !important;
            color: var(--text-main) !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
            -webkit-font-smoothing: antialiased;
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child {
            background-color: var(--bg-surface) !important;
            border-right: 1px solid var(--border-subtle) !important;
        }

        /* Headings */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Inter', sans-serif !important;
            font-weight: 700 !important;
            color: var(--text-main) !important;
            letter-spacing: -0.02em !important;
            text-transform: none !important;
            text-shadow: none !important;
        }

        h1 { font-size: 1.85rem !important; }
        h2 { font-size: 1.45rem !important; color: var(--accent-sky) !important; }
        h3 { font-size: 1.2rem !important; color: var(--text-main) !important; }
        h4 { font-size: 1.05rem !important; color: var(--accent-cyan) !important; }

        p, label, span, div {
            font-family: 'Inter', sans-serif;
            letter-spacing: normal;
        }

        /* Monospace strictly for code, pre, digests */
        code, pre, .stCode, [data-testid="stCodeBlock"] {
            font-family: 'JetBrains Mono', Consolas, monospace !important;
            font-size: 0.88rem !important;
            background-color: #050811 !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 8px !important;
            color: #38BDF8 !important;
        }

        /* Cards, Expanders, Metrics & Containers */
        [data-testid="stExpander"], [data-testid="stForm"], div[data-testid="stMetric"],
        [data-testid="stFileUploader"], [data-testid="stCameraInput"] {
            background-color: var(--bg-surface) !important;
            border: 1px solid var(--border-subtle) !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25) !important;
            padding: 16px !important;
            clip-path: none !important;
        }

        div[data-testid="stMetric"] {
            padding: 14px 18px !important;
            background: linear-gradient(135deg, #111827 0%, #172033 100%) !important;
            border: 1px solid rgba(14, 165, 233, 0.2) !important;
            border-radius: 10px !important;
        }

        [data-testid="stMetricValue"] {
            color: #38BDF8 !important;
            font-size: 1.5rem !important;
            font-weight: 700 !important;
            font-family: 'JetBrains Mono', monospace !important;
            text-shadow: none !important;
        }

        [data-testid="stMetricLabel"] {
            color: var(--text-secondary) !important;
            font-size: 0.78rem !important;
            font-weight: 600 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
        }

        /* Modern Form Inputs & Selects */
        input, textarea, [data-baseweb="input"] > div, [data-baseweb="textarea"] > div,
        [data-baseweb="select"] > div {
            background-color: #162032 !important;
            color: #F8FAFC !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            border-radius: 8px !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 0.95rem !important;
            transition: all 0.2s ease !important;
        }

        input:focus, textarea:focus, [data-baseweb="input"] > div:focus-within {
            border-color: var(--border-focus) !important;
            box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.25) !important;
        }

        /* Buttons: Sleek, Modern Rounded (No Jagged Polygons) */
        .stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button {
            background: #1E293B !important;
            color: #F8FAFC !important;
            border: 1px solid rgba(255, 255, 255, 0.14) !important;
            border-radius: 8px !important;
            padding: 0.55rem 1.3rem !important;
            font-size: 0.92rem !important;
            font-weight: 600 !important;
            letter-spacing: 0.02em !important;
            clip-path: none !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2) !important;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }

        .stButton > button:hover, .stDownloadButton > button:hover,
        [data-testid="stFormSubmitButton"] > button:hover {
            background: #334155 !important;
            border-color: #0EA5E9 !important;
            color: #38BDF8 !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 12px rgba(14, 165, 233, 0.2) !important;
        }

        .stButton > button[kind="primary"], [data-testid="stFormSubmitButton"] > button[kind="primary"] {
            background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%) !important;
            color: #FFFFFF !important;
            border: 1px solid #38BDF8 !important;
            box-shadow: 0 2px 12px rgba(14, 165, 233, 0.35) !important;
        }

        .stButton > button[kind="primary"]:hover, [data-testid="stFormSubmitButton"] > button[kind="primary"]:hover {
            background: linear-gradient(135deg, #0EA5E9 0%, #0284C7 100%) !important;
            box-shadow: 0 4px 18px rgba(14, 165, 233, 0.5) !important;
            color: #FFFFFF !important;
        }

        /* Modern Pill Tabs */
        div[data-baseweb="tab-list"] {
            background-color: transparent !important;
            gap: 8px !important;
            margin-bottom: 12px !important;
        }

        button[data-baseweb="tab"] {
            background-color: #151D2D !important;
            color: #94A3B8 !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 8px !important;
            padding: 8px 18px !important;
            font-size: 0.88rem !important;
            font-weight: 600 !important;
            clip-path: none !important;
            transition: all 0.2s ease !important;
        }

        button[data-baseweb="tab"][aria-selected="true"] {
            background: #0284C7 !important;
            color: #FFFFFF !important;
            border-color: #38BDF8 !important;
            box-shadow: 0 2px 10px rgba(14, 165, 233, 0.35) !important;
        }

        /* TTY Terminal Log Console */
        .cp-cli-window {
            background: #060911;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            overflow: hidden;
            margin-top: 20px;
            box-shadow: 0 6px 24px rgba(0, 0, 0, 0.4);
        }

        .cp-cli-bar {
            background: #0E1424;
            padding: 8px 16px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            color: #94A3B8;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        }

        .cp-cli-body {
            max-height: 220px;
            overflow-y: auto;
            padding: 12px 16px;
            font-family: 'JetBrains Mono', Consolas, monospace;
            font-size: 12px;
            line-height: 1.6;
            color: #E2E8F0;
        }

        .cp-cli-line {
            display: flex;
            align-items: flex-start;
            gap: 10px;
            padding: 2px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.03);
        }

        .cp-cli-time { color: #64748B; font-size: 11px; white-space: nowrap; }
        .cp-cli-subsys { color: #38BDF8; font-weight: 600; white-space: nowrap; }
        .cp-cli-msg { color: #E2E8F0; word-break: break-all; flex: 1; }
        .cp-cli-digest { color: #A855F7; font-size: 11px; white-space: nowrap; }

        .cp-lvl-info { color: #38BDF8; }
        .cp-lvl-ok   { color: #10B981; font-weight: bold; }
        .cp-lvl-warn { color: #F59E0B; font-weight: bold; }
        .cp-lvl-crit { color: #EF4444; font-weight: bold; }

        /* Security Badges */
        .vault-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 5px 12px;
            border-radius: 9999px;
            font-size: 0.78rem;
            font-weight: 600;
            letter-spacing: 0.02em;
        }
        .vault-badge-green {
            background: rgba(16, 185, 129, 0.12);
            color: #10B981;
            border: 1px solid rgba(16, 185, 129, 0.35);
        }
        .vault-badge-red {
            background: rgba(239, 68, 68, 0.12);
            color: #EF4444;
            border: 1px solid rgba(239, 68, 68, 0.35);
        }
        .vault-badge-cyan {
            background: rgba(14, 165, 233, 0.12);
            color: #38BDF8;
            border: 1px solid rgba(14, 165, 233, 0.35);
        }

        /* Modern Horizontal Navigation Pills */
        [data-testid="stPills"] {
            background-color: #0E1424 !important;
            padding: 6px 8px !important;
            border-radius: 12px !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            gap: 6px !important;
            margin-bottom: 22px !important;
        }

        [data-testid="stPills"] button {
            background: transparent !important;
            color: #94A3B8 !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            font-size: 0.88rem !important;
            padding: 7px 18px !important;
            transition: all 0.2s ease !important;
            border: 1px solid transparent !important;
        }

        [data-testid="stPills"] button:hover {
            color: #F8FAFC !important;
            background: rgba(255, 255, 255, 0.05) !important;
        }

        [data-testid="stPills"] button[aria-selected="true"] {
            background: #0284C7 !important;
            color: #FFFFFF !important;
            box-shadow: 0 2px 12px rgba(14, 165, 233, 0.4) !important;
            border-color: #38BDF8 !important;
        }

        /* Feature Dashboard Cards */
        .kv-feature-card {
            background: linear-gradient(135deg, #111827 0%, #162032 100%);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px;
            padding: 20px 22px;
            margin-bottom: 16px;
            transition: all 0.25s ease;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
            min-height: 220px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        .kv-feature-card:hover {
            border-color: rgba(14, 165, 233, 0.5);
            transform: translateY(-2px);
            box-shadow: 0 8px 28px rgba(14, 165, 233, 0.15);
        }

        .kv-card-icon {
            font-size: 2rem;
            margin-bottom: 10px;
        }

        .kv-card-title {
            font-size: 1.12rem;
            font-weight: 700;
            color: #F8FAFC;
            margin-bottom: 6px;
        }

        .kv-card-desc {
            color: #94A3B8;
            font-size: 0.86rem;
            line-height: 1.5;
            margin-bottom: 14px;
        }

        .kv-card-badge {
            background: rgba(14, 165, 233, 0.15);
            color: #38BDF8;
            padding: 3px 10px;
            border-radius: 9999px;
            font-size: 0.72rem;
            font-weight: 600;
            display: inline-block;
            margin-bottom: 10px;
            border: 1px solid rgba(14, 165, 233, 0.3);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------- #
# 2. Interactive CLI Telemetry Engine
# --------------------------------------------------------------------------- #
def init_cli_logs() -> None:
    """Initialize the persistent session state log buffer."""
    if "cli_logs" not in st.session_state:
        st.session_state.cli_logs = []
        boot_digest = SHA256.new(b"KRYPT_VAULT//SECURITY_CORE_INIT").hexdigest()[:24]
        log_cli(
            "KERNEL",
            "Krypt Vault // Security Core Initialized — HKDF-SHA256 key hierarchy mounted",
            digest=boot_digest,
            level="OK",
        )


def log_cli(
    subsystem: str,
    message: str,
    digest: Optional[str] = None,
    level: str = "INFO",
) -> None:
    """Append a structured log record to the TTY session buffer."""
    if "cli_logs" not in st.session_state:
        st.session_state.cli_logs = []

    now = datetime.now(timezone.utc)
    record = {
        "time": now.strftime("%H:%M:%S.%f")[:12],
        "subsys": subsystem.upper()[:12],
        "msg": message,
        "digest": digest[:16] if digest else None,
        "level": level.upper(),
    }
    st.session_state.cli_logs.append(record)
    if len(st.session_state.cli_logs) > MAX_CLI_LOGS:
        st.session_state.cli_logs = st.session_state.cli_logs[-MAX_CLI_LOGS:]


def sha256_hex(data: bytes | str) -> str:
    """Return the full 64-char hex SHA-256 digest of arbitrary data."""
    raw = data.encode("utf-8") if isinstance(data, str) else data
    return SHA256.new(raw).hexdigest()


def render_cli_console(position_label: str = "KRYPT VAULT // TELEMETRY STREAM") -> None:
    """Render the sleek interactive CLI log terminal."""
    if "cli_logs" not in st.session_state or not st.session_state.cli_logs:
        return

    lines = []
    level_classes = {
        "INFO": "cp-lvl-info",
        "OK": "cp-lvl-ok",
        "WARN": "cp-lvl-warn",
        "CRIT": "cp-lvl-crit",
    }

    for log in reversed(st.session_state.cli_logs):
        lvl_cls = level_classes.get(log["level"], "cp-lvl-info")
        digest_tag = (
            f"<span class='cp-cli-digest'>[SHA256:{html.escape(log['digest'])}..]</span>"
            if log.get("digest")
            else ""
        )
        lines.append(
            f"<div class='cp-cli-line'>"
            f"<span class='cp-cli-time'>{html.escape(log['time'])}</span> "
            f"<span class='{lvl_cls}'>[{html.escape(log['level'])}]</span> "
            f"<span class='cp-cli-subsys'>[{html.escape(log['subsys'])}]</span> "
            f"<span class='cp-cli-msg'>{html.escape(log['msg'])}</span> "
            f"{digest_tag}"
            f"</div>"
        )

    lines_joined = "".join(lines)
    st.markdown(
        f"""
        <div class="cp-cli-window">
            <div class="cp-cli-bar">
                <span>⚡ [SYS@KRYPT-VAULT ~]# // {html.escape(position_label)}</span>
                <span style="color:#10B981; font-weight:600;">ACTIVE ({len(st.session_state.cli_logs)} EVENTS)</span>
            </div>
            <div class="cp-cli-body">
                {lines_joined}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------- #
# 3. Clean Security Lockscreen Banner
# --------------------------------------------------------------------------- #
def render_dongle_breach_banner(reason: str, has_tamper_failure: bool = False) -> None:
    """Render modern, clean security halt card when hardware dongle is not detected."""
    title = "AKSES TERKUNCI: HARDWARE DONGLE USB TIDAK TERDETEKSI"
    badge_color = "#EF4444"
    border_color = "rgba(239, 68, 68, 0.4)"

    if has_tamper_failure:
        title = "KEAMANAN KRITIS: TOKEN USB PALSU ATAU DIMANIPULASI"

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.08) 0%, rgba(17, 24, 39, 0.95) 100%);
            border: 1px solid {border_color};
            border-left: 5px solid {badge_color};
            border-radius: 12px;
            padding: 22px 26px;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px rgba(239, 68, 68, 0.15);
        ">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <div style="font-size:1.15rem; font-weight:700; color:#EF4444; display:flex; align-items:center; gap:8px;">
                    <span>🔒</span> {title}
                </div>
                <span style="
                    background: rgba(239,68,68,0.18);
                    color:#EF4444;
                    border:1px solid rgba(239,68,68,0.4);
                    padding:4px 12px;
                    border-radius:9999px;
                    font-size:0.75rem;
                    font-weight:700;
                    letter-spacing:0.05em;
                ">GATE_01 BLOCKED</span>
            </div>
            <div style="color:#CBD5E1; font-size:0.95rem; line-height:1.6; margin-bottom:14px;">
                Aplikasi <strong>Krypt Vault</strong> diamankan dengan gerbang otentikasi fisik. Seluruh fungsi brankas terkunci mati
                hingga <strong>USB Flashdisk otorisasi</strong> (<code style="color:#38BDF8;">.krypt_dongle</code> / <code style="color:#38BDF8;">.geovault_dongle</code>)
                ber-tanda tangan kanonikal <strong>HMAC-SHA256</strong> terhubung ke laptop/komputer Anda.
            </div>
            <div style="
                background: rgba(0, 0, 0, 0.4);
                border-radius: 8px;
                padding: 10px 14px;
                color: #FCA5A5;
                font-family: 'JetBrains Mono', Consolas, monospace;
                font-size: 0.85rem;
            ">
                DIAGNOSTIC STATUS: {html.escape(reason)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------- #
# 4. Clean Biometric Reticle Viewfinder (No Auto-Popup)
# --------------------------------------------------------------------------- #
def render_optical_scanner_hud(session_key: str = "optical_scanner", height: int = 240) -> None:
    """Render a clean, high-tech visual optical scanner viewfinder (without auto-popup)."""
    _ = session_key
    st.markdown(
        f"""
        <div style="
            background: #0E1422;
            border: 1px solid rgba(14, 165, 233, 0.25);
            border-radius: 12px;
            padding: 18px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            margin-bottom: 12px;
        ">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <span style="color:#38BDF8; font-weight:600; font-size:0.88rem; display:flex; align-items:center; gap:6px;">
                    ⚡ SENSOR BIOMETRIK OPTIK WAJAH
                </span>
                <span style="color:#10B981; font-size:0.8rem; font-weight:600; background:rgba(16,185,129,0.12); padding:3px 10px; border-radius:9999px;">
                    ● READY / STANDBY
                </span>
            </div>
            <div style="
                position: relative;
                width: 100%;
                height: 150px;
                background: linear-gradient(180deg, #070B14 0%, #0F172A 100%);
                border: 1px dashed rgba(56, 189, 248, 0.35);
                border-radius: 8px;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                overflow: hidden;
            ">
                <div style="
                    width: 70px;
                    height: 70px;
                    border: 2px dashed #0EA5E9;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 26px;
                ">👤</div>
                <div style="color:#94A3B8; font-size:0.82rem; margin-top:8px;">
                    Normalisasi Matriks 128x128 Grayscale PIL
                </div>
            </div>
            <div style="display:flex; justify-content:space-between; color:#64748B; font-size:0.75rem; margin-top:10px;">
                <span>FORMAT: GRAYSCALE 8-BIT</span>
                <span>RESOLUSI: 128x128 PIKSEL</span>
                <span>ENKRIPSI: AES-128-EAX</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
