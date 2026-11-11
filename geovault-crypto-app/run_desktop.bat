@echo off
title Krypt Vault // Desktop Launcher
echo ======================================================================
echo // KRYPT VAULT [v2.6_DESKTOP] -- INITIALIZING NATIVE WINDOW...
echo ======================================================================
python desktop_launcher.py
if errorlevel 1 (
    echo.
    echo [!] Desktop launcher exited with error code %errorlevel%.
    pause
)
