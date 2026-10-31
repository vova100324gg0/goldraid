"""Сущности игрового мира."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from ..core.config import ENEMY_TYPES, GOLD


@dataclass
class Hero:
    x: float
    y: float
    hp: float = 100.0
    max_hp: float = 100.0
    vx: float = 0.0
    vy: float = 0.0
    facing: float = 0.0
    invuln: float = 0.0
    attack_cd: float = 0.0
    bob: float = 0.0
    moving: bool = False
    carried: int = 0


@dataclass
class Coin:
    x: float
    y: float
    value: int
    phase: float = field(default_factory=lambda: random.random() * 6.28)


@dataclass
class Defender:
    x: float
    y: float
    home_x: float
    home_y: float
    hp: float
    max_hp: float
    damage: float
    home_slot: int = -1
    phase: float = field(default_factory=lambda: random.random() * 6.28)
    facing: float = 0.0
    attack_cd: float = field(default_factory=lambda: random.random() * 0.4)
    bob: float = 0.0
    hit_flash: float = 0.0


@dataclass
class Enemy:
    x: float
    y: float
    kind: str
    hp: float
    max_hp: float
    speed: float
    damage: float
    radius: float
    gold: int
    home_x: float
    home_y: float
    attack_cd: float = 0.0
    phase: float = field(default_factory=lambda: random.random() * 6.28)
    facing: float = 0.0
    wander_t: float = 0.0
    wander_angle: float = 0.0
    hit_flash: float = 0.0
    aggro: float = 0.0
    boss: bool = False
    armor: float = 0.0
    attack_range: float = 0.0
    heal: float = 0.0
    explode: float = 0.0
    elite: bool = False
    route: int = 0
    waypoint: int = 1
    support_cd: float = 1.0
    attack_delay: float = 1.2


@dataclass
class Building:
    kind: str
    slot: int
    x: float
    y: float
    level: int = 1
    hp: float = 100.0
    max_hp: float = 100.0
    cooldown: float = 0.0
    timer: float = 0.0
    flash: float = 0.0


@dataclass
class Effect:
    kind: str
    x: float
    y: float
    life: float
    t: float = 0.0
    radius: float = 24.0
    angle: float = 0.0
    color: tuple = GOLD
    x2: float = 0.0
    y2: float = 0.0


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    t: float = 0.0
    size: float = 3.0
    color: tuple = GOLD


@dataclass
class Mine:
    x: float
    y: float
    timer: float = 1.0


@dataclass
class Barracks:
    x: float
    y: float
    cooldown: float = 0.0


@dataclass
class Camp:
    x: float
    y: float


def make_enemy(kind: str, x: float, y: float, route: int = 0, waypoint: int = 1) -> Enemy:
    """Фабрика врагов: характеристики берутся из бестиария."""
    data = ENEMY_TYPES.get(kind, ENEMY_TYPES["grunt"])
    kind = kind if kind in ENEMY_TYPES else "grunt"
    return Enemy(
        x,
        y,
        kind,
        float(data["hp"]),
        float(data["hp"]),
        float(data["speed"]),
        float(data["damage"]),
        float(data["radius"]),
        int(data["gold"]),
        x,
        y,
        boss=bool(data.get("boss", False)),
        armor=float(data.get("armor", 0.0)),
        attack_range=float(data.get("range", 0.0)),
        heal=float(data.get("heal", 0.0)),
        explode=float(data.get("explode", 0.0)),
        route=route,
        waypoint=waypoint,
        attack_delay=1.7 if kind == "archer" else (1.5 if data.get("boss") else 1.2),
    )
