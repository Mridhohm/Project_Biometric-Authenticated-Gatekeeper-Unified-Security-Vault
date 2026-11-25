"""
Krypt Vault - Native Desktop Application Launcher
=================================================

Standalone Windows Desktop Shell using PyWebView and headless Streamlit:
  1. Spawns the local Krypt Vault Streamlit engine in headless mode.
  2. Waits for the localhost endpoint to become healthy.
  3. Launches a native 1280x800 Windows Desktop Window with dark Cyberpunk background.
  4. Gracefully terminates the background server upon window close.
"""

from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

# Determine base directory whether running from source or PyInstaller bundle
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys._MEIPASS)  # type: ignore[attr-defined]
else:
    BASE_DIR = Path(__file__).resolve().parent

APP_PATH = BASE_DIR / "app.py"


def _is_port_in_use(port: int) -> bool:
    """Check whether another process is actively listening on loopback."""
    for family, addr in ((socket.AF_INET, "127.0.0.1"), (socket.AF_INET6, "::1")):
        try:
            with socket.socket(family, socket.SOCK_STREAM) as probe:
                probe.settimeout(0.15)
                if probe.connect_ex((addr, port)) == 0:
                    return True
        except OSError:
            continue
    return False


def find_free_port(start_port: int = 8501, max_attempts: int = 100) -> int:
    """Locate an available local TCP port for the background Streamlit instance."""
    for port in range(start_port, start_port + max_attempts):
        if _is_port_in_use(port):
            continue
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return start_port


def wait_for_server(url: str, timeout_seconds: float = 25.0) -> bool:
    """Poll the local HTTP endpoint until Streamlit returns HTTP 200."""
    start_time = time.time()
    health_url = f"{url.rstrip('/')}/_stcore/health"
    while time.time() - start_time < timeout_seconds:
        try:
            req = urllib.request.Request(health_url, headers={"User-Agent": "Krypt-Vault-Launcher"})
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            try:
                req_root = urllib.request.Request(url, headers={"User-Agent": "Krypt-Vault-Launcher"})
                with urllib.request.urlopen(req_root, timeout=1.0) as resp_root:
                    if resp_root.status in (200, 404, 403):
                        return True
            except Exception:
                pass
        time.sleep(0.3)
    return False


def run_streamlit_thread(port: int) -> None:
    """Fallback runner for frozen PyInstaller environment."""
    from streamlit.web import cli as stcli

    sys.argv = [
        "streamlit",
        "run",
        str(APP_PATH),
        f"--server.port={port}",
        "--server.address=127.0.0.1",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
        "--server.enableCORS=false",
        "--server.enableXsrfProtection=false",
    ]
    stcli.main()


def main() -> None:
    port = find_free_port(8501)
    server_url = f"http://127.0.0.1:{port}"
    print(f"// [SYS] Initializing Krypt Vault Desktop Engine on {server_url}...")

    server_process: Optional[subprocess.Popen] = None

    if getattr(sys, "frozen", False):
        # In PyInstaller frozen bundle, run Streamlit in daemon thread
        server_thread = threading.Thread(target=run_streamlit_thread, args=(port,), daemon=True)
        server_thread.start()
    else:
        # Running from source, run Streamlit in isolated subprocess
        cmd = [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(APP_PATH),
            f"--server.port={port}",
            "--server.address=127.0.0.1",
            "--server.headless=true",
            "--browser.gatherUsageStats=false",
            "--server.enableCORS=false",
            "--server.enableXsrfProtection=false",
        ]
        server_process = subprocess.Popen(
            cmd,
            cwd=str(BASE_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    # Wait for Streamlit server to initialize
    print("// [SYS] Awaiting localhost engine handshake...")
    is_ready = wait_for_server(server_url, timeout_seconds=25.0)
    if not is_ready:
        print("[!] [ERR] Streamlit server failed to respond within timeout window.")

    # Launch native desktop window with PyWebView
    try:
        import webview

        # Enable native SaveFileDialog downloads for st.download_button inside WebView2
        webview.settings["ALLOW_DOWNLOADS"] = True
        print("// [SYS] Opening native desktop viewport (1280x800)...")
        window = webview.create_window(
            title="Krypt Vault // Forensic Security Suite",
            url=server_url,
            width=1340,
            height=860,
            resizable=True,
            background_color="#06070C",
        )
        webview.start()
    finally:
        # Clean termination when the native desktop window is closed
        print("// [SYS] Native desktop viewport closed. Terminating background engine...")
        if server_process is not None:
            try:
                server_process.terminate()
                server_process.wait(timeout=3.0)
            except Exception:
                try:
                    server_process.kill()
                except Exception:
                    pass
        print("// [SYS] Krypt Vault session terminated cleanly.")


if __name__ == "__main__":
    main()
