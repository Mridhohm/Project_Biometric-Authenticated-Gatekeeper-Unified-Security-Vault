@echo off
title Krypt Vault - Launcher
color 0B
echo =======================================================================
echo          [!] MEMULAI KRYPT VAULT - FORENSIC EVIDENCE VAULT
echo          Mata Kuliah: Kriptografi (UPN "Veteran" Yogyakarta)
echo          Dosen Pengampu: Pak Bagus
echo =======================================================================
echo.
cd /d "%~dp0"

if exist "run_desktop.py" (
    python run_desktop.py
) else if exist "geovault-crypto-app\run_desktop.py" (
    cd geovault-crypto-app
    python run_desktop.py
) else (
    echo Mengaktifkan via Streamlit...
    streamlit run app.py
)

pause
