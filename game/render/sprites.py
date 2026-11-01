"""Отрисовка персонажей и объектов мира примитивами Kivy."""

from __future__ import annotations

import math

from kivy.graphics import Color, PopMatrix, PushMatrix, Rectangle, Rotate, Translate
from kivy.metrics import dp

from ..core.config import (
    BASE_POS,
    BLACK,
    BLUE,
    BLUE_LIGHT,
    BUILD_TYPES,
    CLEAR,
    GOLD,
    GOLD_DARK,
    GOLD_LIGHT,
    GRASS_DARK,
    GRASS_LIGHT,
    GREEN,
    GREEN_LIGHT,
    HERO_ATTACK_ANIM,
    RED,
    RED_DARK,
    RED_LIGHT,
    ROOF,
    ROOF_LIGHT,
    SHADOW,
    SKIN,
    STONE,
    STONE_DARK,
    STONE_LIGHT,
    WHITE,
    WOOD,
    WOOD_LIGHT,
)
from ..entities.entities import (
    Building,
    Coin,
    Defender,
    Effect,
    Enemy,
    Hero,
    Particle,
)
from .gfx import circle, ellipse, line, poly, rect, ring, rounds


def _shadow(group, x: float, y: float, w: float, h: float, alpha: float = 0.28) -> None:
    ellipse(group, x, y, w, h, (0.04, 0.13, 0.07, alpha))


def health_bar(group, x: float, y: float, width: float, ratio: float, color=RED_LIGHT) -> None:
    ratio = max(0.0, min(1.0, ratio))
    rect(group, x - width / 2 - 1, y - 1, width + 2, 6, (0.05, 0.06, 0.07, 0.85))
    rect(group, x - width / 2, y, width * ratio, 4, color)


# Кэш текстур всплывающих цифр: Label.refresh() — дорогая операция, а цифры
# встречаются часто. Ключ — текст и размер, цвет задаётся инструкцией Color.
_TEXT_CACHE: dict[tuple[str, int], object] = {}


def _damage_texture(text: str, size: int):
    """Текстура цифры урона. None, если шрифт недоступен (headless-тесты)."""
    key = (text, size)
    cached = _TEXT_CACHE.get(key)
    if cached is not None:
        return cached
    try:
        from kivy.core.text import Label as CoreLabel

        label = CoreLabel(text=text, font_size=size, bold=True)
        label.refresh()
        texture = label.texture
    except Exception:
        return None
    if len(_TEXT_CACHE) > 240:
        _TEXT_CACHE.clear()
    _TEXT_CACHE[key] = texture
    return texture


def draw_coin(group, coin: Coin, t: float) -> None:
    """Кучка золота на карте."""
    bob = math.sin(t * 4.5 + coin.phase) * 2.4
    x, y = coin.x, coin.y + bob
    pulse = 0.5 + 0.5 * math.sin(t * 3.4 + coin.phase)
    _shadow(group, x, coin.y - 2, 34, 13, 0.24)
    ring(group, x, y + 2, 20 + pulse * 4, (1.0, 0.84, 0.30, 0.22 + pulse * 0.12), 1.5)
    ellipse(group, x, y + 1, 32, 12, GOLD_DARK)
    ellipse(group, x - 4, y + 4, 27, 9, GOLD)
    ellipse(group, x + 6, y + 5, 22, 8, GOLD)
    for dx, dy, r in ((-6, 6, 5.5), (2, 9, 6.0), (9, 5, 4.5)):
        circle(group, x + dx, y + dy, r, GOLD)
        circle(group, x + dx - 1.5, y + dy + 1.5, r * 0.42, GOLD_LIGHT)
    circle(group, x + 13, y + 9, 1.6, WHITE)


def draw_hero(group, hero: Hero, t: float) -> None:
    bob = math.sin(t * 12) * 1.6 if hero.moving else math.sin(t * 2.5) * 0.7
    x, y = hero.x, hero.y
    _shadow(group, x, y - 3, 34, 12, 0.34)

    # Синий магический круг под ногами.
    ring(group, x, y + 1, 24 + math.sin(t * 3) * 2, (0.33, 0.80, 1.0, 0.55), 1.5)
    ring(group, x, y + 1, 19, (0.45, 0.88, 1.0, 0.32), 1.0)

    # Плащ.
    poly(
        group,
        [
            (x - 10, y + 19 + bob),
            (x - 22, y + 9 + bob),
            (x - 15, y + 33 + bob),
            (x + 2, y + 37 + bob),
        ],
        (0.09, 0.22, 0.48, 1),
    )

    # Ноги.
    rect(group, x - 8, y + 1, 6, 13, STONE_DARK)
    rect(group, x + 2, y + 1, 6, 13, STONE_DARK)
    rect(group, x - 9, y, 7, 4, BLACK)
    rect(group, x + 2, y, 7, 4, BLACK)

    # Корпус и наплечники.
    rounds(group, x - 11, y + 13 + bob, 22, 23, 7, BLUE)
    rounds(group, x - 12, y + 27 + bob, 10, 9, 4, BLUE_LIGHT)
    rounds(group, x + 2, y + 27 + bob, 10, 9, 4, BLUE_LIGHT)
    rect(group, x - 10, y + 15 + bob, 20, 4, GOLD_DARK)

    # Голова, шлем и корона.
    circle(group, x, y + 43 + bob, 10, SKIN)
    rounds(group, x - 10, y + 45 + bob, 20, 10, 5, STONE_LIGHT)
    rect(group, x - 12, y + 46 + bob, 24, 3, GOLD_DARK)
    poly(
        group,
        [
            (x - 8, y + 53 + bob),
            (x - 8, y + 62 + bob),
            (x - 4, y + 57 + bob),
            (x, y + 64 + bob),
            (x + 4, y + 57 + bob),
            (x + 8, y + 62 + bob),
            (x + 8, y + 53 + bob),
        ],
        GOLD,
    )

    # Щит.
    circle(group, x - 16, y + 27 + bob, 9, GOLD_DARK)
    circle(group, x - 16, y + 27 + bob, 7.5, BLUE_LIGHT)
    rect(group, x - 18, y + 22 + bob, 4, 10, GOLD)

    # Меч, повёрнутый в сторону движения. Во время удара меч делает
    # заметный замах: видно, что герой именно бьёт, а не просто стоит.
    swing = 0.0
    lunge = 0.0
    if hero.attack_anim > 0:
        progress = 1.0 - max(0.0, hero.attack_anim) / HERO_ATTACK_ANIM
        # Сначала рука уходит назад (замах), затем резко вперёд (удар).
        swing = math.sin(progress * math.pi) * 62.0 - 34.0 * progress
        lunge = math.sin(progress * math.pi) * 11.0
    group.add(PushMatrix())
    group.add(
        Translate(
            x + 10 + math.cos(hero.facing) * lunge,
            y + 27 + bob + math.sin(hero.facing) * lunge,
            0,
        )
    )
    group.add(Rotate(angle=math.degrees(hero.facing) + swing, axis=(0, 0, 1)))
    rect(group, 0, -2, 25, 4, STONE_LIGHT)
    poly(group, [(24, -3), (33, 0), (24, 3)], WHITE)
    rect(group, -3, -5, 5, 10, GOLD)
    group.add(PopMatrix())

    if hero.invuln > 0 and int(hero.invuln * 12) % 2 == 0:
        ring(group, x, y + 24, 29, (1.0, 0.4, 0.3, 0.65), 1.5)


def draw_enemy(group, enemy: Enemy, t: float, detail: bool = True) -> None:
    x, y = enemy.x, enemy.y
    palettes = {
        "grunt": (RED_DARK, RED, (1, 0.86, 0.42, 1)),
        "runner": ((0.42, 0.10, 0.08, 1), (0.90, 0.31, 0.18, 1), (1, 0.88, 0.50, 1)),
        "brute": ((0.28, 0.07, 0.06, 1), (0.66, 0.16, 0.12, 1), (1, 0.80, 0.40, 1)),
        "shield": ((0.20, 0.19, 0.17, 1), (0.50, 0.47, 0.40, 1), (0.92, 0.92, 0.86, 1)),
        "archer": ((0.14, 0.26, 0.11, 1), (0.32, 0.55, 0.24, 1), (1, 0.88, 0.45, 1)),
        "shaman": ((0.21, 0.11, 0.33, 1), (0.50, 0.30, 0.70, 1), (0.86, 0.70, 1.0, 1)),
        "bomber": ((0.33, 0.15, 0.05, 1), (0.84, 0.45, 0.12, 1), (1, 0.72, 0.30, 1)),
        "chief": ((0.34, 0.06, 0.06, 1), (0.78, 0.14, 0.10, 1), (1.0, 0.84, 0.30, 1)),
        "boss": (RED_DARK, RED, (1.0, 0.80, 0.30, 1)),
        "berserker": ((0.35, 0.08, 0.10, 1), (0.88, 0.22, 0.24, 1), (1.0, 0.82, 0.40, 1)),
        "golem": ((0.24, 0.22, 0.20, 1), (0.52, 0.48, 0.42, 1), (0.94, 0.78, 0.40, 1)),
        "necromancer": ((0.16, 0.08, 0.26, 1), (0.46, 0.22, 0.62, 1), (0.78, 0.96, 0.72, 1)),
        "warlord": ((0.12, 0.03, 0.10, 1), (0.52, 0.08, 0.24, 1), (1.0, 0.38, 0.30, 1)),
    }
    robe_color, body_color, eye_color = palettes.get(enemy.kind, palettes["grunt"])
    if enemy.kind == "warlord":
        scale = 2.05
    elif enemy.kind == "boss":
        scale = 1.9
    elif enemy.kind == "chief":
        scale = 1.42
    elif enemy.kind == "golem":
        scale = 1.45
    elif enemy.kind == "brute":
        scale = 1.35
    elif enemy.kind == "berserker":
        scale = 1.05
    elif enemy.kind == "runner":
        scale = 0.86
    elif enemy.kind == "shield":
        scale = 1.12
    else:
        scale = 1.0
    if enemy.elite:
        scale *= 1.08
    bob = math.sin(t * 9 + enemy.phase) * 1.5
    radius = enemy.radius

    if enemy.elite:
        ring(group, x, y + 2, radius * 1.9, (1.0, 0.76, 0.24, 0.55), 2)
    if detail:
        _shadow(group, x, y - 2, radius * 2.6, radius * 0.9, 0.30)

    # Ноги.
    rect(group, x - 5 * scale, y + 1, 5 * scale, 11 * scale, (0.20, 0.08, 0.08, 1))
    rect(group, x + 2 * scale, y + 1, 5 * scale, 11 * scale, (0.20, 0.08, 0.08, 1))

    # Плащ / тело.
    poly(
        group,
        [
            (x - radius * 1.15, y + 10 * scale),
            (x - radius * 0.9, y + 25 * scale + bob),
            (x - radius * 0.3, y + 36 * scale + bob),
            (x + radius * 0.8, y + 23 * scale + bob),
            (x + radius * 1.05, y + 8 * scale),
        ],
        robe_color,
    )
    rounds(group, x - radius * 0.75, y + 12 * scale + bob, radius * 1.5, radius * 1.4, 5 * scale, body_color)

    # Голова в капюшоне.
    circle(group, x, y + 37 * scale + bob, 8 * scale, robe_color)
    poly(
        group,
        [
            (x - 9 * scale, y + 36 * scale + bob),
            (x, y + 48 * scale + bob),
            (x + 9 * scale, y + 36 * scale + bob),
        ],
        body_color,
    )
    if detail:
        circle(group, x - 3 * scale, y + 38 * scale + bob, 1.7 * scale, eye_color)
        circle(group, x + 3 * scale, y + 38 * scale + bob, 1.7 * scale, eye_color)

    # Оружие.
    if detail:
        group.add(PushMatrix())
        group.add(Translate(x + radius * 0.75, y + 22 * scale + bob, 0))
        group.add(Rotate(angle=math.degrees(enemy.facing), axis=(0, 0, 1)))
        if enemy.kind == "boss":
            rect(group, 0, -1.5 * scale, 26 * scale, 3 * scale, STONE_LIGHT)
            poly(group, [(25 * scale, -6 * scale), (39 * scale, 0), (25 * scale, 6 * scale)], WHITE)
        elif enemy.kind == "brute":
            rect(group, 0, -3 * scale, 30 * scale, 6 * scale, WOOD)
            circle(group, 31 * scale, 0, 6 * scale, STONE_DARK)
        elif enemy.kind == "archer":
            rect(group, 0, -1 * scale, 16 * scale, 2 * scale, WOOD_LIGHT)
        elif enemy.kind == "shaman":
            rect(group, 0, -1 * scale, 26 * scale, 2.4 * scale, WOOD)
        else:
            rect(group, 0, -1.5 * scale, 24 * scale, 3 * scale, STONE_LIGHT)
            rect(group, -2 * scale, -4 * scale, 4 * scale, 8 * scale, WOOD)
        group.add(PopMatrix())

    # Особенности видов.
    if enemy.kind == "boss":
        poly(group, [(x - 18, y + 45), (x - 31, y + 62), (x - 11, y + 55)], RED_LIGHT)
        poly(group, [(x + 18, y + 45), (x + 31, y + 62), (x + 11, y + 55)], RED_LIGHT)
        circle(group, x, y + 72, 3.2, GOLD)
    elif enemy.kind == "chief":
        poly(
            group,
            [
                (x - 14, y + 49), (x - 14, y + 60), (x - 7, y + 53),
                (x, y + 64), (x + 7, y + 53), (x + 14, y + 60), (x + 14, y + 49),
            ],
            GOLD,
        )
        rect(group, x - radius - 4, y + 18, 7, 26, STONE_DARK)
    elif enemy.kind == "shield":
        rounds(group, x - radius - 10, y + 12, 13, 26, 5, (0.60, 0.58, 0.52, 1))
        rounds(group, x - radius - 8, y + 15, 9, 20, 4, (0.78, 0.76, 0.68, 1))
        circle(group, x - radius - 3.5, y + 25, 3.0, GOLD_DARK)
    elif enemy.kind == "archer":
        line(
            group,
            [
                x + radius + 6, y + 12,
                x + radius + 14, y + 24,
                x + radius + 6, y + 36,
            ],
            WOOD_LIGHT,
            2.0,
        )
        line(
            group,
            [x + radius + 6, y + 12, x + radius + 6, y + 36],
            (0.92, 0.90, 0.80, 0.8),
            1.0,
        )
    elif enemy.kind == "shaman":
        rect(group, x + radius + 4, y + 10, 3, 40, WOOD)
        orb = 4.5 + math.sin(t * 5 + enemy.phase) * 1.4
        circle(group, x + radius + 5.5, y + 54, orb + 4, (0.72, 0.44, 1.0, 0.22))
        circle(group, x + radius + 5.5, y + 54, orb, (0.80, 0.58, 1.0, 0.95))
        if enemy.support_cd < 0.35:
            ring(group, x, y + 14, 44, (0.62, 0.90, 0.44, 0.45), 2)
    elif enemy.kind == "bomber":
        circle(group, x, y + 52 * scale + bob, 8, (0.20, 0.18, 0.16, 1))
        circle(group, x - 2.5, y + 54 * scale + bob, 2.5, (0.45, 0.42, 0.38, 1))
        line(
            group,
            [x + 3, y + 58 * scale + bob, x + 8, y + 64 * scale + bob],
            (0.90, 0.72, 0.40, 1),
            1.6,
        )
        circle(group, x + 9, y + 65 * scale + bob, 2.0, (1.0, 0.62, 0.20, 1))
    elif enemy.kind == "golem":
        # Каменные наплечники и тяжёлые кулаки.
        rounds(
            group, x - radius * 1.25, y + 24 * scale,
            13 * scale, 12 * scale, 4, (0.38, 0.35, 0.31, 1),
        )
        rounds(
            group, x + radius * 1.25 - 13 * scale, y + 24 * scale,
            13 * scale, 12 * scale, 4, (0.38, 0.35, 0.31, 1),
        )
        rect(
            group, x - radius * 1.35, y + 6 * scale,
            9 * scale, 12 * scale, (0.34, 0.32, 0.28, 1),
        )
        rect(
            group, x + radius * 1.35 - 9 * scale, y + 6 * scale,
            9 * scale, 12 * scale, (0.34, 0.32, 0.28, 1),
        )
    elif enemy.kind == "necromancer":
        # Парящий зелёный шар: некромант готовит призыв.
        orb = 4.0 + math.sin(t * 4 + enemy.phase) * 1.2
        circle(group, x + radius + 8, y + 46, orb + 4, (0.56, 0.94, 0.62, 0.20))
        circle(group, x + radius + 8, y + 46, orb, (0.72, 1.0, 0.74, 0.95))
        if enemy.support_cd < 0.6:
            ring(group, x, y + 14, 40, (0.66, 0.44, 0.96, 0.45), 2)
    elif enemy.kind == "berserker":
        if enemy.max_hp > 0 and enemy.hp <= enemy.max_hp * 0.4:
            # В ярости вокруг берсерка вспыхивает красное пламя.
            pulse = 0.55 + 0.45 * math.sin(t * 12 + enemy.phase)
            ring(
                group, x, y + 8, radius * 1.8,
                (1.0, 0.36, 0.24, 0.28 + 0.22 * pulse), 2,
            )
            circle(
                group, x, y + 44 * scale + bob,
                4 + 2 * pulse, (1.0, 0.50, 0.22, 0.30),
            )
    elif enemy.kind == "warlord":
        # Тёмная корона и алые рога.
        poly(
            group,
            [(x - 20, y + 45), (x - 34, y + 66), (x - 12, y + 56)],
            (0.42, 0.06, 0.18, 1),
        )
        poly(
            group,
            [(x + 20, y + 45), (x + 34, y + 66), (x + 12, y + 56)],
            (0.42, 0.06, 0.18, 1),
        )
        poly(
            group,
            [
                (x - 15, y + 50), (x - 15, y + 62), (x - 7, y + 55),
                (x, y + 67), (x + 7, y + 55), (x + 15, y + 62), (x + 15, y + 50),
            ],
            (0.78, 0.10, 0.28, 1),
        )
        circle(group, x, y + 74, 3.4, (1.0, 0.84, 0.34, 1))

    if enemy.hit_flash > 0:
        circle(group, x, y + 24 * scale, radius * 1.15, (1, 1, 1, 0.25))

    if enemy.hp < enemy.max_hp or enemy.boss or enemy.elite:
        width = 48 if enemy.boss else (34 if enemy.kind == "brute" else 26)
        if enemy.kind == "warlord":
            bar_color = (0.95, 0.36, 0.52, 1)
        elif enemy.kind == "boss":
            bar_color = RED_LIGHT
        elif enemy.elite:
            bar_color = (1.0, 0.78, 0.26, 1)
        else:
            bar_color = (0.95, 0.34, 0.25, 1)
        health_bar(group, x, y + 58 * scale, width, enemy.hp / max(1.0, enemy.max_hp), bar_color)


def draw_spawn_marker(group, x: float, y: float, t: float) -> None:
    """Тёмный портал на дороге: отсюда приходят враги."""
    pulse = 0.5 + 0.5 * math.sin(t * 2.6 + x * 0.01 + y * 0.01)
    circle(group, x, y + 4, 34 + pulse * 6, (0.72, 0.10, 0.08, 0.14 + pulse * 0.06))
    ellipse(group, x, y + 2, 52, 18, (0.10, 0.06, 0.06, 0.55))
    ring(group, x, y + 4, 24, (0.90, 0.20, 0.16, 0.55), 2)
    poly(group, [(x - 22, y), (x - 16, y + 34), (x - 8, y + 6)], STONE_DARK)
    poly(group, [(x + 22, y), (x + 16, y + 34), (x + 8, y + 6)], STONE_DARK)
    rect(group, x - 8, y + 4, 16, 4, (0.88, 0.26, 0.20, 0.8))


def draw_castle(group, t: float, carried: int = 0, hp_ratio: float = 1.0,
                x: float | None = None, y: float | None = None) -> None:
    if x is None:
        x = BASE_POS[0]
    if y is None:
        y = BASE_POS[1]
    if hp_ratio < 0.999:
        pulse = 0.45 + math.sin(t * 4) * 0.15
        circle(group, x, y + 10, 108, (1.0, 0.22, 0.16, 0.08 + pulse * 0.08))
        ring(group, x, y + 10, 100, (1.0, 0.34, 0.26, 0.45), 2)
    else:
        ring(group, x, y + 10, 96, (1.0, 0.85, 0.30, 0.18), 1.5)

    _shadow(group, x, y - 2, 235, 65, 0.30)
    rect(group, x - 112, y, 224, 20, STONE)
    rect(group, x - 99, y + 20, 198, 22, STONE_LIGHT)
    for offset in (-80, -30, 25, 75):
        rect(group, x + offset - 7, y + 20, 14, 30, STONE_DARK)

    # Стены и башни.
    rect(group, x - 84, y + 42, 168, 62, (0.68, 0.53, 0.34, 1))
    rect(group, x - 84, y + 42, 168, 8, WOOD_LIGHT)
    for offset in (-61, -20, 23, 64):
        rect(group, x + offset - 8, y + 42, 16, 62, WOOD)
    rect(group, x - 105, y + 42, 35, 92, STONE_LIGHT)
    rect(group, x + 70, y + 42, 35, 92, STONE_LIGHT)
    rect(group, x - 105, y + 42, 9, 92, STONE_DARK)
    rect(group, x + 96, y + 42, 9, 92, STONE_DARK)

    # Синие крыши.
    poly(
        group,
        [(x - 124, y + 120), (x - 118, y + 160), (x - 88, y + 190), (x - 55, y + 160), (x - 48, y + 120)],
        ROOF,
    )
    poly(
        group,
        [(x - 118, y + 160), (x - 88, y + 190), (x - 58, y + 160), (x - 80, y + 140), (x - 96, y + 140)],
        ROOF_LIGHT,
    )
    poly(
        group,
        [(x + 47, y + 118), (x + 54, y + 158), (x + 86, y + 186), (x + 119, y + 155), (x + 126, y + 118)],
        ROOF,
    )
    poly(
        group,
        [(x + 54, y + 158), (x + 86, y + 186), (x + 118, y + 155), (x + 96, y + 137), (x + 78, y + 137)],
        ROOF_LIGHT,
    )
    # Центральный дом.
    rect(group, x - 52, y + 96, 104, 62, (0.72, 0.57, 0.37, 1))
    rect(group, x - 56, y + 96, 112, 8, WOOD_LIGHT)
    poly(
        group,
        [(x - 67, y + 153), (x - 30, y + 203), (x + 35, y + 203), (x + 67, y + 153)],
        ROOF,
    )
    poly(
        group,
        [(x - 30, y + 203), (x + 35, y + 203), (x + 19, y + 171), (x - 16, y + 171)],
        ROOF_LIGHT,
    )
    rect(group, x - 13, y + 96, 26, 44, (0.25, 0.18, 0.12, 1))
    circle(group, x + 8, y + 121, 2, GOLD)

    # Флаги и корона.
    rect(group, x - 1, y + 200, 3, 43, WOOD)
    poly(group, [(x + 1, y + 238), (x + 40, y + 227), (x + 1, y + 215)], GOLD)
    poly(
        group,
        [(x - 15, y + 210), (x - 15, y + 224), (x - 9, y + 217), (x, y + 229),
         (x + 9, y + 217), (x + 15, y + 224), (x + 15, y + 210)],
        GOLD,
    )

    # Трещины и гарь, когда база повреждена.
    if hp_ratio < 0.66:
        line(group, [x - 40, y + 96, x - 26, y + 122, x - 34, y + 145], (0.12, 0.10, 0.08, 0.65), 2)
        line(group, [x + 30, y + 100, x + 20, y + 128, x + 30, y + 152], (0.12, 0.10, 0.08, 0.65), 2)
    if hp_ratio < 0.33:
        line(group, [x - 70, y + 44, x - 52, y + 68, x - 64, y + 92], (0.10, 0.08, 0.07, 0.8), 3)
        line(group, [x + 62, y + 48, x + 48, y + 72, x + 58, y + 98], (0.10, 0.08, 0.07, 0.8), 3)


def draw_effect(group, effect: Effect) -> None:
    if effect.life <= 0:
        return
    progress = max(0.0, min(1.0, effect.t / effect.life))
    alpha = 1.0 - progress
    if effect.kind == "ring":
        radius = effect.radius + progress * 34
        ring(group, effect.x, effect.y, radius, (*effect.color[:3], alpha * 0.8), 2)
    elif effect.kind == "deposit":
        radius = effect.radius + progress * 65
        ring(group, effect.x, effect.y, radius, (*effect.color[:3], alpha * 0.9), 3)
        circle(group, effect.x, effect.y, 8 * (1 - progress), (*effect.color[:3], alpha * 0.6))
    elif effect.kind == "slash":
        scale = 1.5 if effect.strong else 1.0
        length = (26 + progress * 16) * scale
        angle = effect.angle
        width = 3.4 if effect.strong else 2.4
        color = (*effect.color[:3], alpha)
        # Три коротких штриха веером читаются как взмах меча.
        for spread in (-0.55, 0.0, 0.55):
            a = angle + spread
            line(
                group,
                [
                    effect.x - math.cos(a) * length / 2,
                    effect.y - math.sin(a) * length / 2,
                    effect.x + math.cos(a) * length / 2,
                    effect.y + math.sin(a) * length / 2,
                ],
                color,
                width,
            )
    elif effect.kind == "dmg":
        size = 21 if effect.strong else 16
        texture = _damage_texture(effect.text, size)
        if texture is not None:
            width, height = texture.size
            rise = progress * 34
            group.add(Color(*effect.color[:3], max(0.0, min(1.0, (1.0 - progress) * 1.6))))
            group.add(
                Rectangle(
                    texture=texture,
                    pos=(effect.x - width / 2, effect.y + rise),
                    size=texture.size,
                )
            )
    elif effect.kind == "puff":
        for i in range(6):
            angle = effect.angle + i * math.pi / 3
            distance = 6 + progress * 27
            circle(
                group,
                effect.x + math.cos(angle) * distance,
                effect.y + math.sin(angle) * distance,
                2.5 * (1 - progress) + 1,
                (*effect.color[:3], alpha * 0.9),
            )
    elif effect.kind == "heal":
        circle(group, effect.x, effect.y - progress * 40, 20 * (1 - progress) + 4, (*effect.color[:3], alpha * 0.7))
    elif effect.kind == "bolt":
        line(
            group,
            [effect.x, effect.y, effect.x2, effect.y2],
            (*effect.color[:3], alpha * 0.9),
            3.0 * (0.4 + alpha),
        )
        circle(group, effect.x2, effect.y2, 5 * alpha + 1, (*effect.color[:3], alpha * 0.8))


def draw_particle(group, particle: Particle) -> None:
    if particle.life <= 0:
        return
    alpha = max(0.0, 1.0 - particle.t / particle.life)
    circle(
        group,
        particle.x,
        particle.y,
        particle.size * (0.4 + alpha * 0.8),
        (*particle.color[:3], alpha),
    )


def draw_joystick(group, origin, offset, radius: float) -> None:
    ox, oy = origin
    dx, dy = offset
    circle(group, ox, oy, radius, (0.03, 0.07, 0.10, 0.25))
    ring(group, ox, oy, radius, (1, 1, 1, 0.30), 2)
    circle(group, ox + dx, oy + dy, radius * 0.46, (1, 1, 1, 0.18))
    ring(group, ox + dx, oy + dy, radius * 0.46, (1, 1, 1, 0.55), 1.5)


# ---------------------------------------------------------------------------
# Защита базы: площадки, постройки и бойцы
# ---------------------------------------------------------------------------
def _level_pips(group, x: float, y: float, level: int, max_level: int = 3) -> None:
    """Точки уровня над постройкой."""
    total = max_level
    start = x - (total - 1) * 5.0
    for index in range(total):
        px = start + index * 10.0
        if index < level:
            circle(group, px, y, 3.4, GOLD)
            circle(group, px - 0.8, y + 0.9, 1.5, GOLD_LIGHT)
        else:
            circle(group, px, y, 2.8, (0.16, 0.20, 0.18, 0.65))


def draw_slot(group, x: float, y: float, t: float, active: bool = False,
              affordable: bool = True, focused: bool = False) -> None:
    """Пустая площадка под строительство.

    ``focused`` — площадка, которую выбрал игрок: по ней построит кнопка «✓».
    Её видно издалека: крупное пульсирующее кольцо, стрелка сверху и уголки.
    """
    pulse = 0.5 + 0.5 * math.sin(t * 3.2 + x * 0.01)
    _shadow(group, x, y, 96, 34, 0.22)
    ellipse(group, x, y + 4, 92, 44, (0.92, 0.86, 0.62, 0.10))
    if focused:
        glow = 0.55 + 0.45 * pulse
        # Широкое «поле» вокруг площадки — палец попадает уверенно.
        ellipse(group, x, y + 4, 132, 66, (1.0, 0.82, 0.26, 0.10 + glow * 0.10))
        ring(group, x, y + 4, 58 + pulse * 8, (1.0, 0.80, 0.22, 0.90), 4.0)
        ring(group, x, y + 4, 45 + pulse * 4, (1.0, 0.90, 0.42, 0.55), 2.5)
        ring(group, x, y + 4, 30, (1.0, 0.94, 0.55, 0.35), 1.5)
        _focus_corners(group, x, y + 4, 40 + pulse * 6, (1.0, 0.88, 0.38, 0.95))
        _focus_arrow(group, x, y + 52 + pulse * 6, (1.0, 0.86, 0.30, 0.95))
    elif active:
        ring(group, x, y + 4, 40 + pulse * 5, (1.0, 0.86, 0.32, 0.85), 2.5)
        ring(group, x, y + 4, 30, (1.0, 0.90, 0.45, 0.35), 1.5)
        ellipse(group, x, y + 4, 76, 34, (1.0, 0.84, 0.30, 0.10 + pulse * 0.10))
    else:
        ring(group, x, y + 4, 39, (1.0, 1.0, 1.0, 0.22), 1.6)
        ring(group, x, y + 4, 30, (1.0, 0.95, 0.72, 0.10), 1.0)

    color = (1.0, 0.86, 0.34, 0.92) if affordable else (0.72, 0.72, 0.68, 0.55)
    if focused:
        color = (1.0, 0.94, 0.62, 1.0)
    rect(group, x - 9, y + 10, 18, 4, color)
    rect(group, x - 2, y + 3, 4, 18, color)

    for dx, dy in ((-28, 12), (28, 12), (-28, -4), (28, -4)):
        circle(group, x + dx, y + dy, 2.2, (1.0, 0.95, 0.75, 0.35))


def _focus_corners(group, cx: float, cy: float, r: float, color) -> None:
    """Четыре «уголка» — рамка-прицел вокруг выбранной площадки."""
    arm = 10.0
    for sx, sy in ((-1, 1), (1, 1), (-1, -1), (1, -1)):
        ox, oy = cx + sx * r, cy + sy * r
        line(group, [ox - sx * arm, oy, ox, oy, ox, oy - sy * arm], color, 3.0)


def _focus_arrow(group, cx: float, cy: float, color) -> None:
    """Стрелка, указывающая на выбранную площадку сверху."""
    line(
        group,
        [cx, cy + 6, cx - 11, cy + 20, cx - 4, cy + 20,
         cx - 4, cy + 30, cx + 4, cy + 30, cx + 4, cy + 20,
         cx + 11, cy + 20, cx, cy + 6],
        color, 2.0,
    )


def draw_building(group, building: Building, t: float) -> None:
    """Постройка на площадке."""
    kind = building.kind
    x, y = building.x, building.y
    data = BUILD_TYPES[kind]
    flash = building.flash > 0

    if kind == "mine":
        pulse = 0.5 + 0.5 * math.sin(t * 2.6 + x * 0.02)
        circle(group, x, y + 6, 40, (1.0, 0.78, 0.16, 0.10 + pulse * 0.08))
        _shadow(group, x, y, 82, 32, 0.28)
        poly(
            group,
            [
                (x - 38, y + 4), (x - 32, y + 30), (x - 10, y + 44),
                (x + 22, y + 42), (x + 38, y + 20), (x + 31, y + 2),
            ],
            (0.50, 0.36, 0.15, 1),
        )
        poly(
            group,
            [
                (x - 28, y + 8), (x - 23, y + 28), (x - 6, y + 36),
                (x + 16, y + 32), (x + 26, y + 16), (x + 20, y + 5),
            ],
            GOLD_DARK,
        )
        poly(
            group,
            [
                (x - 18, y + 18), (x - 12, y + 33), (x + 6, y + 36),
                (x + 16, y + 22), (x + 2, y + 12),
            ],
            GOLD,
        )
        poly(
            group,
            [(x - 7, y + 23), (x - 3, y + 33), (x + 6, y + 30), (x + 3, y + 20)],
            GOLD_LIGHT,
        )
        rect(group, x - 28, y + 22, 5, 22, WOOD)
        rect(group, x + 23, y + 19, 5, 22, WOOD)
        rect(group, x - 30, y + 40, 28, 4, WOOD_LIGHT)
        circle(group, x + 34, y + 10, 5, GOLD_DARK)
        circle(group, x + 34, y + 11.5, 3.6, GOLD)
        _level_pips(group, x, y + 58, building.level, data["max_level"])

    elif kind == "tower":
        pulse = 0.5 + 0.5 * math.sin(t * 3.0 + x * 0.03)
        if building.cooldown > 0:
            circle(group, x, y + 52, 38, (1.0, 0.84, 0.32, 0.10 + pulse * 0.10))
        _shadow(group, x, y, 72, 28, 0.30)
        # Основание и ствол башни.
        poly(
            group,
            [(x - 30, y + 2), (x - 24, y + 20), (x + 24, y + 20), (x + 30, y + 2)],
            STONE_DARK,
        )
        rect(group, x - 21, y + 18, 42, 42, STONE_LIGHT)
        rect(group, x - 21, y + 18, 8, 42, STONE)
        rect(group, x + 13, y + 18, 8, 42, STONE)
        rect(group, x - 10, y + 22, 20, 26, (0.31, 0.34, 0.38, 1))
        # Зубцы.
        for offset in (-24, -9, 6, 21):
            rect(group, x + offset, y + 60, 12, 11, STONE_LIGHT)
        rect(group, x - 24, y + 58, 54, 4, STONE_DARK)
        # Флаг.
        rect(group, x + 1, y + 70, 3, 26, WOOD)
        poly(group, [(x + 4, y + 94), (x + 30, y + 86), (x + 4, y + 78)], BLUE_LIGHT)
        circle(group, x, y + 76, 3, GOLD_LIGHT)
        _level_pips(group, x, y + 104, building.level, data["max_level"])

    elif kind == "barracks":
        pulse = 0.5 + 0.5 * math.sin(t * 2.8 + x * 0.02)
        _shadow(group, x, y, 84, 32, 0.28)
        rect(group, x - 34, y + 2, 68, 16, STONE)
        rect(group, x - 28, y + 16, 56, 32, (0.66, 0.50, 0.33, 1))
        rect(group, x - 28, y + 16, 56, 5, WOOD_LIGHT)
        poly(
            group,
            [(x - 38, y + 46), (x - 20, y + 66), (x + 20, y + 66), (x + 38, y + 46)],
            GREEN,
        )
        poly(
            group,
            [(x - 20, y + 66), (x + 20, y + 66), (x + 7, y + 51), (x - 7, y + 51)],
            GREEN_LIGHT,
        )
        rect(group, x - 9, y + 16, 18, 30, (0.24, 0.16, 0.10, 1))
        circle(group, x + 5, y + 34, 1.8, GOLD)
        # Знамя.
        rect(group, x + 31, y + 40, 3, 42, WOOD)
        poly(group, [(x + 34, y + 80), (x + 56, y + 73), (x + 34, y + 66)], (0.24, 0.62, 0.40, 1))
        circle(group, x + 35, y + 73, 3, GOLD_LIGHT)
        _level_pips(group, x, y + 90, building.level, data["max_level"])

    else:  # totem
        pulse = 0.5 + 0.5 * math.sin(t * 3.4 + x * 0.02)
        aura = data["aura"][building.level - 1]
        ring(group, x, y + 4, aura, (0.62, 0.42, 0.92, 0.16 + pulse * 0.10), 2)
        ring(group, x, y + 4, aura * 0.55, (0.78, 0.60, 1.0, 0.14), 1.4)
        _shadow(group, x, y, 58, 24, 0.28)
        # Каменное основание.
        poly(
            group,
            [(x - 26, y + 2), (x - 20, y + 16), (x + 20, y + 16), (x + 26, y + 2)],
            STONE_DARK,
        )
        rect(group, x - 6, y + 14, 12, 54, WOOD)
        rect(group, x - 3, y + 14, 4, 52, WOOD_LIGHT)
        # Резные крылья тотема.
        poly(group, [(x - 6, y + 46), (x - 26, y + 58), (x - 22, y + 40)], (0.42, 0.24, 0.54, 1))
        poly(group, [(x + 6, y + 46), (x + 26, y + 58), (x + 22, y + 40)], (0.42, 0.24, 0.54, 1))
        # Кристалл.
        crystal_y = y + 78 + pulse * 1.5
        circle(group, x, crystal_y, 16, (0.70, 0.46, 1.0, 0.22))
        poly(
            group,
            [(x, crystal_y + 13), (x + 9, crystal_y), (x, crystal_y - 13), (x - 9, crystal_y)],
            (0.74, 0.54, 1.0, 1),
        )
        poly(
            group,
            [(x, crystal_y + 13), (x + 9, crystal_y), (x + 2, crystal_y - 2)],
            (0.92, 0.82, 1.0, 1),
        )
        for angle in (0.0, 2.1, 4.2):
            sparkle = 10 + pulse * 6
            circle(
                group,
                x + math.cos(t * 2 + angle) * sparkle,
                crystal_y + 6 + math.sin(t * 2.6 + angle) * 8,
                1.8,
                (0.90, 0.82, 1.0, 0.85),
            )
        _level_pips(group, x, y + 104, building.level, data["max_level"])

    if building.hp < building.max_hp:
        health_bar(
            group, x, y + 112, 54, building.hp / building.max_hp,
            (0.98, 0.72, 0.28, 1),
        )
    if flash:
        circle(group, x, y + 30, 42, (1, 1, 1, 0.22))


def draw_defender(group, defender: Defender, t: float) -> None:
    bob = math.sin(t * 11 + defender.phase * 3) * 1.3
    x, y = defender.x, defender.y
    _shadow(group, x, y - 1, 24, 8, 0.28)
    rect(group, x - 5, y + 1, 4, 10, (0.15, 0.20, 0.24, 1))
    rect(group, x + 2, y + 1, 4, 10, (0.15, 0.20, 0.24, 1))
    rounds(group, x - 9, y + 9 + bob, 18, 17, 5, (0.20, 0.44, 0.30, 1))
    rect(group, x - 8, y + 11 + bob, 16, 3, GOLD_DARK)
    circle(group, x, y + 29 + bob, 7, SKIN)
    rounds(group, x - 9, y + 30 + bob, 18, 8, 3, STONE_LIGHT)
    poly(group, [(x, y + 38 + bob), (x + 6, y + 45 + bob), (x, y + 50 + bob), (x - 6, y + 45 + bob)], GREEN_LIGHT)
    # Щит и меч.
    circle(group, x - 9, y + 19 + bob, 6.5, STONE_LIGHT)
    circle(group, x - 9, y + 19 + bob, 5, BLUE_LIGHT)
    rect(group, x + 7, y + 14 + bob, 2, 16, WOOD_LIGHT)
    if defender.hit_flash > 0:
        circle(group, x, y + 22, 15, (1, 1, 1, 0.25))
    if defender.hp < defender.max_hp:
        health_bar(group, x, y + 56, 24, defender.hp / defender.max_hp, GREEN_LIGHT)
