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

from .gfx import ring
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

    for enemy in arena.enemies:
        if visible(enemy.x, enemy.y):
            draw_enemy(group, enemy, arena.elapsed, detail=detail)

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

    for effect in arena.effects:
        if visible(effect.x, effect.y):
            draw_effect(group, effect)
    for particle in arena.particles:
        if visible(particle.x, particle.y):
            draw_particle(group, particle)

    group.add(PopMatrix())

    if arena.joy_active:
        draw_joystick(group, arena.joy_origin, arena.joy_offset, dp(46))