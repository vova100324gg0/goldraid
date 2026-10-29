# Сборка APK «Золотой рейд» из Windows.
# Запуск:  powershell -ExecutionPolicy Bypass -File build_apk.ps1
#
# Скрипт сам ничего не устанавливает: он проверяет WSL и запускает
# build_apk.sh внутри Linux. Если WSL нет — показывает варианты.

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "== Золотой рейд: сборка APK ==" -ForegroundColor Yellow

function Show-Options {
    Write-Host ""
    Write-Host "Локальная сборка недоступна: в Windows нет Linux-окружения." -ForegroundColor Red
    Write-Host "Buildozer работает только на Linux (или в WSL2)." -ForegroundColor Red
    Write-Host ""
    Write-Host "Вариант 1 (проще): GitHub Actions" -ForegroundColor Green
    Write-Host "  1. Загрузите проект в репозиторий GitHub (нужен аккаунт)."
    Write-Host "  2. Откройте вкладку Actions -> «Сборка APK» -> Run workflow."
    Write-Host "  3. Через ~30 минут скачайте артефакт goldraid-apk."
    Write-Host "  Файл .github/workflows/build-apk.yml уже готов."
    Write-Host ""
    Write-Host "Вариант 2: WSL2 на этом компьютере" -ForegroundColor Green
    Write-Host "  1. Откройте PowerShell от имени администратора."
    Write-Host "  2. Выполните: wsl --install -d Ubuntu"
    Write-Host "  3. Перезагрузите ПК и создайте пользователя Ubuntu."
    Write-Host "  4. Снова запустите этот скрипт."
    Write-Host "  Нужно ~10-15 ГБ на диске F: (или C:)."
    Write-Host ""
    Write-Host "Вариант 3: любая Linux-машина" -ForegroundColor Green
    Write-Host "  Скопируйте папку проекта и выполните: bash build_apk.sh"
    Write-Host ""
}

# Есть ли wsl.exe и хотя бы один дистрибутив?
$wsl = Get-Command wsl.exe -ErrorAction SilentlyContinue
if (-not $wsl) {
    Show-Options
    exit 1
}

$distros = (& wsl.exe -l -q 2>$null) -split "`r?`n" | Where-Object { $_.Trim() -ne "" }
if ($LASTEXITCODE -ne 0 -or -not $distros) {
    Show-Options
    exit 1
}

$distro = $distros[0].Trim()
Write-Host "Найден WSL-дистрибутив: $distro" -ForegroundColor Green

# Переводим путь Windows в путь WSL.
$linuxPath = (& wsl.exe -d $distro wslpath -a "$PWD" 2>$null).Trim()
if (-not $linuxPath) {
    Write-Host "Не удалось определить путь внутри WSL." -ForegroundColor Red
    exit 1
}

Write-Host "Папка проекта в Linux: $linuxPath" -ForegroundColor Gray
Write-Host "Запускаю build_apk.sh (первый раз — 20-40 минут)..." -ForegroundColor Yellow

& wsl.exe -d $distro bash -lc "cd '$linuxPath' && sed -i 's/\r$//' build_apk.sh 2>/dev/null; bash build_apk.sh"
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Сборка завершилась с ошибкой. Полный лог — выше." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Готово. APK лежит в папке apk:" -ForegroundColor Green
Get-ChildItem apk\*.apk | Select-Object Name, @{n = "МБ"; e = { [math]::Round($_.Length / 1MB, 1) } }