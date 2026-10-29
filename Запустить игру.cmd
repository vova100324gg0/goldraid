@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\pythonw.exe" goto run

echo Окружение не найдено. Создаю .venv и устанавливаю Kivy...
where py >nul 2>nul
if errorlevel 1 (set "PY=python") else (set "PY=py -3")
%PY% -m venv .venv
if errorlevel 1 goto fail
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto fail

:run
start "" ".venv\Scripts\pythonw.exe" "main.py"
exit /b 0

:fail
echo.
echo Не удалось запустить игру. Запустите "Запустить с консолью.cmd", чтобы увидеть ошибку.
pause
exit /b 1