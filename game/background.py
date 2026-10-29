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

    # Кусты и мелкая трава.
    for _ in range(70):
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
