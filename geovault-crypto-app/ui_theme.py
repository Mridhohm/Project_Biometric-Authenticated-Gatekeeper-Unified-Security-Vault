"""
Krypt Vault - Presentation layer
================================
Clean, document-style security console theme (light, IBM Plex typography),
plus a small activity log used across the application.
"""

from __future__ import annotations

import html
from datetime import datetime
from typing import Optional

import streamlit as st
from Crypto.Hash import SHA256

MAX_LOGS = 200

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
  --ink: #0F172A;
  --ink-2: #334155;
  --muted: #64748B;
  --line: #E2E8F0;
  --line-2: #CBD5E1;
  --paper: #FFFFFF;
  --canvas: #F6F7F9;
  --accent: #1D4ED8;
  --accent-soft: #EEF2FF;
  --ok: #047857;
  --ok-soft: #ECFDF5;
  --bad: #B91C1C;
  --bad-soft: #FEF2F2;
  --warn: #B45309;
  --warn-soft: #FFFBEB;
}

html, body, [class*="css"], .stApp, p, label, input, textarea, button, div {
  font-family: 'IBM Plex Sans', -apple-system, 'Segoe UI', sans-serif;
}
.stApp { background: var(--canvas); color: var(--ink); }
code, pre, .mono { font-family: 'IBM Plex Mono', Consolas, monospace !important; }

/* Hide Streamlit chrome, branding, and status dialogs */
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"], .stDeployButton, .stConnectionStatus,
div[class*="StatusWidget"], div[class*="connection-status"],
div[data-testid="stConnectionStatus"], div[role="dialog"]:has(pre),
.viewerBadge_container__1QSob, .viewerBadge_link__1S137 { display: none !important; }
header[data-testid="stHeader"] { background: transparent; height: 0; }

.block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1180px; }

/* Sidebar */
section[data-testid="stSidebar"] {
  background: var(--paper);
  border-right: 1px solid var(--line);
}
section[data-testid="stSidebar"] .block-container { padding-top: 1.5rem; }

/* Sidebar nav radio as a list */
section[data-testid="stSidebar"] div[role="radiogroup"] { gap: 2px; }
section[data-testid="stSidebar"] div[role="radiogroup"] label {
  padding: 8px 12px; border-radius: 6px; margin: 0; width: 100%;
  color: var(--ink-2); font-weight: 500; font-size: 0.92rem;
  border: 1px solid transparent;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover { background: var(--canvas); }
section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child { display: none; }
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
  background: var(--accent-soft); color: var(--accent); border-color: #C7D2FE; font-weight: 600;
}

h1, h2, h3, h4 { color: var(--ink); letter-spacing: -0.01em; font-weight: 600; }
h1 { font-size: 1.6rem; }
h2 { font-size: 1.25rem; }
h3 { font-size: 1.05rem; }

/* Bordered containers as cards */
div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"]) {
  background: var(--paper);
  border-color: var(--line) !important;
  border-radius: 10px;
}

/* Buttons */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
  border-radius: 6px; font-weight: 500; border: 1px solid var(--line-2);
  background: var(--paper); color: var(--ink); box-shadow: none; padding: 0.45rem 1rem;
}
.stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover {
  border-color: var(--accent); color: var(--accent);
}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"],
.stDownloadButton > button[kind="primary"] {
  background: var(--accent); color: #fff; border-color: var(--accent);
}
.stButton > button[kind="primary"]:hover, .stFormSubmitButton > button[kind="primary"]:hover {
  background: #1E40AF; color: #fff;
}

/* Inputs */
input, textarea, div[data-baseweb="select"] > div { border-radius: 6px !important; }

/* Tabs */
button[data-baseweb="tab"] { font-weight: 500; }

/* Metrics */
div[data-testid="stMetric"] {
  background: var(--paper); border: 1px solid var(--line); border-radius: 10px; padding: 14px 16px;
}
div[data-testid="stMetricLabel"] p { color: var(--muted); font-size: 0.8rem; text-transform: uppercase; letter-spacing: .04em; }
div[data-testid="stMetricValue"] { font-size: 1.55rem; font-weight: 600; color: var(--ink); }

/* Custom elements */
.kv-brand { display:flex; align-items:center; gap:10px; margin-bottom: 18px; }
.kv-mark { width:30px; height:30px; border-radius:7px; background: var(--ink); color:#fff;
  display:flex; align-items:center; justify-content:center; font-weight:700; font-size: 14px; }
.kv-brand-name { font-weight:700; font-size: 1.05rem; color: var(--ink); line-height: 1.1; }
.kv-brand-sub { font-size: 0.72rem; color: var(--muted); letter-spacing: .06em; text-transform: uppercase; }

.kv-eyebrow { font-size: 0.74rem; color: var(--muted); letter-spacing: .08em; text-transform: uppercase; font-weight:600; margin-bottom: 4px; }
.kv-title { font-size: 1.6rem; font-weight: 600; color: var(--ink); margin: 0 0 6px 0; letter-spacing: -0.015em; }
.kv-lead { color: var(--ink-2); font-size: 0.95rem; max-width: 760px; margin-bottom: 22px; line-height: 1.55; }

.kv-chip { display:inline-block; padding: 2px 9px; border-radius: 999px; font-size: 0.74rem; font-weight: 600;
  border: 1px solid var(--line-2); color: var(--ink-2); background: var(--paper); margin-right: 6px; }
.kv-chip.ok { color: var(--ok); background: var(--ok-soft); border-color: #A7F3D0; }
.kv-chip.bad { color: var(--bad); background: var(--bad-soft); border-color: #FECACA; }
.kv-chip.warn { color: var(--warn); background: var(--warn-soft); border-color: #FDE68A; }
.kv-chip.info { color: var(--accent); background: var(--accent-soft); border-color: #C7D2FE; }

.kv-kv { display:grid; grid-template-columns: 160px 1fr; gap: 6px 14px; font-size: 0.88rem; }
.kv-kv .k { color: var(--muted); }
.kv-kv .v { color: var(--ink); font-family: 'IBM Plex Mono', monospace; word-break: break-all; }

.kv-steps { display:flex; gap: 0; margin: 4px 0 26px 0; border:1px solid var(--line); border-radius: 10px; background: var(--paper); overflow:hidden; }
.kv-step { flex:1; padding: 12px 16px; border-right: 1px solid var(--line); }
.kv-step:last-child { border-right: none; }
.kv-step .n { font-size: 0.72rem; color: var(--muted); letter-spacing: .06em; text-transform: uppercase; font-weight: 600; }
.kv-step .t { font-size: 0.92rem; font-weight: 600; color: var(--ink); margin-top: 2px; }
.kv-step.done .n { color: var(--ok); }
.kv-step.active { background: var(--accent-soft); }
.kv-step.active .n { color: var(--accent); }

.kv-log { background: #0B1220; color: #CBD5E1; border-radius: 8px; padding: 12px 14px;
  font-family: 'IBM Plex Mono', monospace; font-size: 12px; line-height: 1.65; max-height: 420px; overflow-y:auto; }
.kv-log .t { color: #64748B; }
.kv-log .s { color: #93C5FD; }
.kv-log .OK { color: #34D399; } .kv-log .WARN { color: #FBBF24; } .kv-log .CRIT { color: #F87171; } .kv-log .INFO { color: #94A3B8; }

.kv-table { width:100%; border-collapse: collapse; font-size: 0.88rem; background: var(--paper); }
.kv-table th { text-align:left; color: var(--muted); font-weight:600; font-size: 0.76rem; text-transform: uppercase; letter-spacing:.05em;
  border-bottom: 1px solid var(--line); padding: 9px 10px; }
.kv-table td { border-bottom: 1px solid var(--line); padding: 10px; vertical-align: top; color: var(--ink); }
.kv-table td.mono { font-family: 'IBM Plex Mono', monospace; font-size: 0.8rem; }
</style>
"""


def inject_theme() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# Small render helpers
# --------------------------------------------------------------------------- #
def page_header(eyebrow: str, title: str, lead: str = "") -> None:
    st.markdown(
        f"<div class='kv-eyebrow'>{html.escape(eyebrow)}</div>"
        f"<div class='kv-title'>{html.escape(title)}</div>"
        + (f"<div class='kv-lead'>{html.escape(lead)}</div>" if lead else ""),
        unsafe_allow_html=True,
    )


def chip(text: str, kind: str = "") -> str:
    return f"<span class='kv-chip {kind}'>{html.escape(text)}</span>"


def kv_grid(rows: list[tuple[str, str]]) -> None:
    body = "".join(
        f"<div class='k'>{html.escape(k)}</div><div class='v'>{html.escape(str(v))}</div>" for k, v in rows
    )
    st.markdown(f"<div class='kv-kv'>{body}</div>", unsafe_allow_html=True)


def steps(current: int) -> None:
    items = [(1, "Langkah 1", "Kunci perangkat keras"), (2, "Langkah 2", "Identitas dan biometrik"), (3, "Langkah 3", "Ruang kerja vault")]
    out = []
    for n, label, title in items:
        cls = "done" if n < current else ("active" if n == current else "")
        state = "Selesai" if n < current else ("Sedang berjalan" if n == current else "Terkunci")
        out.append(f"<div class='kv-step {cls}'><div class='n'>{label} - {state}</div><div class='t'>{title}</div></div>")
    st.markdown(f"<div class='kv-steps'>{''.join(out)}</div>", unsafe_allow_html=True)


def brand(sub: str = "Forensic Evidence Vault") -> None:
    st.markdown(
        "<div class='kv-brand'><div class='kv-mark'>KV</div>"
        f"<div><div class='kv-brand-name'>Krypt Vault</div><div class='kv-brand-sub'>{html.escape(sub)}</div></div></div>",
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------- #
# Activity log
# --------------------------------------------------------------------------- #
def init_logs() -> None:
    if "kv_logs" not in st.session_state:
        st.session_state.kv_logs = []
        log("SYSTEM", "Krypt Vault dimulai, hierarki kunci HKDF-SHA256 dimuat", level="OK")


def log(subsystem: str, message: str, digest: Optional[str] = None, level: str = "INFO") -> None:
    if "kv_logs" not in st.session_state:
        st.session_state.kv_logs = []
    st.session_state.kv_logs.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "subsys": subsystem.upper()[:14],
        "msg": message,
        "digest": digest[:16] if digest else None,
        "level": level.upper(),
    })
    st.session_state.kv_logs = st.session_state.kv_logs[-MAX_LOGS:]


def sha256_hex(data: bytes | str) -> str:
    raw = data.encode("utf-8") if isinstance(data, str) else data
    return SHA256.new(raw).hexdigest()


def render_log() -> None:
    logs = st.session_state.get("kv_logs", [])
    if not logs:
        st.caption("Belum ada aktivitas.")
        return
    lines = []
    for r in reversed(logs):
        dg = f" <span class='t'>sha256:{html.escape(r['digest'])}</span>" if r.get("digest") else ""
        lines.append(
            f"<div><span class='t'>{r['time']}</span> <span class='{r['level']}'>{r['level']:<4}</span> "
            f"<span class='s'>{html.escape(r['subsys'])}</span> {html.escape(r['msg'])}{dg}</div>"
        )
    st.markdown(f"<div class='kv-log'>{''.join(lines)}</div>", unsafe_allow_html=True)
