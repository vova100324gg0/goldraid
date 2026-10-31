"""Шрифт интерфейса.

Russo One — бесплатный шрифт с кириллицей (SIL Open Font License).
Он заметно «игровее» стандартного Roboto, поэтому используем его для
кнопок и заголовков. Если файл шрифта не попал в сборку, спокойно
откатываемся на Roboto: игра не должна падать из-за оформления.
"""

from __future__ import annotations

from pathlib import Path

from kivy.core.text import LabelBase

DISPLAY_FONT_NAME = "GoldRaidDisplay"
_FALLBACK = "Roboto"
_FONT_PATH = (
    Path(__file__).resolve().parent.parent
    / "assets"
    / "fonts"
    / "RussoOne-Regular.ttf"
)


def _register() -> str:
    try:
        if _FONT_PATH.exists():
            LabelBase.register(
                name=DISPLAY_FONT_NAME, fn_regular=str(_FONT_PATH)
            )
            return DISPLAY_FONT_NAME
    except Exception:
        pass
    return _FALLBACK


#: Имя шрифта, которое можно передавать в ``font_name`` виджетов.
DISPLAY_FONT = _register()

__all__ = ["DISPLAY_FONT", "DISPLAY_FONT_NAME"]