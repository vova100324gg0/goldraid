"""Отрисовка игрового мира.

Кадр собирается из трёх слоёв:

* ``bg_group``   — земля, дороги и декор: строится один раз на карту;
* ``slow_group`` — площадки, постройки, замок и порталы: пересобирается
  редко (~12 раз в секунду), потому что эти объекты почти не двигаются;
* ``fg_group``   — герой, враги, бойцы, золото и эффекты: пересобирается
  каждый кадр, но только то, что реально видно на экране.

Такое разделение снимает с каждого кадра сотни лишних инструкций Kivy:
на слабых телефонах именно их создание было главным тормозом.
"""

from __future__ import annotations

import math

from kivy.graphics import PopMatrix, PushMatrix, Scale, Translate
from kivy.metrics import dp

from ..core.config import HERO_ATTACK_RANGE
from .gfx import line, ring
from .sprites import (
    draw_coin,
    draw_defender,
    draw_effect,
    draw_enemy,
    draw_hero,
    draw_joystick,
    draw_particle,
)

# Сколько пикселей мира за пределами экрана ещё считаем видимыми.
CULL_MARGIN = 150.0

# Сколько врагов в кадре терпим перед переходом на упрощённый силуэт.
# Полный спрайт — около сорока инструкций Kivy; в большой орде именно их
# создание, а не математика боя, съедает кадр на слабых телефонах.
CROWD_THRESHOLD = 55


def draw_arena(arena) -> None:
    shake_x = arena.shake_x
    shake_y = arena.shake_y
    offset_x = -arena.cam_x + shake_x
    offset_y = -arena.cam_y + shake_y

    # Фон, «медленный» слой и передний план двигаются вместе с камерой.
    arena.bg_translate.x = offset_x
    arena.bg_translate.y = offset_y
    arena.slow_translate.x = offset_x
    arena.slow_translate.y = offset_y
    arena.fg_translate.x = offset_x
    arena.fg_translate.y = offset_y

    if arena.slow_dirty or arena.slow_timer <= 0.0:
        arena.rebuild_slow()

    view_w, view_h = arena._view_size()
    left = arena.cam_x - CULL_MARGIN
    bottom = arena.cam_y - CULL_MARGIN
    right = arena.cam_x + view_w + CULL_MARGIN
    top = arena.cam_y + view_h + CULL_MARGIN

    def visible(x: float, y: float) -> bool:
        return left <= x <= right and bottom <= y <= top

    group = arena.fg_group
    group.clear()
    group.add(PushMatrix())
    group.add(Scale(dp(1), dp(1), 1))
    group.add(arena.fg_translate)

    detail = not arena.low_detail

    for coin in arena.pickups:
        if visible(coin.x, coin.y):
            draw_coin(group, coin, arena.elapsed)

    for defender in arena.defenders:
        if visible(defender.x, defender.y):
            draw_defender(group, defender, arena.elapsed)

    # Если в кадре одновременно много врагов, рисуем упрощённые силуэты:
    # полный спрайт каждого перегружает слабые телефоны.
    visible_enemies = [
        enemy for enemy in arena.enemies if visible(enemy.x, enemy.y)
    ]
    crowd = len(visible_enemies) > CROWD_THRESHOLD
    for enemy in visible_enemies:
        draw_enemy(
            group, enemy, arena.elapsed, detail=detail, crowd=crowd
        )

    if arena.hero.hp > 0:
        draw_hero(group, arena.hero, arena.elapsed)
        if arena.rage_timer > 0:
            pulse = 0.5 + 0.5 * math.sin(arena.elapsed * 8)
            ring(
                group,
                arena.hero.x,
                arena.hero.y + 2,
                30 + pulse * 6,
                (1.0, 0.48, 0.20, 0.45 + pulse * 0.25),
                2,
            )

    # Понятная боёвка: показываем радиус удара героя и метку его цели.
    target = getattr(arena, "hero_target", None)
    if arena.hero.hp > 0 and target is not None and target in arena.enemies:
        swing = 1.0 if arena.hero.attack_anim > 0 else 0.0
        ring(
            group,
            arena.hero.x,
            arena.hero.y + 4,
            HERO_ATTACK_RANGE,
            (1.0, 0.86, 0.40, 0.12 + swing * 0.14),
            1.5,
        )
        pulse = 0.5 + 0.5 * math.sin(arena.elapsed * 7)
        ring(
            group,
            target.x,
            target.y + target.radius * 0.4,
            target.radius + 12 + pulse * 4 + swing * 4,
            (1.0, 0.34, 0.28, 0.85),
            2.5,
        )
        tip_y = target.y + target.radius * 2.2 + dp(18)
        line(
            group,
            [
                target.x - 9, tip_y + 11,
                target.x, tip_y,
                target.x + 9, tip_y + 11,
            ],
            (1.0, 0.44, 0.34, 0.95),
            3.0,
        )

    for effect in arena.effects:
        if visible(effect.x, effect.y):
            draw_effect(group, effect)
    for particle in arena.particles:
        if visible(particle.x, particle.y):
            draw_particle(group, particle)

    group.add(PopMatrix())

    if arena.joy_active:
        draw_joystick(group, arena.joy_origin, arena.joy_offset, dp(46))