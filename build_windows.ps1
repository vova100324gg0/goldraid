# Сборка Windows-версии «Золотой рейд» через PyInstaller.
# Запуск:  powershell -ExecutionPolicy Bypass -File build_windows.ps1
#
# Результат:
#   build\windows\dist\GoldRaid\GoldRaid.exe  — папка для запуска
#   build\windows\goldraid-1.3.0-windows.zip  — архив для раздачи
#
# Скрипт сам создаёт виртуальное окружение и ставит зависимости, если их нет.

param(
    [string]$Version = "1.3.0",
    # Не создавать .venv, а использовать python из PATH
    # (нужно на CI, где зависимости уже установлены setup-python).
    [switch]$NoVenv
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$Root = $PSScriptRoot
$OutDir = Join-Path $Root "build\windows"
$WorkDir = Join-Path $OutDir "work"
$DistDir = Join-Path $OutDir "dist"
$Hook = Join-Path $Root "windows\pyi_rth_fix_site.py"
$ZipPath = Join-Path $OutDir "goldraid-$Version-windows.zip"

Write-Host "== Золотой рейд: сборка Windows ==" -ForegroundColor Yellow

# --- 1. Виртуальное окружение -------------------------------------------
if ($NoVenv) {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $cmd) {
        Write-Host "python не найден в PATH" -ForegroundColor Red
        exit 1
    }
    $Python = $cmd.Source
} else {
    $Python = Join-Path $Root ".venv\Scripts\python.exe"
    if (-not (Test-Path $Python)) {
        Write-Host "Создаю .venv..." -ForegroundColor Gray
        $base = Get-Command py -ErrorAction SilentlyContinue
        if ($base) {
            & py -3 -m venv "$Root\.venv"
        } else {
            & python -m venv "$Root\.venv"
        }
    }
}

# В окружениях, собранных uv, pip может отсутствовать — восстанавливаем.
& $Python -m pip --version *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Восстанавливаю pip..." -ForegroundColor Gray
    & $Python -m ensurepip --upgrade | Out-Null
}
Write-Host ("Interpreter: {0}" -f $Python) -ForegroundColor Gray

# --- 2. Зависимости ------------------------------------------------------
Write-Host "Проверяю зависимости..." -ForegroundColor Gray
& $Python -m pip install --quiet --upgrade -r requirements.txt
& $Python -m pip install --quiet --upgrade pyinstaller

# --- 3. Сборка -----------------------------------------------------------
Write-Host "Собираю приложение (2-3 минуты)..." -ForegroundColor Yellow
& $Python -m PyInstaller --noconfirm --clean --windowed --onedir --name GoldRaid `
    --distpath "$DistDir" --workpath "$WorkDir" --specpath "$OutDir" `
    --collect-all kivy_deps `
    --add-data "$Root\game\assets;game\assets" `
    --runtime-hook "$Hook" `
    --icon "$Root\icon.png" `
    --paths "$Root" `
    "$Root\main.py"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Сборка завершилась с ошибкой. Лог — выше." -ForegroundColor Red
    exit $LASTEXITCODE
}

# --- 4. Архив ------------------------------------------------------------
$AppDir = Join-Path $DistDir "GoldRaid"
if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
Write-Host "Упаковываю архив..." -ForegroundColor Gray
Compress-Archive -Path "$AppDir\*" -DestinationPath $ZipPath -CompressionLevel Optimal

$exe = Get-Item (Join-Path $AppDir "GoldRaid.exe")
$zip = Get-Item $ZipPath

Write-Host ""
Write-Host "Готово." -ForegroundColor Green
Write-Host ("  Папка:  {0}" -f $AppDir)
Write-Host ("  EXE:    {0:N1} МБ" -f ($exe.Length / 1MB))
Write-Host ("  Архив:  {0} ({1:N1} МБ)" -f $zip.FullName, ($zip.Length / 1MB))
Write-Host ""
Write-Host "Запуск: откройте папку dist\GoldRaid и дважды щёлкните GoldRaid.exe." -ForegroundColor Gray
