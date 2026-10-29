"""Отрисовка игрового мира."""

from __future__ import annotations

import math

from kivy.graphics import PopMatrix, PushMatrix, Scale, Translate
from kivy.metrics import dp

from .gfx import ring
from .sprites import (
    draw_building,
    draw_castle,
    draw_coin,
    draw_defender,
    draw_effect,
    draw_enemy,
    draw_hero,
    draw_joystick,
    draw_particle,
    draw_slot,
    draw_spawn_marker,
)


def draw_arena(arena) -> None:
    shake_x = arena.shake_x
    shake_y = arena.shake_y

    # Статичный фон уже лежит в отдельной группе. Двигаем только его transform.
    arena.bg_translate.x = -arena.cam_x + shake_x
    arena.bg_translate.y = -arena.cam_y + shake_y

    group = arena.fg_group
    group.clear()
    group.add(PushMatrix())
    group.add(Scale(dp(1), dp(1), 1))
    group.add(Translate(-arena.cam_x + shake_x, -arena.cam_y + shake_y, 0))

    base_x, base_y = arena.level.base_pos

    # Портал в начале каждой дороги.
    for route in arena.level.routes:
        draw_spawn_marker(group, route[0][0], route[0][1], arena.elapsed)

    ratio = arena.base_hp / max(1.0, arena.base_max_hp)
    draw_castle(group, arena.elapsed, 0, ratio, base_x, base_y)

    for coin in arena.pickups:
        draw_coin(group, coin, arena.elapsed)

    occupied = {building.slot for building in arena.buildings}
    for index, (x, y) in enumerate(arena.level.slots):
        if index in occupied:
            continue
        draw_slot(
            group,
            x,
            y,
            arena.elapsed,
            active=arena.build_mode is not None,
            affordable=(
                arena.build_mode is None
                or arena.gold >= arena.build_cost(arena.build_mode)
            ),
        )

    for building in arena.buildings:
        draw_building(group, building, arena.elapsed)

    for defender in arena.defenders:
        draw_defender(group, defender, arena.elapsed)

    for enemy in arena.enemies:
        draw_enemy(group, enemy, arena.elapsed)

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
        draw_effect(group, effect)
    for particle in arena.particles:
        draw_particle(group, particle)

    group.add(PopMatrix())

    if arena.joy_active:
        draw_joystick(group, arena.joy_origin, arena.joy_offset, dp(46))
