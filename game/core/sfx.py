"""Звуковые эффекты: короткие сигналы на события боя и интерфейса.

Звуки сгенерированы нами (tools/make_sfx.py), поэтому у них нет чужих
авторских прав. Все обращения к звуку обёрнуты в try/except: если на
устройстве нет аудио или файлы потерялись, игра просто играет без эффектов.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# Короткие эффекты: имя события -> файл и желаемая громкость.
_FILES = {
    "click": "sfx_click.wav",
    "build": "sfx_build.wav",
    "shoot": "sfx_shoot.wav",
    "hit": "sfx_hit.wav",
    "coin": "sfx_coin.wav",
    "wave": "sfx_wave.wav",
    "win": "sfx_win.wav",
    "lose": "sfx_lose.wav",
}

_GAIN = {
    "click": 0.55,
    "build": 0.75,
    "shoot": 0.30,
    "hit": 0.70,
    "coin": 0.55,
    "wave": 0.70,
    "win": 0.85,
    "lose": 0.85,
}

# Минимальная пауза между повторами одного эффекта, чтобы частые события
# (выстрелы башен, удары по базе) не превращались в «пулемёт».
_COOLDOWN = {
    "shoot": 0.07,
    "hit": 0.12,
    "coin": 0.05,
    "click": 0.04,
}


def sfx_dir() -> Path:
    """Ищет папку со звуками и в исходниках, и в собранном приложении."""
    here = Path(__file__).resolve().parent.parent / "assets" / "sfx"
    candidates = [here]
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass) / "game" / "assets" / "sfx")
    candidates.append(Path.cwd() / "game" / "assets" / "sfx")
    for path in candidates:
        if path.is_dir():
            return path
    return here


class SfxPlayer:
    """Простой проигрыватель коротких эффектов с ленивой загрузкой."""

    def __init__(self, volume: float = 0.55):
        self.volume = float(volume)
        self.enabled = True
        self._cache: dict[str, object | None] = {}
        self._last: dict[str, float] = {}
        # В тестах и на сборке без звуковой карты эффекты лучше не трогать.
        self._muted_env = bool(os.environ.get("GOLDRAID_NO_AUDIO"))

    # ------------------------------------------------------------------
    def apply_settings(self, enabled: bool) -> None:
        """Применяет пользовательскую настройку «звуки вкл/выкл»."""
        self.set_enabled(enabled)

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = bool(enabled) and not self._muted_env

    def toggle(self) -> bool:
        self.set_enabled(not self.enabled)
        return self.enabled

    # ------------------------------------------------------------------
    def _load(self, name: str):
        if name in self._cache:
            return self._cache[name]
        sound = None
        if not self._muted_env:
            filename = _FILES.get(name)
            if filename:
                path = sfx_dir() / filename
                if path.exists():
                    try:
                        from kivy.core.audio import SoundLoader

                        sound = SoundLoader.load(str(path))
                    except Exception:
                        sound = None
        self._cache[name] = sound
        return sound

    def play(self, name: str) -> None:
        """Проигрывает эффект ``name``. Повторный вызов перезапускает звук."""
        if not self.enabled:
            return
        now = time.monotonic()
        cooldown = _COOLDOWN.get(name, 0.0)
        if cooldown and now - self._last.get(name, -99.0) < cooldown:
            return
        sound = self._load(name)
        if sound is None:
            return
        self._last[name] = now
        try:
            sound.loop = False
            sound.volume = max(0.0, min(1.0, self.volume * _GAIN.get(name, 1.0)))
            sound.play()
        except Exception:
            return


# Единственный общий проигрыватель эффектов на всю игру.
sfx = SfxPlayer()


__all__ = ["sfx", "SfxPlayer", "sfx_dir"]
