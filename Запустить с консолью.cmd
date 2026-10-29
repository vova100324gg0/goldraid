@echo off
setlocal
cd /d "%~dp0"
echo Запускаю игру с выводом ошибок...
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" main.py
) else (
  python main.py
)
if errorlevel 1 (
  echo.
  echo Игра завершилась с ошибкой. Скопируйте текст выше для диагностики.
  pause
)