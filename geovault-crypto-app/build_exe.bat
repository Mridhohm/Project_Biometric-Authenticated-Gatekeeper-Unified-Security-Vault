@echo off
setlocal enabledelayedexpansion
echo ======================================================================
echo KRYPT VAULT // STANDALONE WINDOWS DESKTOP BUILD SCRIPT (.EXE)
echo ======================================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [!] Error: Python is not found in system PATH.
    pause
    exit /b 1
)

echo [+] Checking and installing build dependencies...
pip install --upgrade pyinstaller pywebview streamlit pycryptodome pillow psutil

echo.
echo [+] Compiling KryptVault.exe using PyInstaller...
pyinstaller --noconfirm --onedir --windowed ^
    --name "KryptVault" ^
    --add-data "modules;modules" ^
    --add-data "storage;storage" ^
    --add-data ".streamlit;.streamlit" ^
    --add-data "config.py;." ^
    --add-data "database.py;." ^
    --add-data "ui_theme.py;." ^
    --add-data "app.py;." ^
    --hidden-import "streamlit" ^
    --hidden-import "webview" ^
    --hidden-import "Crypto" ^
    --hidden-import "PIL" ^
    --hidden-import "psutil" ^
    --copy-metadata "streamlit" ^
    desktop_launcher.py

if errorlevel 1 (
    echo.
    echo [!] Build encountered errors. Inspect the terminal log above.
    pause
    exit /b 1
)

echo.
echo ======================================================================
echo [OK] BUILD COMPLETE!
echo Executable located at: dist\KryptVault\KryptVault.exe
echo ======================================================================
echo.
pause
