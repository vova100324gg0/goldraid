"""Вспомогательные виджеты интерфейса."""

from __future__ import annotations

import math

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line, Rectangle, RoundedRectangle
from kivy.graphics.instructions import InstructionGroup
from kivy.metrics import dp, sp
from kivy.properties import BooleanProperty, ListProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget

from .config import BUILD_TYPES, SAFE_BOTTOM, SAFE_SIDE, SAFE_TOP, TOTAL_WAVES
from .gfx import star


def _set_text(label: Label, text: str) -> None:
    """Меняет текст только если он реально другой.

    Перестройка текстуры Label — дорогая операция, а HUD обновляется
    10 раз в секунду: без этой проверки телефон перерисовывал бы
    полтора десятка текстов даже когда на экране ничего не изменилось.
    """
    if label.text != text:
        label.text = text


class GameButton(Button):
    """Кнопка с мягким градиентом, бликом, тенью и золотой подсветкой."""

    bg = ListProperty([0.13, 0.45, 0.28, 1])
    text_color = ListProperty([1.0, 1.0, 1.0, 1.0])

    def __init__(
        self,
        text: str = "",
        color=(0.13, 0.45, 0.28, 1),
        text_color=(1.0, 1.0, 1.0, 1),
        radius: float = 16,
        font_size: float | None = None,
        gloss: bool = True,
        **kwargs,
    ):
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(58))
        super().__init__(
            text=text,
            bold=True,
            font_size=font_size if font_size is not None else sp(17),
            background_normal="",
            background_down="",
            background_color=(0, 0, 0, 0),
            color=text_color,
            disabled_color=(text_color[0], text_color[1], text_color[2], 0.55),
            outline_color=(0, 0, 0, 0.42),
            outline_width=dp(0.8),
            **kwargs,
        )
        self.bg = list(color)
        self.text_color = list(text_color)
        self._normal_bg = list(color)
        self._base_bg = list(color)
        self._radius = [dp(radius)]
        self._radius_value = float(radius)
        self._gloss = bool(gloss)
        self._active = False
        with self.canvas.before:
            self._shadow_color = Color(0, 0, 0, 0.26)
            self._shadow = RoundedRectangle(
                pos=self.pos, size=self.size, radius=self._radius
            )
            self._bg_color = Color(*self.bg)
            self._rect = RoundedRectangle(
                pos=self.pos, size=self.size, radius=self._radius
            )
            self._top_color = Color(1, 1, 1, 0.09)
            self._top = RoundedRectangle(
                pos=self.pos, size=self.size, radius=self._radius
            )
        with self.canvas.after:
            self._edge_color = Color(1.0, 0.86, 0.34, 0.0)
            self._edge = Line(
                rounded_rectangle=(0, 0, 0, 0, dp(radius)),
                width=dp(1.4),
            )
        self.bind(pos=self._sync, size=self._sync, state=self._refresh_style)
        self.bind(disabled=self._refresh_style)
        self._refresh_style()

    def _refresh_style(self, *_args) -> None:
        if not hasattr(self, "_bg_color"):
            return
        base = self._base_bg
        if self.disabled:
            fill = (base[0] * 0.52, base[1] * 0.52, base[2] * 0.52, 0.82)
            edge = (1.0, 1.0, 1.0, 0.03)
            shadow = (0, 0, 0, 0.10)
        elif self.state == "down":
            fill = (base[0] * 0.72, base[1] * 0.72, base[2] * 0.72, base[3])
            edge = (1.0, 1.0, 1.0, 0.26)
            shadow = (0, 0, 0, 0.18)
        else:
            fill = (base[0], base[1], base[2], base[3])
            edge = (1.0, 1.0, 1.0, 0.10)
            shadow = (0, 0, 0, 0.26)
        if self._active and not self.disabled:
            edge = (1.0, 0.87, 0.38, 0.92)
            shadow = (1.0, 0.80, 0.30, 0.16)
        self._bg_color.rgba = fill
        self._edge_color.rgba = edge
        self._shadow_color.rgba = shadow
        if not self._gloss:
            self._top_color.a = 0.0
        elif self.disabled:
            self._top_color.a = 0.025
        elif self.state == "down":
            self._top_color.a = 0.05
        else:
            self._top_color.a = 0.09

    def _sync(self, *_args) -> None:
        if not hasattr(self, "_rect"):
            return
        self._refresh_style()
        pad = dp(1.5)
        radius = dp(self._radius_value)
        self._shadow.pos = (self.x, self.y - dp(3))
        self._shadow.size = self.size
        self._rect.pos = self.pos
        self._rect.size = self.size
        gloss_h = max(0.0, self.height * 0.47)
        self._top.pos = (self.x + pad, self.y + self.height - gloss_h)
        self._top.size = (
            max(0.0, self.width - pad * 2),
            max(0.0, gloss_h - pad),
        )
        self._top.radius = [radius, radius, 0, 0]
        self._edge.rounded_rectangle = (
            self.x + pad,
            self.y + pad,
            max(0, self.width - pad * 2),
            max(0, self.height - pad * 2),
            max(dp(2), radius - pad),
        )

    def set_active(self, active: bool) -> None:
        self._active = bool(active)
        base = self._normal_bg
        if self._active:
            self._base_bg = [
                min(1.0, base[0] * 1.55 + 0.10),
                min(1.0, base[1] * 1.55 + 0.10),
                min(1.0, base[2] * 1.55 + 0.08),
                1.0,
            ]
        else:
            self._base_bg = list(base)
        self._refresh_style()


class StarRow(Widget):
    """Ряд звёзд, нарисованных примитивами (без Unicode-глифов)."""

    count = NumericProperty(0)
    total = NumericProperty(3)

    def __init__(self, count: int = 0, **kwargs):
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("size", (dp(42), dp(14)))
        super().__init__(**kwargs)
        self.count = int(count)
        self._group = InstructionGroup()
        self.canvas.add(self._group)
        self.bind(pos=self._redraw, size=self._redraw, count=self._redraw)
        self._redraw()

    def _redraw(self, *_args) -> None:
        self._group.clear()
        if self.width <= 0 or self.height <= 0 or self.total <= 0:
            return
        step = self.width / self.total
        radius = min(step * 0.42, self.height * 0.5)
        for index in range(int(self.total)):
            cx = self.x + step * (index + 0.5)
            cy = self.center_y
            filled = index < self.count
            color = (
                (1.0, 0.84, 0.30, 1)
                if filled
                else (0.24, 0.33, 0.27, 0.85)
            )
            star(self._group, cx, cy, radius, color, radius * 0.46)


class StatChip(BoxLayout):
    """Плашка со значением в верхней панели."""

    def __init__(self, title: str, value: str = "—", accent=(1, 1, 1, 1), **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint_y=None,
            height=dp(54),
            padding=(dp(6), dp(3)),
            spacing=dp(0),
            **kwargs,
        )
        self.title_label = Label(
            text=title,
            font_size=sp(9.5),
            bold=True,
            color=(0.72, 0.84, 0.76, 1),
            halign="center",
            valign="middle",
        )
        self.title_label.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        self.value_label = Label(
            text=value,
            font_size=sp(15),
            bold=True,
            color=accent,
            halign="center",
            valign="middle",
        )
        self.value_label.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        self.add_widget(self.title_label)
        self.add_widget(self.value_label)

        with self.canvas.before:
            self._color = Color(0.04, 0.10, 0.07, 0.74)
            self._rect = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(12)]
            )
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *_args) -> None:
        self._rect.pos = self.pos
        self._rect.size = self.size

    def set_value(self, text: str, color=None) -> None:
        _set_text(self.value_label, text)
        if color is not None and list(self.value_label.color) != list(color):
            self.value_label.color = color


class Meter(Widget):
    """Полоска прогресса (прочность базы)."""

    def __init__(self, color=(0.34, 0.80, 0.44, 1), **kwargs):
        super().__init__(**kwargs)
        self._ratio = 1.0
        with self.canvas:
            self._bg = Color(0.04, 0.07, 0.05, 0.85)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)
            self._fg = Color(*color)
            self._fg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *_args) -> None:
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size
        self._fg_rect.pos = self.pos
        self._fg_rect.size = (max(0.0, self.width * self._ratio), self.height)

    def set_ratio(self, ratio: float, color=None) -> None:
        ratio = max(0.0, min(1.0, ratio))
        changed = abs(ratio - self._ratio) > 0.002
        self._ratio = ratio
        if color is not None and list(self._fg.rgba) != list(color):
            self._fg.rgba = color
            changed = True
        if changed:
            self._sync()


class HUD(FloatLayout):
    """Верхняя панель: прочность базы, золото и волна."""

    def __init__(self, on_pause=None, on_shop=None, on_speed=None, **kwargs):
        super().__init__(size_hint=(1, 1), **kwargs)
        self.on_pause = on_pause or (lambda *args: None)
        self.on_shop = on_shop or (lambda *args: None)
        self.on_speed = on_speed or (lambda *args: None)

        self.panel = BoxLayout(
            orientation="vertical",
            size_hint=(1, None),
            height=dp(152) + dp(SAFE_TOP),
            pos_hint={"top": 1},
            padding=(dp(9) + dp(SAFE_SIDE), dp(6) + dp(SAFE_TOP)),
            spacing=dp(3),
        )
        # Полупрозрачная подложка: текст не теряется на фоне замка.
        with self.panel.canvas.before:
            self._panel_color = Color(0.03, 0.07, 0.05, 0.80)
            self._panel_bg = RoundedRectangle(
                pos=self.panel.pos, size=self.panel.size, radius=[dp(14)]
            )
        self.panel.bind(
            pos=lambda w, _v: setattr(self._panel_bg, "pos", w.pos),
            size=lambda w, _v: setattr(self._panel_bg, "size", w.size),
        )

        row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(54),
            spacing=dp(6),
        )
        self.base_chip = StatChip("БАЗА", "600", (0.45, 0.90, 0.55, 1))
        self.gold_chip = StatChip("ЗОЛОТО", "0", (1.0, 0.84, 0.35, 1))
        self.wave_chip = StatChip("ВОЛНА", f"1/{TOTAL_WAVES}", (0.86, 0.92, 1.0, 1))
        row.add_widget(self.base_chip)
        row.add_widget(self.gold_chip)
        row.add_widget(self.wave_chip)

        self.speed_button = GameButton(
            text="x1",
            color=(0.10, 0.28, 0.34, 1),
            text_color=(0.84, 0.96, 1.0, 1),
            size_hint=(None, None),
            width=dp(46),
            height=dp(46),
            font_size=sp(13),
            radius=13,
        )
        self.speed_button.pos_hint = {"center_y": 0.5}
        self.speed_button.bind(on_release=lambda *_a: self.on_speed())
        row.add_widget(self.speed_button)

        self.shop_button = GameButton(
            text="МАГ.",
            color=(0.32, 0.20, 0.46, 1),
            text_color=(1.0, 0.92, 1.0, 1),
            size_hint=(None, None),
            width=dp(46),
            height=dp(46),
            font_size=sp(11),
            radius=13,
        )
        self.shop_button.pos_hint = {"center_y": 0.5}
        self.shop_button.bind(on_release=lambda *_a: self.on_shop())
        row.add_widget(self.shop_button)

        self.pause_button = GameButton(
            text="II",
            color=(0.05, 0.13, 0.10, 0.92),
            text_color=(1, 1, 1, 1),
            size_hint=(None, None),
            width=dp(46),
            height=dp(46),
            font_size=sp(16),
            radius=13,
        )
        self.pause_button.pos_hint = {"center_y": 0.5}
        self.pause_button.bind(on_release=lambda *_a: self.on_pause())
        row.add_widget(self.pause_button)
        self.panel.add_widget(row)

        self.base_meter = Meter(size_hint_y=None, height=dp(8))
        self.panel.add_widget(self.base_meter)

        self.boss_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=0,
            spacing=dp(6),
            opacity=0,
        )
        self.boss_label = Label(
            text="",
            font_size=sp(9.5),
            bold=True,
            color=(1.0, 0.58, 0.46, 1),
            size_hint_x=None,
            width=dp(110),
            halign="left",
            valign="middle",
        )
        self.boss_label.bind(
            size=lambda w, _v: setattr(w, "text_size", w.size)
        )
        self.boss_meter = Meter(color=(0.92, 0.24, 0.20, 1), size_hint_y=None, height=dp(10))
        self.boss_row.add_widget(self.boss_label)
        self.boss_row.add_widget(self.boss_meter)
        self.panel.add_widget(self.boss_row)

        self.status_label = Label(
            text="",
            font_size=sp(12),
            bold=True,
            color=(1.0, 0.86, 0.42, 1),
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=dp(22),
        )
        self.status_label.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        self.panel.add_widget(self.status_label)

        self.info_label = Label(
            text="",
            font_size=sp(10.5),
            color=(0.82, 0.92, 0.86, 1),
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=dp(20),
        )
        self.info_label.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        self.panel.add_widget(self.info_label)

        self.add_widget(self.panel)

    def set_stats(self, stats: dict) -> None:
        hp = int(stats.get("base_hp", 0))
        max_hp = max(1, int(stats.get("base_max_hp", 1)))
        ratio = hp / max_hp
        if ratio > 0.55:
            color = (0.45, 0.90, 0.55, 1)
        elif ratio > 0.25:
            color = (1.0, 0.80, 0.30, 1)
        else:
            color = (1.0, 0.40, 0.32, 1)
        self.base_chip.set_value(f"{hp} / {max_hp}", color)
        self.base_meter.set_ratio(ratio, color)
        self.gold_chip.set_value(str(int(stats.get("gold", 0))))
        self.wave_chip.set_value(
            f"{int(stats.get('wave', 1))}/{int(stats.get('total_waves', TOTAL_WAVES))}"
        )
        speed = float(stats.get("time_scale", 1.0))
        _set_text(self.speed_button, f"x{int(speed)}")
        self.speed_button.set_active(speed > 1.0)

        if stats.get("wave_state") == "prep":
            status = (
                f"{stats.get('level_name', '')} · волна {int(stats.get('wave', 1))} через "
                f"{int(math.ceil(stats.get('wave_timer', 0)))} с · "
                f"{stats.get('preview', '')}"
            )
        else:
            status = (
                f"{stats.get('level_name', '')} · волна "
                f"{int(stats.get('wave', 1))} · врагов: "
                f"{int(stats.get('enemies', 0))}"
            )
        if speed > 1.0:
            status += f" · x{int(speed)}"
        _set_text(self.status_label, status)

        if stats.get("boss"):
            boss_max = max(1.0, float(stats.get("boss_max", 1)))
            boss_hp = max(0.0, float(stats.get("boss_hp", 0)))
            self.boss_row.opacity = 1
            self.boss_row.height = dp(20)
            _set_text(self.boss_label, f"{stats.get('boss_name', 'БОСС')}: {int(boss_hp)}")
            self.boss_meter.set_ratio(boss_hp / boss_max, (1.0, 0.35, 0.28, 1))
        else:
            self.boss_row.opacity = 0
            self.boss_row.height = 0

        hero_hp = int(stats.get("hero_hp", 0))
        hero_max = max(1, int(stats.get("hero_max_hp", 1)))
        if stats.get("respawn", 0) > 0:
            hero_text = f"Герой: возрождение {math.ceil(stats.get('respawn', 0))} с"
        elif stats.get("rage", 0) > 0:
            hero_text = f"Герой {hero_hp}/{hero_max} · ярость {math.ceil(stats.get('rage', 0))} с"
        else:
            hero_text = f"Герой {hero_hp}/{hero_max}"
        roam = ""
        if stats.get("base_distance", 0) > 430:
            arrow = {
                "севернее": "↑",
                "южнее": "↓",
                "западнее": "←",
                "восточнее": "→",
            }.get(stats.get("base_dir", ""), "•")
            roam = f" · База {arrow}{int(stats.get('base_distance', 0))}"
        _set_text(
            self.info_label,
            f"{hero_text} · Бой {int(stats.get('defenders', 0))} · "
            f"Ш {int(stats.get('mines', 0))} · "
            f"Б {int(stats.get('towers', 0))} · "
            f"К {int(stats.get('barracks', 0))} · "
            f"Т {int(stats.get('totems', 0))}"
            f"{roam}",
        )

    def update_stats(self, stats: dict) -> None:
        self.set_stats(stats)


class BuildBar(FloatLayout):
    """Нижняя панель строительства и улучшений."""

    def __init__(self, on_build=None, on_upgrades=None, **kwargs):
        super().__init__(size_hint=(1, 1), **kwargs)
        self.on_build = on_build or (lambda *args: None)
        self.on_upgrades = on_upgrades or (lambda *args: None)

        panel = BoxLayout(
            orientation="vertical",
            size_hint=(1, None),
            height=dp(96) + dp(SAFE_BOTTOM) * 2,
            pos_hint={"x": 0, "y": 0},
            padding=(dp(6) + dp(SAFE_SIDE), dp(5) + dp(SAFE_BOTTOM)),
            spacing=dp(2),
        )
        with panel.canvas.before:
            self._bg_color = Color(0.03, 0.07, 0.05, 0.86)
            self._bg = RoundedRectangle(
                pos=panel.pos, size=panel.size, radius=[dp(16)]
            )
        panel.bind(
            pos=lambda w, _v: setattr(self._bg, "pos", w.pos),
            size=lambda w, _v: setattr(self._bg, "size", w.size),
        )

        self.hint = Label(
            text="Строй и защищай базу",
            font_size=sp(10),
            color=(0.76, 0.88, 0.80, 1),
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=dp(14),
        )
        self.hint.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        panel.add_widget(self.hint)

        row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(66),
            spacing=dp(4),
        )
        self.buttons = {}
        for kind, data in BUILD_TYPES.items():
            button = GameButton(
                text=f"{data['short']}\n{data['cost']} з.",
                color=data["color"],
                text_color=(1, 1, 1, 1),
                height=dp(64),
                radius=13,
                font_size=sp(10.5),
            )
            button.bind(on_release=lambda _inst, k=kind: self.on_build(k))
            row.add_widget(button)
            self.buttons[kind] = button

        self.upgrade_button = GameButton(
            text="УЛУЧШ.\n+",
            color=(0.30, 0.20, 0.52, 1),
            text_color=(1.0, 0.92, 1.0, 1),
            height=dp(64),
            radius=13,
            font_size=sp(10.5),
        )
        self.upgrade_button.bind(on_release=lambda *_a: self.on_upgrades())
        row.add_widget(self.upgrade_button)
        panel.add_widget(row)

        self.add_widget(panel)

    def set_state(self, stats: dict, mode: str | None) -> None:
        gold = int(stats.get("gold", 0))
        for kind, button in self.buttons.items():
            cost = int(BUILD_TYPES[kind]["cost"])
            active = mode == kind
            button.set_active(active)
            button.disabled = (not active) and gold < cost
        if mode is None:
            _set_text(self.hint, "Строй и защищай базу")
        else:
            _set_text(
                self.hint,
                f"{BUILD_TYPES[mode]['name']}: выбери свободную площадку · "
                "нажми кнопку ещё раз, чтобы отменить",
            )


class Toast(FloatLayout):
    """Всплывающее сообщение по центру экрана."""

    def __init__(self, **kwargs):
        super().__init__(size_hint=(1, 1), **kwargs)
        self.label = Label(
            text="",
            font_size=sp(16),
            bold=True,
            size_hint=(None, None),
            size=(dp(340), dp(62)),
            pos_hint={"center_x": 0.5, "center_y": 0.66},
            halign="center",
            valign="middle",
            color=(1.0, 1.0, 1.0, 1),
        )
        self.label.bind(
            size=lambda w, _v: setattr(w, "text_size", w.size)
        )
        self.label.text_size = self.label.size
        with self.label.canvas.before:
            self._bg = Color(0.03, 0.08, 0.05, 0.82)
            self._rect = RoundedRectangle(
                pos=self.label.pos,
                size=self.label.size,
                radius=[dp(14)],
            )
        self.label.bind(
            pos=lambda w, _v: setattr(self._rect, "pos", w.pos),
            size=lambda w, _v: setattr(self._rect, "size", w.size),
        )
        self.add_widget(self.label)
        self._timer = None
        self.label.opacity = 0

    def show(self, text: str, kind: str = "info", duration: float = 1.8) -> None:
        colors = {
            "gold": (1.0, 0.84, 0.35, 1),
            "blue": (0.55, 0.82, 1.0, 1),
            "bad": (1.0, 0.44, 0.36, 1),
        }
        _set_text(self.label, text)
        self.label.color = colors.get(kind, colors["gold"])
        Animation.cancel_all(self.label, "opacity")
        self.label.opacity = 1
        if self._timer is not None:
            self._timer.cancel()
        self._timer = Clock.schedule_once(self._hide, duration)

    def _hide(self, *_args) -> None:
        self._timer = None
        Animation(opacity=0, duration=0.25, t="in_quad").start(self.label)


class Overlay(FloatLayout):
    """Полупрозрачный модальный слой. По умолчанию скрыт."""

    visible = BooleanProperty(False)
    dismiss_on_outside = False
    dim_alpha = 0.7

    def __init__(self, **kwargs):
        super().__init__(size_hint=(1, 1), **kwargs)
        with self.canvas.before:
            self._dim = Color(0.02, 0.05, 0.03, 0.0)
            self._dim_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._sync_dim, size=self._sync_dim)
        self.panel = None
        self.opacity = 0

    def _sync_dim(self, *_args) -> None:
        self._dim_rect.pos = self.pos
        self._dim_rect.size = self.size

    def add_panel(self, panel) -> None:
        self.panel = panel
        self.add_widget(panel)

    def on_visible(self, _instance, value: bool) -> None:
        self.opacity = 1.0 if value else 0.0
        self._dim.a = self.dim_alpha if value else 0.0
        if value and self.panel is not None:
            Animation.cancel_all(self.panel, "opacity")
            self.panel.opacity = 1.0

    # Скрытый оверлей не должен участвовать в обработке касаний: иначе
    # невидимая панель перехватывает тапы (disabled-виджет их «съедает»).
    def on_touch_down(self, touch):
        if not self.visible:
            return False
        if self.panel is not None and not self.panel.collide_point(*touch.pos):
            if self.dismiss_on_outside:
                self.close()
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if not self.visible:
            return False
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if not self.visible:
            return False
        return super().on_touch_up(touch)

    def open(self, *_args) -> None:
        self.visible = True

    def close(self, *_args) -> None:
        self.visible = False


class WavePrompt(FloatLayout):
    """Кнопка досрочного вызова волны. Появляется только в подготовке."""

    visible = BooleanProperty(False)

    def __init__(self, on_call=None, **kwargs):
        super().__init__(size_hint=(1, 1), **kwargs)
        self.on_call = on_call or (lambda *args: None)
        self.button = GameButton(
            text="",
            color=(0.44, 0.30, 0.10, 0.96),
            text_color=(1.0, 0.94, 0.72, 1),
            size_hint=(0.76, None),
            height=dp(50),
            pos_hint={"center_x": 0.5, "y": 0.135},
            font_size=sp(10.5),
            radius=15,
        )
        self.button.bind(on_release=lambda *_a: self.on_call())
        self.add_widget(self.button)
        self.opacity = 0

    def on_visible(self, _instance, value: bool) -> None:
        self.opacity = 1.0 if value else 0.0

    def set_state(self, stats: dict) -> None:
        wave = int(stats.get("wave", 1))
        total = int(stats.get("total_waves", TOTAL_WAVES))
        left = int(math.ceil(float(stats.get("wave_timer", 0))))
        bonus = int(stats.get("call_bonus", 0))
        if wave >= total:
            caption = "ПОСЛЕДНЯЯ ВОЛНА"
        else:
            caption = f"ВОЛНА {wave} ЧЕРЕЗ {left} С"
        _set_text(self.button, f"{caption}\nВЫЗВАТЬ РАНЬШЕ · +{bonus} З.")

    def on_touch_down(self, touch):
        if not self.visible:
            return False
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if not self.visible:
            return False
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if not self.visible:
            return False
        return super().on_touch_up(touch)
