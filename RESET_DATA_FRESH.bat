@echo off
title Krypt Vault - Reset Database to Fresh State
color 0E

echo =======================================================================
echo          KRYPT VAULT : RESET TO FACTORY FRESH STATE
echo =======================================================================
echo.
echo PERINGATAN: Tindakan ini akan menghapus semua operator yang terdaftar,
echo semua berkas terenkripsi, dan semua laporan rahasia di vault.db,
echo serta mengembalikan status ke awal pabrik (fresh 0 data).
echo.
set /p confirm="Apakah Anda yakin ingin me-reset aplikasi ke kondisi fresh? (Y/N): "
if /i not "%confirm%"=="Y" (
    echo Operasi dibatalkan.
    pause
    exit /b 0
)

if exist "%~dp0geovault-crypto-app\reset_fresh.py" (
    cd /d "%~dp0geovault-crypto-app"
) else if exist "%~dp0reset_fresh.py" (
    cd /d "%~dp0"
)

python reset_fresh.py
echo.
pause
