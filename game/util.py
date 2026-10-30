"""Небольшие математические помощники."""

from __future__ import annotations

import math
import os
import webbrowser


def clamp(value: float, low: float, high: float) -> float:
    return low if value < low else high if value > high else value


def dist(ax: float, ay: float, bx: float, by: float) -> float:
    return math.hypot(bx - ax, by - ay)


def dist2(ax: float, ay: float, bx: float, by: float) -> float:
    dx = bx - ax
    dy = by - ay
    return dx * dx + dy * dy


def normalize(x: float, y: float) -> tuple[float, float]:
    length = math.hypot(x, y)
    if length < 1e-9:
        return 0.0, 0.0
    return x / length, y / length


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def approach(current: float, target: float, speed: float, dt: float) -> float:
    delta = target - current
    step = speed * dt
    if abs(delta) <= step:
        return target
    return current + math.copysign(step, delta)


def point_segment_distance(
    px: float, py: float, ax: float, ay: float, bx: float, by: float
) -> float:
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return dist(px, py, ax, ay)
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = clamp(t, 0.0, 1.0)
    return dist(px, py, ax + t * dx, ay + t * dy)


def _open_android(url: str) -> bool:
    """Открывает ссылку через Intent на Android (без падения на ПК)."""
    try:
        from jnius import autoclass  # type: ignore[import-not-found]

        intent_cls = autoclass("android.content.Intent")
        uri_cls = autoclass("android.net.Uri")
        try:
            from android import mActivity  # type: ignore[import-not-found]

            activity = mActivity
        except Exception:
            activity = autoclass("org.kivy.android.PythonActivity").mActivity
        intent = intent_cls(intent_cls.ACTION_VIEW, uri_cls.parse(url))
        intent.addFlags(intent_cls.FLAG_ACTIVITY_NEW_TASK)
        activity.startActivity(intent)
        return True
    except Exception:
        return False


def open_url(url: str) -> str:
    """Открывает ссылку. Возвращает: opened / copied / failed.

    Порядок: Android-Intent → системный браузер → буфер обмена.
    """
    android = "ANDROID_ARGUMENT" in os.environ or "ANDROID_PRIVATE" in os.environ
    if android and _open_android(url):
        return "opened"
    try:
        if webbrowser.open(url):
            return "opened"
    except Exception:
        pass
    try:
        from kivy.core.clipboard import Clipboard

        Clipboard.copy(url)
        return "copied"
    except Exception:
        return "failed"
