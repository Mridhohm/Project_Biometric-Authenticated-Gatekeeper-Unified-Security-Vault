"""
Krypt Vault - Cyberpunk 2077 HUD presentation layer
===================================================

Visual language taken from the Cyberpunk 2077 interface sheet:

  * Black void with faint "+" registration marks instead of a flat fill.
  * Crimson is the *structure* colour: thin frames, rules and dividers only.
  * Cyan carries titles and data; yellow marks "you are here" and the primary action.
  * Chamfered plaques, corner brackets and segmented bars (the health-bar motif).

Colour roles are fixed so the interface stays easy to read at a glance:

    yellow  -> current page / current tab / the one primary button
    cyan    -> headings, values, hover and focus
    crimson -> frames and dividers (bright crimson is reserved for errors)
    green   -> verified / success
"""

from __future__ import annotations

import html
from datetime import datetime
from typing import Optional
from urllib.parse import quote

import streamlit as st
from Crypto.Hash import SHA256

MAX_LOGS = 200

# --------------------------------------------------------------------------- #
# Icons (24x24 stroke icons, used inline and as CSS masks in the sidebar)
# --------------------------------------------------------------------------- #
ICONS: dict[str, str] = {
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    "grid": '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>',
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

# Sidebar icons, in the same order as app.PAGES.
NAV_ICONS: list[str] = ["grid", "text", "file", "image", "database", "blocks", "key", "activity"]


def icon(name: str, size: int = 16) -> str:
    """Return an inline SVG stroke icon."""
    body = ICONS.get(name, ICONS["shield"])
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
        f'style="display:inline-block;vertical-align:-2px;flex-shrink:0;" aria-hidden="true">{body}</svg>'
    )


def _mask_url(name: str) -> str:
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="black" '
        f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</svg>'
    )
    return f'url("data:image/svg+xml,{quote(svg)}")'


def _nav_icon_css() -> str:
    rules = []
    for i, name in enumerate(NAV_ICONS, start=1):
        rules.append(
            f'section[data-testid="stSidebar"] div[role="radiogroup"] label:nth-of-type({i})::before '
            f"{{ -webkit-mask-image: {_mask_url(name)}; mask-image: {_mask_url(name)}; }}"
        )
    return "\n".join(rules)


# --------------------------------------------------------------------------- #
# Stylesheet
# --------------------------------------------------------------------------- #
_CROSS_BG = (
    "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='72' height='72'%3E"
    "%3Cpath d='M36 32v8M32 36h8' stroke='%23FF4258' stroke-opacity='.16' stroke-width='1'/%3E%3C/svg%3E\")"
)

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Saira:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --void: #050506;
  --panel: #0D0A0C;
  --panel-2: #160E12;
  --input: #080607;
  --ink: #EFE8EA;
  --ink-2: #C9BBC0;
  --muted: #92828A;

  --red: #FF5266;
  --red-line: rgba(255, 66, 88, 0.30);
  --red-line-2: rgba(255, 66, 88, 0.60);
  --red-soft: rgba(255, 66, 88, 0.10);

  --cyan: #46EEE3;
  --cyan-dim: rgba(70, 238, 227, 0.72);
  --cyan-soft: rgba(70, 238, 227, 0.10);
  --cyan-line: rgba(70, 238, 227, 0.50);

  --yellow: #FCEE0A;
  --yellow-soft: rgba(252, 238, 10, 0.10);
  --yellow-line: rgba(252, 238, 10, 0.50);

  --ok: #5CF29B;
  --ok-soft: rgba(92, 242, 155, 0.10);
  --ok-line: rgba(92, 242, 155, 0.42);
  --warn: #FCEE0A;
  --warn-soft: rgba(252, 238, 10, 0.10);
  --warn-line: rgba(252, 238, 10, 0.42);
  --bad: #FF5266;
  --bad-soft: rgba(255, 66, 88, 0.14);
  --bad-line: rgba(255, 82, 102, 0.55);

  --f-display: 'Saira', 'Bahnschrift', 'Segoe UI', system-ui, sans-serif;
  --f-body: 'Saira', 'Segoe UI', system-ui, sans-serif;
  --f-mono: 'JetBrains Mono', 'Consolas', monospace;

  --cut-6: polygon(0 0, 100% 0, 100% calc(100% - 6px), calc(100% - 6px) 100%, 0 100%);
  --cut-8: polygon(0 0, 100% 0, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0 100%);
}

/* ---------- Base ---------- */
html, body, .stApp, p, label, input, textarea, button, li, td, th {
  font-family: var(--f-body);
}
.stApp {
  background-color: var(--void);
  background-image:
    radial-gradient(ellipse 80% 38% at 50% -12%, rgba(255, 66, 88, 0.10), transparent 70%),
    __CROSS__;
  background-size: auto, 72px 72px;
  color: var(--ink);
}
.stApp::before {
  content: "";
  position: fixed; top: 0; left: 0; right: 0; height: 3px; z-index: 999;
  background: linear-gradient(90deg, var(--yellow) 0 140px, var(--red-line-2) 140px, transparent 82%);
  pointer-events: none;
}
::selection { background: var(--yellow); color: #050506; }
a { color: var(--cyan) !important; }
code, pre, .mono, div[data-testid="stCode"] * { font-family: var(--f-mono) !important; }

#MainMenu, footer, [data-testid="stMainMenu"], [data-testid="stAppDeployButton"],
.stAppDeployButton, .stDeployButton, [data-testid="stToolbarActions"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"], .stConnectionStatus,
div[class*="StatusWidget"], div[class*="connection-status"],
div[data-testid="stConnectionStatus"] { display: none !important; }

header[data-testid="stHeader"] {
  background: transparent !important;
  pointer-events: none;
  z-index: 990;
}
[data-testid="stToolbar"] {
  background: transparent !important;
  pointer-events: none;
}
[data-testid="stExpandSidebarButton"],
[data-testid="stExpandSidebarButton"] button {
  pointer-events: auto !important;
  opacity: 1 !important;
  visibility: visible !important;
}
[data-testid="stExpandSidebarButton"] {
  background: var(--panel) !important;
  color: var(--cyan) !important;
  border: 1px solid var(--cyan-line) !important;
  border-radius: 0 !important;
  clip-path: var(--cut-6);
  margin: 6px 0 0 6px;
}
[data-testid="stExpandSidebarButton"]:hover {
  background: var(--yellow-soft) !important;
  color: var(--yellow) !important;
  border-color: var(--yellow-line) !important;
}
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapseButton"] button {
  opacity: 1 !important;
  visibility: visible !important;
}
[data-testid="stSidebarCollapseButton"] button {
  color: var(--muted) !important;
  border-radius: 0 !important;
}
[data-testid="stSidebarCollapseButton"] button:hover {
  color: var(--cyan) !important;
  background: var(--cyan-soft) !important;
}
.block-container { padding-top: 1.8rem; padding-bottom: 3rem; max-width: 1200px; }

::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: var(--void); }
::-webkit-scrollbar-thumb { background: var(--red-line-2); }
::-webkit-scrollbar-thumb:hover { background: var(--cyan); }

:focus-visible { outline: 2px solid var(--cyan) !important; outline-offset: 2px; }

/* ---------- Typography ---------- */
h1, h2, h3, h4 {
  font-family: var(--f-display) !important;
  color: var(--ink) !important;
  font-weight: 700 !important;
  letter-spacing: 0.02em;
}
h3 { font-size: 1.3rem !important; color: var(--cyan) !important; }
div[data-testid="stMarkdownContainer"] p, li { line-height: 1.6; }
.stCaption, [data-testid="stCaptionContainer"] p { color: var(--muted) !important; }
div[data-testid="stWidgetLabel"] p, label p {
  font-family: var(--f-display);
  font-weight: 600;
  font-size: 1rem;
  letter-spacing: 0.02em;
  color: var(--ink-2) !important;
}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {
  background: #070506 !important;
  border-right: 1px solid var(--red-line) !important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] { gap: 4px; }
section[data-testid="stSidebar"] div[role="radiogroup"] label {
  display: flex; align-items: center;
  width: 100%; margin: 0; padding: 10px 12px;
  border: 1px solid transparent;
  border-left: 3px solid transparent;
  color: var(--ink-2);
  cursor: pointer;
  transition: background 140ms ease, border-color 140ms ease, color 140ms ease;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child { display: none; }
section[data-testid="stSidebar"] div[role="radiogroup"] label::before {
  content: ""; width: 18px; height: 18px; margin-right: 12px; flex-shrink: 0;
  background-color: currentColor;
  -webkit-mask-size: contain; mask-size: contain;
  -webkit-mask-repeat: no-repeat; mask-repeat: no-repeat;
  -webkit-mask-position: center; mask-position: center;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label p {
  color: inherit !important;
  font-family: var(--f-display);
  font-weight: 600;
  font-size: 1.08rem;
  letter-spacing: 0.02em;
  margin: 0;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
  background: var(--cyan-soft);
  border-color: var(--cyan-line);
  border-left-color: var(--cyan);
  color: var(--cyan);
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
  background: var(--yellow-soft);
  border-color: var(--yellow-line);
  border-left-color: var(--yellow);
  color: var(--yellow);
}
/* system pages sit apart from the workspace pages */
section[data-testid="stSidebar"] div[role="radiogroup"] label:nth-of-type(7) { margin-top: 14px; }

/* ---------- Bordered containers: frame with cyan corner brackets ---------- */
div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"]) {
  position: relative;
  background: var(--panel);
  border: 1px solid var(--red-line) !important;
  border-radius: 0 !important;
  padding: 4px 6px;
  transition: border-color 160ms ease;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"]):hover {
  border-color: var(--red-line-2) !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"])::before,
div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"])::after {
  content: ""; position: absolute; width: 14px; height: 14px; pointer-events: none;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"])::before {
  top: -1px; left: -1px; border-top: 2px solid var(--cyan); border-left: 2px solid var(--cyan);
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"])::after {
  bottom: -1px; right: -1px; border-bottom: 2px solid var(--cyan); border-right: 2px solid var(--cyan);
}

/* ---------- Buttons ---------- */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button,
div[data-testid="stPopover"] > button {
  border-radius: 0;
  clip-path: var(--cut-8);
  font-family: var(--f-display);
  font-weight: 600;
  font-size: 1.02rem;
  letter-spacing: 0.03em;
  border: 1px solid var(--red-line-2);
  background: transparent;
  color: var(--ink);
  padding: 0.5rem 1.1rem;
  min-height: 2.5rem;
  transition: border-color 150ms ease, background 150ms ease, color 150ms ease, transform 100ms ease;
}
.stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover,
div[data-testid="stPopover"] > button:hover {
  border-color: var(--cyan);
  color: var(--cyan);
  background: var(--cyan-soft);
}
.stButton > button:active, .stFormSubmitButton > button:active { transform: translateY(1px); }
.stButton > button:disabled, .stDownloadButton > button:disabled, .stFormSubmitButton > button:disabled {
  opacity: 0.38; border-color: var(--red-line);
}
.stButton > button p, .stDownloadButton > button p, .stFormSubmitButton > button p,
div[data-testid="stPopover"] > button p { color: inherit !important; font-family: var(--f-display); font-weight: inherit; }

.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"], .stFormSubmitButton > button[kind="primaryFormSubmit"] {
  background: var(--yellow);
  border: 1px solid var(--yellow);
  color: #050506 !important;
  font-weight: 700;
}
.stButton > button[kind="primary"] p, .stDownloadButton > button[kind="primary"] p,
.stFormSubmitButton > button[kind="primary"] p, .stFormSubmitButton > button[kind="primaryFormSubmit"] p {
  color: #050506 !important;
}
.stButton > button[kind="primary"]:hover, .stDownloadButton > button[kind="primary"]:hover,
.stFormSubmitButton > button[kind="primary"]:hover, .stFormSubmitButton > button[kind="primaryFormSubmit"]:hover {
  background: #FFF76B; border-color: #FFF76B; color: #050506 !important;
}
.stButton > button[kind="primary"]:disabled, .stFormSubmitButton > button[kind="primary"]:disabled {
  background: rgba(252, 238, 10, 0.22); border-color: transparent;
}
.stButton > button[kind="primary"]:disabled p { color: rgba(5, 5, 6, 0.55) !important; }

/* ---------- Inputs ---------- */
div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div, div[data-baseweb="select"] > div {
  background: var(--input) !important;
  border-color: var(--red-line-2) !important;
  color: var(--ink) !important;
  border-radius: 0 !important;
}
div[data-baseweb="input"] > div:focus-within, div[data-baseweb="textarea"] > div:focus-within,
div[data-baseweb="select"] > div:focus-within {
  border-color: var(--cyan) !important;
  box-shadow: 0 0 0 1px var(--cyan-line);
}
input, textarea { color: var(--ink) !important; background: transparent !important; }
input::placeholder, textarea::placeholder { color: var(--muted) !important; opacity: 1; }
div[data-baseweb="popover"] > div, div[data-testid="stPopoverBody"], ul[role="listbox"] {
  background: var(--panel) !important; color: var(--ink) !important;
  border: 1px solid var(--cyan-line) !important; border-radius: 0 !important;
}
li[role="option"] { color: var(--ink) !important; }
li[role="option"]:hover, li[role="option"][aria-selected="true"] { background: var(--cyan-soft) !important; }
div[role="dialog"] > div { background: var(--panel) !important; border: 1px solid var(--cyan-line) !important; border-radius: 0 !important; }

section[data-testid="stFileUploaderDropzone"], section[data-testid="stFileUploadDropzone"] {
  background: var(--input) !important;
  border: 1px dashed var(--cyan-line) !important;
  border-radius: 0 !important;
}
section[data-testid="stFileUploaderDropzone"]:hover, section[data-testid="stFileUploadDropzone"]:hover {
  border-color: var(--cyan) !important; background: var(--cyan-soft) !important;
}
div[data-testid="stExpander"] { background: var(--panel) !important; border: 1px solid var(--red-line) !important; border-radius: 0 !important; }
div[data-testid="stExpander"] summary p { font-family: var(--f-display); font-weight: 600; font-size: 1.02rem; }
div[data-testid="stAlert"] { border-radius: 0 !important; border-left: 3px solid currentColor; }
div[data-testid="stCode"], div[data-testid="stCode"] pre {
  background: var(--input) !important; border-radius: 0 !important;
}
div[data-testid="stCode"] { border: 1px solid var(--red-line); border-left: 2px solid var(--cyan); }
div[data-testid="stImage"] img { border: 1px solid var(--red-line); }

/* segmented control (Kamera / Unggah foto, filter log) */
button[data-testid="stBaseButton-segmented_control"], button[data-testid="stBaseButton-segmented_controlActive"] {
  border-radius: 0 !important; font-family: var(--f-display); font-weight: 600;
  border: 1px solid var(--red-line-2) !important; background: transparent !important; color: var(--ink-2) !important;
}
button[data-testid="stBaseButton-segmented_controlActive"] {
  background: var(--yellow) !important; border-color: var(--yellow) !important; color: #050506 !important;
}
button[data-testid="stBaseButton-segmented_controlActive"] p { color: #050506 !important; }

/* ---------- Tabs: the reference's top navigation (yellow = active) ---------- */
div[data-baseweb="tab-list"] { gap: 6px; border-bottom: 1px solid var(--red-line); padding-bottom: 0; }
button[data-baseweb="tab"] {
  background: rgba(70, 238, 227, 0.12) !important;
  color: var(--cyan-dim) !important;
  padding: 0.55rem 1.3rem !important;
  height: auto !important;
  clip-path: polygon(0 0, calc(100% - 9px) 0, 100% 9px, 100% 100%, 0 100%);
  transition: background 140ms ease, color 140ms ease;
}
button[data-baseweb="tab"] p {
  color: inherit !important;
  font-family: var(--f-display); font-weight: 600; font-size: 0.98rem;
  letter-spacing: 0.04em; text-transform: uppercase;
}
button[data-baseweb="tab"]:hover { background: rgba(70, 238, 227, 0.22) !important; color: var(--cyan) !important; }
button[data-baseweb="tab"][aria-selected="true"] { background: var(--yellow) !important; color: #050506 !important; }
div[data-baseweb="tab-highlight"], div[data-baseweb="tab-border"] { display: none !important; }
div[data-testid="stTabs"] [role="tabpanel"] { padding-top: 1.2rem; }

/* ---------- Metrics ---------- */
div[data-testid="stMetric"] {
  position: relative;
  background: var(--panel);
  border: 1px solid var(--red-line);
  border-left: 3px solid var(--cyan);
  padding: 14px 18px;
  clip-path: var(--cut-8);
}
div[data-testid="stMetricLabel"] p {
  font-family: var(--f-display); color: var(--muted) !important;
  font-size: 0.98rem; font-weight: 600; letter-spacing: 0.04em;
}
div[data-testid="stMetricValue"] {
  font-family: var(--f-display) !important; font-size: 2.1rem; font-weight: 700; color: var(--ink) !important;
}

/* ---------- Motion ---------- */
@keyframes kv-pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.4; transform: scale(0.8); } }
@keyframes kv-wipe { from { clip-path: inset(0 100% 0 0); } to { clip-path: inset(0 0 0 0); } }
@keyframes kv-draw { from { transform: scaleX(0); } to { transform: scaleX(1); } }
.kv-dot {
  width: 7px; height: 7px; border-radius: 50%; display: inline-block; background: currentColor;
  animation: kv-pulse 1.8s infinite ease-in-out; flex-shrink: 0;
}
@media (prefers-reduced-motion: reduce) {
  .kv-dot, .kv-plaque, .kv-head-line { animation: none !important; }
}

/* ---------- Brand + breadcrumb ---------- */
.kv-brand { display: flex; align-items: center; gap: 12px; }
.kv-mark { width: 38px; height: 38px; flex-shrink: 0; color: var(--cyan); }
.kv-brand-name { font-family: var(--f-display); font-weight: 700; font-size: 1.35rem; color: var(--ink); line-height: 1; letter-spacing: 0.04em; }
.kv-brand-sub { font-family: var(--f-body); font-size: 0.8rem; color: var(--red); margin-top: 4px; }
.kv-crumb { display: flex; align-items: center; gap: 9px; white-space: nowrap; font-family: var(--f-display); font-weight: 500; font-size: 1rem; color: var(--muted); }
.kv-crumb i { font-style: normal; color: var(--red-line-2); }
.kv-crumb b { color: var(--yellow); font-weight: 400; }

/* ---------- Page header: chamfered plaque (the reference's section boxes) ---------- */
.kv-head { margin: 0 0 22px 0; }
.kv-head-row { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; margin-bottom: 14px; }
.kv-plaque {
  display: inline-block; max-width: 100%; padding: 1px;
  background: var(--cyan-line);
  clip-path: polygon(0 0, calc(100% - 14px) 0, 100% 14px, 100% 100%, 14px 100%, 0 calc(100% - 14px));
  animation: kv-wipe 520ms cubic-bezier(.2, .8, .2, 1) both;
}
.kv-plaque-in {
  display: flex; align-items: center; gap: 12px;
  padding: 11px 32px 11px 20px;
  background: #07100F;
  color: var(--cyan);
  font-family: var(--f-display); font-weight: 600; font-size: 1.45rem; line-height: 1.1;
  letter-spacing: 0.03em; text-transform: uppercase;
  clip-path: polygon(0 0, calc(100% - 13px) 0, 100% 13px, 100% 100%, 13px 100%, 0 calc(100% - 13px));
}
.kv-head-tag { font-family: var(--f-display); font-weight: 500; font-size: 0.95rem; color: var(--red); white-space: nowrap; }
.kv-head-line {
  flex: 1; min-width: 40px; height: 1px; transform-origin: left;
  background: linear-gradient(90deg, var(--red-line-2), transparent);
  animation: kv-draw 700ms 200ms ease-out both;
}
.kv-lead { color: var(--ink-2); font-size: 1.02rem; max-width: 74ch; line-height: 1.65; }

/* ---------- Module heading inside cards ---------- */
.kv-mod { display: flex; align-items: center; gap: 12px; margin: 2px 0 6px 0; }
.kv-mod-ic {
  width: 38px; height: 38px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  background: var(--yellow-soft); color: var(--yellow); border: 1px solid var(--yellow-line);
  clip-path: var(--cut-6);
}
.kv-mod-t { font-family: var(--f-display); font-weight: 700; font-size: 1.2rem; color: var(--ink); line-height: 1.1; }
.kv-mod-d { color: var(--muted); font-size: 0.92rem; line-height: 1.45; margin-top: 8px; }

/* ---------- Status (top bar): one quiet line, no boxes ---------- */
.kv-status { display: flex; align-items: center; justify-content: flex-end; gap: 9px; font-family: var(--f-display); font-weight: 500; font-size: 0.98rem; color: var(--ink-2); white-space: nowrap; }
.kv-status small { color: var(--muted); font-size: 0.92rem; font-weight: 400; }
.kv-status.ok .kv-dot { color: var(--ok); }
.kv-status.warn .kv-dot { color: var(--warn); }
.kv-status.bad .kv-dot { color: var(--bad); }

/* ---------- Operator block (sidebar) ---------- */
.kv-op { display: flex; align-items: center; gap: 12px; padding: 10px 0; }
.kv-op-ic { width: 34px; height: 34px; display: flex; align-items: center; justify-content: center; color: var(--cyan); border: 1px solid var(--cyan-line); background: var(--cyan-soft); clip-path: var(--cut-6); flex-shrink: 0; }
.kv-op-n { font-family: var(--f-display); font-weight: 600; font-size: 1.05rem; color: var(--ink); line-height: 1.15; }
.kv-op-s { font-size: 0.86rem; color: var(--muted); }

/* ---------- Chips ---------- */
.kv-chip {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 3px 11px;
  font-family: var(--f-display); font-weight: 500; font-size: 0.88rem; white-space: nowrap;
  border: 1px solid var(--red-line-2); color: var(--ink-2); background: var(--panel-2);
  clip-path: var(--cut-6);
  margin: 0 6px 4px 0;
}
.kv-chip.ok { color: var(--ok); background: var(--ok-soft); border-color: var(--ok-line); }
.kv-chip.bad { color: var(--bad); background: var(--bad-soft); border-color: var(--bad-line); }
.kv-chip.warn { color: var(--warn); background: var(--warn-soft); border-color: var(--warn-line); }
.kv-chip.info { color: var(--cyan); background: var(--cyan-soft); border-color: var(--cyan-line); }
.kv-chip.standby { color: var(--muted); }
.kv-chip span { color: inherit; }

/* ---------- Key / value ---------- */
.kv-kv { display: grid; grid-template-columns: 170px 1fr; gap: 9px 16px; font-size: 0.96rem; }
.kv-kv .k { color: var(--muted); font-family: var(--f-display); font-weight: 600; font-size: 1.02rem; letter-spacing: 0.02em; }
.kv-kv .v { color: var(--ink); font-family: var(--f-mono); word-break: break-all; }

/* ---------- Three-gate stepper ---------- */
.kv-steps { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin: 6px 0 24px 0; }
.kv-step {
  display: flex; align-items: center; gap: 14px;
  padding: 12px 16px;
  background: var(--panel);
  border: 1px solid var(--red-line);
  border-top: 3px solid var(--red-line-2);
  clip-path: var(--cut-8);
}
.kv-step .num { font-family: var(--f-display); font-weight: 700; font-size: 2.2rem; line-height: 1; color: var(--muted); min-width: 34px; }
.kv-step .st { font-family: var(--f-body); font-size: 0.84rem; color: var(--muted); display: flex; align-items: center; gap: 6px; }
.kv-step .t { font-family: var(--f-display); font-weight: 700; font-size: 1.08rem; color: var(--ink-2); margin-top: 3px; line-height: 1.15; }
.kv-step.done { border-top-color: var(--ok); background: linear-gradient(180deg, var(--ok-soft), var(--panel) 70%); }
.kv-step.done .num, .kv-step.done .st { color: var(--ok); }
.kv-step.active { border-top-color: var(--yellow); background: linear-gradient(180deg, var(--yellow-soft), var(--panel) 70%); }
.kv-step.active .num, .kv-step.active .st { color: var(--yellow); }
.kv-step.active .t { color: var(--ink); }

/* ---------- Segmented meter (health-bar motif) ---------- */
.kv-meter-wrap { margin: 10px 0 16px 0; }
.kv-meter-head { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 6px; }
.kv-meter-lbl { font-family: var(--f-display); font-weight: 600; font-size: 1.02rem; color: var(--ink-2); letter-spacing: 0.02em; }
.kv-meter-val { font-family: var(--f-display); font-weight: 700; font-size: 1.7rem; line-height: 1; color: var(--ink); }
.kv-meter-val small { font-size: 0.9rem; color: var(--muted); margin-left: 2px; }
.kv-meter-track {
  position: relative; height: 14px;
  background: repeating-linear-gradient(90deg, rgba(255, 66, 88, 0.16) 0 10px, transparent 10px 13px);
}
.kv-meter-fill { height: 100%; transition: width 300ms ease; }
.kv-meter-fill.ok { background: repeating-linear-gradient(90deg, var(--ok) 0 10px, transparent 10px 13px); }
.kv-meter-fill.info { background: repeating-linear-gradient(90deg, var(--cyan) 0 10px, transparent 10px 13px); }
.kv-meter-fill.warn { background: repeating-linear-gradient(90deg, var(--warn) 0 10px, transparent 10px 13px); }
.kv-meter-fill.bad { background: repeating-linear-gradient(90deg, var(--bad) 0 10px, transparent 10px 13px); }
.kv-meter-tick { position: absolute; top: -5px; bottom: -5px; width: 2px; background: var(--yellow); }
.kv-meter-tick::before {
  content: ""; position: absolute; top: -5px; left: -4px;
  border: 5px solid transparent; border-top-color: var(--yellow); border-bottom: 0;
}
.kv-meter-sub { font-size: 0.88rem; color: var(--muted); margin-top: 8px; }

/* ---------- Crypto pipeline ---------- */
.kv-pipeline { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-bottom: 20px; }
.kv-pipe-node {
  padding: 8px 14px; border: 1px solid var(--red-line); background: var(--panel);
  clip-path: var(--cut-6);
}
.kv-pipe-node .pn-t { font-family: var(--f-display); font-weight: 700; font-size: 1.02rem; color: var(--muted); }
.kv-pipe-node .pn-s { font-family: var(--f-body); font-size: 0.8rem; color: var(--muted); }
.kv-pipe-node.on { border-color: var(--yellow-line); background: var(--yellow-soft); }
.kv-pipe-node.on .pn-t { color: var(--yellow); }
.kv-pipe-arrow { color: var(--red-line-2); display: inline-flex; }

/* ---------- Activity console ---------- */
.kv-log {
  background: var(--input); color: var(--ink-2);
  border: 1px solid var(--red-line); border-left: 2px solid var(--cyan);
  padding: 12px 14px;
  font-family: var(--f-mono); font-size: 13px; line-height: 1.75;
  max-height: 420px; overflow-y: auto;
}
.kv-log .t { color: var(--muted); }
.kv-log .s { color: var(--cyan); }
.kv-log .OK { color: var(--ok); }
.kv-log .WARN { color: var(--warn); }
.kv-log .CRIT { color: var(--bad); }
.kv-log .INFO { color: var(--ink-2); }

/* ---------- Tables ---------- */
.kv-table { width: 100%; border-collapse: collapse; font-size: 0.95rem; }
.kv-table th {
  text-align: left; padding: 9px 10px;
  font-family: var(--f-display); font-weight: 700; font-size: 0.98rem; letter-spacing: 0.04em; color: var(--cyan);
  border-bottom: 1px solid var(--red-line-2);
}
.kv-table td { padding: 10px; border-bottom: 1px solid var(--red-line); color: var(--ink); vertical-align: middle; }
.kv-table tr:last-child td { border-bottom: none; }
.kv-table tr:hover td { background: var(--red-soft); }
.kv-table td.mono { font-family: var(--f-mono); font-size: 0.88rem; }

@media (max-width: 760px) {
  .kv-steps { grid-template-columns: 1fr; }
  .kv-plaque-in { font-size: 1.25rem; padding-right: 26px; }
  .kv-kv { grid-template-columns: 1fr; gap: 2px 0; }
  .kv-kv .v { margin-bottom: 8px; }
}
__NAV_ICONS__
</style>
"""


def inject_theme() -> None:
    css = _CSS.replace("__CROSS__", _CROSS_BG).replace("__NAV_ICONS__", _nav_icon_css())
    st.markdown(css, unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# Render helpers
# --------------------------------------------------------------------------- #
def page_header(eyebrow: str, title: str, lead: str = "", icon_name: Optional[str] = None) -> None:
    """Chamfered title plaque; the eyebrow says which requirement the page satisfies."""
    ic = icon(icon_name, 24) if icon_name else ""
    st.markdown(
        "<div class='kv-head'><div class='kv-head-row'>"
        f"<div class='kv-plaque'><div class='kv-plaque-in'>{ic}<span>{html.escape(title)}</span></div></div>"
        f"<span class='kv-head-tag'>{html.escape(eyebrow)}</span><span class='kv-head-line'></span></div>"
        + (f"<div class='kv-lead'>{html.escape(lead)}</div>" if lead else "")
        + "</div>",
        unsafe_allow_html=True,
    )


def module_head(icon_name: str, title: str, desc: str = "") -> None:
    """Icon + title (+ short description) used at the top of a card."""
    st.markdown(
        f"<div class='kv-mod'><div class='kv-mod-ic'>{icon(icon_name, 20)}</div>"
        f"<div class='kv-mod-t'>{html.escape(title)}</div></div>"
        + (f"<div class='kv-mod-d'>{html.escape(desc)}</div>" if desc else ""),
        unsafe_allow_html=True,
    )


def crumb(*parts: str) -> None:
    """Breadcrumb: the last part is the current page."""
    items = [html.escape(p) for p in parts]
    body = "<i>/</i>".join(f"<b>{p}</b>" if n == len(items) - 1 else f"<span>{p}</span>" for n, p in enumerate(items))
    st.markdown(f"<div class='kv-crumb'>{body}</div>", unsafe_allow_html=True)


def status(text: str, kind: str = "ok", detail: str = "") -> None:
    """Single quiet status line for the top bar: a pulsing dot and plain text."""
    extra = f"<small>{html.escape(detail)}</small>" if detail else ""
    st.markdown(
        f"<div class='kv-status {kind}'><span class='kv-dot'></span><span>{html.escape(text)}</span>{extra}</div>",
        unsafe_allow_html=True,
    )


def operator(name: str, detail: str = "") -> None:
    """Signed-in operator, shown once at the bottom of the sidebar."""
    st.markdown(
        f"<div class='kv-op'><div class='kv-op-ic'>{icon('user', 17)}</div><div>"
        f"<div class='kv-op-n'>{html.escape(name)}</div>"
        + (f"<div class='kv-op-s'>{html.escape(detail)}</div>" if detail else "")
        + "</div></div>",
        unsafe_allow_html=True,
    )


def chip(text: str, kind: str = "", icon_name: Optional[str] = None, dot: bool = False) -> str:
    if dot:
        prefix = "<span class='kv-dot'></span>"
    elif icon_name:
        prefix = icon(icon_name, 12)
    elif kind == "bad":
        prefix = icon("alert", 12)  # errors never rely on colour alone
    else:
        prefix = ""
    return f"<span class='kv-chip {kind}'>{prefix}<span>{html.escape(text)}</span></span>"


def kv_grid(rows: list[tuple[str, str]]) -> None:
    body = "".join(
        f"<div class='k'>{html.escape(k)}</div><div class='v'>{html.escape(str(v))}</div>" for k, v in rows
    )
    st.markdown(f"<div class='kv-kv'>{body}</div>", unsafe_allow_html=True)


def steps(current: int) -> None:
    items = [
        (1, "Kunci perangkat keras", "usb"),
        (2, "Identitas dan biometrik", "user"),
        (3, "Ruang kerja vault", "shield"),
    ]
    out = []
    for n, title, _ic in items:
        if n < current:
            cls, state, prefix = "done", "Terverifikasi", icon("check", 13)
        elif n == current:
            cls, state, prefix = "active", "Sedang berjalan", "<span class='kv-dot'></span>"
        else:
            cls, state, prefix = "", "Terkunci", icon("lock", 12)
        out.append(
            f"<div class='kv-step {cls}'><div class='num'>0{n}</div>"
            f"<div><div class='st'>{prefix}<span>{state}</span></div><div class='t'>{title}</div></div></div>"
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
        f"<span class='kv-meter-val'>{clamped:.1f}<small>%</small></span></div>"
        f"<div class='kv-meter-track'><div class='kv-meter-fill {kind}' style='width:{clamped:.1f}%;'></div>{tick}</div>"
        f"{sub_html}</div>",
        unsafe_allow_html=True,
    )


def pipeline(stages: list[tuple[str, str, bool]]) -> None:
    """Horizontal cryptographic pipeline strip."""
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


_MARK_SVG = (
    '<svg class="kv-mark" viewBox="0 0 40 40" fill="none" aria-hidden="true">'
    '<path d="M20 4 37 35H3z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>'
    '<g fill="#FCEE0A"><circle cx="20" cy="17" r="2"/><circle cx="16" cy="25" r="2"/>'
    '<circle cx="24" cy="25" r="2"/><circle cx="12" cy="31" r="1.6"/><circle cx="20" cy="31" r="1.6"/>'
    '<circle cx="28" cy="31" r="1.6"/></g></svg>'
)


def brand(sub: str = "Forensic evidence vault") -> None:
    st.markdown(
        f"<div class='kv-brand'>{_MARK_SVG}"
        f"<div><div class='kv-brand-name'>KRYPT VAULT</div>"
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
