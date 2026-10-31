"""Иконки интерфейса, нарисованные примитивами Kivy.

Свои иконки нужны, чтобы HUD выглядел опрятно и одинаково на телефоне,
где Unicode-глифы могут отсутствовать в системном шрифте.
Все фигуры строятся вокруг точки ``(cx, cy)`` в квадрате ``size``.
"""

from __future__ import annotations

import math

from .gfx import circle, ellipse, line, poly, rect, ring, rounds


def _arc(group, cx, cy, r, a0, a1, color, width=1.4, steps=10) -> None:
    """Дуга окружности из отрезков (для «звуковых волн» динамика)."""
    points = []
    for i in range(steps + 1):
        angle = a0 + (a1 - a0) * i / steps
        points.extend((cx + math.cos(angle) * r, cy + math.sin(angle) * r))
    line(group, points, color, width)


def draw_icon(group, kind: str, cx: float, cy: float, size: float, color) -> None:
    """Рисует иконку ``kind`` размером ``size`` с центром в ``(cx, cy)``."""
    s = size / 2.0
    r, g, b = color[0], color[1], color[2]
    shade = (r * 0.62, g * 0.62, b * 0.62, color[3] if len(color) > 3 else 1)
    light = (min(1.0, r * 1.35 + 0.10), min(1.0, g * 1.35 + 0.10),
             min(1.0, b * 1.35 + 0.10), color[3] if len(color) > 3 else 1)

    if kind == "coin":
        circle(group, cx, cy, s, shade)
        circle(group, cx, cy, s * 0.86, color)
        ring(group, cx, cy, s * 0.62, light, 1.4)
        circle(group, cx - s * 0.20, cy + s * 0.22, s * 0.18, (1, 1, 1, 0.55))
    elif kind == "base":
        rect(group, cx - s, cy - s * 0.9, s * 2, s * 0.9, color)
        for dx in (-0.78, -0.30, 0.30, 0.62):
            rect(group, cx + dx * s - s * 0.16, cy, s * 0.32, s * 0.5, color)
        rect(group, cx - s * 0.30, cy - s * 0.9, s * 0.6, s * 0.66, shade)
        rect(group, cx - s * 0.9, cy - s * 0.9, s * 1.8, s * 0.2, light)
    elif kind == "wave":
        rect(group, cx - s * 0.7, cy - s, s * 0.24, s * 2, shade)
        poly(group, [(cx - s * 0.46, cy + s * 0.9), (cx + s, cy + s * 0.35),
                     (cx - s * 0.46, cy - s * 0.1)], color)
    elif kind == "hero":
        circle(group, cx, cy + s * 0.42, s * 0.40, color)
        poly(group, [(cx - s * 0.72, cy - s * 0.9), (cx + s * 0.72, cy - s * 0.9),
                     (cx + s * 0.5, cy - s * 0.05), (cx - s * 0.5, cy - s * 0.05)], color)
    elif kind == "speed":
        for ox in (-s * 0.55, s * 0.1):
            poly(group, [(cx + ox, cy - s * 0.8), (cx + ox + s * 0.7, cy),
                         (cx + ox, cy + s * 0.8), (cx + ox + s * 0.22, cy)], color)
    elif kind == "shop":
        ring(group, cx, cy + s * 0.55, s * 0.44, shade, 2.0)
        rounds(group, cx - s * 0.82, cy - s * 0.9, s * 1.64, s * 1.5, s * 0.34, color)
        circle(group, cx, cy - s * 0.1, s * 0.16, (1, 1, 1, 0.55))
    elif kind == "pause":
        rounds(group, cx - s * 0.7, cy - s * 0.85, s * 0.5, s * 1.7, s * 0.16, color)
        rounds(group, cx + s * 0.2, cy - s * 0.85, s * 0.5, s * 1.7, s * 0.16, color)
    elif kind == "mine":
        poly(group, [(cx, cy + s), (cx + s * 0.86, cy), (cx, cy - s),
                     (cx - s * 0.86, cy)], color)
        poly(group, [(cx, cy + s), (cx + s * 0.86, cy), (cx, cy)], light)
        poly(group, [(cx, cy - s), (cx - s * 0.86, cy), (cx, cy)], shade)
    elif kind == "tower":
        poly(group, [(cx - s * 0.7, cy - s), (cx + s * 0.7, cy - s),
                     (cx + s * 0.5, cy + s * 0.5), (cx - s * 0.5, cy + s * 0.5)], color)
        for dx in (-0.5, 0.0, 0.5):
            rect(group, cx + dx * s - s * 0.14, cy + s * 0.5, s * 0.28, s * 0.5, color)
        rect(group, cx - s * 0.16, cy - s, s * 0.32, s * 0.6, shade)
    elif kind == "barracks":
        poly(group, [(cx - s, cy), (cx, cy + s), (cx + s, cy)], color)
        rect(group, cx - s * 0.8, cy - s, s * 1.6, s, color)
        rect(group, cx - s * 0.22, cy - s, s * 0.44, s * 0.6, shade)
        rect(group, cx - s * 0.8, cy - s, s * 1.6, s * 0.14, light)
    elif kind == "totem":
        rounds(group, cx - s * 0.42, cy - s, s * 0.84, s * 1.7, s * 0.2, color)
        circle(group, cx - s * 0.18, cy + s * 0.22, s * 0.1, shade)
        circle(group, cx + s * 0.18, cy + s * 0.22, s * 0.1, shade)
        poly(group, [(cx - s * 0.2, cy + s * 0.7), (cx + s * 0.2, cy + s * 0.7),
                     (cx, cy + s)], light)
    elif kind == "upgrade":
        poly(group, [(cx, cy + s * 0.9), (cx + s * 0.8, cy), (cx + s * 0.3, cy),
                     (cx + s * 0.3, cy - s * 0.2), (cx - s * 0.3, cy - s * 0.2),
                     (cx - s * 0.3, cy), (cx - s * 0.8, cy)], color)
    elif kind in ("sound", "mute"):
        # Корпус динамика: прямоугольник + раструб.
        rect(group, cx - s * 0.86, cy - s * 0.34, s * 0.42, s * 0.68, color)
        poly(group, [(cx - s * 0.46, cy - s * 0.34), (cx + s * 0.06, cy - s * 0.86),
                     (cx + s * 0.06, cy + s * 0.86), (cx - s * 0.46, cy + s * 0.34)],
             color)
        if kind == "sound":
            _arc(group, cx - s * 0.05, cy, s * 0.5, -0.9, 0.9, light, 1.5)
            _arc(group, cx - s * 0.05, cy, s * 0.84, -0.9, 0.9, light, 1.5)
        else:
            line(group, [(cx + s * 0.34, cy - s * 0.34), (cx + s * 0.9, cy + s * 0.34)],
                 light, 2.0)
            line(group, [(cx + s * 0.9, cy - s * 0.34), (cx + s * 0.34, cy + s * 0.34)],
                 light, 2.0)


__all__ = ["draw_icon"]
