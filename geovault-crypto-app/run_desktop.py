"""
Krypt Vault - Native Desktop Application Launcher
=================================================
Launches Krypt Vault as a standalone frameless desktop window.
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _is_port_in_use(port: int) -> bool:
    for family, host in ((socket.AF_INET, "127.0.0.1"), (socket.AF_INET6, "::1")):
        try:
            with socket.socket(family, socket.SOCK_STREAM) as sock:
                sock.settimeout(0.2)
                if sock.connect_ex((host, port)) == 0:
                    return True
        except OSError:
            pass
    return False


def find_free_port(start_port: int = 8501) -> int:
    for port in range(start_port, start_port + 100):
        if not _is_port_in_use(port):
            return port
    return start_port


def find_browser_app_cmd(url: str) -> list[str] | None:
    """Find Microsoft Edge or Google Chrome to launch in application window mode."""
    candidates = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    ]
    profile_dir = Path(os.path.expandvars(r"%LOCALAPPDATA%\KryptVault\EdgeProfile"))
    try:
        profile_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    for c in candidates:
        if os.path.isfile(c):
            return [c, f"--user-data-dir={profile_dir}", f"--app={url}", "--window-size=1320,880"]
    return None


def wait_for_server(url: str, timeout: float = 20.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as resp:
                if resp.status == 200:
                    return
        except Exception:
            time.sleep(0.3)


def main():
    print("=" * 65)
    print("      KRYPT VAULT : FORENSIC SECURITY EDITION")
    print("      Tugas Akhir Kriptografi — UPN \"Veteran\" Yogyakarta")
    print("=" * 65)
    print("\n[+] Menginisialisasi Server Krypt Vault...")

    os.chdir(str(BASE_DIR))
    port = find_free_port(8501)
    url = f"http://127.0.0.1:{port}"

    # Start streamlit server in background
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "app.py",
        "--server.port",
        str(port),
        "--server.address",
        "127.0.0.1",
        "--server.headless",
        "true",
        "--browser.serverAddress",
        "127.0.0.1",
        "--server.enableCORS",
        "false",
        "--server.enableXsrfProtection",
        "false",
    ]

    server_proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    wait_for_server(url)

    print(f"[+] Server aktif di {url}")
    opened_webview = False
    try:
        import webview

        print("[+] Membuka jendela Desktop Native (PyWebView 1340x860)...")
        webview.create_window(
            title="Krypt Vault // Forensic Security Suite",
            url=url,
            width=1340,
            height=860,
            min_size=(1024, 680),
            resizable=True,
            background_color="#090D16",
        )
        webview.start()
        opened_webview = True
    except Exception as exc:
        print(f"[i] PyWebView tidak tersedia ({exc}); beralih ke mode App Browser...")

    if opened_webview:
        print("\n[*] Jendela ditutup. Mematikan server Krypt Vault...")
        server_proc.terminate()
        try:
            server_proc.wait(timeout=4.0)
        except Exception:
            server_proc.kill()
        return

    browser_cmd = find_browser_app_cmd(url)
    if browser_cmd:
        print("[+] Membuka jendela Desktop App Mode (Frameless)...")
        subprocess.Popen(browser_cmd)
    else:
        print("[+] Membuka browser default...")
        webbrowser.open(url)

    print("\n[OK] KRYPT VAULT BERHASIL DIJALANKAN!")
    print("[i] Tekan Ctrl+C pada jendela ini untuk mematikan server aplikasi.")

    try:
        server_proc.wait()
    except KeyboardInterrupt:
        print("\n[*] Mematikan server Krypt Vault...")
        server_proc.terminate()
        server_proc.wait()


if __name__ == "__main__":
    main()
