"""Портреты героев для сюжетных катсцен.

PNG-файлы лежат в ``game/assets/portraits`` и уже обрезаны по круглому
медальону с прозрачным фоном. Здесь — поиск папки (в исходниках и в
собранном приложении) и кэш текстур, чтобы не перечитывать файлы на
каждой реплике.
"""

from __future__ import annotations

import sys
from pathlib import Path

from kivy.core.image import Image as CoreImage

#: Ключи, для которых есть готовый портрет.
PORTRAIT_KEYS = frozenset({"hero", "elder", "scout", "chief", "warlord"})

_TEXTURES: dict[str, object | None] = {}
_IMAGES: dict[str, object] = {}


def portraits_dir() -> Path:
    """Ищет папку с портретами и в исходниках, и в собранном приложении."""
    here = Path(__file__).resolve().parent.parent / "assets" / "portraits"
    candidates = [here]
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass) / "game" / "assets" / "portraits")
    candidates.append(Path.cwd() / "game" / "assets" / "portraits")
    for path in candidates:
        if path.is_dir():
            return path
    return here


def portrait_texture(key: str | None):
    """Текстура портрета по ключу говорящего или ``None``.

    ``None`` возвращается и тогда, когда картинки нет: вызывающий код
    спокойно откатывается на нарисованный силуэт.
    """
    if not key or key not in PORTRAIT_KEYS:
        return None
    if key in _TEXTURES:
        return _TEXTURES[key]
    texture = None
    path = portraits_dir() / f"{key}.png"
    if path.exists():
        try:
            image = CoreImage(str(path))
            texture = image.texture
            _IMAGES[key] = image
        except Exception:
            texture = None
    _TEXTURES[key] = texture
    return texture


__all__ = ["PORTRAIT_KEYS", "portraits_dir", "portrait_texture"]