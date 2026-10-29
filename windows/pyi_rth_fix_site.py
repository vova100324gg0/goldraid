"""Runtime-хук PyInstaller для «Золотого рейда».

В собранном приложении `site.USER_BASE` равен None, из-за чего пакеты
`kivy_deps` падают на `os.path.join(None, 'share', ...)` ещё до старта игры.
Подставляем пустую строку — путь вида `share\\sdl2\\bin` просто не найдётся,
а DLL всё равно лежат рядом с исполняемым файлом и подхватываются загрузчиком.
"""

import site

if getattr(site, "USER_BASE", None) is None:
    site.USER_BASE = ""
