"""Примитивы рисования поверх kivy.graphics."""

from __future__ import annotations

import math

from kivy.graphics import (
    Color,
    Ellipse,
    Line,
    Mesh,
    Rectangle,
    RoundedRectangle,
)
from kivy.metrics import dp


def ellipse(group, x: float, y: float, w: float, h: float, color) -> None:
    group.add(Color(*color))
    group.add(Ellipse(pos=(x - w / 2, y - h / 2), size=(w, h)))


def circle(group, x: float, y: float, r: float, color) -> None:
    ellipse(group, x, y, r * 2, r * 2, color)


def rect(group, x: float, y: float, w: float, h: float, color) -> None:
    group.add(Color(*color))
    group.add(Rectangle(pos=(x, y), size=(w, h)))


def rounds(group, x: float, y: float, w: float, h: float, r: float, color) -> None:
    group.add(Color(*color))
    group.add(
        RoundedRectangle(pos=(x, y), size=(w, h), radius=[dp(r)])
    )


def poly(group, points, color) -> None:
    """Закрашенный выпуклый многоугольник."""
    if len(points) < 3:
        return
    vertices = []
    for x, y in points:
        vertices.extend((x, y, 0.0, 0.0))
    indices = list(range(len(points)))
    group.add(Color(*color))
    group.add(Mesh(vertices=vertices, indices=indices, mode="triangle_fan"))


def line(group, points, color, width: float = 2.0, close: bool = False) -> None:
    group.add(Color(*color))
    group.add(Line(points=points, width=dp(width), close=close))


def ring(group, x: float, y: float, r: float, color, width: float = 2.0) -> None:
    group.add(Color(*color))
    group.add(Line(circle=(x, y, r), width=dp(width)))


def rounded_outline(
    group, x: float, y: float, w: float, h: float, r: float, color, width: float = 2.0
) -> None:
    group.add(Color(*color))
    group.add(
        Line(
            rounded_rectangle=(x, y, w, h, dp(r)),
            width=dp(width),
        )
    )


def star_points(
    cx: float,
    cy: float,
    r_outer: float,
    r_inner: float | None = None,
    points: int = 5,
    rotation: float = -math.pi / 2,
) -> list[tuple[float, float]]:
    """Вершины звезды по кругу (без Unicode-глифов)."""
    if r_inner is None:
        r_inner = r_outer * 0.45
    result = []
    step = math.pi / max(1, points)
    for i in range(points * 2):
        radius = r_outer if i % 2 == 0 else r_inner
        angle = rotation + i * step
        result.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))
    return result


def star(group, cx: float, cy: float, r: float, color, inner: float | None = None) -> None:
    """Закрашенная звезда: веер треугольников из центра."""
    pts = star_points(cx, cy, r, inner)
    vertices = [cx, cy, 0.0, 0.0]
    for x, y in pts:
        vertices.extend((x, y, 0.0, 0.0))
    vertices.extend((pts[0][0], pts[0][1], 0.0, 0.0))
    group.add(Color(*color))
    group.add(
        Mesh(
            vertices=vertices,
            indices=list(range(len(pts) + 2)),
            mode="triangle_fan",
        )
    )
