[app]

# Название на экране Android.
title = Золотой рейд

# Идентификатор приложения: org.goldraid.goldraid
package.name = goldraid
package.domain = org.goldraid

# Версия видна в настройках Android.
version = 1.4.0

# Что попадает в APK.
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,json,txt,wav
source.include_patterns = game/*.py,game/*/*.py,game/assets/music/*.wav,game/assets/sfx/*.wav,main.py,icon.png,presplash.png
source.exclude_dirs = .venv,.git,.github,.buildozer,bin,apk,build,__pycache__,Сборка,.idea,.vscode
source.exclude_patterns = *.pyc,*.pyo,*.apk,*.aab,*.spec.bak,README.md,СБОРКА APK.txt

# Зависимости Python. Версии закреплены, чтобы сборка была повторяемой.
requirements = python3,kivy==2.3.1,pillow

# Игра вертикальная.
orientation = portrait
fullscreen = 0

# Иконка приложения (512x512 PNG).
icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/presplash.png

# Android: API 33, минимальная версия 21 (Android 5.0).
# NDK 28c — рекомендованная p4a/Buildozer версия; в ней каталог clang
# лежит в lib/clang (а не lib64/clang), как ожидает рецепт libthorvg.
android.api = 33
android.minapi = 21
android.ndk = 28c
android.archs = arm64-v8a,armeabi-v7a
android.accept_sdk_license = True
android.allow_backup = True
android.release_artifact = apk

# SDL2 — стандартный бэкенд Kivy.
p4a.bootstrap = sdl2

# Фикс p4a: очистка build-venv и отказ от self-upgrade pip
# (иначе сборка падает с ImportError: BuildDependencyInstallError).
p4a.branch = develop
p4a.commit = 0382d27de2f7315ed98e74884bafb30365decdee

[buildozer]
log_level = 2
warn_on_root = 1