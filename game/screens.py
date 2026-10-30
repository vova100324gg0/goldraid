"""Экраны игры: меню, арена и модальные окна."""

from __future__ import annotations

import math
import random

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, Rectangle, RoundedRectangle
from kivy.graphics.instructions import InstructionGroup
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget

from .arena import Arena
from .config import (
    AUTHOR,
    BUILD_TYPES,
    DISCORD_HANDLE,
    DISCORD_URL,
    GAME_TITLE,
    GLOBAL_UPGRADES,
    SHOP_ITEMS,
    TOTAL_WAVES,
    UI_MUTED,
    VERSION,
)
from .gfx import circle, poly, ring
from .levels import LEVELS
from .progress import PROGRESS
from .util import open_url
from .widgets import BuildBar, GameButton, HUD, Overlay, StarRow, Toast, WavePrompt


class Backdrop(FloatLayout):
    """Фон меню: ночной градиент, свечение, холмы и золотые искры."""

    BANDS = (
        (0.030, 0.098, 0.070, 1),
        (0.023, 0.078, 0.056, 1),
        (0.017, 0.057, 0.042, 1),
        (0.011, 0.038, 0.029, 1),
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.running = True
        self._t = 0.0
        rng = random.Random(20261030)
        self._sparks = [
            {
                "x": rng.uniform(0.02, 0.98),
                "y": rng.random(),
                "r": rng.uniform(1.0, 3.0),
                "v": rng.uniform(0.010, 0.045),
                "sway": rng.uniform(0.004, 0.016),
                "phase": rng.uniform(0.0, math.tau),
                "twinkle": rng.uniform(1.2, 2.6),
                "alpha": rng.uniform(0.18, 0.60),
            }
            for _ in range(28)
        ]
        self._spark_colors = []
        self._spark_ellipses = []
        with self.canvas.before:
            self._band_colors = []
            self._band_rects = []
            for color in self.BANDS:
                band_color = Color(*color)
                band_rect = Rectangle()
                self._band_colors.append(band_color)
                self._band_rects.append(band_rect)

            self._glow_color = Color(1.0, 0.78, 0.28, 0.11)
            self._glow = Ellipse()
            self._glow_b_color = Color(0.30, 0.90, 0.58, 0.05)
            self._glow_b = Ellipse()

            self._arc_color = Color(1.0, 0.86, 0.44, 0.10)
            self._arc = Line(width=dp(1.2))
            self._arc_b_color = Color(1.0, 0.86, 0.44, 0.05)
            self._arc_b = Line(width=dp(1.0))

            self._ridge_colors = []
            self._ridges = []
            for color in (
                (0.020, 0.055, 0.042, 0.90),
                (0.014, 0.042, 0.032, 0.92),
                (0.009, 0.030, 0.024, 0.95),
            ):
                ridge_color = Color(*color)
                ridge = Ellipse()
                self._ridge_colors.append(ridge_color)
                self._ridges.append(ridge)

            for spark in self._sparks:
                spark_color = Color(1.0, 0.86, 0.46, spark["alpha"])
                spark_ellipse = Ellipse()
                self._spark_colors.append(spark_color)
                self._spark_ellipses.append(spark_ellipse)
        self.bind(pos=self._layout, size=self._layout)
        Clock.schedule_interval(self._animate, 1 / 30)
        self._layout()

    def _layout(self, *_args) -> None:
        width, height = self.size
        if width <= 0 or height <= 0:
            return
        count = len(self._band_rects)
        band_height = height / count
        for index, rect in enumerate(self._band_rects):
            rect.pos = (
                self.x,
                self.y + height - (index + 1) * band_height,
            )
            rect.size = (width, band_height + dp(1))

        self._glow.pos = (
            self.x + width * 0.5 - width * 0.62,
            self.y + height * 0.46,
        )
        self._glow.size = (width * 1.24, height * 0.58)
        self._glow_b.pos = (
            self.x - width * 0.20,
            self.y + height * 0.02,
        )
        self._glow_b.size = (width * 0.86, height * 0.36)

        self._arc.circle = (
            self.x + width * 0.5,
            self.y + height * 0.80,
            width * 0.46,
        )
        self._arc_b.circle = (
            self.x + width * 0.5,
            self.y + height * 0.80,
            width * 0.62,
        )

        ridge_specs = (
            (0.10, 0.02, 1.25, 0.26),
            (0.92, 0.00, 1.10, 0.22),
            (0.50, -0.05, 1.50, 0.20),
        )
        for (cx_f, cy_f, w_f, h_f), ridge in zip(ridge_specs, self._ridges):
            ridge_width = width * w_f
            ridge_height = height * h_f
            ridge.pos = (
                self.x + width * cx_f - ridge_width / 2,
                self.y + height * cy_f - ridge_height / 2,
            )
            ridge.size = (ridge_width, ridge_height)

        self._update_sparks()

    def _update_sparks(self) -> None:
        width, height = self.size
        if width <= 0 or height <= 0:
            return
        time = self._t
        for spark, color, ellipse in zip(
            self._sparks, self._spark_colors, self._spark_ellipses
        ):
            x = self.x + (
                (spark["x"] + math.sin(time * 0.5 + spark["phase"]) * spark["sway"])
                % 1.0
            ) * width
            y = self.y + ((spark["y"] + time * spark["v"]) % 1.0) * height
            radius = spark["r"] * (
                0.80 + 0.25 * math.sin(time * 1.7 + spark["phase"])
            )
            ellipse.pos = (x - radius, y - radius)
            ellipse.size = (radius * 2, radius * 2)
            twinkle = math.sin(time * spark["twinkle"] + spark["phase"])
            color.a = spark["alpha"] * (0.55 + 0.45 * twinkle * twinkle)

    def _animate(self, dt: float) -> None:
        if not self.running:
            return
        self._t += dt
        self._glow_color.a = 0.10 + 0.028 * math.sin(self._t * 0.9)
        self._glow_b_color.a = 0.045 + 0.015 * math.sin(self._t * 0.6 + 1.2)
        self._update_sparks()


class CoinEmblem(Widget):
    """Золотая монета с короной — эмблема игры."""

    def __init__(self, **kwargs):
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("size", (dp(84), dp(84)))
        super().__init__(**kwargs)
        self._group = InstructionGroup()
        self.canvas.add(self._group)
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _redraw(self, *_args) -> None:
        group = self._group
        group.clear()
        cx, cy = self.center
        radius = min(self.width, self.height) * 0.5
        if radius <= 1:
            return
        group.add(Color(1.0, 0.80, 0.30, 0.10))
        group.add(
            Ellipse(
                pos=(cx - radius * 1.14, cy - radius * 1.14),
                size=(radius * 2.28, radius * 2.28),
            )
        )
        circle(group, cx, cy, radius * 0.92, (0.60, 0.38, 0.05, 1))
        circle(group, cx, cy, radius * 0.84, (0.99, 0.81, 0.28, 1))
        circle(group, cx, cy, radius * 0.73, (0.90, 0.64, 0.14, 1))
        ring(group, cx, cy, radius * 0.75, (1.0, 0.95, 0.64, 0.85), 1.4)

        dark = (0.40, 0.23, 0.03, 1)
        poly(
            group,
            [
                (cx - radius * 0.46, cy - radius * 0.14),
                (cx - radius * 0.20, cy - radius * 0.14),
                (cx - radius * 0.44, cy + radius * 0.26),
            ],
            dark,
        )
        poly(
            group,
            [
                (cx - radius * 0.22, cy - radius * 0.14),
                (cx + radius * 0.22, cy - radius * 0.14),
                (cx, cy + radius * 0.46),
            ],
            dark,
        )
        poly(
            group,
            [
                (cx + radius * 0.20, cy - radius * 0.14),
                (cx + radius * 0.46, cy - radius * 0.14),
                (cx + radius * 0.44, cy + radius * 0.26),
            ],
            dark,
        )
        group.add(Color(*dark))
        group.add(
            RoundedRectangle(
                pos=(cx - radius * 0.46, cy - radius * 0.27),
                size=(radius * 0.92, radius * 0.21),
                radius=[max(1.5, radius * 0.09)],
            )
        )
        for gem in (-0.26, 0.0, 0.26):
            circle(
                group,
                cx + radius * gem,
                cy - radius * 0.17,
                radius * 0.055,
                (1.0, 0.94, 0.58, 1),
            )
        group.add(Color(1.0, 1.0, 1.0, 0.22))
        group.add(
            Ellipse(
                pos=(cx - radius * 0.64, cy + radius * 0.18),
                size=(radius * 0.56, radius * 0.22),
            )
        )


class AdSlot(FloatLayout):
    """Зарезервированное место под будущий рекламный баннер."""

    def __init__(self, **kwargs):
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(66))
        super().__init__(**kwargs)
        with self.canvas.before:
            self._fill = Color(0.045, 0.100, 0.080, 0.62)
            self._rect = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(16)]
            )
            self._edge_color = Color(1.0, 0.84, 0.38, 0.16)
            self._edge = Line(
                rounded_rectangle=(0, 0, 0, 0, dp(16)), width=dp(1.1)
            )
            self._mark_color = Color(1.0, 0.84, 0.38, 0.30)
            self._mark_a = Line(width=dp(1.4))
            self._mark_b = Line(width=dp(1.4))

        self.badge = Label(
            text="AD",
            font_size=sp(8.5),
            bold=True,
            color=(0.15, 0.12, 0.05, 1),
            size_hint=(None, None),
            size=(dp(30), dp(19)),
            pos_hint={"x": 0.028, "center_y": 0.5},
            halign="center",
            valign="middle",
        )
        self.badge.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        with self.badge.canvas.before:
            self._badge_fill = Color(0.98, 0.80, 0.34, 0.85)
            self._badge_rect = RoundedRectangle(
                pos=self.badge.pos, size=self.badge.size, radius=[dp(6)]
            )
        self.badge.bind(
            pos=lambda w, _v: setattr(self._badge_rect, "pos", w.pos),
            size=lambda w, _v: setattr(self._badge_rect, "size", w.size),
        )
        self.add_widget(self.badge)

        self.title = Label(
            text="МЕСТО ДЛЯ РЕКЛАМЫ",
            font_size=sp(9.5),
            bold=True,
            color=(0.96, 0.84, 0.52, 0.80),
            size_hint=(1, None),
            height=dp(19),
            pos_hint={"center_x": 0.5, "top": 0.90},
            halign="center",
            valign="middle",
        )
        self.title.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        self.add_widget(self.title)

        self.subtitle = Label(
            text="баннер партнёра · 320 x 50",
            font_size=sp(8.5),
            color=(0.60, 0.73, 0.65, 0.75),
            size_hint=(1, None),
            height=dp(17),
            pos_hint={"center_x": 0.5, "y": 0.13},
            halign="center",
            valign="middle",
        )
        self.subtitle.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        self.add_widget(self.subtitle)

        self.bind(pos=self._sync, size=self._sync)
        self._sync()

    def _sync(self, *_args) -> None:
        pad = dp(1)
        self._rect.pos = self.pos
        self._rect.size = self.size
        self._edge.rounded_rectangle = (
            self.x + pad,
            self.y + pad,
            max(0, self.width - pad * 2),
            max(0, self.height - pad * 2),
            dp(15),
        )
        inset = dp(6)
        arm = dp(10)
        self._mark_a.points = [
            self.x + inset,
            self.y + self.height - inset,
            self.x + inset + arm,
            self.y + self.height - inset,
            self.x + inset,
            self.y + self.height - inset,
            self.x + inset,
            self.y + self.height - inset - arm,
        ]
        self._mark_b.points = [
            self.x + self.width - inset,
            self.y + inset,
            self.x + self.width - inset - arm,
            self.y + inset,
            self.x + self.width - inset,
            self.y + inset,
            self.x + self.width - inset,
            self.y + inset + arm,
        ]


class MenuCard(BoxLayout):
    """Стеклянная карточка с тенью и золотой окантовкой."""

    def __init__(self, **kwargs):
        kwargs.setdefault("padding", (dp(16), dp(14)))
        super().__init__(**kwargs)
        with self.canvas.before:
            self._shadow_color = Color(0, 0, 0, 0.32)
            self._shadow = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(26)]
            )
            self._fill = Color(0.035, 0.085, 0.066, 0.94)
            self._rect = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(26)]
            )
            self._top_color = Color(1, 1, 1, 0.035)
            self._top = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(26)]
            )
        with self.canvas.after:
            self._edge = Color(1.0, 0.83, 0.38, 0.20)
            self._outline = Line(
                rounded_rectangle=(0, 0, 0, 0, dp(26)), width=dp(1.1)
            )
        self.bind(pos=self._sync, size=self._sync)
        self._sync()

    def _sync(self, *_args) -> None:
        pad = dp(1)
        radius = dp(26)
        self._shadow.pos = (self.x, self.y - dp(5))
        self._shadow.size = self.size
        self._rect.pos = self.pos
        self._rect.size = self.size
        gloss_h = max(0.0, self.height * 0.40)
        self._top.pos = (self.x + pad, self.y + self.height - gloss_h)
        self._top.size = (
            max(0, self.width - pad * 2),
            max(0, gloss_h - pad),
        )
        self._top.radius = [radius, radius, 0, 0]
        self._outline.rounded_rectangle = (
            self.x + pad,
            self.y + pad,
            max(0, self.width - pad * 2),
            max(0, self.height - pad * 2),
            radius - pad,
        )


class Divider(Widget):
    """Тонкая линия-разделитель."""

    def __init__(self, **kwargs):
        super().__init__(size_hint_y=None, height=dp(1), **kwargs)
        with self.canvas:
            self._color = Color(1.0, 0.95, 0.80, 0.10)
            self._rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *_args) -> None:
        self._rect.pos = self.pos
        self._rect.size = self.size


class Medallion(Widget):
    """Круглый номер карты слева от названия."""

    def __init__(self, number: int, accent=(0.30, 0.70, 0.42, 1), **kwargs):
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("size", (dp(50), dp(50)))
        super().__init__(**kwargs)
        self.accent = list(accent)
        self._group = InstructionGroup()
        self.canvas.add(self._group)
        self.number = Label(
            text=str(number),
            font_size=sp(18),
            bold=True,
            color=(1.0, 0.90, 0.56, 1),
            disabled_color=(0.55, 0.60, 0.55, 0.8),
            halign="center",
            valign="middle",
            size_hint=(1, 1),
        )
        self.number.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        self.add_widget(self.number)
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def set_locked(self, locked: bool) -> None:
        if locked:
            self.accent = [0.36, 0.42, 0.38, 1]
        self._redraw()

    def _redraw(self, *_args) -> None:
        group = self._group
        group.clear()
        cx, cy = self.center
        radius = min(self.width, self.height) * 0.5
        if radius <= 1:
            return
        group.add(Color(1.0, 0.84, 0.38, 0.08))
        group.add(
            Ellipse(
                pos=(cx - radius * 1.08, cy - radius * 1.08),
                size=(radius * 2.16, radius * 2.16),
            )
        )
        circle(group, cx, cy, radius * 0.96, tuple(self.accent))
        circle(group, cx, cy, radius * 0.81, (0.040, 0.095, 0.072, 1))
        ring(group, cx, cy, radius * 0.87, (1.0, 0.89, 0.52, 0.45), 1.2)


class Badge(Label):
    """Небольшая плашка со статусом карты."""

    def __init__(
        self,
        text: str = "",
        fill=(0.20, 0.58, 0.32, 0.92),
        color=(0.94, 1.0, 0.95, 1),
        **kwargs,
    ):
        kwargs.setdefault("font_size", sp(8.5))
        super().__init__(
            text=text,
            bold=True,
            color=color,
            disabled_color=(0.55, 0.62, 0.56, 0.9),
            halign="center",
            valign="middle",
            shorten=True,
            **kwargs,
        )
        with self.canvas.before:
            self._fill = Color(*fill)
            self._rect = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(8)]
            )
        self.bind(pos=self._sync, size=self._sync)
        self.bind(size=lambda w, _v: setattr(w, "text_size", w.size))

    def _sync(self, *_args) -> None:
        self._rect.pos = self.pos
        self._rect.size = self.size

    def set_colors(self, fill, color) -> None:
        self._fill.rgba = fill
        self.color = color
        self.disabled_color = (color[0] * 0.72, color[1] * 0.72, color[2] * 0.72, 0.9)


class LevelTile(GameButton):
    """Карточка карты: медальон, название, звёзды и статус."""

    def __init__(self, index: int, level, **kwargs):
        self.index = index
        self.level = level
        accent = level.accent
        tint = (
            0.050 + accent[0] * 0.13,
            0.110 + accent[1] * 0.13,
            0.085 + accent[2] * 0.13,
            0.98,
        )
        super().__init__(
            text="",
            color=tint,
            text_color=(1, 1, 1, 1),
            radius=16,
            height=dp(110),
            font_size=sp(12),
            **kwargs,
        )
        # Текст карточки рисуем отдельными подписями, штатный текст скрыт.
        self.color = (0, 0, 0, 0)
        self.disabled_color = (0, 0, 0, 0)
        self._accent = list(accent)
        self._tint = list(tint)
        self._locked = False

        self.medallion = Medallion(index + 1, accent)
        self.add_widget(self.medallion)

        self.title = self._make_label((1, 1), (0.96, 0.99, 0.95, 1), bold=True, font_size=sp(15))
        self.subtitle = self._make_label((1, 1), (0.72, 0.86, 0.77, 1), font_size=sp(10))
        self.meta = self._make_label((1, 1), (1.0, 0.84, 0.44, 0.95), bold=True, font_size=sp(9))
        self.record = self._make_label(
            (1, 1), (0.66, 0.78, 0.69, 1), font_size=sp(8.5)
        )
        self.record.halign = "right"
        self.stars = StarRow(0)
        self.status = Badge("ИГРАТЬ")
        for widget in (
            self.title,
            self.subtitle,
            self.meta,
            self.stars,
            self.record,
            self.status,
        ):
            self.add_widget(widget)

        with self.canvas.after:
            self._stripe_color = Color(*accent)
            self._stripe = RoundedRectangle(
                pos=self.pos, size=(dp(3), self.height), radius=[dp(2)]
            )
        self._sync()

    def _make_label(self, size, color, bold=False, font_size=sp(10)):
        label = Label(
            text="",
            font_size=font_size,
            bold=bold,
            color=color,
            disabled_color=(
                color[0] * 0.70,
                color[1] * 0.70,
                color[2] * 0.70,
                0.85,
            ),
            size_hint=(None, None),
            size=size,
            halign="left",
            valign="middle",
            shorten=True,
            max_lines=1,
        )
        label.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        return label

    def _sync(self, *_args) -> None:
        super()._sync()
        if not hasattr(self, "title"):
            return
        width, height = self.size
        pad = dp(10)
        med = dp(50)
        self.medallion.size = (med, med)
        self.medallion.pos = (self.x + pad, self.y + (height - med) / 2)
        left = self.x + pad + med + dp(12)
        right_w = dp(84)
        right_x = self.x + width - pad - right_w
        info_w = max(dp(40), right_x - dp(10) - left)
        self.title.pos = (left, self.y + height - dp(40))
        self.title.size = (info_w, dp(24))
        self.subtitle.pos = (left, self.y + height - dp(61))
        self.subtitle.size = (info_w, dp(19))
        self.meta.pos = (left, self.y + dp(11))
        self.meta.size = (info_w, dp(18))
        self.stars.pos = (right_x, self.y + height - dp(36))
        self.stars.size = (right_w, dp(15))
        self.record.pos = (right_x, self.y + height - dp(55))
        self.record.size = (right_w, dp(15))
        self.status.pos = (right_x, self.y + dp(12))
        self.status.size = (right_w, dp(24))
        self._stripe.pos = (self.x + dp(4), self.y + dp(10))
        self._stripe.size = (dp(3), max(0, height - dp(20)))

    def set_data(self, available: bool, stars: int, best_wave: int) -> None:
        self._locked = not available
        self.disabled = not available
        self.title.text = self.level.name
        self.subtitle.text = self.level.subtitle
        self.meta.text = f"{self.level.waves} волн · {len(self.level.routes)} дороги"
        self.stars.count = max(0, min(3, stars))
        if not available:
            self.record.text = "пройди предыдущую"
        elif best_wave:
            self.record.text = f"лучшая {best_wave}/{self.level.waves}"
        else:
            self.record.text = "ещё не пройдена"
        if available:
            self.status.text = "ИГРАТЬ"
            self.status.set_colors((0.20, 0.60, 0.33, 0.94), (0.94, 1.0, 0.95, 1))
            self.title.color = (0.96, 0.99, 0.95, 1)
            self.subtitle.color = (0.72, 0.86, 0.77, 1)
            self.meta.color = (1.0, 0.84, 0.44, 0.95)
            self.record.color = (0.66, 0.78, 0.69, 1)
        else:
            self.status.text = "ЗАКРЫТО"
            self.status.set_colors((0.18, 0.23, 0.20, 0.94), (0.62, 0.68, 0.62, 1))
            self.title.color = (0.66, 0.73, 0.67, 1)
            self.subtitle.color = (0.52, 0.61, 0.54, 1)
            self.meta.color = (0.68, 0.62, 0.44, 0.8)
            self.record.color = (0.50, 0.58, 0.52, 1)
        self.medallion.set_locked(self._locked)
        self._apply_tint()
        state = "открыто" if available else "закрыто"
        self.text = f"{self.level.name}\n{self.level.waves} волн · {state}"

    def _apply_tint(self) -> None:
        if self._locked:
            base = (0.068, 0.096, 0.084, 0.94)
            self._stripe_color.rgba = (0.42, 0.50, 0.45, 0.45)
        else:
            base = list(self._tint)
            self._stripe_color.rgba = tuple(self._accent)
        self._normal_bg = list(base)
        self._base_bg = list(base)
        self._refresh_style()


class MenuScreen(Screen):
    def __init__(self, app_ref, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.name = "menu"
        self.app_ref = app_ref
        self.screen_manager = screen_manager
        self.level_buttons = []
        self._discord_timer = None

        self.backdrop = Backdrop()
        self.add_widget(self.backdrop)

        self.column = BoxLayout(
            orientation="vertical",
            size_hint=(0.94, None),
            height=dp(794),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )

        # ---------------------------------------------------------- бренд
        brand = FloatLayout(size_hint_y=None, height=dp(164))
        self.emblem = CoinEmblem()
        self.emblem.pos_hint = {"center_x": 0.5, "top": 0.995}
        brand.add_widget(self.emblem)

        title = Label(
            text=GAME_TITLE,
            font_size=sp(30),
            bold=True,
            color=(1.0, 0.84, 0.35, 1),
            outline_color=(0.28, 0.14, 0.02, 0.65),
            outline_width=dp(1.1),
            size_hint=(1, None),
            height=dp(42),
            pos_hint={"center_x": 0.5, "y": 0.17},
            halign="center",
            valign="middle",
        )
        title.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        brand.add_widget(title)

        tagline = Label(
            text="ОБОРОНА · ВОЛНЫ · ЗОЛОТО",
            font_size=sp(9.5),
            bold=True,
            color=(0.62, 0.78, 0.67, 0.95),
            size_hint=(1, None),
            height=dp(18),
            pos_hint={"center_x": 0.5, "y": 0.0},
            halign="center",
            valign="middle",
        )
        tagline.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        brand.add_widget(tagline)

        self.column.add_widget(brand)
        self.column.add_widget(self._spacer(12))

        # ------------------------------------------------ место под рекламу
        self.ad_slot = AdSlot()
        self.column.add_widget(self.ad_slot)
        self.column.add_widget(self._spacer(14))

        # ---------------------------------------------------------- карты
        self.levels_card = MenuCard(
            orientation="vertical",
            size_hint_y=None,
            height=dp(402),
            padding=(dp(12), dp(12)),
            spacing=dp(8),
        )
        header = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(24),
            spacing=dp(6),
        )
        header_title = Label(
            text="КАРТЫ",
            font_size=sp(11),
            bold=True,
            color=(1.0, 0.84, 0.40, 1),
            halign="left",
            valign="middle",
        )
        header_title.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        header.add_widget(header_title)

        self.summary = Label(
            text="",
            font_size=sp(9.5),
            bold=True,
            color=UI_MUTED,
            halign="right",
            valign="middle",
        )
        self.summary.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        header.add_widget(self.summary)
        self.levels_card.add_widget(header)

        for index, level in enumerate(LEVELS):
            tile = LevelTile(index, level)
            tile.bind(on_release=lambda _inst, i=index: self._play(i))
            self.levels_card.add_widget(tile)
            self.level_buttons.append(tile)

        self.column.add_widget(self.levels_card)
        self.column.add_widget(self._spacer(14))

        # ---------------------------------------------------------- подсказка
        help_card = MenuCard(
            orientation="vertical",
            size_hint_y=None,
            height=dp(56),
            padding=(dp(12), dp(7)),
            spacing=dp(1),
        )
        help_top = Label(
            text="Собирай золото, строй оборону и не дай снести ворота",
            font_size=sp(9.5),
            color=(0.82, 0.91, 0.84, 1),
            halign="center",
            valign="middle",
        )
        help_top.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        help_card.add_widget(help_top)
        help_bottom = Label(
            text="WASD — бой · 1-4 постройки · U улучшения · F волна · T скорость · Space пауза",
            font_size=sp(8),
            color=UI_MUTED,
            halign="center",
            valign="middle",
        )
        help_bottom.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        help_card.add_widget(help_bottom)
        self.column.add_widget(help_card)
        self.column.add_widget(self._spacer(12))

        # ---------------------------------------------------------- футер
        footer = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(54),
            spacing=dp(8),
        )
        left = BoxLayout(orientation="vertical", size_hint_x=0.44)
        copyright_label = Label(
            text=f"© 2026 {AUTHOR}",
            font_size=sp(11),
            bold=True,
            color=(0.98, 0.84, 0.42, 1),
            halign="left",
            valign="middle",
        )
        copyright_label.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        left.add_widget(copyright_label)
        made_label = Label(
            text=f"автор игры · v{VERSION}",
            font_size=sp(8),
            color=UI_MUTED,
            halign="left",
            valign="middle",
        )
        made_label.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        left.add_widget(made_label)
        footer.add_widget(left)

        right = BoxLayout(orientation="vertical", size_hint_x=0.56, spacing=dp(2))
        self.discord_button = GameButton(
            text="DISCORD · elsty",
            color=(0.255, 0.300, 0.700, 1),
            text_color=(0.95, 0.96, 1.0, 1),
            height=dp(34),
            radius=11,
            font_size=sp(10.5),
        )
        self.discord_button.bind(on_release=self._discord)
        right.add_widget(self.discord_button)
        self.discord_link = Label(
            text=DISCORD_HANDLE,
            font_size=sp(7.5),
            color=(0.55, 0.68, 0.60, 0.9),
            halign="right",
            valign="middle",
            shorten=True,
        )
        self.discord_link.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        right.add_widget(self.discord_link)
        footer.add_widget(right)

        self.column.add_widget(footer)
        self.add_widget(self.column)

        self.quit = GameButton(
            text="ВЫХОД",
            color=(0.11, 0.16, 0.13, 0.78),
            text_color=(0.82, 0.90, 0.84, 1),
            size_hint=(None, None),
            size=(dp(84), dp(34)),
            pos_hint={"right": 0.985, "top": 0.99},
            font_size=sp(10.5),
            radius=10,
        )
        self.quit.bind(on_release=self._quit)
        self.add_widget(self.quit)

        Clock.schedule_once(lambda _dt: self.refresh_levels(), 0)

    # ------------------------------------------------------------------
    @staticmethod
    def _spacer(height: float) -> Widget:
        return Widget(size_hint_y=None, height=height)

    def on_enter(self) -> None:
        self.backdrop.running = True
        self.refresh_levels()

    def on_leave(self) -> None:
        self.backdrop.running = False

    def refresh_levels(self) -> None:
        unlocked = max(1, min(len(LEVELS), PROGRESS.unlocked))
        self.summary.text = f"ОТКРЫТО {unlocked} ИЗ {len(LEVELS)}"
        for index, (level, tile) in enumerate(zip(LEVELS, self.level_buttons)):
            available = PROGRESS.is_unlocked(index)
            stars = PROGRESS.stars(level.id) if available else 0
            best_wave = PROGRESS.best_wave(level.id) if available else 0
            tile.set_data(available, stars, best_wave)

    def _play(self, index: int) -> None:
        if not PROGRESS.is_unlocked(index):
            return
        game = self.screen_manager.get_screen("game")
        game.start_level(index)
        self.screen_manager.current = "game"

    def _quit(self, _instance) -> None:
        self.app_ref.stop()

    def _discord(self, *_args) -> None:
        result = open_url(DISCORD_URL)
        messages = {
            "opened": ("Ссылка открыта в браузере", (0.60, 0.94, 0.64, 1)),
            "copied": ("Ссылка скопирована в буфер", (0.98, 0.86, 0.48, 1)),
            "failed": ("Не удалось открыть ссылку", (1.0, 0.55, 0.48, 1)),
        }
        text, color = messages.get(result, messages["failed"])
        self.discord_link.text = text
        self.discord_link.color = color
        if self._discord_timer is not None:
            self._discord_timer.cancel()
        self._discord_timer = Clock.schedule_once(self._restore_discord_link, 2.6)

    def _restore_discord_link(self, *_args) -> None:
        self._discord_timer = None
        self.discord_link.text = DISCORD_HANDLE
        self.discord_link.color = (0.55, 0.68, 0.60, 0.9)


class PauseOverlay(Overlay):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        box = MenuCard(
            orientation="vertical",
            size_hint=(0.84, None),
            height=dp(292),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            padding=(dp(20), dp(18)),
            spacing=dp(12),
        )
        title = Label(
            text="ПАУЗА",
            font_size=sp(26),
            bold=True,
            color=(1.0, 0.84, 0.35, 1),
            size_hint_y=None,
            height=dp(42),
            halign="center",
            valign="middle",
        )
        title.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        box.add_widget(title)

        self.continue_button = GameButton("ПРОДОЛЖИТЬ", color=(0.16, 0.55, 0.30, 1))
        self.restart_button = GameButton("ЗАНОВО", color=(0.36, 0.30, 0.12, 1))
        self.menu_button = GameButton("В МЕНЮ", color=(0.30, 0.13, 0.12, 1))
        for button in (
            self.continue_button,
            self.restart_button,
            self.menu_button,
        ):
            box.add_widget(button)

        self.add_panel(box)


class UpgradeOverlay(Overlay):
    """Общие улучшения героя и базы. Открывается отдельной кнопкой."""

    dim_alpha = 0.30

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.arena = None
        box = MenuCard(
            orientation="vertical",
            size_hint=(0.9, None),
            height=dp(512),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            padding=(dp(18), dp(16)),
            spacing=dp(6),
        )
        self.title = Label(
            text="УЛУЧШЕНИЯ",
            font_size=sp(23),
            bold=True,
            color=(1.0, 0.84, 0.35, 1),
            size_hint_y=None,
            height=dp(36),
            halign="center",
            valign="middle",
        )
        self.title.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        box.add_widget(self.title)

        self.gold_label = Label(
            text="",
            font_size=sp(13),
            bold=True,
            color=(1.0, 0.86, 0.42, 1),
            size_hint_y=None,
            height=dp(24),
            halign="center",
            valign="middle",
        )
        self.gold_label.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        box.add_widget(self.gold_label)

        self.buttons = {}
        for key, data in GLOBAL_UPGRADES.items():
            button = GameButton(
                text="",
                color=(0.11, 0.27, 0.22, 1),
                height=dp(64),
                radius=12,
                font_size=sp(11.5),
            )
            button.bind(on_release=lambda _inst, k=key: self._buy(k))
            box.add_widget(button)
            self.buttons[key] = button

        self.close_button = GameButton(
            "ЗАКРЫТЬ",
            color=(0.22, 0.24, 0.28, 1),
            height=dp(46),
            radius=12,
            font_size=sp(14),
        )
        box.add_widget(self.close_button)

        self.add_panel(box)

    def open(self, arena) -> None:
        self.arena = arena
        self.refresh()
        self.visible = True

    def refresh(self) -> None:
        if self.arena is None:
            return
        self.gold_label.text = f"Золото: {int(self.arena.gold)}"
        for key, button in self.buttons.items():
            data = GLOBAL_UPGRADES[key]
            level = self.arena.upgrades.get(key, 0)
            maxed = self.arena.upgrade_maxed(key)
            cost = self.arena.upgrade_cost(key)
            price = "макс." if maxed else f"{cost} з."
            button.text = (
                f"{data['name']}  ур. {level}/{data['max_level']}\n"
                f"{data['desc']} · {price}"
            )
            button.disabled = maxed or self.arena.gold < cost

    def _buy(self, key: str) -> None:
        if self.arena is None:
            return
        ok, message = self.arena.buy_upgrade(key)
        self.arena.on_toast(message, "gold" if ok else "bad")
        self.refresh()


class ShopOverlay(Overlay):
    """Магазин разовой помощи: лечение, ремонт, клич и наёмник."""

    dim_alpha = 0.30

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.arena = None
        box = MenuCard(
            orientation="vertical",
            size_hint=(0.9, None),
            height=dp(452),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            padding=(dp(18), dp(16)),
            spacing=dp(6),
        )
        title = Label(
            text="МАГАЗИН",
            font_size=sp(23),
            bold=True,
            color=(1.0, 0.84, 0.35, 1),
            size_hint_y=None,
            height=dp(36),
            halign="center",
            valign="middle",
        )
        title.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        box.add_widget(title)

        self.gold_label = Label(
            text="",
            font_size=sp(13),
            bold=True,
            color=(1.0, 0.86, 0.42, 1),
            size_hint_y=None,
            height=dp(24),
            halign="center",
            valign="middle",
        )
        self.gold_label.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        box.add_widget(self.gold_label)

        self.buttons = {}
        for key, data in SHOP_ITEMS.items():
            button = GameButton(
                text="",
                color=data["color"],
                height=dp(64),
                radius=12,
                font_size=sp(11.5),
            )
            button.bind(on_release=lambda _inst, k=key: self._buy(k))
            box.add_widget(button)
            self.buttons[key] = button

        self.close_button = GameButton(
            "ЗАКРЫТЬ",
            color=(0.22, 0.24, 0.28, 1),
            height=dp(46),
            radius=12,
            font_size=sp(14),
        )
        box.add_widget(self.close_button)

        self.add_panel(box)

    def open(self, arena) -> None:
        self.arena = arena
        self.refresh()
        self.visible = True

    def refresh(self) -> None:
        if self.arena is None:
            return
        self.gold_label.text = f"Золото: {int(self.arena.gold)}"
        for key, button in self.buttons.items():
            data = SHOP_ITEMS[key]
            button.text = f"{data['name']} · {data['cost']} з.\n{data['desc']}"
            allowed, _reason = self.arena.item_available(key)
            button.disabled = not allowed

    def _buy(self, key: str) -> None:
        if self.arena is None:
            return
        ok, message = self.arena.buy_item(key)
        self.arena.on_toast(message, "gold" if ok else "bad")
        self.refresh()


class BuildingOverlay(Overlay):
    """Карточка выбранной постройки: улучшение и прочность."""

    dismiss_on_outside = True
    dim_alpha = 0.35

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.arena = None
        self.building = None

        box = MenuCard(
            orientation="vertical",
            size_hint=(0.9, None),
            height=dp(302),
            pos_hint={"center_x": 0.5, "y": 0.09},
            padding=(dp(16), dp(12)),
            spacing=dp(5),
        )
        self.title = Label(
            text="",
            font_size=sp(20),
            bold=True,
            color=(1.0, 0.84, 0.35, 1),
            size_hint_y=None,
            height=dp(30),
            halign="center",
            valign="middle",
        )
        self.title.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        box.add_widget(self.title)

        self.hp_label = Label(
            text="",
            font_size=sp(11),
            color=(0.80, 0.86, 0.82, 1),
            size_hint_y=None,
            height=dp(18),
            halign="center",
            valign="middle",
        )
        self.hp_label.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        box.add_widget(self.hp_label)

        self.effect_label = Label(
            text="",
            font_size=sp(13),
            bold=True,
            color=(0.92, 0.96, 0.92, 1),
            size_hint_y=None,
            height=dp(30),
            halign="center",
            valign="middle",
        )
        self.effect_label.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        box.add_widget(self.effect_label)

        self.next_label = Label(
            text="",
            font_size=sp(10.5),
            color=(0.66, 0.80, 0.70, 1),
            size_hint_y=None,
            height=dp(22),
            halign="center",
            valign="middle",
        )
        self.next_label.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        box.add_widget(self.next_label)

        self.upgrade_button = GameButton(
            "УЛУЧШИТЬ",
            color=(0.16, 0.48, 0.30, 1),
            height=dp(50),
            radius=12,
            font_size=sp(14),
        )
        self.upgrade_button.bind(on_release=lambda *_a: self._upgrade())
        box.add_widget(self.upgrade_button)

        self.close_button = GameButton(
            "ЗАКРЫТЬ",
            color=(0.22, 0.24, 0.28, 1),
            height=dp(42),
            radius=12,
            font_size=sp(13),
        )
        box.add_widget(self.close_button)

        self.add_panel(box)

    def open(self, arena, building, info: dict) -> None:
        self.arena = arena
        self.building = building
        self.refresh(info)
        self.visible = True

    def refresh(self, info: dict | None = None) -> None:
        if self.arena is None or self.building is None:
            return
        if info is None:
            info = self.arena.building_info(self.building)
        self.title.text = f"{info['name'].upper()} · ур. {info['level']}"
        self.hp_label.text = (
            f"Прочность {int(info['hp'])} / {int(info['max_hp'])}"
        )
        self.effect_label.text = info["effect"]
        if info["maxed"]:
            self.next_label.text = "Максимальный уровень"
            self.upgrade_button.text = "МАКС."
            self.upgrade_button.disabled = True
        else:
            self.next_label.text = info["next"]
            self.upgrade_button.text = f"УЛУЧШИТЬ · {info['cost']} з."
            self.upgrade_button.disabled = self.arena.gold < info["cost"]

    def _upgrade(self) -> None:
        if self.arena is None or self.building is None:
            return
        ok, message = self.arena.upgrade_building(self.building)
        self.arena.on_toast(message, "gold" if ok else "bad")
        if self.building in self.arena.buildings:
            self.refresh()
        else:
            self.close()


class EndOverlay(Overlay):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        box = MenuCard(
            orientation="vertical",
            size_hint=(0.88, None),
            height=dp(418),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            padding=(dp(20), dp(16)),
            spacing=dp(6),
        )
        self.title = Label(
            text="",
            font_size=sp(27),
            bold=True,
            color=(1.0, 0.84, 0.35, 1),
            size_hint_y=None,
            height=dp(44),
            halign="center",
            valign="middle",
        )
        self.title.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        box.add_widget(self.title)

        self.level_label = Label(
            text="",
            font_size=sp(12),
            color=(0.78, 0.90, 0.82, 1),
            size_hint_y=None,
            height=dp(20),
            halign="center",
            valign="middle",
        )
        self.level_label.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        box.add_widget(self.level_label)

        self.stars_label = Label(
            text="",
            font_size=sp(25),
            bold=True,
            color=(1.0, 0.82, 0.28, 1),
            size_hint_y=None,
            height=dp(32),
            halign="center",
            valign="middle",
        )
        self.stars_label.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        box.add_widget(self.stars_label)

        self.unlock_label = Label(
            text="",
            font_size=sp(11.5),
            bold=True,
            color=(0.54, 0.94, 0.58, 1),
            size_hint_y=None,
            height=dp(22),
            halign="center",
            valign="middle",
        )
        self.unlock_label.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        box.add_widget(self.unlock_label)

        self.stats_label = Label(
            text="",
            font_size=sp(12),
            color=(0.86, 0.93, 0.88, 1),
            size_hint_y=None,
            height=dp(62),
            halign="center",
            valign="middle",
        )
        self.stats_label.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        box.add_widget(self.stats_label)

        self.again_button = GameButton("ИГРАТЬ СНОВА", color=(0.16, 0.55, 0.30, 1))
        self.menu_button = GameButton("К ВЫБОРУ КАРТЫ", color=(0.30, 0.13, 0.12, 1))
        box.add_widget(self.again_button)
        box.add_widget(self.menu_button)

        self.add_panel(box)

    def open(self, win: bool, stats: dict, stars: int = 0,
             unlock_name: str = "", level_name: str = "") -> None:
        total = int(stats.get("total_waves", TOTAL_WAVES))
        wave = int(stats.get("wave", 1))
        waves = total if win else max(0, wave - 1)
        self.title.text = "БАЗА ВЫСТОЯЛА!" if win else "БАЗА ПАЛА"
        self.title.color = (
            (1.0, 0.84, 0.35, 1) if win else (1.0, 0.48, 0.42, 1)
        )
        self.level_label.text = level_name
        if win:
            self.stars_label.text = f"ЗВЁЗДЫ: {stars} / 3"
            self.stars_label.color = (1.0, 0.82, 0.28, 1)
        else:
            self.stars_label.text = "ЗВЁЗДЫ: 0 / 3"
            self.stars_label.color = (0.58, 0.64, 0.58, 1)
        self.unlock_label.text = (
            f"Открыта новая карта: {unlock_name}!" if unlock_name else ""
        )
        self.stats_label.text = (
            f"Отбито волн: {waves} / {total}\n"
            f"Добыто золота: {int(stats.get('gold_earned', 0))} · "
            f"Побед: {int(stats.get('kills', 0))}\n"
            f"Построек осталось: {int(stats.get('buildings', 0))}"
        )
        self.visible = True


class GameScreen(Screen):
    def __init__(self, app_ref, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.name = "game"
        self.app_ref = app_ref
        self.screen_manager = screen_manager
        self.level_index = 0
        self._selected_level = 0

        self.arena = Arena(self._on_toast, self._on_end, self._on_building)
        self.add_widget(self.arena)

        self.hud = HUD(on_pause=self._toggle_pause, on_shop=self._open_shop)
        self.add_widget(self.hud)

        self.build_bar = BuildBar(
            on_build=self._select_build,
            on_upgrades=self._open_upgrades,
        )
        self.add_widget(self.build_bar)

        self.toast = Toast()
        self.add_widget(self.toast)

        self.pause = PauseOverlay()
        self.add_widget(self.pause)
        self.upgrades = UpgradeOverlay()
        self.add_widget(self.upgrades)
        self.shop = ShopOverlay()
        self.add_widget(self.shop)
        self.building_panel = BuildingOverlay()
        self.add_widget(self.building_panel)
        self.end = EndOverlay()
        self.add_widget(self.end)

        self.pause.continue_button.bind(on_release=self._close_pause)
        self.pause.restart_button.bind(on_release=self._restart)
        self.pause.menu_button.bind(on_release=self._menu)
        self.upgrades.close_button.bind(on_release=self._close_upgrades)
        self.shop.close_button.bind(on_release=self._close_shop)
        self.building_panel.close_button.bind(
            on_release=lambda *_a: self.building_panel.close()
        )
        self.end.again_button.bind(on_release=self._restart)
        self.end.menu_button.bind(on_release=self._menu)

        self._sync = Clock.schedule_interval(self._sync_hud, 0.1)
        Window.bind(on_key_down=self._on_key_down)

    # ------------------------------------------------------------------
    def start_level(self, index: int) -> None:
        """Выбор карты из меню. Старт произойдёт при входе на экран."""
        self._selected_level = max(0, min(len(LEVELS) - 1, index))

    def on_enter(self) -> None:
        self._close_all()
        self.level_index = self._selected_level
        level = LEVELS[self.level_index]
        self.arena.load_level(level, self.level_index)
        self.arena.start_new()
        self.arena.resume()
        self._sync_hud()
        self.toast.show(
            f"{level.name}: {level.desc}",
            "gold",
            3.8,
        )

    def on_leave(self) -> None:
        self._close_all()
        self.arena.stop()

    # ------------------------------------------------------------------
    def _on_toast(self, text: str, kind: str = "info") -> None:
        self.toast.show(text, kind)

    def _on_end(self, win: bool, stats: dict) -> None:
        self._hide_toast()
        self.building_panel.close()
        self.upgrades.close()
        self.shop.close()
        self.pause.visible = False
        level = self.arena.level
        index = self.arena.level_index
        total = int(level.waves)
        waves = total if win else max(0, int(stats.get("wave", 1)) - 1)
        ratio = self.arena.base_hp / max(1.0, self.arena.base_max_hp)
        stars, newly_unlocked = PROGRESS.record(
            index, level.id, win, waves, ratio, total
        )
        unlock_name = ""
        if newly_unlocked and index + 1 < len(LEVELS):
            unlock_name = LEVELS[index + 1].name
        self.end.open(win, stats, stars, unlock_name, level.name)

    def _on_building(self, building, info: dict) -> None:
        if self.arena.ended:
            return
        self.building_panel.open(self.arena, building, info)

    def _hide_toast(self) -> None:
        if self.toast._timer is not None:
            self.toast._timer.cancel()
            self.toast._timer = None
        self.toast.label.opacity = 0

    def _sync_hud(self, *_args) -> None:
        stats = self.arena.stats()
        self.hud.update_stats(stats)
        self.build_bar.set_state(stats, self.arena.build_mode)
        if self.upgrades.visible:
            self.upgrades.refresh()
        if self.shop.visible:
            self.shop.refresh()
        if self.building_panel.visible:
            if self.building_panel.building in self.arena.buildings:
                self.building_panel.refresh()
            else:
                self.building_panel.close()

    def _on_key_down(self, _window, key, *_args):
        if self.manager is None or self.manager.current != "game":
            return False
        if key != 27:
            return False
        if self.end.visible:
            return True
        if self.building_panel.visible:
            self.building_panel.close()
            return True
        if self.shop.visible:
            self._close_shop()
            return True
        if self.upgrades.visible:
            self._close_upgrades()
            return True
        self._toggle_pause(None)
        return True

    # ------------------------------------------------------------------
    def _select_build(self, kind: str) -> None:
        if self.arena.ended:
            return
        mode = self.arena.set_build_mode(kind)
        self.build_bar.set_state(self.arena.stats(), mode)
        if mode:
            self.toast.show(
                f"{mode.upper()}: нажми на свободную площадку",
                "blue",
                1.8,
            )

    def _open_upgrades(self, *_args) -> None:
        if self.arena.ended:
            return
        self._hide_toast()
        self.building_panel.close()
        self.shop.close()
        self.pause.visible = False
        if self.arena.paused:
            self.arena.resume()
        # Улучшения открываются поверх боя и не останавливают игру.
        self.upgrades.open(self.arena)

    def _close_upgrades(self, *_args) -> None:
        self.upgrades.close()

    def _open_shop(self, *_args) -> None:
        if self.arena.ended:
            return
        self._hide_toast()
        self.building_panel.close()
        self.upgrades.close()
        self.pause.visible = False
        if self.arena.paused:
            self.arena.resume()
        self.shop.open(self.arena)

    def _close_shop(self, *_args) -> None:
        self.shop.close()

    def _toggle_pause(self, _instance=None) -> None:
        if self.arena.ended or self.end.visible:
            return
        if self.pause.visible:
            self._close_pause()
            return
        self._hide_toast()
        self.building_panel.close()
        self.shop.close()
        self.upgrades.close()
        self.pause.visible = True
        self.arena.pause()

    def _close_pause(self, *_args) -> None:
        self.pause.visible = False
        if not self.arena.ended:
            self.arena.resume()

    def _close_all(self) -> None:
        self.pause.visible = False
        self.upgrades.visible = False
        self.shop.visible = False
        self.building_panel.visible = False
        self.end.visible = False

    def _restart(self, *_args) -> None:
        self._close_all()
        self.arena.start_new()
        self.arena.resume()
        self._sync_hud()
        self.toast.show("Новая оборона началась", "gold", 2.0)

    def _menu(self, *_args) -> None:
        self._close_all()
        self.arena.stop()
        self.screen_manager.current = "menu"
