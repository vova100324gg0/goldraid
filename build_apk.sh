#!/usr/bin/env bash
# Сборка APK «Золотой рейд» на Linux или в WSL2.
# Запуск:  bash build_apk.sh
# Результат: bin/goldraid-1.0.0-*-debug.apk и копия в apk/

set -euo pipefail

cd "$(dirname "$0")"

echo "== Золотой рейд: сборка APK =="

# 1. Проверяем Python и Java.
command -v python3 >/dev/null || { echo "Нет python3. Установите: sudo apt install python3 python3-pip"; exit 1; }
command -v java >/dev/null || { echo "Нет Java. Установите: sudo apt install openjdk-17-jdk"; exit 1; }

# 2. Ставим buildozer и системные зависимости (нужен sudo).
if ! command -v buildozer >/dev/null; then
  echo "-- Устанавливаю buildozer --"
  python3 -m pip install --user buildozer cython
  export PATH="$HOME/.local/bin:$PATH"
fi

if ! dpkg -s zlib1g-dev >/dev/null 2>&1; then
  echo "-- Ставлю зависимости сборки Android (потребуется пароль sudo) --"
  sudo apt-get update
  sudo apt-get install -y git zip unzip openjdk-17-jdk python3-pip \
    autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev \
    libtinfo5 cmake libffi-dev libssl-dev
fi

# 3. Чистим прошлые артефакты, чтобы не получить старый APK.
rm -rf bin

# 4. Собираем. Первый запуск скачивает SDK/NDK и занимает 20-40 минут.
echo "-- buildozer android debug --"
buildozer -v android debug

# 5. Кладём готовый файл в apk/ рядом с проектом.
mkdir -p apk
cp -v bin/*.apk apk/
echo
echo "Готово:"
ls -lh apk/*.apk