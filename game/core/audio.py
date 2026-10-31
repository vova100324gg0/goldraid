"""Фоновая музыка: тема на каждую локацию, зациклено и с мягким откатом.

Музыка сгенерирована нами (tools/make_music.py), поэтому она свободна от
чужих авторских прав. Все обращения к звуку обёрнуты в try/except: если на
устройстве нет аудио или файл потерялся, игра просто играет без музыки.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from .i18n import t

# Тема локации. Одна мелодия может обслуживать несколько похожих карт.
THEME_BY_LEVEL = {
    "tutorial": "green",
    "valley": "green",
    "forest": "green",
    "pass": "stone",
    "ash": "ash",
    "frost": "frost",
    "crater": "ember",
    "ruins": "stone",
    "citadel": "ember",
}

MENU_THEME = "menu"

_FILES = {
    "menu": "theme_menu.wav",
    "green": "theme_green.wav",
    "stone": "theme_stone.wav",
    "ash": "theme_ash.wav",
    "frost": "theme_frost.wav",
    "ember": "theme_ember.wav",
}

_TITLES = {
    "menu": "Главное меню",
    "green": "Зелёные земли",
    "stone": "Каменный перевал",
    "ash": "Пепельная пустошь",
    "frost": "Студёная теснина",
    "ember": "Пылающий кратер",
}


def music_dir() -> Path:
    """Ищет папку с музыкой и в исходниках, и в собранном приложении."""
    here = Path(__file__).resolve().parent.parent / "assets" / "music"
    candidates = [here]
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass) / "game" / "assets" / "music")
    candidates.append(Path.cwd() / "game" / "assets" / "music")
    for path in candidates:
        if path.is_dir():
            return path
    return here


def theme_title(theme: str) -> str:
    return t(_TITLES.get(theme, theme))


class MusicPlayer:
    """Простейший проигрыватель зацикленной музыки с ленивой загрузкой."""

    def __init__(self, volume: float = 0.34):
        self.volume = float(volume)
        self.enabled = True
        self._sound = None
        self._current: str | None = None
        self._desired: str | None = None
        self._cache: dict[str, object | None] = {}
        # В тестах и на сборке без звуковой карты музыку лучше не трогать.
        self._muted_env = bool(os.environ.get("GOLDRAID_NO_AUDIO"))

    # ------------------------------------------------------------------
    def apply_settings(self, enabled: bool) -> None:
        """Применяет пользовательскую настройку «музыка вкл/выкл»."""
        self.set_enabled(enabled)

    def set_enabled(self, enabled: bool) -> None:
        enabled = bool(enabled) and not self._muted_env
        if enabled == self.enabled:
            if enabled and self._desired is not None and self._sound is None:
                self.play(self._desired)
            return
        self.enabled = enabled
        if not enabled:
            # Запоминаем текущую тему, чтобы вернуть её при повторном включении.
            self.stop(keep_desired=True)
        elif self._desired is not None:
            self.play(self._desired)

    def toggle(self) -> bool:
        self.set_enabled(not self.enabled)
        return self.enabled

    # ------------------------------------------------------------------
    def _load(self, theme: str):
        if theme in self._cache:
            return self._cache[theme]
        sound = None
        if not self._muted_env:
            name = _FILES.get(theme)
            if name:
                path = music_dir() / name
                if path.exists():
                    try:
                        from kivy.core.audio import SoundLoader

                        sound = SoundLoader.load(str(path))
                    except Exception:
                        sound = None
        self._cache[theme] = sound
        return sound

    def play(self, theme: str | None) -> None:
        """Включает тему ``theme``. Повторный вызов для той же темы ничего не делает."""
        if theme is None:
            return
        self._desired = theme
        if not self.enabled:
            return
        if self._current == theme and self._sound is not None:
            try:
                if self._sound.state == "play":
                    return
            except Exception:
                pass
        self.stop(keep_desired=True)
        sound = self._load(theme)
        if sound is None:
            return
        try:
            sound.loop = True
            sound.volume = self.volume
            sound.play()
        except Exception:
            return
        self._sound = sound
        self._current = theme

    def stop(self, keep_desired: bool = False) -> None:
        sound = self._sound
        self._sound = None
        self._current = None
        if not keep_desired:
            self._desired = None
        if sound is not None:
            try:
                sound.stop()
            except Exception:
                pass


# Единственный общий проигрыватель на всю игру.
music = MusicPlayer()


__all__ = ["music", "MusicPlayer", "THEME_BY_LEVEL", "MENU_THEME", "theme_title"]
