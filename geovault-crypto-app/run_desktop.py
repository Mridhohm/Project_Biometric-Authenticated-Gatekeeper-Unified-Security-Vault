"""
Krypt Vault - Native Desktop Application Launcher
=================================================
Launches Krypt Vault as a standalone frameless desktop window.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PORT = 8501
URL = f"http://localhost:{PORT}"


def find_browser_app_cmd() -> list[str] | None:
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
            return [c, f"--user-data-dir={profile_dir}", f"--app={URL}", "--window-size=1320,880"]
    return None


def main():
    print("=" * 65)
    print("      KRYPT VAULT : FORENSIC SECURITY EDITION")
    print("      Tugas Akhir Kriptografi — UPN \"Veteran\" Yogyakarta")
    print("=" * 65)
    print("\n[+] Menginisialisasi Server Krypt Vault...")

    os.chdir(str(BASE_DIR))

    # Start streamlit server in background
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "app.py",
        "--server.port",
        str(PORT),
        "--server.headless",
        "true",
        "--browser.serverAddress",
        "localhost",
        "--server.enableCORS",
        "false",
        "--server.enableXsrfProtection",
        "false",
    ]

    server_proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2.0)

    print(f"[+] Server aktif di {URL}")
    browser_cmd = find_browser_app_cmd()
    if browser_cmd:
        print("[+] Membuka jendela Desktop App Mode (Frameless)...")
        subprocess.Popen(browser_cmd)
    else:
        print("[+] Membuka browser default...")
        webbrowser.open(URL)

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
