@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
echo Золотой рейд: подготовка APK...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "build_apk.ps1"
echo.
pause