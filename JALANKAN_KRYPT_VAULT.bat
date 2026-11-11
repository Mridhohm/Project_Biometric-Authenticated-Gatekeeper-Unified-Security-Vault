@echo off
setlocal enabledelayedexpansion
title Krypt Vault - Forensic Evidence Security Suite
color 0B

echo =======================================================================
echo          KRYPT VAULT : FORENSIC SECURITY EDITION
echo          Tugas Akhir Kriptografi - UPN "Veteran" Yogyakarta
echo          Dosen Pengampu: Pak Bagus
echo =======================================================================
echo.

:: 1. Cek apakah Python terpasang di komputer
python --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo [ERROR] Python tidak terdeteksi di sistem komputer ini.
    echo.
    echo Silakan unduh dan pasang Python 3.10+ dari: https://www.python.org/downloads/
    echo PENTING: Saat instalasi, pastikan mencentang "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

:: 2. Navigasi ke direktori aplikasi
if exist "%~dp0geovault-crypto-app\app.py" (
    cd /d "%~dp0geovault-crypto-app"
) else if exist "%~dp0app.py" (
    cd /d "%~dp0"
)

:: 3. Cek dependensi (Streamlit, PyCryptodome, Pillow, Psutil)
echo [*] Memeriksa dependensi Python...
python -c "import streamlit, Crypto, PIL, psutil" >nul 2>&1
if errorlevel 1 (
    echo [!] Dependensi belum lengkap terpasang.
    echo [*] Mengunduh dan memasang paket dependensi via pip...
    echo     (Hanya dilakukan sekali, memerlukan koneksi internet)
    echo.
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        color 0C
        echo.
        echo [ERROR] Gagal memasang dependensi.
        echo Pastikan komputer terhubung ke internet lalu jalankan ulang file ini.
        pause
        exit /b 1
    )
    echo.
    echo [OK] Seluruh dependensi berhasil dipasang!
)

:: 4. Jalankan aplikasi Krypt Vault
echo [+] Menjalankan Krypt Vault...
python run_desktop.py
if errorlevel 1 (
    echo.
    echo [*] Mencoba menjalankan via Streamlit CLI langsung...
    streamlit run app.py
)

pause
