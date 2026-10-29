"""Игровая логика: защита базы, строительство и волны врагов."""

from __future__ import annotations

import math
import random

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import PopMatrix, PushMatrix, Scale, Translate
from kivy.graphics.instructions import InstructionGroup
from kivy.metrics import dp
from kivy.uix.widget import Widget

from .background import build_background
from .config import (
    BUILD_TYPES,
    ENEMY_TYPES,
    GLOBAL_UPGRADES,
    GOLD_PILE_COUNT,
    GOLD_PILE_RANGE,
    GOLD_PILE_RESPAWN,
    GOLD_PILE_VALUE,
    HERO_ATTACK_COOLDOWN,
    HERO_ATTACK_DAMAGE,
    HERO_ATTACK_RANGE,
    HERO_REGEN,
    HERO_RESPAWN,
    HERO_SPEED,
    SHOP_ITEMS,
    WAVE_REWARD,
    WAVE_REWARD_STEP,
)
from .entities import (
    Building,
    Coin,
    Defender,
    Effect,
    Enemy,
    Hero,
    Particle,
    make_enemy,
)
from .levels import LEVELS, Level
from .renderer import draw_arena
from .util import clamp, dist, normalize

_KEYMAP = {
    119: "w", 87: "w", 1094: "w", 1062: "w",
    97: "a", 65: "a", 1092: "a", 1060: "a",
    115: "s", 83: "s", 1099: "s", 1067: "s",
    100: "d", 68: "d", 1074: "d", 1042: "d",
    273: "up", 274: "down", 275: "right", 276: "left",
}


class Arena(Widget):
    """Виджет с картой, героем, постройками и игровым циклом."""

    def __init__(self, on_toast=None, on_end=None, on_building=None, **kwargs):
        super().__init__(**kwargs)
        self.on_toast = on_toast or (lambda *args, **kwargs: None)
        self.on_end = on_end or (lambda *args, **kwargs: None)
        self.on_building = on_building or (lambda *args, **kwargs: None)

        self.bg_group = InstructionGroup()
        self.fg_group = InstructionGroup()
        self.canvas.add(self.bg_group)
        self.canvas.add(self.fg_group)

        self.level: Level = LEVELS[0]
        self.level_index = 0
        self.world_w = self.level.world_w
        self.world_h = self.level.world_h
        self.hero_bounds = (40.0, 40.0, self.world_w - 40.0, self.world_h - 40.0)
        self.bg_translate = Translate(0, 0)
        self._rebuild_background()

        self.running = False
        self.paused = False
        self.ended = False
        self.joy_active = False
        self.joy_origin = (0.0, 0.0)
        self.joy_offset = (0.0, 0.0)
        self._joy_uid = None
        self._joy_input = (0.0, 0.0)
        self._keys = set()
        self._reset_state()
        self.bind(size=self._on_size, pos=self._on_size)
        # Клавиатура для ПК: WASD и стрелки.
        Window.bind(on_key_down=self.on_key_down, on_key_up=self.on_key_up)
        Clock.schedule_interval(self._tick, 1 / 60)

    # ------------------------------------------------------------------
    # Состояние
    # ------------------------------------------------------------------
    def load_level(self, level: Level, index: int = 0) -> None:
        """Переключает карту: новый фон, площадки и баланс."""
        self.level = level
        self.level_index = index
        self.world_w = level.world_w
        self.world_h = level.world_h
        self.hero_bounds = (40.0, 40.0, self.world_w - 40.0, self.world_h - 40.0)
        self._rebuild_background()
        self._reset_state()

    def _rebuild_background(self) -> None:
        self.bg_group.clear()
        self.bg_translate = Translate(0, 0)
        self.bg_group.add(PushMatrix())
        self.bg_group.add(Scale(dp(1), dp(1), 1))
        self.bg_group.add(self.bg_translate)
        build_background(self.bg_group, self.level)
        self.bg_group.add(PopMatrix())

    def _reset_state(self) -> None:
        level = self.level
        self.elapsed = 0.0
        self.gold = level.start_gold
        self.gold_earned = 0
        self.base_max_hp = float(level.base_hp)
        self.base_hp = float(level.base_hp)
        self.kills = 0
        self.upgrades = {key: 0 for key in GLOBAL_UPGRADES}
        self.buildings: list[Building] = []
        self.defenders: list[Defender] = []
        self.enemies: list[Enemy] = []
        self.effects: list[Effect] = []
        self.particles: list[Particle] = []
        self.pickups: list[Coin] = []
        self.pickup_timer = GOLD_PILE_RESPAWN
        self.rage_timer = 0.0
        self.build_mode = None

        self.wave = 1
        self.wave_state = "prep"
        self.wave_timer = level.first_delay
        self.pending: list[str] = []
        self.next_units: list[str] = self._wave_units(1)
        self.spawn_timer = 0.0
        self._base_notice_cd = 0.0

        self.hero = Hero(level.base_pos[0], level.base_pos[1] - 88)
        for _ in range(GOLD_PILE_COUNT):
            self._spawn_pickup()
        self.respawn_timer = 0.0
        self._shake = 0.0
        self.shake_x = 0.0
        self.shake_y = 0.0
        self.cam_x = 0.0
        self.cam_y = 0.0
        self._snap_camera()
        self._draw()

    def start_new(self) -> None:
        self._reset_state()
        self.running = True
        self.paused = False
        self.ended = False
        self._clear_input()
        self._draw()

    def stop(self) -> None:
        self.running = False
        self.paused = False
        self._clear_input()

    def pause(self) -> None:
        self.paused = True
        self._clear_input()
        self._shake = 0.0
        self.shake_x = self.shake_y = 0.0
        self._draw()

    def resume(self) -> None:
        if not self.ended:
            self.paused = False
            self._clear_input()

    def stats(self) -> dict:
        base_x, base_y = self.level.base_pos
        base_distance = dist(self.hero.x, self.hero.y, base_x, base_y)
        dx = base_x - self.hero.x
        dy = base_y - self.hero.y
        if abs(dx) > abs(dy):
            base_dir = "восточнее" if dx > 0 else "западнее"
        else:
            base_dir = "севернее" if dy > 0 else "южнее"
        boss = self._strongest_boss()
        return {
            "base_hp": max(0, self.base_hp),
            "base_max_hp": self.base_max_hp,
            "gold": int(self.gold),
            "gold_earned": int(self.gold_earned),
            "wave": self.wave,
            "total_waves": self.level.waves,
            "level_name": self.level.name,
            "level_index": self.level_index,
            "wave_state": self.wave_state,
            "wave_timer": max(0.0, self.wave_timer),
            "enemies": len(self.enemies) + len(self.pending),
            "kills": self.kills,
            "hero_hp": max(0.0, self.hero.hp),
            "hero_max_hp": self.hero.max_hp,
            "respawn": max(0.0, self.respawn_timer),
            "defenders": len(self.defenders),
            "buildings": len(self.buildings),
            "mines": sum(1 for b in self.buildings if b.kind == "mine"),
            "towers": sum(1 for b in self.buildings if b.kind == "tower"),
            "barracks": sum(1 for b in self.buildings if b.kind == "barracks"),
            "totems": sum(1 for b in self.buildings if b.kind == "totem"),
            "upgrades": dict(self.upgrades),
            "base_distance": int(base_distance),
            "base_dir": base_dir,
            "rage": max(0.0, self.rage_timer),
            "pickups": len(self.pickups),
            "time": self.elapsed,
            "preview": self._preview_text(),
            "boss_hp": boss.hp if boss else 0.0,
            "boss_max": boss.max_hp if boss else 0.0,
            "boss_name": ENEMY_TYPES.get(boss.kind, {}).get("name", "") if boss else "",
            "boss": boss is not None,
        }

    def _strongest_boss(self) -> Enemy | None:
        best = None
        for enemy in self.enemies:
            if not enemy.boss:
                continue
            if best is None or enemy.max_hp > best.max_hp:
                best = enemy
        return best

    def _preview_text(self) -> str:
        units = self.next_units if self.wave_state == "prep" else self.pending
        if not units:
            return ""
        count = len(units)
        labels = []
        if "boss" in units:
            labels.append("босс")
        elif "chief" in units:
            labels.append("вожак")
        kinds = {ENEMY_TYPES.get(kind, {}).get("name", "") for kind in units}
        if "Шаман" in kinds:
            labels.append("шаманы")
        if "Лучник" in kinds:
            labels.append("лучники")
        extra = f" · {', '.join(labels)}" if labels else ""
        return f"{count} врагов{extra}"

    # ------------------------------------------------------------------
    # Строительство и улучшения
    # ------------------------------------------------------------------
    def build_cost(self, kind: str) -> int:
        return int(BUILD_TYPES[kind]["cost"])

    def slot_free(self, index: int) -> bool:
        return not any(b.slot == index for b in self.buildings)

    def build(self, index: int, kind: str) -> tuple[bool, str]:
        if kind not in BUILD_TYPES:
            return False, "Неизвестная постройка"
        if index < 0 or index >= len(self.level.slots):
            return False, "Неверная площадка"
        if not self.slot_free(index):
            return False, "Площадка занята"
        data = BUILD_TYPES[kind]
        cost = self.build_cost(kind)
        if self.gold < cost:
            return False, "Не хватает золота"
        self.gold -= cost
        x, y = self.level.slots[index]
        hp = float(data["hp"][0])
        building = Building(
            kind=kind,
            slot=index,
            x=x,
            y=y,
            level=1,
            hp=hp,
            max_hp=hp,
            cooldown=0.0,
            timer=float(data["period"][0]) if kind == "mine" else 0.0,
        )
        self.buildings.append(building)
        self.build_mode = None
        self._add_ring(x, y + 16, 32, (1.0, 0.86, 0.30, 1))
        self._add_particles(x, y + 26, 10, (1.0, 0.86, 0.36, 1), speed=90)
        if kind == "barracks":
            self._spawn_defender(building)
        return True, f"{data['name']} построена"

    def building_upgrade_cost(self, building: Building) -> int:
        data = BUILD_TYPES[building.kind]
        return int(data["upgrade_cost"] * building.level)

    def building_info(self, building: Building) -> dict:
        data = BUILD_TYPES[building.kind]
        level = building.level
        maxed = level >= data["max_level"]
        cost = 0 if maxed else self.building_upgrade_cost(building)
        if building.kind == "mine":
            effect = (
                f"{data['income'][level - 1]} золота "
                f"каждые {data['period'][level - 1]:.1f} с"
            )
            nxt = ""
            if not maxed:
                nxt = (
                    f"далее: {data['income'][level]} за "
                    f"{data['period'][level]:.1f} с"
                )
        elif building.kind == "tower":
            effect = (
                f"Урон {data['damage'][level - 1]} · "
                f"дальность {data['range'][level - 1]}"
            )
            nxt = ""
            if not maxed:
                nxt = (
                    f"далее: урон {data['damage'][level]}, "
                    f"дальность {data['range'][level]}"
                )
        elif building.kind == "totem":
            effect = (
                f"+{int(data['boost'][level - 1] * 100)}% урона в радиусе "
                f"{data['aura'][level - 1]}"
            )
            nxt = ""
            if not maxed:
                nxt = (
                    f"далее: +{int(data['boost'][level] * 100)}% в радиусе "
                    f"{data['aura'][level]}"
                )
        else:
            effect = (
                f"Бойцов {data['squad'][level - 1] + self.upgrades['squad']} · "
                f"урон {data['defender_damage'][level - 1]}"
            )
            nxt = ""
            if not maxed:
                nxt = (
                    f"далее: {data['squad'][level] + self.upgrades['squad']} бойцов, "
                    f"урон {data['defender_damage'][level]}"
                )
        return {
            "kind": building.kind,
            "name": data["name"],
            "level": level,
            "max_level": data["max_level"],
            "maxed": maxed,
            "cost": cost,
            "effect": effect,
            "next": nxt,
            "hp": max(0.0, building.hp),
            "max_hp": building.max_hp,
        }

    def upgrade_building(self, building: Building) -> tuple[bool, str]:
        if building not in self.buildings:
            return False, "Постройка разрушена"
        data = BUILD_TYPES[building.kind]
        if building.level >= data["max_level"]:
            return False, "Максимальный уровень"
        cost = self.building_upgrade_cost(building)
        if self.gold < cost:
            return False, "Не хватает золота"
        self.gold -= cost
        building.level += 1
        old_max = building.max_hp
        building.max_hp = float(data["hp"][building.level - 1])
        building.hp = min(building.max_hp, building.hp + (building.max_hp - old_max))
        if building.kind == "barracks":
            self._spawn_defender(building)
        self._add_ring(building.x, building.y + 30, 30, (1.0, 0.86, 0.30, 1))
        self._add_particles(building.x, building.y + 40, 8, (1.0, 0.88, 0.40, 1), speed=70)
        return True, f"{data['name']} улучшена до ур. {building.level}"

    def upgrade_cost(self, key: str) -> int:
        data = GLOBAL_UPGRADES[key]
        return int(data["base_cost"] * (1 + 0.8 * self.upgrades[key]))

    def upgrade_maxed(self, key: str) -> bool:
        return self.upgrades[key] >= GLOBAL_UPGRADES[key]["max_level"]

    def buy_upgrade(self, key: str) -> tuple[bool, str]:
        if key not in GLOBAL_UPGRADES:
            return False, "Неизвестное улучшение"
        if self.upgrade_maxed(key):
            return False, "Максимальный уровень"
        cost = self.upgrade_cost(key)
        if self.gold < cost:
            return False, "Не хватает золота"
        self.gold -= cost
        self.upgrades[key] += 1
        if key == "armor":
            self.hero.max_hp += 30
            self.hero.hp = min(self.hero.max_hp, self.hero.hp + 30)
        elif key == "fortify":
            self.base_max_hp += 120
            self.base_hp = min(self.base_max_hp, self.base_hp + 120)
        elif key == "squad":
            for building in self.buildings:
                if building.kind == "barracks":
                    self._spawn_defender(building)
        self._draw()
        return True, f"{GLOBAL_UPGRADES[key]['name']} улучшен"

    def set_build_mode(self, kind: str | None) -> str | None:
        """Включает/выключает режим строительства. Возвращает активный тип."""
        self.build_mode = None if self.build_mode == kind else kind
        self._draw()
        return self.build_mode

    # ------------------------------------------------------------------
    # Магазин
    # ------------------------------------------------------------------
    def item_available(self, key: str) -> tuple[bool, str]:
        if key not in SHOP_ITEMS:
            return False, "Неизвестный товар"
        data = SHOP_ITEMS[key]
        if self.gold < data["cost"]:
            return False, "Не хватает золота"
        if key == "heal":
            if self.hero.hp <= 0:
                return False, "Герой возрождается"
            if self.hero.hp >= self.hero.max_hp:
                return False, "Герой полон сил"
        elif key == "repair":
            if self.base_hp >= self.base_max_hp:
                return False, "База не повреждена"
        elif key == "guard":
            if not any(b.kind == "barracks" for b in self.buildings):
                return False, "Сначала построй казармы"
        return True, ""

    def buy_item(self, key: str) -> tuple[bool, str]:
        ok, reason = self.item_available(key)
        if not ok:
            return False, reason
        data = SHOP_ITEMS[key]
        self.gold -= data["cost"]
        if key == "heal":
            amount = self.hero.max_hp * 0.5
            self.hero.hp = min(self.hero.max_hp, self.hero.hp + amount)
            self._add_ring(self.hero.x, self.hero.y + 20, 26, (0.40, 0.95, 0.55, 1))
            self._add_particles(self.hero.x, self.hero.y + 26, 8, (0.45, 1.0, 0.60, 1), speed=70)
        elif key == "repair":
            self.base_hp = min(self.base_max_hp, self.base_hp + 180)
            bx, by = self.level.base_pos
            self._add_ring(bx, by + 10, 70, (0.45, 0.80, 1.0, 1))
            self._add_particles(bx, by - 20, 10, (0.55, 0.85, 1.0, 1), speed=70)
        elif key == "rage":
            self.rage_timer = 20.0
            self._add_ring(self.hero.x, self.hero.y + 20, 34, (1.0, 0.55, 0.24, 1))
            self._add_particles(self.hero.x, self.hero.y + 26, 10, (1.0, 0.62, 0.26, 1), speed=95)
        elif key == "guard":
            for building in self.buildings:
                if building.kind == "barracks":
                    self._spawn_defender(building)
                    break
        self._draw()
        return True, f"Куплено: {data['name']}"

    # ------------------------------------------------------------------
    # Ввод
    # ------------------------------------------------------------------
    def _world_at(self, x: float, y: float) -> tuple[float, float]:
        return (
            (x - self.x) / dp(1) + self.cam_x,
            (y - self.y) / dp(1) + self.cam_y,
        )

    def on_touch_down(self, touch):
        if not self.running or self.paused or self.ended:
            return False
        if not self.collide_point(*touch.pos):
            return False

        wx, wy = self._world_at(touch.x, touch.y)

        for building in self.buildings:
            if dist(wx, wy, building.x, building.y) <= 54:
                self.on_building(building, self.building_info(building))
                return True

        for index, (sx, sy) in enumerate(self.level.slots):
            if dist(wx, wy, sx, sy) > 50 or not self.slot_free(index):
                continue
            if self.build_mode:
                ok, message = self.build(index, self.build_mode)
                self.on_toast(message, "gold" if ok else "bad")
            else:
                self.on_toast("Выбери постройку на нижней панели", "info")
            return True

        self._joy_uid = touch.uid
        self.joy_origin = (touch.x, touch.y)
        self.joy_offset = (0.0, 0.0)
        self.joy_active = True
        self._joy_input = (0.0, 0.0)
        touch.grab(self)
        return True

    def on_touch_move(self, touch):
        if self._joy_uid != touch.uid or not self.joy_active:
            return False
        radius = dp(46)
        dx = touch.x - self.joy_origin[0]
        dy = touch.y - self.joy_origin[1]
        length = math.hypot(dx, dy)
        if length > radius:
            dx = dx / length * radius
            dy = dy / length * radius
        self.joy_offset = (dx, dy)
        self._joy_input = (dx / radius, dy / radius)
        return True

    def on_touch_up(self, touch):
        if self._joy_uid != touch.uid:
            return False
        self._joy_uid = None
        self.joy_active = False
        self.joy_offset = (0.0, 0.0)
        self._joy_input = (0.0, 0.0)
        if touch.grab_current is self:
            touch.ungrab(self)
        return True

    def on_key_down(self, window, key, *args):
        if key == 27:
            return False
        if not self.running or self.paused or self.ended:
            return False
        name = _KEYMAP.get(key)
        if name:
            self._keys.add(name)
            return True
        return False

    def on_key_up(self, window, key, *args):
        name = _KEYMAP.get(key)
        if name:
            self._keys.discard(name)
            return True
        return False

    def _clear_input(self) -> None:
        self._keys.clear()
        self._joy_input = (0.0, 0.0)
        self.joy_active = False
        self.joy_offset = (0.0, 0.0)
        self._joy_uid = None

    def _read_input(self) -> tuple[float, float]:
        if self.joy_active and math.hypot(*self._joy_input) > 0.04:
            return self._joy_input
        keys = self._keys
        ix = (1 if ("right" in keys or "d" in keys) else 0) - (
            1 if ("left" in keys or "a" in keys) else 0
        )
        iy = (1 if ("up" in keys or "w" in keys) else 0) - (
            1 if ("down" in keys or "s" in keys) else 0
        )
        if ix or iy:
            length = math.hypot(ix, iy)
            return ix / length, iy / length
        return 0.0, 0.0

    # ------------------------------------------------------------------
    # Главный цикл
    # ------------------------------------------------------------------
    def _tick(self, dt: float) -> None:
        if not self.running or self.paused or self.ended:
            return
        dt = min(dt, 0.05)
        self.elapsed += dt
        self._base_notice_cd = max(0.0, self._base_notice_cd - dt)
        self.rage_timer = max(0.0, self.rage_timer - dt)

        self._update_hero(dt)
        self._update_defenders(dt)
        self._update_towers(dt)
        self._update_mines(dt)
        self._update_totems(dt)
        self._update_barracks(dt)
        self._update_pickups(dt)
        self._update_enemies(dt)
        self._update_waves(dt)
        self._update_effects(dt)
        self._update_shake(dt)
        self._update_camera(dt)
        self._draw()

    def _update_hero(self, dt: float) -> None:
        hero = self.hero
        if hero.hp <= 0:
            self.respawn_timer -= dt
            if self.respawn_timer <= 0:
                self.respawn_timer = 0.0
                hero.hp = hero.max_hp
                hero.x, hero.y = self.level.base_pos[0], self.level.base_pos[1] - 88
                hero.vx = hero.vy = 0.0
                hero.invuln = 2.0
                self.on_toast("Герой вернулся в бой", "blue")
            return

        hero.invuln = max(0.0, hero.invuln - dt)
        hero.attack_cd -= dt
        hero.hp = min(hero.max_hp, hero.hp + HERO_REGEN * dt)
        ix, iy = self._read_input()
        speed = HERO_SPEED
        if ix or iy:
            hero.vx += (ix * speed - hero.vx) * min(1.0, dt * 14)
            hero.vy += (iy * speed - hero.vy) * min(1.0, dt * 14)
        else:
            damping = max(0.0, 1.0 - dt * 11)
            hero.vx *= damping
            hero.vy *= damping
        min_x, min_y, max_x, max_y = self.hero_bounds
        hero.x = clamp(hero.x + hero.vx * dt, min_x, max_x)
        hero.y = clamp(hero.y + hero.vy * dt, min_y, max_y)
        hero.moving = math.hypot(hero.vx, hero.vy) > 12
        if hero.moving:
            hero.facing = math.atan2(hero.vy, hero.vx)

        if hero.attack_cd <= 0:
            target = self._nearest_enemy(hero.x, hero.y, HERO_ATTACK_RANGE)
            if target:
                damage = HERO_ATTACK_DAMAGE + self.upgrades["blade"] * 7
                if self.rage_timer > 0:
                    damage *= 1.6
                self._damage_enemy(target, damage, hero.x, hero.y)
                hero.attack_cd = HERO_ATTACK_COOLDOWN
                self._add_slash(hero.x, hero.y, target)

    def _update_defenders(self, dt: float) -> None:
        for defender in list(self.defenders):
            defender.hit_flash = max(0.0, defender.hit_flash - dt)
            defender.attack_cd -= dt
            defender.bob += dt
            target = self._defender_target(defender)
            if target is not None:
                dx = target.x - defender.x
                dy = target.y - defender.y
                length = math.hypot(dx, dy) or 1.0
                defender.facing = math.atan2(dy, dx)
                if length > 44:
                    step = min(length - 40, 165 * dt)
                    defender.x += dx / length * step
                    defender.y += dy / length * step
                elif defender.attack_cd <= 0:
                    damage = defender.damage * (
                        1 + self._totem_boost(defender.x, defender.y)
                    )
                    self._damage_enemy(target, damage, defender.x, defender.y)
                    defender.attack_cd = 0.72
                    self._add_slash(defender.x, defender.y, target)
                continue

            dx = defender.home_x - defender.x
            dy = defender.home_y - defender.y
            length = math.hypot(dx, dy)
            if length > 18:
                step = min(length, 120 * dt)
                defender.x += dx / length * step
                defender.y += dy / length * step
                defender.facing = math.atan2(dy, dx)

    def _defender_target(self, defender: Defender):
        best = None
        best_d = 250.0
        bx, by = self.level.base_pos
        for enemy in self.enemies:
            if dist(enemy.x, enemy.y, bx, by) > 560:
                continue
            d = dist(enemy.x, enemy.y, defender.x, defender.y)
            if d < best_d:
                best_d = d
                best = enemy
        return best

    def _update_towers(self, dt: float) -> None:
        for building in self.buildings:
            if building.kind != "tower":
                continue
            building.cooldown = max(0.0, building.cooldown - dt)
            building.flash = max(0.0, building.flash - dt)
            if building.cooldown > 0:
                continue
            data = BUILD_TYPES["tower"]
            level = building.level - 1
            target = self._nearest_enemy(
                building.x, building.y, data["range"][level]
            )
            if target is None:
                continue
            damage = data["damage"][level] * (
                1 + self._totem_boost(building.x, building.y)
            )
            self._damage_enemy(target, damage, building.x, building.y, aggro=False)
            building.cooldown = data["cooldown"][level]
            self.effects.append(
                Effect(
                    "bolt",
                    building.x,
                    building.y + 62,
                    0.18,
                    color=(1.0, 0.88, 0.42, 1),
                    x2=target.x,
                    y2=target.y + 24,
                )
            )

    def _totem_boost(self, x: float, y: float) -> float:
        """Максимальный бонус урона от тотемов рядом с точкой."""
        boost = 0.0
        for building in self.buildings:
            if building.kind != "totem":
                continue
            data = BUILD_TYPES["totem"]
            level = building.level - 1
            if dist(x, y, building.x, building.y) <= data["aura"][level]:
                boost = max(boost, data["boost"][level])
        return boost

    def _update_mines(self, dt: float) -> None:
        for building in self.buildings:
            if building.kind != "mine":
                continue
            building.flash = max(0.0, building.flash - dt)
            building.timer -= dt
            if building.timer > 0:
                continue
            data = BUILD_TYPES["mine"]
            level = building.level - 1
            amount = data["income"][level]
            self.gold += amount
            self.gold_earned += amount
            building.timer = data["period"][level]
            self._add_ring(building.x, building.y + 24, 14, (1.0, 0.84, 0.28, 1))
            self._add_particles(
                building.x, building.y + 30, 3, (1.0, 0.86, 0.32, 1), speed=45
            )

    def _update_totems(self, dt: float) -> None:
        for building in self.buildings:
            if building.kind == "totem":
                building.flash = max(0.0, building.flash - dt)

    def _update_barracks(self, dt: float) -> None:
        for building in self.buildings:
            if building.kind != "barracks":
                continue
            building.flash = max(0.0, building.flash - dt)
            building.cooldown = max(0.0, building.cooldown - dt)
            data = BUILD_TYPES["barracks"]
            level = building.level - 1
            wanted = data["squad"][level] + self.upgrades["squad"]
            owned = sum(1 for d in self.defenders if d.home_slot == building.slot)
            if owned >= wanted or building.cooldown > 0:
                continue
            self._spawn_defender(building)
            building.cooldown = data["spawn"][level]

    # ------------------------------------------------------------------
    # Золото на карте
    # ------------------------------------------------------------------
    def _spawn_pickup(self) -> None:
        used = {(round(p.x), round(p.y)) for p in self.pickups}
        free = [
            spot
            for spot in self.level.gold_spots
            if (round(spot[0]), round(spot[1])) not in used
        ]
        if not free:
            return
        x, y = random.choice(free)
        value = random.randint(GOLD_PILE_VALUE[0], GOLD_PILE_VALUE[1])
        self.pickups.append(Coin(x, y, value))

    def _update_pickups(self, dt: float) -> None:
        if self.hero.hp > 0:
            for coin in list(self.pickups):
                if dist(self.hero.x, self.hero.y, coin.x, coin.y) > GOLD_PILE_RANGE:
                    continue
                self.pickups.remove(coin)
                self.gold += coin.value
                self.gold_earned += coin.value
                self._add_ring(coin.x, coin.y, 18, (1.0, 0.86, 0.32, 1))
                self._add_particles(coin.x, coin.y + 6, 6, (1.0, 0.88, 0.36, 1), speed=70)
                self.on_toast(f"+{coin.value} золота", "gold")
        self.pickup_timer -= dt
        if self.pickup_timer > 0 or len(self.pickups) >= GOLD_PILE_COUNT:
            return
        self.pickup_timer = GOLD_PILE_RESPAWN
        self._spawn_pickup()

    def _update_enemies(self, dt: float) -> None:
        for enemy in list(self.enemies):
            if enemy not in self.enemies:
                continue
            enemy.phase += dt
            enemy.attack_cd -= dt
            enemy.support_cd -= dt
            enemy.hit_flash = max(0.0, enemy.hit_flash - dt)
            enemy.aggro = max(0.0, enemy.aggro - dt)

            # Шаман лечит соседей и не рвётся в бой.
            if enemy.heal > 0:
                if enemy.support_cd <= 0:
                    self._shaman_heal(enemy)
                    enemy.support_cd = 1.3

            target = self._combat_target(enemy)
            if target is not None:
                tx, ty, reach, kind, obj = target
                dx = tx - enemy.x
                dy = ty - enemy.y
                length = math.hypot(dx, dy) or 1.0
                enemy.facing = math.atan2(dy, dx)
                if length <= reach:
                    if enemy.attack_cd <= 0:
                        self._enemy_attack(enemy, kind, obj, tx, ty)
                        enemy.attack_cd = enemy.attack_delay
                    continue
                mx, my = dx / length, dy / length
            else:
                wx, wy = self._route_point(enemy)
                dx = wx - enemy.x
                dy = wy - enemy.y
                length = math.hypot(dx, dy) or 1.0
                if length < 10:
                    continue
                enemy.facing = math.atan2(dy, dx)
                mx, my = dx / length, dy / length

            # Мягкое расталкивание толпы.
            for other in self.enemies:
                if other is enemy:
                    continue
                ox = enemy.x - other.x
                oy = enemy.y - other.y
                od = math.hypot(ox, oy)
                minimum = enemy.radius + other.radius + 2
                if 0 < od < minimum:
                    push = (minimum - od) / minimum * 55 * dt
                    mx += ox / od * push
                    my += oy / od * push
            enemy.x = clamp(enemy.x + mx * enemy.speed * dt, 20, self.world_w - 20)
            enemy.y = clamp(enemy.y + my * enemy.speed * dt, 20, self.world_h - 20)

    def _route_point(self, enemy: Enemy) -> tuple[float, float]:
        """Точка на дороге, к которой идёт враг."""
        routes = self.level.routes
        if not routes:
            return self.level.base_pos
        route = routes[enemy.route % len(routes)]
        while enemy.waypoint < len(route):
            wx, wy = route[enemy.waypoint]
            if dist(enemy.x, enemy.y, wx, wy) > 44:
                return wx, wy
            enemy.waypoint += 1
        return self.level.base_pos

    def _shaman_heal(self, enemy: Enemy) -> None:
        healed = False
        for other in self.enemies:
            if other is enemy or other.hp >= other.max_hp:
                continue
            if dist(enemy.x, enemy.y, other.x, other.y) > 175:
                continue
            other.hp = min(other.max_hp, other.hp + enemy.heal)
            healed = True
        if healed:
            self._add_ring(enemy.x, enemy.y + 10, 46, (0.58, 0.92, 0.46, 0.45))

    def _combat_target(self, enemy: Enemy):
        """Ближайшая цель рядом или None — тогда враг идёт по дороге."""
        bx, by = self.level.base_pos
        best = None
        best_d = 1e9
        base_reach = 128.0 + enemy.radius * 0.5

        base_d = dist(enemy.x, enemy.y, bx, by)
        if base_d <= base_reach:
            best = (bx, by, base_reach, "base", None)
            best_d = base_d

        if self.hero.hp > 0:
            hero_d = dist(enemy.x, enemy.y, self.hero.x, self.hero.y)
            hero_reach = 34.0 + enemy.radius * 0.3
            if enemy.attack_range > 0:
                hero_reach = enemy.attack_range * 0.8
            if enemy.aggro > 0:
                if hero_d < 320 and hero_d < best_d:
                    best = (self.hero.x, self.hero.y, hero_reach, "hero", self.hero)
                    best_d = hero_d
            elif hero_d < 70 + enemy.radius and hero_d < best_d:
                best = (self.hero.x, self.hero.y, hero_reach, "hero", self.hero)
                best_d = hero_d

        for defender in self.defenders:
            d = dist(enemy.x, enemy.y, defender.x, defender.y)
            reach = 34.0 + enemy.radius * 0.3
            if enemy.attack_range > 0:
                reach = max(reach, enemy.attack_range)
            if d < 110 + enemy.radius and d < best_d:
                best_d = d
                best = (defender.x, defender.y, reach, "defender", defender)

        for building in self.buildings:
            d = dist(enemy.x, enemy.y, building.x, building.y)
            reach = 48.0 + enemy.radius * 0.3
            if enemy.attack_range > 0:
                reach = max(reach, enemy.attack_range)
            if d < 90 + enemy.radius and d < best_d:
                best_d = d
                best = (building.x, building.y, reach, "building", building)

        return best

    def _enemy_attack(self, enemy: Enemy, kind: str, obj, tx: float = 0.0, ty: float = 0.0) -> None:
        if enemy.attack_range > 0:
            self.effects.append(
                Effect(
                    "bolt",
                    enemy.x,
                    enemy.y + 26,
                    0.16,
                    color=(1.0, 0.58, 0.30, 1),
                    x2=tx,
                    y2=ty + 16,
                )
            )
        if kind == "base":
            self._damage_base(enemy.damage)
        elif kind == "building":
            if obj in self.buildings:
                self._damage_building(obj, enemy.damage)
        elif kind == "defender":
            if obj in self.defenders:
                self._damage_defender(obj, enemy.damage)
        elif kind == "hero":
            self._damage_hero(enemy)

    # ------------------------------------------------------------------
    # Волны
    # ------------------------------------------------------------------
    def _wave_units(self, wave: int) -> list[str]:
        """Состав волны: чем дальше, тем больше новых видов и вожаков."""
        total = self.level.waves
        count = 4 + wave + max(0, wave - 6)
        if wave == total:
            count += 3
        units: list[str] = []
        for _ in range(count):
            roll = random.random()
            if wave >= 9 and roll < 0.10:
                units.append("bomber")
            elif wave >= 7 and roll < 0.22:
                units.append("shaman")
            elif wave >= 5 and roll < 0.36:
                units.append("shield")
            elif wave >= 4 and roll < 0.54:
                units.append("archer")
            elif wave >= 3 and roll < 0.72:
                units.append("brute")
            elif wave >= 2 and roll < 0.88:
                units.append("runner")
            else:
                units.append("grunt")
        # Каждую чётную волну ведёт вожак. На последней волне его
        # заменяет большой босс, чтобы не было двойного пика.
        if wave % 2 == 0 and wave < total:
            units.append("chief")
        if wave >= total:
            units.append("boss")
        return units

    def _start_wave(self) -> None:
        self.wave_state = "fight"
        self.pending = list(self.next_units) if self.next_units else self._wave_units(self.wave)
        self.next_units = []
        self.spawn_timer = 0.0
        count = len(self.pending)
        label = f"ВОЛНА {self.wave} · врагов: {count}"
        if "boss" in self.pending:
            label = f"ВОЛНА {self.wave} · БОСС И {count - 1} ВРАГОВ"
        elif "chief" in self.pending:
            label = f"ВОЛНА {self.wave} · ВОЖАК И {count - 1} ВРАГОВ"
        self.on_toast(label, "bad")

    def _update_waves(self, dt: float) -> None:
        if self.wave_state == "prep":
            self.wave_timer -= dt
            if self.wave_timer <= 0:
                self._start_wave()
            return
        if self.wave_state != "fight":
            return

        if self.pending:
            self.spawn_timer -= dt
            if self.spawn_timer <= 0 and len(self.enemies) < 34:
                self._spawn_enemy(self.pending.pop(0))
                self.spawn_timer = max(0.36, 0.92 - self.wave * 0.04)
            return

        if not self.enemies:
            self._complete_wave()

    def _spawn_enemy(self, kind: str) -> None:
        routes = self.level.routes
        route_index = random.randrange(len(routes))
        point = routes[route_index][0]
        x = clamp(point[0] + random.uniform(-24, 24), 30, self.world_w - 30)
        y = clamp(point[1] + random.uniform(-20, 20), 30, self.world_h - 30)
        enemy = make_enemy(kind, x, y, route=route_index, waypoint=1)

        wave = self.wave
        diff = self.level.difficulty
        hp_scale = diff * (1 + 0.16 * (wave - 1) + 0.013 * (wave - 1) ** 2)
        enemy.hp *= hp_scale
        enemy.max_hp = enemy.hp
        enemy.damage *= diff * (1 + 0.075 * (wave - 1))
        enemy.speed *= min(1.35, 1 + 0.012 * (wave - 1))
        enemy.gold = int(enemy.gold * (1 + 0.06 * (wave - 1)))

        # Редкий элитный враг: крепче, злее и вдвое дороже.
        if not enemy.boss and wave >= 5 and random.random() < 0.10:
            enemy.elite = True
            enemy.hp *= 1.7
            enemy.max_hp = enemy.hp
            enemy.damage *= 1.2
            enemy.radius *= 1.12
            enemy.gold *= 2

        self.enemies.append(enemy)
        if kind == "boss":
            self.on_toast("АЛЫЙ БОСС ВЕДЁТ АРМИЮ!", "bad")
            self._shake = 12.0
        elif kind == "chief":
            self.on_toast("Вожак ведёт отряд!", "bad")
            self._shake = 6.0

    def _complete_wave(self) -> None:
        bonus = WAVE_REWARD + (self.wave - 1) * WAVE_REWARD_STEP
        self.gold += bonus
        self.gold_earned += bonus
        if self.wave >= self.level.waves:
            self._end(True)
            return
        self.on_toast(f"Волна {self.wave} отбита! +{bonus} золота", "gold")
        self.wave += 1
        self.wave_state = "prep"
        self.wave_timer = self.level.wave_pause
        self.next_units = self._wave_units(self.wave)
        bx, by = self.level.base_pos
        self._add_ring(bx, by + 10, 80, (1.0, 0.86, 0.32, 1))

    # ------------------------------------------------------------------
    # Урон и смерть
    # ------------------------------------------------------------------
    def _damage_base(self, amount: float) -> None:
        if self.ended:
            return
        self.base_hp -= amount
        self._shake = max(self._shake, 7.0)
        bx, by = self.level.base_pos
        self._add_particles(
            bx + random.uniform(-60, 60),
            by + random.uniform(10, 80),
            3,
            (1.0, 0.42, 0.30, 1),
            speed=60,
        )
        if self._base_notice_cd <= 0:
            self.on_toast("База под атакой!", "bad")
            self._base_notice_cd = 5.0
        if self.base_hp <= 0:
            self.base_hp = 0
            self._end(False)

    def _damage_building(self, building: Building, amount: float) -> None:
        if building not in self.buildings:
            return
        building.hp -= amount
        building.flash = 0.12
        self._add_particles(building.x, building.y + 30, 2, (0.95, 0.72, 0.34, 1), speed=45)
        if building.hp > 0:
            return
        self.buildings.remove(building)
        data = BUILD_TYPES[building.kind]
        self.on_toast(f"{data['name']} разрушена!", "bad")
        self._add_puff(building.x, building.y + 24, (0.85, 0.52, 0.24, 1))
        self._shake = max(self._shake, 9.0)

    def _damage_defender(self, defender: Defender, amount: float) -> None:
        if defender not in self.defenders:
            return
        defender.hp -= amount
        defender.hit_flash = 0.12
        if defender.hp > 0:
            return
        self.defenders.remove(defender)
        self._add_puff(defender.x, defender.y + 16, (0.38, 0.62, 0.85, 1))

    def _damage_hero(self, enemy: Enemy) -> None:
        hero = self.hero
        if hero.hp <= 0 or hero.invuln > 0:
            return
        hero.hp -= enemy.damage
        hero.invuln = 1.1
        self._shake = max(self._shake, 10.0)
        knockback = normalize(hero.x - enemy.x, hero.y - enemy.y)
        min_x, min_y, max_x, max_y = self.hero_bounds
        hero.x = clamp(hero.x + knockback[0] * 26, min_x, max_x)
        hero.y = clamp(hero.y + knockback[1] * 26, min_y, max_y)
        self._add_puff(hero.x, hero.y, (1.0, 0.35, 0.25, 1))
        if hero.hp <= 0:
            hero.hp = 0
            self.respawn_timer = HERO_RESPAWN
            self.on_toast("Герой пал! Вернётся через 4 с", "bad")

    def _end(self, win: bool) -> None:
        if self.ended:
            return
        self.ended = True
        self.running = False
        self._clear_input()
        self.on_end(win, self.stats())

    # ------------------------------------------------------------------
    # Поиск целей и награды
    # ------------------------------------------------------------------
    def _nearest_enemy(self, x: float, y: float, radius: float):
        best = None
        best_d = radius * radius
        for enemy in self.enemies:
            d2 = (enemy.x - x) ** 2 + (enemy.y - y) ** 2
            if d2 <= best_d:
                best_d = d2
                best = enemy
        return best

    def _damage_enemy(self, enemy: Enemy, amount: float, source_x: float = 0, source_y: float = 0,
                      aggro: bool = True) -> None:
        if enemy not in self.enemies:
            return
        if enemy.armor > 0:
            amount = max(1.0, amount * (1.0 - enemy.armor))
        enemy.hp -= amount
        enemy.hit_flash = 0.12
        if aggro:
            enemy.aggro = 4.5
        self._add_particles(enemy.x, enemy.y + 20, 2, (0.95, 0.35, 0.24, 1), speed=42)
        if enemy.hp <= 0:
            self._kill_enemy(enemy)

    def _kill_enemy(self, enemy: Enemy) -> None:
        if enemy not in self.enemies:
            return
        self.enemies.remove(enemy)
        self.kills += 1
        reward = int(enemy.gold * (1 + 0.06 * (self.wave - 1)))
        self.gold += reward
        self.gold_earned += reward
        self._add_puff(enemy.x, enemy.y + 15, (0.85, 0.18, 0.15, 1))
        self._add_particles(enemy.x, enemy.y + 24, 3, (1.0, 0.84, 0.30, 1), speed=60)
        if enemy.explode > 0:
            self._explode_enemy(enemy)
        if enemy.boss:
            self._shake = 14.0
            self.on_toast(
                "Босс повержен!" if enemy.kind == "boss" else "Вожак повержен!",
                "gold",
            )

    def _explode_enemy(self, enemy: Enemy) -> None:
        """Бомбист взрывается, задевая всё рядом."""
        radius = 130.0
        self._shake = max(self._shake, 10.0)
        self._add_ring(enemy.x, enemy.y + 10, 60, (1.0, 0.62, 0.20, 1))
        self._add_particles(enemy.x, enemy.y + 18, 14, (1.0, 0.58, 0.18, 1), speed=150)
        damage = enemy.damage * 2.0
        for building in list(self.buildings):
            if dist(enemy.x, enemy.y, building.x, building.y) <= radius:
                self._damage_building(building, damage)
        for defender in list(self.defenders):
            if dist(enemy.x, enemy.y, defender.x, defender.y) <= radius:
                self._damage_defender(defender, damage)
        hero = self.hero
        if hero.hp > 0 and dist(enemy.x, enemy.y, hero.x, hero.y) <= radius:
            hero.hp = max(0.0, hero.hp - damage * 0.6)
            self._add_puff(hero.x, hero.y, (1.0, 0.45, 0.20, 1))
            if hero.hp <= 0:
                self.respawn_timer = HERO_RESPAWN
                self.on_toast("Герой пал от взрыва! Вернётся через 4 с", "bad")
        bx, by = self.level.base_pos
        if dist(enemy.x, enemy.y, bx, by) <= radius + 40:
            self._damage_base(damage * 0.5)

    def _spawn_defender(self, building: Building) -> None:
        data = BUILD_TYPES["barracks"]
        level = building.level - 1
        squad = self.upgrades["squad"]
        hp = data["defender_hp"][level] * (1 + 0.10 * squad)
        damage = data["defender_damage"][level] * (1 + 0.10 * squad)
        angle = random.uniform(0, math.pi * 2)
        radius = random.uniform(26, 44)
        self.defenders.append(
            Defender(
                x=clamp(building.x + math.cos(angle) * radius, 20, self.world_w - 20),
                y=clamp(building.y + math.sin(angle) * radius, 20, self.world_h - 20),
                home_x=building.x,
                home_y=building.y - 34,
                hp=hp,
                max_hp=hp,
                damage=damage,
                home_slot=building.slot,
                phase=random.uniform(0, math.pi * 2),
            )
        )
        self._add_ring(building.x, building.y + 20, 14, (0.36, 0.78, 0.52, 1))

    # ------------------------------------------------------------------
    # Камера
    # ------------------------------------------------------------------
    def _view_size(self) -> tuple[float, float]:
        density = dp(1)
        return max(1.0, self.width / density), max(1.0, self.height / density)

    def _clamp_axis(self, target: float, world: float, view: float) -> float:
        if view >= world:
            return (world - view) * 0.5
        return clamp(target, 0.0, world - view)

    def _camera_target(self) -> tuple[float, float]:
        view_w, view_h = self._view_size()
        # Камера идёт за героем и чуть смотрит вперёд, к базе.
        focus_x = self.hero.x
        focus_y = self.hero.y + 70.0
        return (
            self._clamp_axis(focus_x - view_w / 2, self.world_w, view_w),
            self._clamp_axis(focus_y - view_h / 2, self.world_h, view_h),
        )

    def _snap_camera(self) -> None:
        self.cam_x, self.cam_y = self._camera_target()

    def _update_camera(self, dt: float) -> None:
        target_x, target_y = self._camera_target()
        ease = min(1.0, dt * 6.0)
        self.cam_x += (target_x - self.cam_x) * ease
        self.cam_y += (target_y - self.cam_y) * ease

    def _on_size(self, *args) -> None:
        self._snap_camera()
        if hasattr(self, "fg_group"):
            self._draw()

    # ------------------------------------------------------------------
    # Визуальные эффекты
    # ------------------------------------------------------------------
    def _add_ring(self, x: float, y: float, radius: float, color) -> None:
        self.effects.append(Effect("ring", x, y, 0.55, radius=radius, color=color))

    def _add_slash(self, x: float, y: float, enemy) -> None:
        angle = math.atan2(enemy.y - y, enemy.x - x)
        mx = (x + enemy.x) / 2
        my = (y + enemy.y) / 2 + 18
        self.effects.append(
            Effect("slash", mx, my, 0.2, angle=angle, color=(1, 0.95, 0.75, 1))
        )

    def _add_puff(self, x: float, y: float, color) -> None:
        self.effects.append(
            Effect("puff", x, y, 0.45, angle=random.uniform(0, 6.28), color=color)
        )
        self._add_particles(x, y, 7, color, speed=75)

    def _add_particles(self, x: float, y: float, count: int, color, speed: float = 80) -> None:
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            velocity = random.uniform(speed * 0.35, speed)
            self.particles.append(
                Particle(
                    x,
                    y,
                    math.cos(angle) * velocity,
                    math.sin(angle) * velocity,
                    random.uniform(0.35, 0.7),
                    size=random.uniform(1.8, 3.8),
                    color=color,
                )
            )

    def _update_effects(self, dt: float) -> None:
        for effect in list(self.effects):
            effect.t += dt
            if effect.t >= effect.life:
                self.effects.remove(effect)
        for particle in list(self.particles):
            particle.t += dt
            particle.x += particle.vx * dt
            particle.y += particle.vy * dt
            particle.vx *= 0.94
            particle.vy *= 0.94
            if particle.t >= particle.life:
                self.particles.remove(particle)

    def _update_shake(self, dt: float) -> None:
        self._shake = max(0.0, self._shake - dt * 30)
        if self._shake > 0:
            self.shake_x = random.uniform(-self._shake, self._shake) * 0.5
            self.shake_y = random.uniform(-self._shake, self._shake) * 0.5
        else:
            self.shake_x = self.shake_y = 0.0

    # ------------------------------------------------------------------
    # Отрисовка
    # ------------------------------------------------------------------
    def _draw(self) -> None:
        if self.width <= 2 or self.height <= 2:
            return
        draw_arena(self)
