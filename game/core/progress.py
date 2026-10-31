"""Сохранение прогресса: карты, настройки, достижения и счётчики."""

from __future__ import annotations

import json
import os
from datetime import date, timedelta
from pathlib import Path

from ..world.levels import LEVELS

# Версия формата сохранения. При изменении структуры старые файлы
# дочитываются значениями по умолчанию, а не теряются.
SAVE_VERSION = 4

DEFAULT_COUNTERS = {
    "runs": 0,
    "wins": 0,
    "bosses": 0,
    "buildings": 0,
    "gold": 0,
    "waves": 0,
    "kills": 0,
    "daily_wins": 0,
}


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
    """Открытые уровни, настройки, достижения и лучшие результаты."""

    def __init__(self, path: Path | None = None):
        self.path = path or _storage_path()
        self.version = SAVE_VERSION
        self.unlocked = 1
        self.best: dict[str, dict] = {}
        self.tutorial_done = False
        self.music = True
        self.language = "ru"
        self.quality = "auto"
        self.sfx = True
        self.achievements: dict[str, bool] = {}
        self.seen_version = ""
        self.counters = dict(DEFAULT_COUNTERS)
        # Рекорды режимов: бесконечный и ежедневная карта.
        self.endless_best = 0
        self.daily: dict = {
            "date": "",
            "best": 0,
            "done": False,
            "win": False,
            "streak": 0,
        }
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
        self.language = str(raw.get("language", "ru"))
        if self.language not in ("ru", "en"):
            self.language = "ru"
        self.quality = str(raw.get("quality", "auto"))
        if self.quality not in ("auto", "high", "low"):
            self.quality = "auto"
        self.sfx = bool(raw.get("sfx", True))
        achievements = raw.get("achievements")
        if isinstance(achievements, dict):
            self.achievements = {
                str(key): bool(value) for key, value in achievements.items()
            }
        self.seen_version = str(raw.get("seen_version", ""))
        counters = raw.get("counters")
        if isinstance(counters, dict):
            for key, value in DEFAULT_COUNTERS.items():
                try:
                    self.counters[key] = max(0, int(counters.get(key, value)))
                except (TypeError, ValueError):
                    self.counters[key] = value
        try:
            self.endless_best = max(0, int(raw.get("endless_best", 0)))
        except (TypeError, ValueError):
            self.endless_best = 0
        daily = raw.get("daily")
        if isinstance(daily, dict):
            try:
                best = max(0, int(daily.get("best", 0)))
            except (TypeError, ValueError):
                best = 0
            self.daily = {
                "date": str(daily.get("date", "")),
                "best": best,
                "done": bool(daily.get("done", False)),
                "win": bool(daily.get("win", False)),
                "streak": max(0, int(daily.get("streak", 0))),
            }
        # Карты, добавленные в обновлении, открываются тем, кто уже прошёл
        # предыдущую: переигрывать старую карту не нужно.
        won = [
            index
            for index, level in enumerate(LEVELS)
            if bool(self.best.get(level.id, {}).get("win", False))
        ]
        if won:
            self.unlocked = max(
                self.unlocked, min(len(LEVELS), max(won) + 2)
            )
        # Старый файл без версии — просто миграция: все поля уже с
        # значениями по умолчанию, а прогресс карт сохранён.
        try:
            self.version = max(SAVE_VERSION, int(raw.get("version", 1)))
        except (TypeError, ValueError):
            self.version = SAVE_VERSION

    def save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "version": SAVE_VERSION,
                "unlocked": self.unlocked,
                "best": self.best,
                "tutorial_done": self.tutorial_done,
                "music": self.music,
                "language": self.language,
                "quality": self.quality,
                "sfx": self.sfx,
                "achievements": self.achievements,
                "seen_version": self.seen_version,
                "counters": dict(self.counters),
                "endless_best": self.endless_best,
                "daily": dict(self.daily),
            }
            self.path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            # Прогресс не критичен для игры: молча живём без сохранения.
            pass

    # ------------------------------------------------------------------
    def mark_tutorial_done(self) -> None:
        if not self.tutorial_done:
            self.tutorial_done = True
            self.save()

    def set_music(self, enabled: bool) -> None:
        enabled = bool(enabled)
        if enabled != self.music:
            self.music = enabled
            self.save()

    def set_language(self, code: str) -> str:
        code = code if code in ("ru", "en") else "ru"
        if code != self.language:
            self.language = code
            self.save()
        return self.language

    def set_quality(self, mode: str) -> str:
        mode = mode if mode in ("auto", "high", "low") else "auto"
        if mode != self.quality:
            self.quality = mode
            self.save()
        return self.quality

    def set_sfx(self, enabled: bool) -> None:
        enabled = bool(enabled)
        if enabled != self.sfx:
            self.sfx = enabled
            self.save()

    # ------------------------------------------------------------------
    # Режимы: бесконечный и ежедневная карта
    # ------------------------------------------------------------------
    @staticmethod
    def today() -> str:
        return date.today().isoformat()

    def daily_seed(self) -> int:
        """Сид ежедневной карты: один и тот же для всех в этот день."""
        return int(self.today().replace("-", ""))

    def record_endless(self, waves: int) -> bool:
        """Обновляет рекорд бесконечного режима. True — если рекорд побит."""
        waves = max(0, int(waves))
        if waves <= self.endless_best:
            return False
        self.endless_best = waves
        self.save()
        return True

    def daily_of_today(self) -> dict:
        """Результат ежедневной карты за сегодня; сбрасывается на новый день."""
        today = self.today()
        if self.daily.get("date") != today:
            yesterday = (date.today() - timedelta(days=1)).isoformat()
            streak = int(self.daily.get("streak", 0))
            if bool(self.daily.get("win", False)) and self.daily.get("date") == yesterday:
                streak += 1
            else:
                streak = 0
            self.daily = {
                "date": today,
                "best": 0,
                "done": False,
                "win": False,
                "streak": streak,
            }
            self.save()
        return self.daily

    def daily_done(self) -> bool:
        return bool(self.daily_of_today().get("done", False))

    def record_daily(self, waves: int, win: bool) -> None:
        entry = self.daily_of_today()
        was_win = bool(entry.get("win", False))
        entry["best"] = max(int(entry.get("best", 0)), max(0, int(waves)))
        entry["done"] = True
        entry["win"] = was_win or bool(win)
        if win and not was_win:
            self.counters["daily_wins"] = (
                int(self.counters.get("daily_wins", 0)) + 1
            )
        self.daily = entry
        self.save()

    def mark_seen(self, version: str) -> None:
        if version and self.seen_version != version:
            self.seen_version = version
            self.save()

    # ------------------------------------------------------------------
    def is_unlocked(self, index: int) -> bool:
        return index < self.unlocked

    def stars(self, level_id: str) -> int:
        return int(self.best.get(level_id, {}).get("stars", 0))

    def best_wave(self, level_id: str) -> int:
        return int(self.best.get(level_id, {}).get("wave", 0))

    def has_achievement(self, key: str) -> bool:
        return bool(self.achievements.get(key, False))

    def unlock_achievement(self, key: str) -> bool:
        """Открывает достижение. Возвращает True, если оно новое."""
        if self.achievements.get(key):
            return False
        self.achievements[key] = True
        self.save()
        return True

    def add_run(self, run: dict) -> None:
        """Учитывает завершённый бой в общих счётчиках."""
        self.counters["runs"] += 1
        if run.get("win"):
            self.counters["wins"] += 1
        self.counters["bosses"] += max(0, int(run.get("bosses_killed", 0)))
        self.counters["buildings"] += max(0, int(run.get("buildings_built", 0)))
        self.counters["gold"] += max(0, int(run.get("gold_earned", 0)))
        self.counters["waves"] += max(0, int(run.get("waves", 0)))
        self.counters["kills"] += max(0, int(run.get("kills", 0)))
        self.save()

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

    # ------------------------------------------------------------------
    def reset(self) -> None:
        """Сбрасывает прогресс, сохраняя язык, музыку, звуки и качество."""
        self.unlocked = 1
        self.best = {}
        self.tutorial_done = False
        self.achievements = {}
        self.seen_version = ""
        self.counters = dict(DEFAULT_COUNTERS)
        self.endless_best = 0
        self.daily = {"date": "", "best": 0, "done": False, "win": False, "streak": 0}
        self.version = SAVE_VERSION
        self.save()


PROGRESS = Progress()