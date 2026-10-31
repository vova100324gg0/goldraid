"""Сохранение прогресса: открытые карты и лучшие результаты."""

from __future__ import annotations

import json
import os
from pathlib import Path

from ..world.levels import LEVELS


def _storage_path() -> Path:
    override = os.environ.get("GOLDRAID_PROGRESS")
    if override:
        return Path(override)
    android = os.environ.get("ANDROID_PRIVATE")
    if android:
        # В APK нет APPDATA/XDG: пишем в приватную папку приложения.
        return Path(android) / "progress.json"
    base = os.environ.get("APPDATA") or os.environ.get("XDG_DATA_HOME")
    if not base:
        base = os.path.join(os.path.expanduser("~"), ".local", "share")
    return Path(base) / "GoldRaid" / "progress.json"


class Progress:
    """Открытые уровни, звёзды и лучшая волна по каждой карте."""

    def __init__(self, path: Path | None = None):
        self.path = path or _storage_path()
        self.unlocked = 1
        self.best: dict[str, dict] = {}
        self.tutorial_done = False
        self.music = True
        self.load()

    # ------------------------------------------------------------------
    def load(self) -> None:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return
        if not isinstance(raw, dict):
            return
        try:
            self.unlocked = max(1, min(len(LEVELS), int(raw.get("unlocked", 1))))
        except (TypeError, ValueError):
            self.unlocked = 1
        best = raw.get("best")
        if isinstance(best, dict):
            self.best = {
                str(key): value
                for key, value in best.items()
                if isinstance(value, dict)
            }
        self.tutorial_done = bool(raw.get("tutorial_done", False))
        self.music = bool(raw.get("music", True))

    def save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "unlocked": self.unlocked,
                "best": self.best,
                "tutorial_done": self.tutorial_done,
                "music": self.music,
            }
            self.path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            # Прогресс не критичен для игры: молча живём без сохранения.
            pass

    def mark_tutorial_done(self) -> None:
        if not self.tutorial_done:
            self.tutorial_done = True
            self.save()

    def set_music(self, enabled: bool) -> None:
        enabled = bool(enabled)
        if enabled != self.music:
            self.music = enabled
            self.save()

    # ------------------------------------------------------------------
    def is_unlocked(self, index: int) -> bool:
        return index < self.unlocked

    def stars(self, level_id: str) -> int:
        return int(self.best.get(level_id, {}).get("stars", 0))

    def best_wave(self, level_id: str) -> int:
        return int(self.best.get(level_id, {}).get("wave", 0))

    def record(
        self,
        index: int,
        level_id: str,
        win: bool,
        waves_cleared: int,
        base_ratio: float,
        total_waves: int,
    ) -> tuple[int, bool]:
        """Записывает результат. Возвращает (звёзды, открыт ли новый уровень)."""
        stars = 0
        if win:
            stars = 1
            if base_ratio >= 0.5:
                stars += 1
            if base_ratio >= 0.85:
                stars += 1
        entry = self.best.get(level_id, {})
        entry["stars"] = max(int(entry.get("stars", 0)), stars)
        entry["wave"] = max(int(entry.get("wave", 0)), min(waves_cleared, total_waves))
        entry["win"] = bool(entry.get("win", False)) or win
        self.best[level_id] = entry

        newly_unlocked = False
        if win and index + 1 >= self.unlocked and index + 2 <= len(LEVELS):
            self.unlocked = index + 2
            newly_unlocked = True
        self.save()
        return stars, newly_unlocked


PROGRESS = Progress()
