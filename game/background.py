"""Фон карты: трава, дороги врагов, скалы и растительность."""

from __future__ import annotations

import random

from .config import (
    PATH,
    PATH_EDGE,
    PATH_LIGHT,
    STONE,
    STONE_DARK,
    STONE_LIGHT,
    WOOD,
    WOOD_LIGHT,
)
from .gfx import circle, ellipse, poly, rect
from .util import dist, point_segment_distance


def _samples(paths, step: float = 22.0):
    result = []
    for path in paths:
        for (ax, ay), (bx, by) in zip(path, path[1:]):
            length = dist(ax, ay, bx, by)
            count = max(1, int(length / step))
            for i in range(count + 1):
                t = i / count
                result.append((ax + (bx - ax) * t, ay + (by - ay) * t))
    return result


def _band(group, path, width: float, color) -> None:
    radius = width * 0.5
    for (ax, ay), (bx, by) in zip(path, path[1:]):
        length = dist(ax, ay, bx, by)
        count = max(1, int(length / (radius * 0.55)))
        for i in range(count + 1):
            t = i / count
            circle(group, ax + (bx - ax) * t, ay + (by - ay) * t, radius, color)


def _clear_of_paths(x: float, y: float, margin: float, samples) -> bool:
    for px, py in samples:
        if (px - x) ** 2 + (py - y) ** 2 < margin * margin:
            return False
    return True


def _near_landmark(x: float, y: float, margin: float, landmarks) -> bool:
    return any(dist(x, y, lx, ly) < margin for lx, ly in landmarks)


def _tree(group, x: float, y: float, scale: float) -> None:
    ellipse(group, x + 5 * scale, y + 1, 62 * scale, 17 * scale, (0.07, 0.20, 0.10, 0.22))
    rect(group, x - 4 * scale, y, 8 * scale, 30 * scale, WOOD)
    rect(group, x - 1 * scale, y, 3 * scale, 28 * scale, WOOD_LIGHT)
    for width, height, offset, color in (
        (55, 48, 27, (0.10, 0.39, 0.20, 1)),
        (44, 40, 43, (0.13, 0.47, 0.24, 1)),
        (30, 31, 58, (0.17, 0.55, 0.28, 1)),
    ):
        w = width * scale
        h = height * scale
        base = y + offset * scale
        poly(
            group,
            [
                (x - w / 2, base),
                (x + w / 2, base),
                (x + w * 0.16, base + h),
                (x - w * 0.16, base + h),
            ],
            color,
        )


def _dead_tree(group, x: float, y: float, scale: float) -> None:
    ellipse(group, x + 4 * scale, y, 44 * scale, 12 * scale, (0.05, 0.05, 0.05, 0.2))
    rect(group, x - 3 * scale, y, 7 * scale, 42 * scale, (0.24, 0.18, 0.14, 1))
    for dx, dy, length, angle in (
        (-4, 24, 30, 0.7), (4, 30, 26, -0.6), (0, 36, 18, 0.15),
    ):
        poly(
            group,
            [
                (x + dx * scale, y + dy * scale),
                (x + (dx + length * 0.7) * scale, y + (dy + length) * scale),
                (x + (dx + length * 0.3) * scale, y + (dy + length * 0.5) * scale),
            ],
            (0.26, 0.19, 0.15, 1),
        )


def _rock(group, x: float, y: float, scale: float) -> None:
    ellipse(group, x + 4 * scale, y, 38 * scale, 12 * scale, (0.07, 0.20, 0.10, 0.22))
    poly(
        group,
        [
            (x - 18 * scale, y),
            (x - 21 * scale, y + 12 * scale),
            (x - 8 * scale, y + 24 * scale),
            (x + 10 * scale, y + 25 * scale),
            (x + 21 * scale, y + 11 * scale),
            (x + 16 * scale, y),
        ],
        STONE,
    )
    poly(
        group,
        [
            (x - 8 * scale, y + 24 * scale),
            (x + 10 * scale, y + 25 * scale),
            (x + 8 * scale, y + 17 * scale),
            (x - 2 * scale, y + 15 * scale),
        ],
        STONE_LIGHT,
    )
    poly(
        group,
        [(x - 21 * scale, y + 12 * scale), (x - 8 * scale, y + 24 * scale), (x - 3 * scale, y + 3 * scale)],
        STONE_DARK,
    )


def _cliff(group, points, top_points) -> None:
    poly(group, points, STONE_DARK)
    poly(group, top_points, STONE_LIGHT)
    for i in range(1, len(points) - 1, 2):
        x, y = points[i]
        poly(group, [(x, y), (x + 6, y + 12), (x + 2, y + 22)], STONE)


def _flower(group, x: float, y: float, color) -> None:
    circle(group, x, y, 1.7, color)
    circle(group, x + 4, y + 1, 1.3, (1, 0.92, 0.55, 1))


def _ruin(group, x: float, y: float, scale: float) -> None:
    """Разрушенная колонна — наполняет карту следами старой крепости."""
    ellipse(group, x + 4 * scale, y, 46 * scale, 14 * scale, (0.06, 0.14, 0.08, 0.24))
    poly(
        group,
        [
            (x - 16 * scale, y),
            (x - 19 * scale, y + 20 * scale),
            (x - 12 * scale, y + 42 * scale),
            (x + 9 * scale, y + 44 * scale),
            (x + 18 * scale, y + 18 * scale),
            (x + 15 * scale, y),
        ],
        STONE,
    )
    poly(
        group,
        [
            (x - 12 * scale, y + 42 * scale),
            (x + 9 * scale, y + 44 * scale),
            (x + 7 * scale, y + 30 * scale),
            (x - 9 * scale, y + 28 * scale),
        ],
        STONE_LIGHT,
    )
    poly(
        group,
        [
            (x - 19 * scale, y + 20 * scale),
            (x - 12 * scale, y + 42 * scale),
            (x - 5 * scale, y + 8 * scale),
        ],
        STONE_DARK,
    )
    # Поваленный обломок рядом.
    rect(group, x + 22 * scale, y + 2 * scale, 26 * scale, 9 * scale, STONE_DARK)
    ellipse(group, x + 60 * scale, y + 1 * scale, 20 * scale, 8 * scale,
            (0.20, 0.42, 0.22, 0.5))


def _banner(group, x: float, y: float, color) -> None:
    """Знамя на краю дороги."""
    rect(group, x - 2, y, 4, 46, WOOD)
    poly(group, [(x + 2, y + 46), (x + 30, y + 38), (x + 2, y + 28)], color)
    circle(group, x, y + 47, 3.2, (1.0, 0.86, 0.36, 1))


def _gold_vein(group, x: float, y: float, scale: float) -> None:
    """Золотая жила: украшение рядом с точками сбора золота."""
    ellipse(group, x, y, 54 * scale, 22 * scale, (1.0, 0.80, 0.20, 0.10))
    poly(
        group,
        [
            (x - 20 * scale, y),
            (x - 10 * scale, y + 16 * scale),
            (x + 6 * scale, y + 19 * scale),
            (x + 20 * scale, y + 6 * scale),
            (x + 14 * scale, y),
        ],
        STONE_DARK,
    )
    for dx, dy, r in ((-8, 8, 3.4), (2, 12, 4.2), (10, 5, 3.0)):
        circle(group, x + dx * scale, y + dy * scale, r * scale,
               (1.0, 0.84, 0.28, 0.95))
        circle(group, x + dx * scale - 1, y + dy * scale + 1.4, r * 0.4,
               (1.0, 0.97, 0.72, 1))


def _plaza(group, x: float, y: float, radius: float) -> None:
    """Вымощенная площадка у базы — двор выглядит обжитым."""
    ellipse(group, x, y, radius * 2.2, radius * 1.5, (0.30, 0.34, 0.30, 0.55))
    ellipse(group, x, y, radius * 1.95, radius * 1.3, (0.52, 0.53, 0.50, 0.55))
    step = radius * 0.42
    row = 0
    yy = y - radius * 0.5
    while yy <= y + radius * 0.5:
        xx = x - radius * 0.8 + (step * 0.5 if row % 2 else 0)
        while xx <= x + radius * 0.8:
            dx = (xx - x) / (radius * 0.9)
            dy = (yy - y) / (radius * 0.6)
            if dx * dx + dy * dy <= 1.0:
                ellipse(group, xx, yy, step * 0.72, step * 0.5,
                        (0.66, 0.67, 0.63, 0.32))
            xx += step
        yy += step * 0.62
        row += 1


def build_background(group, level) -> None:
    """Добавляет статичные инструкции фона выбранной карты."""
    rnd = random.Random(level.seed)
    w = level.world_w
    h = level.world_h
    paths = level.routes
    samples = _samples(paths, 22.0)
    landmarks = [level.base_pos, *level.gold_spots, *[route[0] for route in paths]]
    ash = level.id == "ash"

    # Тёмная подложка за границами мира.
    rect(group, -800, -900, w + 1600, h + 1800, (0.10, 0.13, 0.11, 1))
    rect(group, 0, 0, w, h, level.ground)

    for _ in range(120):
        x = rnd.uniform(0, w)
        y = rnd.uniform(0, h)
        cw = rnd.uniform(70, 220)
        ch = rnd.uniform(30, 100)
        color = level.ground_light if rnd.random() < 0.55 else level.ground_dark
        ellipse(group, x, y, cw, ch, (*color[:3], rnd.uniform(0.10, 0.22)))

    # Скальные выступы по углам карты.
    cw = min(330.0, w * 0.24)
    ch = min(200.0, h * 0.11)
    for corner_x, corner_y, sx, sy in ((0, h, 1, -1), (w, h, -1, -1), (0, 0, 1, 1), (w, 0, -1, 1)):
        base_x = corner_x + sx * cw
        base_y = corner_y + sy * ch
        _cliff(
            group,
            [
                (corner_x, corner_y),
                (base_x, corner_y),
                (base_x + sx * 80, corner_y + sy * ch * 0.35),
                (corner_x + sx * cw * 0.4, corner_y + sy * ch * 0.6),
                (corner_x, corner_y + sy * ch * 0.25),
            ],
            [
                (corner_x, corner_y),
                (base_x, corner_y),
                (base_x + sx * 70, corner_y + sy * ch * 0.16),
                (corner_x + sx * cw * 0.35, corner_y + sy * ch * 0.34),
                (corner_x, corner_y + sy * ch * 0.12),
            ],
        )

    # Мощёный двор у базы: карта перестаёт выглядеть пустой.
    base_x, base_y = level.base_pos
    _plaza(group, base_x, base_y - 26, 175.0)

    # Дороги врагов: тёмная кромка, полотно и светлая середина.
    for path in paths:
        _band(group, path, 112, PATH_EDGE)
    for path in paths:
        _band(group, path, 92, PATH)
    for path in paths:
        _band(group, path, 58, (*PATH_LIGHT[:3], 0.26))

    # Камешки и следы на дороге.
    for _ in range(70):
        x = rnd.uniform(140, w - 140)
        y = rnd.uniform(100, h - 100)
        if not _clear_of_paths(x, y, 38, samples):
            continue
        ellipse(group, x, y, rnd.uniform(4, 11), rnd.uniform(3, 6),
                (*STONE[:3], rnd.uniform(0.18, 0.34)))

    # Деревья (в пустоши — сухие).
    trees = 0
    attempts = 0
    while trees < level.trees and attempts < 900:
        attempts += 1
        x = rnd.uniform(55, w - 55)
        y = rnd.uniform(55, h - 55)
        if not _clear_of_paths(x, y, 105, samples) or _near_landmark(x, y, 140, landmarks):
            continue
        if ash:
            _dead_tree(group, x, y, rnd.uniform(0.8, 1.2))
        else:
            _tree(group, x, y, rnd.uniform(0.75, 1.25))
        trees += 1

    # Камни.
    for _ in range(18):
        x = rnd.uniform(45, w - 45)
        y = rnd.uniform(45, h - 45)
        if not _clear_of_paths(x, y, 70, samples) or _near_landmark(x, y, 95, landmarks):
            continue
        _rock(group, x, y, rnd.uniform(0.6, 1.2))

    # Руины старой крепости — наполняют пустующие участки карты.
    ruins = 0
    attempts = 0
    while ruins < 7 and attempts < 400:
        attempts += 1
        x = rnd.uniform(90, w - 90)
        y = rnd.uniform(90, h - 90)
        if not _clear_of_paths(x, y, 120, samples) or _near_landmark(x, y, 150, landmarks):
            continue
        _ruin(group, x, y, rnd.uniform(0.85, 1.35))
        ruins += 1

    # Знамёна у подступов к воротам.
    for path in paths:
        if len(path) < 5:
            continue
        px, py = path[-4]
        _banner(group, px + 62, py - 6, level.accent)
        qx, qy = path[-3]
        _banner(group, qx - 62, qy - 6, level.accent)

    # Золотые жилы возле точек сбора золота.
    for gx, gy in level.gold_spots[::2]:
        _gold_vein(group, gx + rnd.uniform(-16, 16), gy - 30,
                   rnd.uniform(0.85, 1.15))

    # Кусты и мелкая трава.
    for _ in range(120):
        x = rnd.uniform(30, w - 30)
        y = rnd.uniform(30, h - 30)
        if not _clear_of_paths(x, y, 45, samples):
            continue
        if rnd.random() < 0.45:
            ellipse(group, x, y, rnd.uniform(14, 30), rnd.uniform(7, 14),
                    (*level.ground_dark[:3], 0.7))
            ellipse(group, x + 5, y + 4, rnd.uniform(7, 14), rnd.uniform(4, 8),
                    (*level.ground_light[:3], 0.8))
        else:
            color = (0.42, 0.36, 0.28, 0.9) if ash else (0.20, 0.57, 0.30, 0.85)
            for i in range(3):
                ox = (i - 1) * 4
                poly(
                    group,
                    [(x + ox - 2, y), (x + ox + 2, y), (x + ox, y + rnd.uniform(6, 12))],
                    color,
                )
        if not ash and rnd.random() < 0.3:
            _flower(group, x + rnd.uniform(-8, 8), y + rnd.uniform(-7, 7),
                    (0.98, 0.94, 0.58, 1) if rnd.random() < 0.5 else (0.95, 0.58, 0.51, 1))

    # Рамка мира.
    rect(group, 0, 0, w, 8, (0.23, 0.40, 0.23, 0.8))
    rect(group, 0, h - 8, w, 8, (0.23, 0.40, 0.23, 0.8))
    rect(group, 0, 0, 8, h, (0.23, 0.40, 0.23, 0.8))
    rect(group, w - 8, 0, 8, h, (0.23, 0.40, 0.23, 0.8))


# Совместимость со старым кодом: путь точки до отрезка нужен рендеру.
__all__ = ["build_background", "point_segment_distance"]
