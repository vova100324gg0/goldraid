"""Достижения: условия, проверка и открытие наград."""

from __future__ import annotations

from ..world.levels import LEVELS


def _all_maps(progress) -> bool:
    for level in LEVELS:
        if not bool(progress.best.get(level.id, {}).get("win", False)):
            return False
    return True


def _three_stars(progress) -> bool:
    return any(int(v.get("stars", 0)) >= 3 for v in progress.best.values())


# Порядок важен только для показа в списке.
ACHIEVEMENTS: list[dict] = [
    {
        "id": "tutorial",
        "name": "Первые шаги",
        "desc": "Пройди обучение",
        "check": lambda p, run: p.tutorial_done,
    },
    {
        "id": "first_win",
        "name": "Защитник ворот",
        "desc": "Выиграй первую карту",
        "check": lambda p, run: int(p.counters.get("wins", 0)) >= 1,
    },
    {
        "id": "stars3",
        "name": "Безупречная оборона",
        "desc": "Получи 3 звезды на любой карте",
        "check": lambda p, run: _three_stars(p),
    },
    {
        "id": "boss",
        "name": "Убийца боссов",
        "desc": "Победи босса",
        "check": lambda p, run: int(p.counters.get("bosses", 0)) >= 1,
    },
    {
        "id": "builder",
        "name": "Строитель",
        "desc": "Построй 50 построек за всё время",
        "check": lambda p, run: int(p.counters.get("buildings", 0)) >= 50,
    },
    {
        "id": "gold",
        "name": "Золотая жила",
        "desc": "Добудь 5000 золота за всё время",
        "check": lambda p, run: int(p.counters.get("gold", 0)) >= 5000,
    },
    {
        "id": "waves",
        "name": "Стойкий защитник",
        "desc": "Отбей 100 волн",
        "check": lambda p, run: int(p.counters.get("waves", 0)) >= 100,
    },
    {
        "id": "all_maps",
        "name": "Покоритель карт",
        "desc": "Пройди все карты",
        "check": lambda p, run: _all_maps(p),
    },
    {
        "id": "ruins_win",
        "name": "Пепельный след",
        "desc": "Пройди «Забытые руины»",
        "check": lambda p, run: bool(p.best.get("ruins", {}).get("win", False)),
    },
    {
        "id": "citadel_win",
        "name": "Владыка пепла",
        "desc": "Пройди «Тёмную цитадель»",
        "check": lambda p, run: bool(p.best.get("citadel", {}).get("win", False)),
    },
    {
        "id": "endless_25",
        "name": "Несокрушимый",
        "desc": "Дойди до 25-й волны в бесконечном режиме",
        "check": lambda p, run: int(p.endless_best) >= 25,
    },
    {
        "id": "kills_1000",
        "name": "Истребитель",
        "desc": "Уничтожь 1000 врагов за всё время",
        "check": lambda p, run: int(p.counters.get("kills", 0)) >= 1000,
    },
]


def check_achievements(progress, run: dict | None = None) -> list[dict]:
    """Проверяет все условия и возвращает список новых достижений."""
    run = run or {}
    unlocked: list[dict] = []
    for item in ACHIEVEMENTS:
        if progress.has_achievement(item["id"]):
            continue
        try:
            reached = bool(item["check"](progress, run))
        except Exception:
            reached = False
        if reached and progress.unlock_achievement(item["id"]):
            unlocked.append(item)
    return unlocked


def unlocked_count(progress) -> int:
    return sum(1 for item in ACHIEVEMENTS if progress.has_achievement(item["id"]))


__all__ = ["ACHIEVEMENTS", "check_achievements", "unlocked_count"]