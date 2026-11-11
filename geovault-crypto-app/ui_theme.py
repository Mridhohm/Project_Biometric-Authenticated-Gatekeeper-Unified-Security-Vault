"""
Krypt Vault - Modern Minimalist Presentation Layer
================================================
Combines clean minimalist ergonomics with a refined modern Obsidian/Slate
dark security aesthetic (plus an instant Light Mode toggle), crisp SVG icons,
interactive status meters, cipher pipeline visualizers, and telemetry logs.
"""

from __future__ import annotations

import html
from datetime import datetime
from typing import Optional

import streamlit as st
from Crypto.Hash import SHA256

MAX_LOGS = 200

ICONS: dict[str, str] = {
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    "usb": '<path d="M10 2v6m4-6v6M7 8h10v6a5 5 0 0 1-10 0V8z"/><path d="M12 19v3"/>',
    "user": '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
    "lock": '<rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    "unlock": '<rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 9.9-1"/>',
    "text": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="8" y1="13" x2="16" y2="13"/><line x1="8" y1="17" x2="13" y2="17"/>',
    "file": '<path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><polyline points="13 2 13 9 20 9"/>',
    "image": '<rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/>',
    "database": '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>',
    "blocks": '<rect x="2" y="7" width="8" height="8" rx="1.5"/><rect x="14" y="7" width="8" height="8" rx="1.5"/><line x1="10" y1="11" x2="14" y2="11"/>',
    "activity": '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
    "key": '<path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/>',
    "check": '<polyline points="20 6 9 17 4 12"/>',
    "alert": '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
    "arrow": '<line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>',
}


def icon(name: str, size: int = 16) -> str:
    """Return an inline SVG stroke icon."""
    body = ICONS.get(name, ICONS["shield"])
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
        f'style="display:inline-block;vertical-align:-2px;flex-shrink:0;">{body}</svg>'
    )


THEMES: dict[str, dict[str, str]] = {
    "dark": {
        "canvas": "#090D16",
        "canvas_glow": "radial-gradient(ellipse 85% 42% at 50% -12%, rgba(56, 189, 248, 0.12), transparent 72%)",
        "paper": "#111827",
        "paper_2": "#172033",
        "input_bg": "#0B1120",
        "ink": "#F1F5F9",
        "ink_2": "#CBD5E1",
        "muted": "#94A3B8",
        "line": "#1E293B",
        "line_2": "#334155",
        "accent": "#38BDF8",
        "accent_soft": "rgba(56, 189, 248, 0.13)",
        "accent_border": "rgba(56, 189, 248, 0.36)",
        "btn_primary": "linear-gradient(135deg, #0EA5E9 0%, #2563EB 100%)",
        "btn_primary_hover": "linear-gradient(135deg, #38BDF8 0%, #1D4ED8 100%)",
        "mark_bg": "linear-gradient(135deg, #0EA5E9 0%, #2563EB 100%)",
        "mark_fg": "#FFFFFF",
        "ok": "#34D399",
        "ok_soft": "rgba(16, 185, 129, 0.14)",
        "ok_border": "rgba(52, 211, 153, 0.34)",
        "bad": "#F87171",
        "bad_soft": "rgba(239, 68, 68, 0.14)",
        "bad_border": "rgba(248, 113, 113, 0.34)",
        "warn": "#FBBF24",
        "warn_soft": "rgba(245, 158, 11, 0.14)",
        "warn_border": "rgba(251, 191, 36, 0.34)",
        "log_bg": "#060911",
        "log_fg": "#CBD5E1",
        "shadow": "0 8px 28px rgba(2, 6, 23, 0.45)",
    },
    "light": {
        "canvas": "#F6F7F9",
        "canvas_glow": "none",
        "paper": "#FFFFFF",
        "paper_2": "#F8FAFC",
        "input_bg": "#FFFFFF",
        "ink": "#0F172A",
        "ink_2": "#334155",
        "muted": "#64748B",
        "line": "#E2E8F0",
        "line_2": "#CBD5E1",
        "accent": "#1D4ED8",
        "accent_soft": "#EEF2FF",
        "accent_border": "#C7D2FE",
        "btn_primary": "linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%)",
        "btn_primary_hover": "linear-gradient(135deg, #1D4ED8 0%, #1E40AF 100%)",
        "mark_bg": "#0F172A",
        "mark_fg": "#FFFFFF",
        "ok": "#047857",
        "ok_soft": "#ECFDF5",
        "ok_border": "#A7F3D0",
        "bad": "#B91C1C",
        "bad_soft": "#FEF2F2",
        "bad_border": "#FECACA",
        "warn": "#B45309",
        "warn_soft": "#FFFBEB",
        "warn_border": "#FDE68A",
        "log_bg": "#0B1220",
        "log_fg": "#CBD5E1",
        "shadow": "0 4px 16px rgba(15, 23, 42, 0.05)",
    },
}


def get_theme() -> str:
    mode = st.session_state.get("kv_theme", "dark")
    return mode if mode in THEMES else "dark"


def toggle_theme() -> str:
    nxt = "light" if get_theme() == "dark" else "dark"
    st.session_state.kv_theme = nxt
    return nxt


def _build_css(mode: str) -> str:
    t = THEMES[mode]
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

:root {{
  --canvas: {t['canvas']};
  --paper: {t['paper']};
  --paper-2: {t['paper_2']};
  --input-bg: {t['input_bg']};
  --ink: {t['ink']};
  --ink-2: {t['ink_2']};
  --muted: {t['muted']};
  --line: {t['line']};
  --line-2: {t['line_2']};
  --accent: {t['accent']};
  --accent-soft: {t['accent_soft']};
  --accent-border: {t['accent_border']};
  --ok: {t['ok']};
  --ok-soft: {t['ok_soft']};
  --ok-border: {t['ok_border']};
  --bad: {t['bad']};
  --bad-soft: {t['bad_soft']};
  --bad-border: {t['bad_border']};
  --warn: {t['warn']};
  --warn-soft: {t['warn_soft']};
  --warn-border: {t['warn_border']};
}}

html, body, [class*="css"], .stApp, p, label, input, textarea, button, div {{
  font-family: 'Plus Jakarta Sans', -apple-system, 'Segoe UI', sans-serif;
}}

.stApp {{
  background-color: var(--canvas);
  background-image: {t['canvas_glow']};
  color: var(--ink);
}}

code, pre, .mono {{
  font-family: 'IBM Plex Mono', Consolas, monospace !important;
}}

/* Hide Streamlit built-in chrome for standalone desktop window feel */
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"], .stDeployButton, .stConnectionStatus,
div[class*="StatusWidget"], div[class*="connection-status"],
div[data-testid="stConnectionStatus"], div[role="dialog"]:has(pre),
.viewerBadge_container__1QSob, .viewerBadge_link__1S137 {{
  display: none !important;
}}
header[data-testid="stHeader"] {{
  background: transparent !important;
  height: 0 !important;
  min-height: 0 !important;
}}

.block-container {{
  padding-top: 1.25rem;
  padding-bottom: 3rem;
  max-width: 1200px;
}}

/* Custom thin scrollbars */
::-webkit-scrollbar {{ width: 7px; height: 7px; }}
::-webkit-scrollbar-track {{ background: var(--canvas); }}
::-webkit-scrollbar-thumb {{ background: var(--line-2); border-radius: 999px; }}
::-webkit-scrollbar-thumb:hover {{ background: var(--muted); }}

/* Sidebar shell */
section[data-testid="stSidebar"] {{
  background: var(--paper) !important;
  border-right: 1px solid var(--line) !important;
}}
section[data-testid="stSidebar"] .block-container {{
  padding-top: 1.25rem;
}}
section[data-testid="stSidebar"] div[role="radiogroup"] {{
  gap: 4px;
}}
section[data-testid="stSidebar"] div[role="radiogroup"] label {{
  padding: 9px 12px;
  border-radius: 8px;
  margin: 0;
  width: 100%;
  color: var(--ink-2);
  font-weight: 500;
  font-size: 0.9rem;
  border: 1px solid transparent;
  transition: background 140ms ease, border-color 140ms ease, color 140ms ease;
}}
section[data-testid="stSidebar"] div[role="radiogroup"] label p {{
  color: inherit !important;
}}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {{
  background: var(--paper-2);
  color: var(--ink);
}}
section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child {{
  display: none;
}}
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {{
  background: var(--accent-soft);
  color: var(--accent);
  border-color: var(--accent-border);
  font-weight: 600;
}}

/* Typography */
h1, h2, h3, h4 {{
  color: var(--ink) !important;
  letter-spacing: -0.015em;
  font-weight: 600;
}}
h1 {{ font-size: 1.55rem; }}
h2 {{ font-size: 1.22rem; }}
h3 {{ font-size: 1.02rem; }}
.stCaption, [data-testid="stCaptionContainer"] p {{
  color: var(--muted) !important;
}}

/* Cards */
div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"]) {{
  background: var(--paper);
  border: 1px solid var(--line) !important;
  border-radius: 12px;
  box-shadow: {t['shadow']};
  transition: border-color 180ms ease, transform 180ms ease;
}}
div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"]):hover {{
  border-color: var(--line-2) !important;
}}

/* Buttons */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button,
div[data-testid="stPopover"] > button {{
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.88rem;
  border: 1px solid var(--line-2);
  background: var(--paper-2);
  color: var(--ink);
  box-shadow: none;
  padding: 0.45rem 0.95rem;
  transition: border-color 150ms ease, background 150ms ease, transform 120ms ease, color 150ms ease;
}}
.stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover,
div[data-testid="stPopover"] > button:hover {{
  border-color: var(--accent);
  color: var(--accent);
  background: var(--accent-soft);
}}
.stButton > button:active {{
  transform: translateY(1px);
}}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"],
.stDownloadButton > button[kind="primary"] {{
  background: {t['btn_primary']};
  color: #FFFFFF !important;
  border: 1px solid transparent;
  font-weight: 600;
}}
.stButton > button[kind="primary"] p, .stFormSubmitButton > button[kind="primary"] p,
.stDownloadButton > button[kind="primary"] p {{
  color: #FFFFFF !important;
}}
.stButton > button[kind="primary"]:hover, .stFormSubmitButton > button[kind="primary"]:hover,
.stDownloadButton > button[kind="primary"]:hover {{
  background: {t['btn_primary_hover']};
  border-color: transparent;
  color: #FFFFFF !important;
}}

/* Form Inputs, Selects, Uploaders, Modals, Popovers */
div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] > div,
div[data-baseweb="select"] > div {{
  background: var(--input-bg) !important;
  border-color: var(--line-2) !important;
  color: var(--ink) !important;
  border-radius: 8px !important;
}}
input, textarea {{
  color: var(--ink) !important;
  background: transparent !important;
}}
div[data-baseweb="popover"] > div,
div[data-testid="stPopoverBody"],
ul[role="listbox"],
div[role="dialog"] > div {{
  background: var(--paper) !important;
  color: var(--ink) !important;
  border: 1px solid var(--line-2) !important;
  border-radius: 12px !important;
}}
li[role="option"] {{
  color: var(--ink) !important;
}}
li[role="option"]:hover {{
  background: var(--accent-soft) !important;
}}
section[data-testid="stFileUploadDropzone"] {{
  background: var(--input-bg) !important;
  border: 1px dashed var(--line-2) !important;
  border-radius: 10px !important;
}}
section[data-testid="stFileUploadDropzone"]:hover {{
  border-color: var(--accent) !important;
}}
div[data-testid="stExpander"] {{
  background: var(--paper) !important;
  border: 1px solid var(--line) !important;
  border-radius: 10px !important;
}}

/* Segmented controls & Tabs */
button[data-baseweb="tab"] {{
  font-weight: 500;
  color: var(--muted) !important;
}}
button[data-baseweb="tab"][aria-selected="true"] {{
  color: var(--accent) !important;
  font-weight: 600;
}}
div[data-testid="stTabs"] [data-baseweb="tab-border"] {{
  background-color: var(--line) !important;
}}

/* Code blocks */
pre, code {{
  background: var(--input-bg) !important;
  border-color: var(--line) !important;
}}

/* Metrics */
div[data-testid="stMetric"] {{
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 15px 18px;
  box-shadow: {t['shadow']};
}}
div[data-testid="stMetricLabel"] p {{
  color: var(--muted) !important;
  font-size: 0.74rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}}
div[data-testid="stMetricValue"] {{
  font-size: 1.65rem;
  font-weight: 700;
  color: var(--ink) !important;
}}

/* Animations */
@keyframes kv-pulse {{
  0%, 100% {{ opacity: 1; transform: scale(1); }}
  50% {{ opacity: 0.45; transform: scale(0.86); }}
}}
.kv-dot {{
  width: 8px;
  height: 8px;
  border-radius: 999px;
  display: inline-block;
  margin-right: 6px;
  background: currentColor;
  animation: kv-pulse 2s infinite ease-in-out;
}}

/* Brand mark */
.kv-brand {{
  display: flex;
  align-items: center;
  gap: 11px;
}}
.kv-mark {{
  width: 34px;
  height: 34px;
  border-radius: 9px;
  background: {t['mark_bg']};
  color: {t['mark_fg']};
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 13px;
  letter-spacing: 0.04em;
  flex-shrink: 0;
}}
.kv-brand-name {{
  font-weight: 700;
  font-size: 1.02rem;
  color: var(--ink);
  line-height: 1.15;
}}
.kv-brand-sub {{
  font-size: 0.7rem;
  color: var(--muted);
  letter-spacing: 0.07em;
  text-transform: uppercase;
}}

/* Page headings */
.kv-eyebrow {{
  font-size: 0.73rem;
  color: var(--accent);
  letter-spacing: 0.09em;
  text-transform: uppercase;
  font-weight: 700;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 6px;
}}
.kv-title {{
  font-size: 1.62rem;
  font-weight: 700;
  color: var(--ink);
  margin: 0 0 6px 0;
  letter-spacing: -0.02em;
}}
.kv-lead {{
  color: var(--ink-2);
  font-size: 0.93rem;
  max-width: 780px;
  margin-bottom: 20px;
  line-height: 1.6;
}}

/* Chips */
.kv-chip {{
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 0.74rem;
  font-weight: 600;
  border: 1px solid var(--line-2);
  color: var(--ink-2);
  background: var(--paper-2);
  margin-right: 6px;
  margin-bottom: 4px;
}}
.kv-chip.ok {{ color: var(--ok); background: var(--ok-soft); border-color: var(--ok-border); }}
.kv-chip.bad {{ color: var(--bad); background: var(--bad-soft); border-color: var(--bad-border); }}
.kv-chip.warn {{ color: var(--warn); background: var(--warn-soft); border-color: var(--warn-border); }}
.kv-chip.info {{ color: var(--accent); background: var(--accent-soft); border-color: var(--accent-border); }}

/* Key-Value grid */
.kv-kv {{
  display: grid;
  grid-template-columns: 165px 1fr;
  gap: 8px 14px;
  font-size: 0.87rem;
}}
.kv-kv .k {{ color: var(--muted); }}
.kv-kv .v {{ color: var(--ink); font-family: 'IBM Plex Mono', monospace; word-break: break-all; }}

/* 3-Step horizontal security stepper */
.kv-steps {{
  display: flex;
  margin: 8px 0 22px 0;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: var(--paper);
  overflow: hidden;
  box-shadow: {t['shadow']};
}}
.kv-step {{
  flex: 1;
  padding: 13px 18px;
  border-right: 1px solid var(--line);
  transition: background 180ms ease;
}}
.kv-step:last-child {{ border-right: none; }}
.kv-step .n {{
  font-size: 0.71rem;
  color: var(--muted);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 6px;
}}
.kv-step .t {{
  font-size: 0.94rem;
  font-weight: 600;
  color: var(--ink);
  margin-top: 3px;
}}
.kv-step.done {{ background: var(--ok-soft); }}
.kv-step.done .n {{ color: var(--ok); }}
.kv-step.active {{ background: var(--accent-soft); box-shadow: inset 0 -2px 0 var(--accent); }}
.kv-step.active .n {{ color: var(--accent); }}

/* Visual progress / score / capacity gauge */
.kv-meter-wrap {{ margin: 8px 0 12px 0; }}
.kv-meter-head {{
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  font-size: 0.82rem;
  margin-bottom: 5px;
}}
.kv-meter-lbl {{ color: var(--ink-2); font-weight: 600; }}
.kv-meter-val {{ font-family: 'IBM Plex Mono', monospace; font-weight: 600; color: var(--ink); }}
.kv-meter-track {{
  position: relative;
  height: 9px;
  background: var(--input-bg);
  border: 1px solid var(--line);
  border-radius: 999px;
  overflow: visible;
}}
.kv-meter-fill {{
  height: 100%;
  border-radius: 999px;
  transition: width 300ms ease;
}}
.kv-meter-fill.ok {{ background: var(--ok); }}
.kv-meter-fill.info {{ background: var(--accent); }}
.kv-meter-fill.warn {{ background: var(--warn); }}
.kv-meter-fill.bad {{ background: var(--bad); }}
.kv-meter-tick {{
  position: absolute;
  top: -3px;
  bottom: -3px;
  width: 2px;
  background: var(--ink);
  opacity: 0.75;
}}
.kv-meter-sub {{ font-size: 0.76rem; color: var(--muted); margin-top: 5px; }}

/* Horizontal crypto pipeline strip */
.kv-pipeline {{
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding: 12px 14px;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: 10px;
  margin-bottom: 18px;
}}
.kv-pipe-node {{
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid var(--line-2);
  background: var(--paper-2);
  font-size: 0.8rem;
}}
.kv-pipe-node.on {{
  border-color: var(--accent-border);
  background: var(--accent-soft);
  color: var(--accent);
}}
.kv-pipe-node .pn-t {{ font-weight: 600; color: var(--ink); }}
.kv-pipe-node.on .pn-t {{ color: var(--accent); }}
.kv-pipe-node .pn-s {{ font-size: 0.71rem; color: var(--muted); font-family: 'IBM Plex Mono', monospace; }}
.kv-pipe-arrow {{ color: var(--muted); display: inline-flex; }}

/* Activity console */
.kv-log {{
  background: {t['log_bg']};
  color: {t['log_fg']};
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 12px 14px;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 12px;
  line-height: 1.68;
  max-height: 400px;
  overflow-y: auto;
}}
.kv-log .t {{ color: #64748B; }}
.kv-log .s {{ color: #7DD3FC; }}
.kv-log .OK {{ color: #34D399; font-weight: 600; }}
.kv-log .WARN {{ color: #FBBF24; font-weight: 600; }}
.kv-log .CRIT {{ color: #F87171; font-weight: 600; }}
.kv-log .INFO {{ color: #94A3B8; }}

/* Data tables */
.kv-table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 0.86rem;
  background: var(--paper);
  border-radius: 8px;
  overflow: hidden;
}}
.kv-table th {{
  text-align: left;
  color: var(--muted);
  font-weight: 600;
  font-size: 0.73rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid var(--line);
  padding: 9px 10px;
  background: var(--paper-2);
}}
.kv-table td {{
  border-bottom: 1px solid var(--line);
  padding: 10px;
  vertical-align: middle;
  color: var(--ink);
}}
.kv-table tr:last-child td {{ border-bottom: none; }}
.kv-table td.mono {{ font-family: 'IBM Plex Mono', monospace; font-size: 0.79rem; }}
</style>
"""


def inject_theme() -> None:
    st.markdown(_build_css(get_theme()), unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# Render helpers
# --------------------------------------------------------------------------- #
def page_header(eyebrow: str, title: str, lead: str = "", icon_name: Optional[str] = None) -> None:
    ic = icon(icon_name, 14) if icon_name else ""
    st.markdown(
        f"<div class='kv-eyebrow'>{ic}<span>{html.escape(eyebrow)}</span></div>"
        f"<div class='kv-title'>{html.escape(title)}</div>"
        + (f"<div class='kv-lead'>{html.escape(lead)}</div>" if lead else ""),
        unsafe_allow_html=True,
    )


def chip(text: str, kind: str = "", icon_name: Optional[str] = None, dot: bool = False) -> str:
    prefix = "<span class='kv-dot'></span>" if dot else (icon(icon_name, 12) if icon_name else "")
    return f"<span class='kv-chip {kind}'>{prefix}<span>{html.escape(text)}</span></span>"


def kv_grid(rows: list[tuple[str, str]]) -> None:
    body = "".join(
        f"<div class='k'>{html.escape(k)}</div><div class='v'>{html.escape(str(v))}</div>" for k, v in rows
    )
    st.markdown(f"<div class='kv-kv'>{body}</div>", unsafe_allow_html=True)


def steps(current: int) -> None:
    items = [
        (1, "Langkah 1", "Kunci perangkat keras", "usb"),
        (2, "Langkah 2", "Identitas dan biometrik", "user"),
        (3, "Langkah 3", "Ruang kerja vault", "shield"),
    ]
    out = []
    for n, label, title, ic in items:
        if n < current:
            cls, state, prefix = "done", "Terverifikasi", icon("check", 13)
        elif n == current:
            cls, state, prefix = "active", "Aktif", "<span class='kv-dot'></span>"
        else:
            cls, state, prefix = "", "Terkunci", icon("lock", 12)
        out.append(
            f"<div class='kv-step {cls}'>"
            f"<div class='n'>{prefix}<span>{label} - {state}</span></div>"
            f"<div class='t'>{icon(ic, 15)} <span style='margin-left:4px;'>{title}</span></div>"
            "</div>"
        )
    st.markdown(f"<div class='kv-steps'>{''.join(out)}</div>", unsafe_allow_html=True)


def meter(
    label: str,
    pct: float,
    threshold_pct: Optional[float] = None,
    kind: str = "info",
    subtitle: str = "",
) -> None:
    clamped = max(0.0, min(100.0, float(pct)))
    tick = ""
    if threshold_pct is not None:
        t_pos = max(0.0, min(100.0, float(threshold_pct)))
        tick = f"<div class='kv-meter-tick' style='left:{t_pos:.1f}%;' title='Ambang batas {t_pos:.0f}%'></div>"
    sub_html = f"<div class='kv-meter-sub'>{html.escape(subtitle)}</div>" if subtitle else ""
    st.markdown(
        "<div class='kv-meter-wrap'>"
        f"<div class='kv-meter-head'><span class='kv-meter-lbl'>{html.escape(label)}</span>"
        f"<span class='kv-meter-val'>{clamped:.1f}%</span></div>"
        f"<div class='kv-meter-track'><div class='kv-meter-fill {kind}' style='width:{clamped:.1f}%;'></div>{tick}</div>"
        f"{sub_html}</div>",
        unsafe_allow_html=True,
    )


def pipeline(stages: list[tuple[str, str, bool]]) -> None:
    """Render horizontal cryptographic pipeline strip."""
    parts = []
    for idx, (title, sub, active) in enumerate(stages):
        cls = "on" if active else ""
        parts.append(
            f"<div class='kv-pipe-node {cls}'>"
            f"<div class='pn-t'>{html.escape(title)}</div>"
            f"<div class='pn-s'>{html.escape(sub)}</div>"
            "</div>"
        )
        if idx < len(stages) - 1:
            parts.append(f"<span class='kv-pipe-arrow'>{icon('arrow', 14)}</span>")
    st.markdown(f"<div class='kv-pipeline'>{''.join(parts)}</div>", unsafe_allow_html=True)


def brand(sub: str = "Forensic Evidence Vault") -> None:
    st.markdown(
        "<div class='kv-brand'><div class='kv-mark'>KV</div>"
        f"<div><div class='kv-brand-name'>Krypt Vault</div>"
        f"<div class='kv-brand-sub'>{html.escape(sub)}</div></div></div>",
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


def render_log(level_filter: str = "Semua", query: str = "", limit: int = MAX_LOGS) -> None:
    logs = st.session_state.get("kv_logs", [])
    q = query.strip().lower()
    filtered = [
        r for r in reversed(logs)
        if (level_filter == "Semua" or r["level"] == level_filter)
        and (not q or q in r["msg"].lower() or q in r["subsys"].lower())
    ][:limit]
    if not filtered:
        st.caption("Belum ada aktivitas yang cocok dengan filter.")
        return
    lines = []
    for r in filtered:
        dg = f" <span class='t'>sha256:{html.escape(r['digest'])}</span>" if r.get("digest") else ""
        lines.append(
            f"<div><span class='t'>{r['time']}</span> <span class='{r['level']}'>{r['level']:<4}</span> "
            f"<span class='s'>{html.escape(r['subsys'])}</span> {html.escape(r['msg'])}{dg}</div>"
        )
    st.markdown(f"<div class='kv-log'>{''.join(lines)}</div>", unsafe_allow_html=True)
