"""Фон карты: рельеф, возвышенности, вода, дороги и растительность.

Карта рисуется не «плоским видом сверху», а с намёком на высоту:
у холмов и скальных полок есть освещённая вершина и тёмный склон-тень,
поэтому земля выглядит объёмной. У каждой карты свой нрав — вода и поля
у спокойных долин, лёд у теснины, лава у пустоши и кратера.
"""

from __future__ import annotations

import random

from ..core.config import (
    PATH,
    PATH_EDGE,
    PATH_LIGHT,
    STONE,
    STONE_DARK,
    STONE_LIGHT,
    WOOD,
    WOOD_LIGHT,
)
from ..render.gfx import circle, ellipse, poly, rect, ring
from ..core.util import dist, point_segment_distance


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


def _tint(color, factor: float, alpha: float | None = None):
    """Осветляет/затемняет цвет, сохраняя прозрачность."""
    r, g, b = color[0] * factor, color[1] * factor, color[2] * factor
    a = color[3] if len(color) > 3 else 1.0
    if alpha is not None:
        a = alpha
    return (min(1.0, r), min(1.0, g), min(1.0, b), a)


# ---------------------------------------------------------------------------
# Рельеф
# ---------------------------------------------------------------------------
def _hill(group, x: float, y: float, w: float, h: float, light, dark) -> None:
    """Пологий холм: тёмная подошва и освещённая вершина."""
    ellipse(group, x, y - h * 0.14, w * 1.04, h * 0.72, _tint(dark, 0.9, 0.30))
    ellipse(group, x, y, w, h, dark)
    ellipse(group, x - w * 0.06, y + h * 0.20, w * 0.72, h * 0.58, light)
    ellipse(group, x - w * 0.16, y + h * 0.34, w * 0.30, h * 0.22, _tint(light, 1.12))


def _mesa(group, x: float, y: float, w: float, h: float, rnd, top, side) -> None:
    """Скальная полка: приподнятая площадка с тёмными боками.

    Именно она даёт ощущение высоты: земля под ней в тени, а верх
    заметно светлее и словно приподнят над дорогой.
    """
    ellipse(group, x, y - h * 0.20, w * 1.10, h * 0.55, (0.0, 0.0, 0.0, 0.16))
    ellipse(group, x, y, w, h, side)
    ellipse(group, x, y + h * 0.24, w * 0.86, h * 0.70, top)
    ellipse(group, x - w * 0.06, y + h * 0.32, w * 0.60, h * 0.42, _tint(top, 1.10))
    ring(group, x, y + h * 0.16, w * 0.40, _tint(top, 1.18, 0.35), 1.4)
    for _ in range(3):
        px = x + rnd.uniform(-w * 0.32, w * 0.32)
        py = y - rnd.uniform(0.0, h * 0.30)
        poly(
            group,
            [
                (px, py),
                (px + rnd.uniform(8, 18), py - rnd.uniform(6, 16)),
                (px + rnd.uniform(2, 8), py - rnd.uniform(10, 22)),
            ],
            _tint(side, 0.74),
        )


def _rock_shelf(group, x: float, y: float, w: float, h: float) -> None:
    """Небольшой каменный уступ у дороги."""
    ellipse(group, x, y, w, h, STONE)
    poly(
        group,
        [
            (x - w * 0.5, y),
            (x - w * 0.35, y + h * 0.9),
            (x + w * 0.30, y + h * 1.05),
            (x + w * 0.5, y),
        ],
        STONE_LIGHT,
    )
    ellipse(group, x, y - h * 0.35, w * 0.95, h * 0.5, (0.0, 0.0, 0.0, 0.16))


def _water(group, x: float, y: float, w: float, h: float, rnd, frozen=False) -> None:
    """Пруд или лужа: мокрый берег, вода и блики."""
    if frozen:
        ellipse(group, x, y, w * 1.06, h * 1.16, (0.70, 0.82, 0.90, 0.45))
        ellipse(group, x, y, w, h, (0.80, 0.90, 0.96, 0.92))
        ellipse(group, x - w * 0.06, y + h * 0.12, w * 0.66, h * 0.5, (0.94, 0.98, 1.0, 0.9))
        for _ in range(4):
            rx = x + rnd.uniform(-w * 0.32, w * 0.32)
            ry = y + rnd.uniform(-h * 0.34, h * 0.34)
            ring(group, rx, ry, rnd.uniform(w * 0.06, w * 0.14), (1.0, 1.0, 1.0, 0.4), 1.2)
        return
    ellipse(group, x, y, w * 1.08, h * 1.24, (0.20, 0.34, 0.30, 0.45))
    ellipse(group, x, y, w, h, (0.18, 0.40, 0.55, 0.94))
    ellipse(group, x, y + h * 0.14, w * 0.80, h * 0.58, (0.28, 0.55, 0.70, 0.9))
    ellipse(group, x, y + h * 0.20, w * 0.60, h * 0.34, (0.36, 0.66, 0.80, 0.7))
    for _ in range(5):
        rx = x + rnd.uniform(-w * 0.34, w * 0.34)
        ry = y + rnd.uniform(-h * 0.30, h * 0.30)
        ellipse(group, rx, ry, rnd.uniform(w * 0.10, w * 0.24), rnd.uniform(2.0, 4.0),
                (0.80, 0.92, 0.98, 0.42))


def _lava(group, x: float, y: float, w: float, h: float, rnd) -> None:
    """Раскалённая трещина-лава: светится изнутри."""
    ellipse(group, x, y, w * 1.25, h * 1.6, (1.0, 0.42, 0.12, 0.10))
    ellipse(group, x, y, w, h, (0.20, 0.10, 0.08, 0.85))
    ellipse(group, x, y, w * 0.78, h * 0.62, (0.98, 0.42, 0.10, 0.95))
    ellipse(group, x, y, w * 0.48, h * 0.36, (1.0, 0.72, 0.28, 0.95))
    for _ in range(3):
        px = x + rnd.uniform(-w * 0.4, w * 0.4)
        py = y + rnd.uniform(-h * 0.4, h * 0.4)
        circle(group, px, py, rnd.uniform(1.6, 3.0), (1.0, 0.86, 0.44, 0.9))


def _cracks(group, x: float, y: float, w: float, h: float, rnd, color) -> None:
    ellipse(group, x, y, w, h * 0.5, (*color[:3], 0.22))
    px = x - w * 0.5
    py = y
    for _ in range(5):
        nx = px + w / 5
        ny = y + rnd.uniform(-h * 0.4, h * 0.4)
        poly(group, [(px, py - 1.6), (nx, ny - 1.6), (nx, ny + 1.6), (px, py + 1.6)], color)
        px, py = nx, ny


def _field(group, x: float, y: float, w: float, h: float, rnd, tint) -> None:
    """Вспаханное поле с бороздами — колорит обжитых земель."""
    rect(group, x - w / 2 - 2, y - h / 2 - 2, w + 4, h + 4, (0.26, 0.20, 0.12, 0.4))
    rect(group, x - w / 2, y - h / 2, w, h, tint)
    rows = max(2, int(h / 13))
    for i in range(rows):
        yy = y - h / 2 + 5 + i * (h - 10) / rows
        rect(group, x - w / 2 + 5, yy, w - 10, 1.6, (0.0, 0.0, 0.0, 0.18))
        rect(group, x - w / 2 + 5, yy + 1.6, w - 10, 1.2, _tint(tint, 1.12, 0.5))


def _fence(group, x: float, y: float, length: float, rnd) -> None:
    posts = max(2, int(length / 34))
    step = length / posts
    for i in range(posts + 1):
        px = x + i * step
        rect(group, px - 2, y, 4, 22, WOOD)
        rect(group, px - 2, y + 18, 4, 4, WOOD_LIGHT)
    rect(group, x, y + 13, length, 3, WOOD_LIGHT)
    rect(group, x, y + 5, length, 3, WOOD)


def _camp(group, x: float, y: float, scale: float, accent, rnd) -> None:
    """Лагерь: пара шатров и костёр."""
    ellipse(group, x, y - 2 * scale, 70 * scale, 20 * scale, (0.0, 0.0, 0.0, 0.18))
    for dx in (-24, 4):
        tx = x + dx * scale
        poly(group, [(tx - 16 * scale, y), (tx + 16 * scale, y), (tx, y + 26 * scale)],
             _tint(accent, 0.85))
        poly(group, [(tx - 1 * scale, y), (tx + 14 * scale, y), (tx, y + 24 * scale)],
             _tint(accent, 1.15))
    fx = x + 26 * scale
    circle(group, fx, y + 4 * scale, 7 * scale, (0.30, 0.16, 0.10, 1))
    circle(group, fx, y + 8 * scale, 4.4 * scale, (1.0, 0.62, 0.22, 0.95))
    circle(group, fx, y + 10 * scale, 2.2 * scale, (1.0, 0.86, 0.44, 0.95))


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


def build_background(group, level, detail: bool = True) -> None:
    """Добавляет статичные инструкции фона выбранной карты.

    ``detail=False`` (на слабом телефоне) оставляет только крупные формы:
    рельеф, дороги и основные деревья — без полей, лагерей и мелкого сора.
    """
    rnd = random.Random(level.seed)
    w = level.world_w
    h = level.world_h
    paths = level.routes
    samples = _samples(paths, 22.0)
    landmarks = [level.base_pos, *level.gold_spots, *[route[0] for route in paths]]
    theme = level.id
    ash = theme in ("ash", "crater", "citadel")
    frost = theme == "frost"
    forest = theme == "forest"

    # Тёмная подложка за границами мира.
    rect(group, -900, -1100, w + 1800, h + 2200, (0.09, 0.12, 0.10, 1))
    rect(group, 0, 0, w, h, level.ground)

    # --- Рельеф: мягкие всхолмления с направленной тенью -----------------
    for _ in range(150 if detail else 70):
        x = rnd.uniform(-40, w + 40)
        y = rnd.uniform(-40, h + 40)
        cw = rnd.uniform(180, 460)
        ch = rnd.uniform(90, 210)
        roll = rnd.random()
        if roll < 0.5:
            _hill(group, x, y, cw, ch, level.ground_light, level.ground_dark)
        elif roll < 0.8:
            ellipse(group, x, y, cw, ch, _tint(level.ground_dark, 0.92, 0.30))
        else:
            ellipse(group, x, y, cw * 0.8, ch * 0.7, _tint(level.ground_light, 1.06, 0.24))

    # --- Возвышенности (скальные полки) — дают объём ---------------------
    mesas = 10 if detail else 5
    placed = 0
    tries = 0
    while placed < mesas and tries < 500:
        tries += 1
        x = rnd.uniform(120, w - 120)
        y = rnd.uniform(160, h - 160)
        if not _clear_of_paths(x, y, 150, samples) or _near_landmark(x, y, 210, landmarks):
            continue
        _mesa(group, x, y, rnd.uniform(220, 380), rnd.uniform(120, 190), rnd,
              _tint(level.ground_light, 1.06), _tint(level.ground_dark, 0.80))
        placed += 1

    # --- Вода: пруды, лёд или лава ---------------------------------------
    if detail:
        if ash:
            pools = 6
        else:
            pools = 4
        placed = 0
        tries = 0
        while placed < pools and tries < 400:
            tries += 1
            x = rnd.uniform(160, w - 160)
            y = rnd.uniform(180, h - 180)
            if not _clear_of_paths(x, y, 160, samples) or _near_landmark(x, y, 190, landmarks):
                continue
            pw = rnd.uniform(200, 340)
            ph = rnd.uniform(110, 170)
            if ash:
                _lava(group, x, y, pw * 0.5, ph * 0.5, rnd)
            else:
                _water(group, x, y, pw, ph, rnd, frozen=frost)
            placed += 1

        # Трещины по пустоши и кратеру.
        if ash:
            for _ in range(20):
                x = rnd.uniform(60, w - 60)
                y = rnd.uniform(60, h - 60)
                if not _clear_of_paths(x, y, 60, samples):
                    continue
                color = (0.60, 0.22, 0.10, 0.5) if not frost else (0.20, 0.28, 0.34, 0.4)
                _cracks(group, x, y, rnd.uniform(60, 140), rnd.uniform(26, 60), rnd, color)

    # --- Каменные уступы по углам карты ----------------------------------
    cw = min(360.0, w * 0.22)
    ch = min(210.0, h * 0.09)
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

    # --- Обжитые земли: поля, изгороди, лагеря ---------------------------
    if detail and not ash:
        for _ in range(4):
            x = rnd.uniform(220, w - 220)
            y = rnd.uniform(240, h - 240)
            if not _clear_of_paths(x, y, 150, samples) or _near_landmark(x, y, 200, landmarks):
                continue
            _field(group, x, y, rnd.uniform(150, 260), rnd.uniform(90, 150), rnd,
                   (0.52, 0.44, 0.22, 0.55) if not frost else (0.72, 0.80, 0.78, 0.5))
        for _ in range(3):
            x = rnd.uniform(220, w - 220)
            y = rnd.uniform(240, h - 240)
            if not _clear_of_paths(x, y, 140, samples) or _near_landmark(x, y, 190, landmarks):
                continue
            _fence(group, x, y, rnd.uniform(120, 240), rnd)

    if detail:
        for _ in range(3):
            x = rnd.uniform(200, w - 200)
            y = rnd.uniform(220, h - 220)
            if not _clear_of_paths(x, y, 150, samples) or _near_landmark(x, y, 200, landmarks):
                continue
            _camp(group, x, y, rnd.uniform(0.9, 1.3), level.accent, rnd)

    # --- Мощёный двор у базы ---------------------------------------------
    base_x, base_y = level.base_pos
    _plaza(group, base_x, base_y - 26, 175.0)

    # --- Дороги врагов: тень, кромка, полотно и светлая середина ---------
    for path in paths:
        _band(group, path, 124, (0.0, 0.0, 0.0, 0.14))
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

    # --- Деревья (в пустоши — сухие) -------------------------------------
    tree_target = level.trees * (1.0 if detail else 0.6)
    trees = 0
    attempts = 0
    while trees < tree_target and attempts < 1400:
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

    # --- Камни ------------------------------------------------------------
    for _ in range(24 if detail else 14):
        x = rnd.uniform(45, w - 45)
        y = rnd.uniform(45, h - 45)
        if not _clear_of_paths(x, y, 70, samples) or _near_landmark(x, y, 95, landmarks):
            continue
        _rock(group, x, y, rnd.uniform(0.6, 1.2))

    # --- Руины старой крепости -------------------------------------------
    ruins = 9 if detail else 4
    placed = 0
    attempts = 0
    while placed < ruins and attempts < 600:
        attempts += 1
        x = rnd.uniform(90, w - 90)
        y = rnd.uniform(90, h - 90)
        if not _clear_of_paths(x, y, 120, samples) or _near_landmark(x, y, 150, landmarks):
            continue
        _ruin(group, x, y, rnd.uniform(0.85, 1.35))
        placed += 1

    # --- Знамена у подступов к воротам -----------------------------------
    for path in paths:
        if len(path) < 5:
            continue
        px, py = path[-4]
        _banner(group, px + 62, py - 6, level.accent)
        qx, qy = path[-3]
        _banner(group, qx - 62, qy - 6, level.accent)

    # --- Золотые жилы возле точек сбора золота ---------------------------
    for gx, gy in level.gold_spots[::2]:
        _gold_vein(group, gx + rnd.uniform(-16, 16), gy - 30,
                   rnd.uniform(0.85, 1.15))

    # --- Кусты и мелкая трава --------------------------------------------
    for _ in range(120 if detail else 60):
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
            if ash:
                color = (0.42, 0.36, 0.28, 0.9)
            elif frost:
                color = (0.70, 0.82, 0.86, 0.85)
            else:
                color = (0.20, 0.57, 0.30, 0.85)
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

    # --- Мягкая кромка мира вместо резкой «стены» ------------------------
    for i, alpha in enumerate((0.16, 0.26, 0.40)):
        thick = 26 + i * 22
        rect(group, -thick, -thick, w + thick * 2, thick, (0.05, 0.08, 0.06, alpha))
        rect(group, -thick, h, w + thick * 2, thick, (0.05, 0.08, 0.06, alpha))
        rect(group, -thick, 0, thick, h, (0.05, 0.08, 0.06, alpha))
        rect(group, w, 0, thick, h, (0.05, 0.08, 0.06, alpha))
    for x0, y0, ww, hh in (
        (0, 0, w, 6), (0, h - 6, w, 6), (0, 0, 6, h), (w - 6, 0, 6, h),
    ):
        rect(group, x0, y0, ww, hh, (0.20, 0.33, 0.22, 0.55))


# Совместимость со старым кодом: путь точки до отрезка нужен рендеру.
__all__ = ["build_background", "point_segment_distance"]
