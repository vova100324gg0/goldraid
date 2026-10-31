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
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from ..world.arena import Arena
from ..core.config import (
    AUTHOR,
    BUILD_TYPES,
    DISCORD_HANDLE,
    DISCORD_URL,
    GAME_TITLE,
    GLOBAL_UPGRADES,
    SAFE_BOTTOM,
    SHOP_ITEMS,
    TOTAL_WAVES,
    UI_MUTED,
    VERSION,
)
from ..render.gfx import circle, poly, ring
from ..world.levels import LEVELS, TUTORIAL, TUTORIAL_HINTS
from ..core.achievements import ACHIEVEMENTS, check_achievements, unlocked_count
from ..core.audio import MENU_THEME, THEME_BY_LEVEL, music
from ..core.changelog import CHANGELOG, latest_version
from ..core.i18n import LANGUAGES, set_language, t
from ..core.progress import PROGRESS
from ..core.sfx import sfx
from ..core.util import open_url
from .widgets import (
    BuildBar,
    GameButton,
    HUD,
    Overlay,
    RibbonLabel,
    StarRow,
    Toast,
    WavePrompt,
)
from .fonts import DISPLAY_FONT


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
        # Монеты, медленно плывущие вверх: оживляют фон и напоминают,
        # за чем мы вообще здесь охотимся.
        self._coins = [
            {
                "x": rng.uniform(0.03, 0.97),
                "y": rng.random(),
                "r": dp(rng.uniform(3.0, 6.5)),
                "v": rng.uniform(0.006, 0.020),
                "sway": rng.uniform(0.003, 0.012),
                "sway_speed": rng.uniform(0.4, 1.1),
                "phase": rng.uniform(0.0, math.tau),
                "twinkle": rng.uniform(0.7, 1.6),
                "alpha": rng.uniform(0.30, 0.68),
            }
            for _ in range(7)
        ]
        self._coin_rim_colors = []
        self._coin_rims = []
        self._coin_face_colors = []
        self._coin_faces = []
        self._coin_shine_colors = []
        self._coin_shines = []
        with self.canvas.before:
            self._band_colors = []
            self._band_rects = []
            for color in self.BANDS:
                band_color = Color(*color)
                band_rect = Rectangle()
                self._band_colors.append(band_color)
                self._band_rects.append(band_rect)

            self._glow_color = Color(1.0, 0.82, 0.42, 0.07)
            self._glow = Ellipse()
            self._glow_b_color = Color(0.30, 0.90, 0.58, 0.04)
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

            for coin in self._coins:
                rim_color = Color(0.44, 0.28, 0.04, coin["alpha"] * 0.85)
                rim = Ellipse()
                face_color = Color(1.0, 0.79, 0.24, coin["alpha"])
                face = Ellipse()
                shine_color = Color(1.0, 0.96, 0.72, coin["alpha"] * 0.75)
                shine = Ellipse()
                self._coin_rim_colors.append(rim_color)
                self._coin_rims.append(rim)
                self._coin_face_colors.append(face_color)
                self._coin_faces.append(face)
                self._coin_shine_colors.append(shine_color)
                self._coin_shines.append(shine)
        self.bind(pos=self._layout, size=self._layout)
        self._event = Clock.schedule_interval(self._animate, 1 / 30)
        self._layout()

    def dispose(self) -> None:
        self.running = False
        event = getattr(self, "_event", None)
        if event is not None:
            event.cancel()
            self._event = None

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
            self.x + width * 0.5 - width * 0.55,
            self.y + height * 0.58,
        )
        self._glow.size = (width * 1.10, height * 0.44)
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

    def _update_coins(self) -> None:
        width, height = self.size
        if width <= 0 or height <= 0:
            return
        time = self._t
        for coin, rim_c, rim, face_c, face, shine_c, shine in zip(
            self._coins,
            self._coin_rim_colors,
            self._coin_rims,
            self._coin_face_colors,
            self._coin_faces,
            self._coin_shine_colors,
            self._coin_shines,
        ):
            x = self.x + (
                coin["x"]
                + math.sin(time * coin["sway_speed"] + coin["phase"])
                * coin["sway"]
            ) % 1.0 * width
            y = self.y + ((coin["y"] + time * coin["v"]) % 1.0) * height
            pulse = 0.88 + 0.14 * math.sin(time * coin["twinkle"] + coin["phase"])
            radius = coin["r"]
            alpha = coin["alpha"] * pulse
            rim_c.a = alpha * 0.85
            face_c.a = alpha
            shine_c.a = alpha * 0.75
            rim.pos = (x - radius, y - radius)
            rim.size = (radius * 2, radius * 2)
            inner = radius * 0.78
            face.pos = (x - inner, y - inner)
            face.size = (inner * 2, inner * 2)
            shine.pos = (x - radius * 0.45, y + radius * 0.05)
            shine.size = (radius * 0.62, radius * 0.40)

    def _animate(self, dt: float) -> None:
        if not self.running:
            return
        self._t += dt
        self._glow_color.a = 0.062 + 0.018 * math.sin(self._t * 0.9)
        self._glow_b_color.a = 0.035 + 0.012 * math.sin(self._t * 0.6 + 1.2)
        self._update_sparks()
        self._update_coins()


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
        Clock.schedule_once(lambda _dt: self._redraw(), 0)
        # Три золотые искры медленно облетают монету.
        self.running = True
        self._t = 0.0
        self._orbit_group = InstructionGroup()
        self.canvas.add(self._orbit_group)
        self._orbit_dots = []
        for index in range(3):
            dot_color = Color(1.0, 0.92, 0.55, 0.0)
            dot = Ellipse()
            self._orbit_group.add(dot_color)
            self._orbit_group.add(dot)
            self._orbit_dots.append((dot_color, dot, index))
        self._orbit_event = Clock.schedule_interval(self._orbit_tick, 1 / 30)

    def _orbit_tick(self, dt: float) -> None:
        if not self.running:
            return
        self._t += dt
        cx = self.x + self.width * 0.5
        cy = self.y + self.height * 0.5
        radius = min(self.width, self.height) * 0.5
        if radius <= 1:
            return
        for dot_color, dot, index in self._orbit_dots:
            angle = self._t * 0.9 + index * math.tau / 3.0
            orbit = radius * 1.22
            x = cx + math.cos(angle) * orbit
            y = cy + math.sin(angle) * orbit
            size = dp(2.0) + dp(1.1) * (0.5 + 0.5 * math.sin(angle * 2))
            dot.pos = (x - size, y - size)
            dot.size = (size * 2, size * 2)
            dot_color.a = 0.45 + 0.35 * math.sin(angle * 1.7) ** 2

    def _redraw(self, *_args) -> None:
        group = self._group
        group.clear()
        cx = self.x + self.width * 0.5
        cy = self.y + self.height * 0.5
        radius = min(self.width, self.height) * 0.5
        if radius <= 1:
            return
        group.add(Color(1.0, 0.80, 0.30, 0.17))
        group.add(
            Ellipse(
                pos=(cx - radius * 1.30, cy - radius * 1.30),
                size=(radius * 2.60, radius * 2.60),
            )
        )
        group.add(Color(1.0, 0.86, 0.44, 0.12))
        group.add(
            Ellipse(
                pos=(cx - radius * 1.16, cy - radius * 1.16),
                size=(radius * 2.32, radius * 2.32),
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
        cx = self.x + self.width * 0.5
        cy = self.y + self.height * 0.5
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
        self.status = Badge(t("ИГРАТЬ"))
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
        self.title.text = t(self.level.name)
        self.subtitle.text = t(self.level.subtitle)
        self.meta.text = t("{waves} волн · {roads} дороги").format(
            waves=self.level.waves, roads=len(self.level.routes)
        )
        self.stars.count = max(0, min(3, stars))
        if not available:
            self.record.text = t("пройди предыдущую")
        elif best_wave:
            self.record.text = t("лучшая {best}/{total}").format(
                best=best_wave, total=self.level.waves
            )
        else:
            self.record.text = t("ещё не пройдена")
        if available:
            self.status.text = t("ИГРАТЬ")
            self.status.set_colors((0.20, 0.60, 0.33, 0.94), (0.94, 1.0, 0.95, 1))
            self.title.color = (0.96, 0.99, 0.95, 1)
            self.subtitle.color = (0.72, 0.86, 0.77, 1)
            self.meta.color = (1.0, 0.84, 0.44, 0.95)
            self.record.color = (0.66, 0.78, 0.69, 1)
        else:
            self.status.text = t("ЗАКРЫТО")
            self.status.set_colors((0.18, 0.23, 0.20, 0.94), (0.62, 0.68, 0.62, 1))
            self.title.color = (0.66, 0.73, 0.67, 1)
            self.subtitle.color = (0.52, 0.61, 0.54, 1)
            self.meta.color = (0.68, 0.62, 0.44, 0.8)
            self.record.color = (0.50, 0.58, 0.52, 1)
        self.medallion.set_locked(self._locked)
        self._apply_tint()
        state = t("открыто") if available else t("закрыто")
        self.text = t("{name}\n{waves} волн · {state}").format(
            name=t(self.level.name), waves=self.level.waves, state=state
        )

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


class InfoOverlay(Overlay):
    """Экран «Об игре»: автор, лицензия, управление и связь."""

    dim_alpha = 0.62
    dismiss_on_outside = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        box = MenuCard(
            orientation="vertical",
            size_hint=(0.9, None),
            height=dp(470),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            padding=(dp(18), dp(16)),
            spacing=dp(7),
        )

        title = Label(
            text=t("ОБ АВТОРЕ"),
            font_size=sp(24),
            bold=True,
            color=(1.0, 0.84, 0.35, 1),
            size_hint_y=None,
            height=dp(36),
            halign="center",
            valign="middle",
        )
        title.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        box.add_widget(title)

        version_label = Label(
            text=t("версия {version} · {title}").format(
                version=VERSION, title=t(GAME_TITLE)
            ),
            font_size=sp(10.5),
            bold=True,
            color=UI_MUTED,
            size_hint_y=None,
            height=dp(20),
            halign="center",
            valign="middle",
        )
        version_label.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        box.add_widget(version_label)
        box.add_widget(Divider())

        for text, height, color, font in (
            (
                t(
                    "Защищай ворота: собирай золото, строй башни, шахты, казармы "
                    "и тотемы, отбивай волны врагов."
                ),
                dp(44),
                (0.86, 0.94, 0.88, 1),
                sp(10.5),
            ),
            (
                t("Автор: {author}").format(author=AUTHOR),
                dp(20),
                (0.98, 0.84, 0.42, 1),
                sp(11),
            ),
            (
                t(
                    "© 2026 elsty. Все права защищены.\n"
                    "Проприетарная лицензия: копирование, изменение\n"
                    "и распространение игры запрещены."
                ),
                dp(56),
                (0.74, 0.86, 0.78, 1),
                sp(9.5),
            ),
        ):
            label = Label(
                text=text,
                font_size=font,
                color=color,
                size_hint_y=None,
                height=height,
                halign="center",
                valign="middle",
            )
            label.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
            box.add_widget(label)

        controls = Label(
            text=t(
                "Тяни палец по полю — герой идёт за ним.\n"
                "Собирай золото и строй обороны вокруг базы."
            ),
            font_size=sp(9.5),
            color=UI_MUTED,
            size_hint_y=None,
            height=dp(58),
            halign="center",
            valign="middle",
        )
        controls.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        box.add_widget(controls)

        self.discord_button = GameButton(
            "DISCORD · elsty",
            color=(0.255, 0.300, 0.700, 1),
            text_color=(0.95, 0.96, 1.0, 1),
            height=dp(44),
            radius=13,
            font_size=sp(13),
        )
        box.add_widget(self.discord_button)

        self.discord_status = Label(
            text=DISCORD_HANDLE,
            font_size=sp(8.5),
            color=(0.62, 0.74, 0.66, 0.9),
            size_hint_y=None,
            height=dp(16),
            halign="center",
            valign="middle",
            shorten=True,
            max_lines=1,
        )
        self.discord_status.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        box.add_widget(self.discord_status)

        self.close_button = GameButton(
            t("ЗАКРЫТЬ"),
            color=(0.22, 0.24, 0.28, 1),
            height=dp(44),
            radius=13,
            font_size=sp(14),
        )
        box.add_widget(self.close_button)

        self.add_panel(box)

    def set_discord_status(self, text: str, color) -> None:
        self.discord_status.text = text
        self.discord_status.color = color


class SettingsOverlay(Overlay):
    """Настройки: язык, музыка, качество графики, сброс и «Что нового»."""

    dim_alpha = 0.55

    _LANG_LABEL = {"ru": "РУССКИЙ", "en": "АНГЛИЙСКИЙ"}
    _QUALITY_LABEL = {
        "auto": "АВТО",
        "high": "ВЫСОКОЕ",
        "low": "НИЗКОЕ",
    }

    def __init__(
        self,
        on_language=None,
        on_music=None,
        on_sfx=None,
        on_quality=None,
        on_reset=None,
        on_whats_new=None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.on_language = on_language or (lambda *_a: None)
        self.on_music = on_music or (lambda *_a: None)
        self.on_sfx = on_sfx or (lambda *_a: None)
        self.on_quality = on_quality or (lambda *_a: None)
        self.on_reset = on_reset or (lambda *_a: None)
        self.on_whats_new = on_whats_new or (lambda *_a: None)
        self._confirm_reset = False
        self._confirm_event = None

        box = MenuCard(
            orientation="vertical",
            size_hint=(0.92, None),
            height=dp(530),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            padding=(dp(18), dp(14)),
            spacing=dp(6),
        )
        self.title = Label(
            text=t("НАСТРОЙКИ"),
            font_size=sp(23),
            bold=True,
            color=(1.0, 0.84, 0.35, 1),
            size_hint_y=None,
            height=dp(34),
            halign="center",
            valign="middle",
        )
        self.title.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        box.add_widget(self.title)

        box.add_widget(self._section(t("ЯЗЫК")))
        self.language_buttons = {}
        lang_row = self._row()
        for code in LANGUAGES:
            button = self._choice(t(self._LANG_LABEL.get(code, code)))
            button.bind(on_release=lambda _i, c=code: self.on_language(c))
            lang_row.add_widget(button)
            self.language_buttons[code] = button
        box.add_widget(lang_row)

        box.add_widget(self._section(t("МУЗЫКА")))
        self.music_button = GameButton(
            text="",
            color=(0.15, 0.30, 0.24, 1),
            height=dp(44),
            radius=12,
            font_size=sp(13),
        )
        self.music_button.bind(on_release=lambda *_a: self.on_music())
        box.add_widget(self.music_button)

        box.add_widget(self._section(t("ЗВУКИ")))
        self.sfx_button = GameButton(
            text="",
            color=(0.15, 0.30, 0.24, 1),
            height=dp(44),
            radius=12,
            font_size=sp(13),
        )
        self.sfx_button.bind(on_release=lambda *_a: self.on_sfx())
        box.add_widget(self.sfx_button)

        box.add_widget(self._section(t("КАЧЕСТВО ГРАФИКИ")))
        self.quality_buttons = {}
        quality_row = self._row()
        for mode in ("auto", "high", "low"):
            button = self._choice(
                t(self._QUALITY_LABEL.get(mode, mode))
            )
            button.bind(on_release=lambda _i, m=mode: self.on_quality(m))
            quality_row.add_widget(button)
            self.quality_buttons[mode] = button
        box.add_widget(quality_row)

        self.whats_new_button = GameButton(
            t("ЧТО НОВОГО"),
            color=(0.16, 0.22, 0.36, 1),
            text_color=(0.86, 0.92, 1.0, 1),
            height=dp(44),
            radius=12,
            font_size=sp(13),
        )
        self.whats_new_button.bind(on_release=lambda *_a: self.on_whats_new())
        box.add_widget(self.whats_new_button)

        self.reset_button = GameButton(
            t("СБРОСИТЬ ПРОГРЕСС"),
            color=(0.36, 0.16, 0.14, 1),
            text_color=(1.0, 0.84, 0.78, 1),
            height=dp(44),
            radius=12,
            font_size=sp(12.5),
        )
        self.reset_button.bind(on_release=self._tap_reset)
        box.add_widget(self.reset_button)

        self.close_button = GameButton(
            t("ЗАКРЫТЬ"),
            color=(0.22, 0.24, 0.28, 1),
            height=dp(44),
            radius=12,
            font_size=sp(14),
        )
        box.add_widget(self.close_button)

        self.add_panel(box)

    def _section(self, text: str) -> Label:
        label = Label(
            text=text,
            font_size=sp(10.5),
            bold=True,
            color=(0.62, 0.76, 0.66, 1),
            size_hint_y=None,
            height=dp(18),
            halign="left",
            valign="middle",
        )
        label.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        return label

    def _row(self) -> BoxLayout:
        return BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(44),
            spacing=dp(8),
        )

    def _choice(self, text: str) -> GameButton:
        return GameButton(
            text=text,
            color=(0.14, 0.18, 0.22, 1),
            text_color=(0.82, 0.88, 0.92, 1),
            height=dp(44),
            radius=12,
            font_size=sp(12),
        )

    def open(self, *_args) -> None:
        self._cancel_reset()
        self.refresh()
        super().open()

    def refresh(self) -> None:
        for code, button in self.language_buttons.items():
            button.set_active(code == PROGRESS.language)
        self.music_button.text = t("ВКЛ") if PROGRESS.music else t("ВЫКЛ")
        self.sfx_button.text = t("ВКЛ") if PROGRESS.sfx else t("ВЫКЛ")
        for mode, button in self.quality_buttons.items():
            button.set_active(mode == PROGRESS.quality)
        if not self._confirm_reset:
            self.reset_button.text = t("СБРОСИТЬ ПРОГРЕСС")

    def _tap_reset(self, *_args) -> None:
        if not self._confirm_reset:
            self._confirm_reset = True
            self.reset_button.text = t("ТОЧНО СБРОСИТЬ?")
            self._confirm_event = Clock.schedule_once(self._cancel_reset, 4.0)
            return
        self._cancel_reset()
        self.on_reset()

    def _cancel_reset(self, *_args) -> None:
        if self._confirm_event is not None:
            self._confirm_event.cancel()
            self._confirm_event = None
        self._confirm_reset = False
        if hasattr(self, "reset_button"):
            self.reset_button.text = t("СБРОСИТЬ ПРОГРЕСС")


class AchievementsOverlay(Overlay):
    """Список достижений: открытые подсвечены золотом."""

    dim_alpha = 0.55

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        count = len(ACHIEVEMENTS)
        box = MenuCard(
            orientation="vertical",
            size_hint=(0.92, None),
            height=dp(200) + count * dp(42),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            padding=(dp(18), dp(14)),
            spacing=dp(6),
        )
        self.title = Label(
            text=t("ДОСТИЖЕНИЯ"),
            font_size=sp(23),
            bold=True,
            color=(1.0, 0.84, 0.35, 1),
            size_hint_y=None,
            height=dp(34),
            halign="center",
            valign="middle",
        )
        self.title.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        box.add_widget(self.title)

        self.counter = Label(
            text="",
            font_size=sp(11),
            bold=True,
            color=(0.72, 0.84, 0.74, 1),
            size_hint_y=None,
            height=dp(20),
            halign="center",
            valign="middle",
        )
        self.counter.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        box.add_widget(self.counter)

        self.rows = []
        for _item in ACHIEVEMENTS:
            label = Label(
                text="",
                font_size=sp(11),
                color=(0.70, 0.78, 0.72, 1),
                size_hint_y=None,
                height=dp(42),
                halign="left",
                valign="middle",
            )
            label.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
            box.add_widget(label)
            self.rows.append(label)

        self.close_button = GameButton(
            t("ЗАКРЫТЬ"),
            color=(0.22, 0.24, 0.28, 1),
            height=dp(44),
            radius=12,
            font_size=sp(14),
        )
        box.add_widget(self.close_button)

        self.add_panel(box)

    def open(self, *_args) -> None:
        self.refresh()
        super().open()

    def refresh(self) -> None:
        unlocked = unlocked_count(PROGRESS)
        self.counter.text = t("ОТКРЫТО {unlocked} ИЗ {total}").format(
            unlocked=unlocked, total=len(ACHIEVEMENTS)
        )
        for item, label in zip(ACHIEVEMENTS, self.rows):
            done = PROGRESS.has_achievement(item["id"])
            mark = "★ " if done else "• "
            label.text = mark + f"{t(item['name'])}\n{t(item['desc'])}"
            label.color = (
                (1.0, 0.86, 0.44, 1) if done else (0.60, 0.68, 0.62, 1)
            )


class WhatsNewOverlay(Overlay):
    """История изменений текущей версии."""

    dim_alpha = 0.55

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.version = latest_version() or VERSION
        lines = CHANGELOG.get(self.version, [])
        box = MenuCard(
            orientation="vertical",
            size_hint=(0.92, None),
            height=dp(160) + len(lines) * dp(34),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            padding=(dp(18), dp(14)),
            spacing=dp(6),
        )
        self.title = Label(
            text="",
            font_size=sp(21),
            bold=True,
            color=(1.0, 0.84, 0.35, 1),
            size_hint_y=None,
            height=dp(34),
            halign="center",
            valign="middle",
        )
        self.title.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        box.add_widget(self.title)

        self.bullets = []
        for _line in lines:
            label = Label(
                text="",
                font_size=sp(11),
                color=(0.84, 0.92, 0.86, 1),
                size_hint_y=None,
                height=dp(34),
                halign="left",
                valign="middle",
            )
            label.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
            box.add_widget(label)
            self.bullets.append(label)

        self.close_button = GameButton(
            t("ЗАКРЫТЬ"),
            color=(0.22, 0.24, 0.28, 1),
            height=dp(44),
            radius=12,
            font_size=sp(14),
        )
        box.add_widget(self.close_button)

        self.add_panel(box)

    def open(self, *_args) -> None:
        self.refresh()
        super().open()

    def refresh(self) -> None:
        self.title.text = t("ЧТО НОВОГО · {version}").format(version=self.version)
        for label, line in zip(self.bullets, CHANGELOG.get(self.version, [])):
            label.text = t(line)


class MenuScreen(Screen):
    def __init__(self, app_ref, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.name = "menu"
        self.app_ref = app_ref
        self.screen_manager = screen_manager
        self._discord_timer = None
        self._fun_t = 0.0
        self._fun_event = None

        self.backdrop = Backdrop()
        self.add_widget(self.backdrop)

        self.scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=0,
            scroll_type=["bars", "content"],
        )
        self.add_widget(self.scroll)

        self._base_height = dp(344)
        self.column = BoxLayout(
            orientation="vertical",
            size_hint=(1, None),
            height=self._base_height,
            padding=(dp(13), 0, dp(13), 0),
        )
        self.scroll.add_widget(self.column)

        # ---------------------------------------------------------- бренд
        brand = FloatLayout(size_hint_y=None, height=dp(164))
        self.emblem = CoinEmblem()
        self.emblem.pos_hint = {"center_x": 0.5, "top": 0.995}
        brand.add_widget(self.emblem)

        title = Label(
            text=t(GAME_TITLE),
            font_name=DISPLAY_FONT,
            font_size=sp(31),
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
        self.title_label = title

        tagline = RibbonLabel(
            text=t("ОБОРОНА · ВОЛНЫ · ЗОЛОТО"),
            font_size=sp(9.5),
            color=(0.86, 0.94, 0.80, 0.96),
            size_hint=(None, None),
            width=dp(236),
            height=dp(24),
            pos_hint={"center_x": 0.5, "y": 0.0},
        )
        brand.add_widget(tagline)

        self.column.add_widget(brand)
        self.column.add_widget(self._spacer(12))

        # ---------------------------------------------- продолжить / играть
        self.continue_button = GameButton(
            text=t("ПРОДОЛЖИТЬ"),
            color=(0.16, 0.56, 0.30, 1),
            text_color=(0.96, 1.0, 0.96, 1),
            height=dp(64),
            radius=18,
            font_size=sp(22),
        )
        self.continue_button.bind(on_release=self._continue)
        self.column.add_widget(self.continue_button)
        self.column.add_widget(self._spacer(9))

        self.play_button = GameButton(
            text=t("ИГРАТЬ · КАРТЫ И РЕЖИМЫ"),
            color=(0.22, 0.36, 0.66, 1),
            text_color=(0.94, 0.97, 1.0, 1),
            height=dp(56),
            radius=16,
            font_size=sp(16),
        )
        self.play_button.bind(on_release=self._open_levels)
        self.column.add_widget(self.play_button)
        self.column.add_widget(self._spacer(9))

        # -------------------------------------------------- строка прогресса
        self.progress_label = Label(
            text="",
            font_size=sp(10),
            bold=True,
            color=UI_MUTED,
            size_hint_y=None,
            height=dp(20),
            halign="center",
            valign="middle",
        )
        self.progress_label.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        self.column.add_widget(self.progress_label)
        self.column.add_widget(self._spacer(10))

        # ------------------- «ОБ АВТОРЕ»: маленькая кнопка у нижнего края
        # Держим её отдельно от прокручиваемой колонки, чтобы она всегда
        # была прижата к самому низу экрана, а не «висела» в середине.
        self.bottom_bar = FloatLayout(
            size_hint=(1, None),
            height=dp(46) + dp(SAFE_BOTTOM),
            pos_hint={"x": 0, "y": 0},
        )
        self.achievements_button = GameButton(
            text=t("ДОСТИЖЕНИЯ"),
            color=(0.24, 0.20, 0.10, 1),
            text_color=(1.0, 0.90, 0.62, 1),
            size_hint=(None, None),
            width=dp(126),
            height=dp(34),
            radius=11,
            font_size=sp(9.5),
            pos_hint={"center_x": 0.17, "center_y": 0.5},
        )
        self.achievements_button.bind(on_release=self._open_achievements)
        self.bottom_bar.add_widget(self.achievements_button)

        self.about_button = GameButton(
            text=t("ОБ АВТОРЕ"),
            color=(0.17, 0.20, 0.25, 1),
            text_color=(0.84, 0.89, 0.94, 1),
            size_hint=(None, None),
            width=dp(126),
            height=dp(34),
            radius=11,
            font_size=sp(9.5),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )
        self.about_button.bind(on_release=self._open_info)
        self.bottom_bar.add_widget(self.about_button)

        self.settings_button = GameButton(
            text=t("НАСТРОЙКИ"),
            color=(0.15, 0.24, 0.30, 1),
            text_color=(0.84, 0.93, 1.0, 1),
            size_hint=(None, None),
            width=dp(126),
            height=dp(34),
            radius=11,
            font_size=sp(9.5),
            pos_hint={"center_x": 0.83, "center_y": 0.5},
        )
        self.settings_button.bind(on_release=self._open_settings)
        self.bottom_bar.add_widget(self.settings_button)
        self.add_widget(self.bottom_bar)

        self.scroll.bind(size=self._fit_column)
        Clock.schedule_once(self._fit_column, 0)

        self.info = InfoOverlay()
        self.info.discord_button.bind(on_release=self._discord)
        self.info.close_button.bind(on_release=lambda *_a: self.info.close())
        self.add_widget(self.info)

        self.settings = SettingsOverlay(
            on_language=self._set_language,
            on_music=self._toggle_music_setting,
            on_sfx=self._toggle_sfx_setting,
            on_quality=self._set_quality,
            on_reset=self._reset_progress,
            on_whats_new=self._open_whats_new,
        )
        self.settings.close_button.bind(
            on_release=lambda *_a: self.settings.close()
        )
        self.add_widget(self.settings)

        self.achievements = AchievementsOverlay()
        self.achievements.close_button.bind(
            on_release=lambda *_a: self.achievements.close()
        )
        self.add_widget(self.achievements)

        self.whats_new = WhatsNewOverlay()
        self.whats_new.close_button.bind(
            on_release=lambda *_a: self.whats_new.close()
        )
        self.add_widget(self.whats_new)

        Clock.schedule_once(lambda _dt: self.refresh_menu(), 0)

    # ------------------------------------------------------------------
    @staticmethod
    def _spacer(height: float) -> Widget:
        return Widget(size_hint_y=None, height=height)

    def _fit_column(self, *_args) -> None:
        """Растягивает колонку на высоту экрана и делит лишнее на отступы."""
        reserve = self.bottom_bar.height + dp(6)
        viewport = max(dp(1), self.scroll.height)
        base = self._base_height
        usable = max(dp(1), viewport - reserve)
        if usable <= base + dp(1):
            self.column.height = usable
            self.column.padding = (dp(13), 0, dp(13), 0)
            return
        extra = usable - base
        top = int(extra * 0.45)
        bottom = int(extra) - top
        self.column.height = usable
        self.column.padding = (dp(13), top, dp(13), bottom)
        Clock.schedule_once(lambda _dt: self.emblem._redraw(), 0)

    def on_enter(self) -> None:
        self.backdrop.running = True
        self.emblem.running = True
        music.apply_settings(PROGRESS.music)
        music.play(MENU_THEME)
        sfx.apply_settings(PROGRESS.sfx)
        self.refresh_menu()
        if self._fun_event is None:
            self._fun_event = Clock.schedule_interval(self._fun_tick, 1 / 20)

    def on_leave(self) -> None:
        self.backdrop.running = False
        self.emblem.running = False
        if self._fun_event is not None:
            self._fun_event.cancel()
            self._fun_event = None

    def _fun_tick(self, dt: float) -> None:
        """Лёгкое «дыхание» заголовка: золото переливается, не мигает."""
        self._fun_t += dt
        wave = math.sin(self._fun_t * 1.4)
        self.title_label.color = (
            1.0,
            0.82 + 0.06 * wave,
            0.33 + 0.10 * wave,
            1.0,
        )

    def refresh_menu(self) -> None:
        if not PROGRESS.tutorial_done and PROGRESS.unlocked <= 1:
            self.progress_label.text = t(
                "СНАЧАЛА — КОРОТКОЕ ОБУЧЕНИЕ · 3 ВОЛНЫ"
            )
            return
        unlocked = max(1, min(len(LEVELS), PROGRESS.unlocked))
        text = t("ОТКРЫТО КАРТ: {unlocked} ИЗ {total}").format(
            unlocked=unlocked, total=len(LEVELS)
        )
        if PROGRESS.tutorial_done:
            text += t("  ·  обучение пройдено")
        self.progress_label.text = text

    def _continue(self, *_args) -> None:
        """Продолжает обучение (в первый раз) или самую дальнюю открытую карту."""
        if not PROGRESS.tutorial_done and PROGRESS.unlocked <= 1:
            game = self.screen_manager.get_screen("game")
            game.start_tutorial()
            self.screen_manager.current = "game"
            return
        index = max(0, min(len(LEVELS) - 1, PROGRESS.unlocked - 1))
        self._start_level(index)

    def _start_level(self, index: int) -> None:
        game = self.screen_manager.get_screen("game")
        game.start_level(index)
        self.screen_manager.current = "game"

    def _open_levels(self, *_args) -> None:
        self.screen_manager.current = "levels"

    def _open_info(self, *_args) -> None:
        self.info.open()

    def _close_info(self, *_args) -> None:
        self.info.close()

    def _open_achievements(self, *_args) -> None:
        self.achievements.refresh()
        self.achievements.open()

    def _open_settings(self, *_args) -> None:
        self.settings.refresh()
        self.settings.open()

    def _open_whats_new(self, *_args) -> None:
        self.settings.close()
        self.whats_new.open()

    def _set_language(self, code: str) -> None:
        if code == PROGRESS.language:
            return
        PROGRESS.set_language(code)
        set_language(code)
        # Экраны создают подписи один раз, поэтому их нужно пересобрать.
        self.app_ref.rebuild_ui()

    def _toggle_music_setting(self, *_args) -> None:
        enabled = not PROGRESS.music
        PROGRESS.set_music(enabled)
        music.apply_settings(enabled)
        self.settings.refresh()

    def _toggle_sfx_setting(self, *_args) -> None:
        enabled = not PROGRESS.sfx
        PROGRESS.set_sfx(enabled)
        sfx.apply_settings(enabled)
        sfx.play("click")
        self.settings.refresh()

    def _set_quality(self, mode: str) -> None:
        PROGRESS.set_quality(mode)
        self.settings.refresh()
        game = self.screen_manager.get_screen("game")
        if game is not None:
            game.arena.apply_quality()

    def _reset_progress(self, *_args) -> None:
        PROGRESS.reset()
        self.settings.refresh()
        self.refresh_menu()

    def dispose(self) -> None:
        if self._discord_timer is not None:
            self._discord_timer.cancel()
            self._discord_timer = None
        self.settings._cancel_reset()
        self.backdrop.dispose()

    def _discord(self, *_args) -> None:
        result = open_url(DISCORD_URL)
        messages = {
            "opened": (t("Ссылка открыта в браузере"), (0.60, 0.94, 0.64, 1)),
            "copied": (t("Ссылка скопирована в буфер"), (0.98, 0.86, 0.48, 1)),
            "failed": (t("Не удалось открыть ссылку"), (1.0, 0.55, 0.48, 1)),
        }
        text, color = messages.get(result, messages["failed"])
        self.info.set_discord_status(text, color)
        if self._discord_timer is not None:
            self._discord_timer.cancel()
        self._discord_timer = Clock.schedule_once(self._restore_discord_link, 2.6)

    def _restore_discord_link(self, *_args) -> None:
        self._discord_timer = None
        self.info.set_discord_status(DISCORD_HANDLE, (0.62, 0.74, 0.66, 0.9))


class LevelsScreen(Screen):
    """Экран выбора карты: обучение и шесть настоящих уровней."""

    def __init__(self, app_ref, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.name = "levels"
        self.app_ref = app_ref
        self.screen_manager = screen_manager
        self.level_buttons = []

        self.backdrop = Backdrop()
        self.add_widget(self.backdrop)

        self.scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=0,
            scroll_type=["bars", "content"],
        )
        self.add_widget(self.scroll)

        self._base_height = dp(420) + self._levels_block()
        self.column = BoxLayout(
            orientation="vertical",
            size_hint=(1, None),
            height=self._base_height,
            padding=(dp(13), 0, dp(13), 0),
        )
        self.scroll.add_widget(self.column)

        # ---------------------------------------------------------- шапка
        top = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(52),
            spacing=dp(10),
        )
        self.back_button = GameButton(
            text=t("НАЗАД"),
            color=(0.18, 0.22, 0.28, 1),
            text_color=(0.88, 0.93, 0.98, 1),
            size_hint=(None, None),
            size=(dp(96), dp(44)),
            radius=13,
            font_size=sp(12),
        )
        self.back_button.bind(on_release=self._back)
        top.add_widget(self.back_button)

        title = Label(
            text=t("ВЫБОР КАРТЫ"),
            font_size=sp(20),
            bold=True,
            color=(1.0, 0.84, 0.35, 1),
            halign="left",
            valign="middle",
        )
        title.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        top.add_widget(title)
        self.column.add_widget(top)
        self.column.add_widget(Widget(size_hint_y=None, height=dp(10)))

        # ---------------------------------------------------------- обучение
        self.tutorial_button = GameButton(
            text=t("ОБУЧЕНИЕ · короткая карта\nдвижение · золото · первая башня"),
            color=(0.14, 0.42, 0.34, 1),
            text_color=(0.92, 1.0, 0.95, 1),
            height=dp(72),
            radius=15,
            font_size=sp(12),
        )
        self.tutorial_button.bind(on_release=self._play_tutorial)
        self.column.add_widget(self.tutorial_button)
        self.column.add_widget(Widget(size_hint_y=None, height=dp(12)))

        # ---------------------------------------------------------- режимы
        self.modes_card = MenuCard(
            orientation="vertical",
            size_hint_y=None,
            height=dp(116),
            padding=(dp(12), dp(10)),
            spacing=dp(6),
        )
        modes_header = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(20),
            spacing=dp(6),
        )
        modes_title = Label(
            text=t("РЕЖИМЫ"),
            font_size=sp(11),
            bold=True,
            color=(1.0, 0.84, 0.40, 1),
            halign="left",
            valign="middle",
        )
        modes_title.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        modes_header.add_widget(modes_title)
        self.modes_card.add_widget(modes_header)

        modes_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(56),
            spacing=dp(8),
        )
        self.endless_button = GameButton(
            text="",
            color=(0.26, 0.24, 0.52, 1),
            text_color=(0.94, 0.93, 1.0, 1),
            height=dp(56),
            radius=13,
            font_size=sp(10.5),
        )
        self.endless_button.bind(on_release=self._play_endless)
        modes_row.add_widget(self.endless_button)

        self.daily_button = GameButton(
            text="",
            color=(0.18, 0.40, 0.38, 1),
            text_color=(0.90, 1.0, 0.96, 1),
            height=dp(56),
            radius=13,
            font_size=sp(10.5),
        )
        self.daily_button.bind(on_release=self._play_daily)
        modes_row.add_widget(self.daily_button)

        self.modes_card.add_widget(modes_row)
        self.column.add_widget(self.modes_card)
        self.column.add_widget(Widget(size_hint_y=None, height=dp(12)))

        # ---------------------------------------------------------- карты
        self.levels_card = MenuCard(
            orientation="vertical",
            size_hint_y=None,
            height=self._levels_block(),
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
            text=t("КАРТЫ"),
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
        self.column.add_widget(Widget(size_hint_y=None, height=dp(14)))
        self.scroll.bind(size=self._fit_column)
        Clock.schedule_once(self._fit_column, 0)
        Clock.schedule_once(lambda _dt: self.refresh_levels(), 0)

    # ------------------------------------------------------------------
    @staticmethod
    def _levels_block() -> float:
        """Высота карточки со списком карт (растёт с числом карт)."""
        count = max(1, len(LEVELS))
        return dp(24) + count * dp(110) + count * dp(8) + dp(24)

    def _fit_column(self, *_args) -> None:
        """Растягивает колонку на всю высоту и делит лишнее место на отступы."""
        viewport = max(dp(1), self.scroll.height)
        base = self._base_height
        if viewport <= base + dp(1):
            self.column.height = base
            self.column.padding = (dp(13), 0, dp(13), 0)
            return
        extra = viewport - base
        top = int(extra * 0.45)
        bottom = int(extra) - top
        self.column.height = viewport
        self.column.padding = (dp(13), top, dp(13), bottom)

    def on_enter(self) -> None:
        self.backdrop.running = True
        music.apply_settings(PROGRESS.music)
        music.play(MENU_THEME)
        sfx.apply_settings(PROGRESS.sfx)
        self.refresh_levels()

    def on_leave(self) -> None:
        self.backdrop.running = False

    def refresh_levels(self) -> None:
        unlocked = max(1, min(len(LEVELS), PROGRESS.unlocked))
        self.summary.text = t("ОТКРЫТО {unlocked} ИЗ {total}").format(
            unlocked=unlocked, total=len(LEVELS)
        )
        for index, (level, tile) in enumerate(zip(LEVELS, self.level_buttons)):
            available = PROGRESS.is_unlocked(index)
            stars = PROGRESS.stars(level.id) if available else 0
            best_wave = PROGRESS.best_wave(level.id) if available else 0
            tile.set_data(available, stars, best_wave)
        if PROGRESS.tutorial_done:
            self.tutorial_button.text = t(
                "ОБУЧЕНИЕ · пройдено\nможно повторить в любой момент"
            )
        else:
            self.tutorial_button.text = t(
                "ОБУЧЕНИЕ · короткая карта\n"
                "движение · золото · первая башня"
            )
        best = int(PROGRESS.endless_best)
        if best > 0:
            self.endless_button.text = t(
                "БЕСКОНЕЧНЫЙ РЕЖИМ\nрекорд: волна {n}"
            ).format(n=best)
        else:
            self.endless_button.text = t("БЕСКОНЕЧНЫЙ РЕЖИМ\nбез конца волн")
        daily = PROGRESS.daily_of_today()
        if daily.get("done"):
            self.daily_button.text = t(
                "ЕЖЕДНЕВНАЯ КАРТА\nпройдена · волна {n}"
            ).format(n=int(daily.get("best", 0)))
            self.daily_button.disabled = True
        else:
            self.daily_button.text = t("ЕЖЕДНЕВНАЯ КАРТА\nновая карта дня")
            self.daily_button.disabled = False

    def _back(self, *_args) -> None:
        self.screen_manager.current = "menu"

    def _play(self, index: int) -> None:
        if not PROGRESS.is_unlocked(index):
            return
        game = self.screen_manager.get_screen("game")
        game.start_level(index)
        self.screen_manager.current = "game"

    def _play_endless(self, *_args) -> None:
        game = self.screen_manager.get_screen("game")
        game.start_endless()
        self.screen_manager.current = "game"

    def _play_daily(self, *_args) -> None:
        if PROGRESS.daily_done():
            return
        game = self.screen_manager.get_screen("game")
        game.start_daily()
        self.screen_manager.current = "game"

    def _play_tutorial(self, *_args) -> None:
        game = self.screen_manager.get_screen("game")
        game.start_tutorial()
        self.screen_manager.current = "game"


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
            text=t("ПАУЗА"),
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

        self.continue_button = GameButton(t("ПРОДОЛЖИТЬ"), color=(0.16, 0.55, 0.30, 1))
        self.restart_button = GameButton(t("ЗАНОВО"), color=(0.36, 0.30, 0.12, 1))
        self.menu_button = GameButton(t("В МЕНЮ"), color=(0.30, 0.13, 0.12, 1))
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
            text=t("УЛУЧШЕНИЯ"),
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
            t("ЗАКРЫТЬ"),
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
        self.gold_label.text = t("Золото: {gold}").format(gold=int(self.arena.gold))
        for key, button in self.buttons.items():
            data = GLOBAL_UPGRADES[key]
            level = self.arena.upgrades.get(key, 0)
            maxed = self.arena.upgrade_maxed(key)
            cost = self.arena.upgrade_cost(key)
            price = t("макс.") if maxed else t("{cost} з.").format(cost=cost)
            button.text = t(
                "{name}  ур. {level}/{max}\n{desc} · {price}"
            ).format(
                name=t(data["name"]),
                level=level,
                max=data["max_level"],
                desc=t(data["desc"]),
                price=price,
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
            text=t("МАГАЗИН"),
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
            t("ЗАКРЫТЬ"),
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
        self.gold_label.text = t("Золото: {gold}").format(gold=int(self.arena.gold))
        for key, button in self.buttons.items():
            data = SHOP_ITEMS[key]
            button.text = t("{name} · {cost} з.\n{desc}").format(
                name=t(data["name"]), cost=data["cost"], desc=t(data["desc"])
            )
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
            t("УЛУЧШИТЬ"),
            color=(0.16, 0.48, 0.30, 1),
            height=dp(50),
            radius=12,
            font_size=sp(14),
        )
        self.upgrade_button.bind(on_release=lambda *_a: self._upgrade())
        box.add_widget(self.upgrade_button)

        self.sell_button = GameButton(
            t("ПРОДАТЬ"),
            color=(0.38, 0.20, 0.14, 1),
            text_color=(1.0, 0.88, 0.80, 1),
            height=dp(42),
            radius=12,
            font_size=sp(12),
        )
        self.sell_button.bind(on_release=lambda *_a: self._sell())
        box.add_widget(self.sell_button)

        self.close_button = GameButton(
            t("ЗАКРЫТЬ"),
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
        self.title.text = t("{name} · ур. {level}").format(
            name=t(info["name"]).upper(), level=info["level"]
        )
        self.hp_label.text = t("Прочность {hp} / {max}").format(
            hp=int(info["hp"]), max=int(info["max_hp"])
        )
        self.effect_label.text = info["effect"]
        if info["maxed"]:
            self.next_label.text = t("Максимальный уровень")
            self.upgrade_button.text = t("МАКС.")
            self.upgrade_button.disabled = True
        else:
            self.next_label.text = info["next"]
            self.upgrade_button.text = t("УЛУЧШИТЬ · {cost} з.").format(
                cost=info["cost"]
            )
            self.upgrade_button.disabled = self.arena.gold < info["cost"]
        refund = self.arena.building_refund(self.building)
        self.sell_button.text = t("ПРОДАТЬ · +{refund} з.").format(refund=refund)
        self.sell_button.disabled = self.arena.ended

    def _sell(self) -> None:
        if self.arena is None or self.building is None:
            return
        ok, message = self.arena.sell_building(self.building)
        self.arena.on_toast(message, "gold" if ok else "bad")
        self.close()

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

        self.achievements_label = Label(
            text="",
            font_size=sp(11),
            bold=True,
            color=(1.0, 0.86, 0.44, 1),
            size_hint_y=None,
            height=dp(44),
            halign="center",
            valign="middle",
        )
        self.achievements_label.bind(
            size=lambda w, _v: setattr(w, "text_size", w.size)
        )
        box.add_widget(self.achievements_label)

        self.again_button = GameButton(t("ИГРАТЬ СНОВА"), color=(0.16, 0.55, 0.30, 1))
        self.menu_button = GameButton(t("К ВЫБОРУ КАРТЫ"), color=(0.30, 0.13, 0.12, 1))
        box.add_widget(self.again_button)
        box.add_widget(self.menu_button)

        self.add_panel(box)

    def open(self, win: bool, stats: dict, stars: int = 0,
             unlock_name: str = "", level_name: str = "",
             achievements: list | None = None) -> None:
        total = int(stats.get("total_waves", TOTAL_WAVES))
        wave = int(stats.get("wave", 1))
        waves = total if win else max(0, wave - 1)
        self.title.text = t("БАЗА ВЫСТОЯЛА!") if win else t("БАЗА ПАЛА")
        self.title.color = (
            (1.0, 0.84, 0.35, 1) if win else (1.0, 0.48, 0.42, 1)
        )
        self.level_label.text = level_name
        if win:
            self.stars_label.text = t("ЗВЁЗДЫ: {stars} / 3").format(stars=stars)
            self.stars_label.color = (1.0, 0.82, 0.28, 1)
        else:
            self.stars_label.text = t("ЗВЁЗДЫ: {stars} / 3").format(stars=0)
            self.stars_label.color = (0.58, 0.64, 0.58, 1)
        self.unlock_label.text = (
            t("Открыта новая карта: {name}!").format(name=t(unlock_name))
            if unlock_name
            else ""
        )
        if achievements:
            names = ", ".join(t(item["name"]) for item in achievements)
            self.achievements_label.text = t("Достижения: {names}").format(
                names=names
            )
        else:
            self.achievements_label.text = ""
        if stats.get("endless"):
            self.stats_label.text = t(
                "Отбито волн: {waves}\n"
                "Добыто золота: {gold} · Побед: {kills}\n"
                "Построек осталось: {buildings}"
            ).format(
                waves=waves,
                gold=int(stats.get("gold_earned", 0)),
                kills=int(stats.get("kills", 0)),
                buildings=int(stats.get("buildings", 0)),
            )
        else:
            self.stats_label.text = t(
                "Отбито волн: {waves} / {total}\n"
                "Добыто золота: {gold} · Побед: {kills}\n"
                "Построек осталось: {buildings}"
            ).format(
                waves=waves,
                total=total,
                gold=int(stats.get("gold_earned", 0)),
                kills=int(stats.get("kills", 0)),
                buildings=int(stats.get("buildings", 0)),
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
        self._selected_tutorial = False
        self._tutorial_finished = False
        self.mode = "campaign"
        self._daily_seed = None
        self._hint_events = []

        self.arena = Arena(self._on_toast, self._on_end, self._on_building)
        self.add_widget(self.arena)

        self.hud = HUD(
            on_pause=self._toggle_pause,
            on_shop=self._open_shop,
            on_speed=self._toggle_speed,
            on_music=self._toggle_music,
        )
        self.hud.set_music_state(PROGRESS.music)
        self.add_widget(self.hud)

        self.build_bar = BuildBar(
            on_build=self._select_build,
            on_upgrades=self._open_upgrades,
        )
        self.add_widget(self.build_bar)

        self.wave_prompt = WavePrompt(on_call=self._call_wave)
        self.add_widget(self.wave_prompt)

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
        self.end.menu_button.bind(on_release=self._to_levels)

        self._sync = Clock.schedule_interval(self._sync_hud, 0.1)
        Window.bind(on_key_down=self._on_key_down)

    # ------------------------------------------------------------------
    def start_level(self, index: int, mode: str = "campaign") -> None:
        """Выбор карты из меню. Старт произойдёт при входе на экран."""
        self._selected_tutorial = False
        self._tutorial_finished = False
        self.mode = mode if mode in ("campaign", "endless", "daily") else "campaign"
        self._daily_seed = None
        self._selected_level = max(0, min(len(LEVELS) - 1, index))

    def start_endless(self) -> None:
        """Бесконечный режим: последняя карта, волны без конца."""
        self._selected_tutorial = False
        self._tutorial_finished = False
        self.mode = "endless"
        self._daily_seed = None
        self._selected_level = len(LEVELS) - 1

    def start_daily(self) -> None:
        """Ежедневная карта: сид от даты, одна попытка в день."""
        self._selected_tutorial = False
        self._tutorial_finished = False
        self.mode = "daily"
        seed = PROGRESS.daily_seed()
        self._daily_seed = seed
        self._selected_level = seed % len(LEVELS)

    def start_tutorial(self) -> None:
        """Запускает короткую обучающую карту."""
        self._selected_tutorial = True
        self._tutorial_finished = False
        self.mode = "campaign"
        self._daily_seed = None

    def _current_level(self):
        if self._selected_tutorial:
            return TUTORIAL, 0
        return LEVELS[self._selected_level], self._selected_level

    def _load_current(self) -> None:
        level, index = self._current_level()
        self.level_index = index
        seed = self._daily_seed if self.mode == "daily" else None
        self.arena.load_level(level, index, mode=self.mode, seed=seed)
        self.arena.start_new()
        self.arena.resume()
        music.apply_settings(PROGRESS.music)
        music.play(THEME_BY_LEVEL.get(level.id, MENU_THEME))
        sfx.apply_settings(PROGRESS.sfx)
        self._sync_hud()
        if self.mode == "endless":
            self.toast.show(
                t("Бесконечный режим: держись как можно дольше"), "gold", 3.8
            )
        elif self.mode == "daily":
            self.toast.show(
                t("Ежедневная карта: {name}").format(name=t(level.name)),
                "gold",
                3.8,
            )
        else:
            self.toast.show(
                t("{name}: {desc}").format(name=t(level.name), desc=t(level.desc)),
                "gold",
                3.8,
            )
        if level.tutorial:
            self._schedule_hints()

    def on_enter(self) -> None:
        self._close_all()
        self._cancel_hints()
        self._load_current()

    def on_leave(self) -> None:
        self._cancel_hints()
        self._close_all()
        self.arena.stop()

    # ------------------------------------------------------------------
    def _schedule_hints(self) -> None:
        """Показывает подсказки обучения по очереди, не мешая бою."""
        self._cancel_hints()
        for step, text in enumerate(TUTORIAL_HINTS):
            event = Clock.schedule_once(
                lambda _dt, hint=text: self.toast.show(t(hint), "blue", 3.0),
                4.2 + step * 5.8,
            )
            self._hint_events.append(event)

    def _cancel_hints(self) -> None:
        for event in self._hint_events:
            event.cancel()
        self._hint_events = []

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
        self.end.again_button.disabled = False
        if self.mode in ("endless", "daily"):
            run = dict(stats)
            run["win"] = win
            run["waves"] = waves
            PROGRESS.add_run(run)
            new_achievements = check_achievements(PROGRESS, run)
            if self.mode == "endless":
                previous = PROGRESS.endless_best
                updated = PROGRESS.record_endless(waves)
                self.end.open(
                    False, stats, 0, "", t(level.name), new_achievements
                )
                self.end.title.text = t("БЕСКОНЕЧНЫЙ РЕЖИМ · ВОЛНА {n}").format(
                    n=waves
                )
                self.end.title.color = (1.0, 0.84, 0.35, 1)
                self.end.stars_label.text = ""
                self.end.again_button.text = t("ЕЩЁ РАЗ")
                self.end.unlock_label.text = (
                    t("Новый рекорд!")
                    if updated
                    else t("Лучший результат: волна {n}").format(n=previous)
                )
            else:
                PROGRESS.record_daily(waves, win)
                self.end.open(
                    win, stats, 3 if win else 0, "", t(level.name),
                    new_achievements,
                )
                self.end.title.text = t("ЕЖЕДНЕВНАЯ КАРТА · ВОЛНА {n}").format(
                    n=waves
                )
                self.end.title.color = (1.0, 0.84, 0.35, 1)
                self.end.stars_label.text = ""
                self.end.again_button.text = t("СЕГОДНЯ ПРОЙДЕНО")
                self.end.again_button.disabled = True
                self.end.unlock_label.text = t(
                    "Возвращайся завтра за новой картой"
                )
            return
        if level.tutorial:
            self._cancel_hints()
            if win:
                PROGRESS.mark_tutorial_done()
                self._tutorial_finished = True
            run = dict(stats)
            run["win"] = win
            run["waves"] = waves
            PROGRESS.add_run(run)
            new_achievements = check_achievements(PROGRESS, run)
            self.end.open(win, stats, 3 if win else 0, "", t(level.name), new_achievements)
            if win:
                self.end.title.text = t("ОБУЧЕНИЕ ПРОЙДЕНО!")
                self.end.unlock_label.text = t("Дальше — первая настоящая карта")
                self.end.again_button.text = t("НАЧАТЬ ДОЛИНУ")
            else:
                self.end.title.text = t("ПОПРОБУЙ ЕЩЁ")
                self.end.again_button.text = t("ПОВТОРИТЬ ОБУЧЕНИЕ")
            return
        ratio = self.arena.base_hp / max(1.0, self.arena.base_max_hp)
        stars, newly_unlocked = PROGRESS.record(
            index, level.id, win, waves, ratio, total
        )
        run = dict(stats)
        run["win"] = win
        run["waves"] = waves
        PROGRESS.add_run(run)
        new_achievements = check_achievements(PROGRESS, run)
        self.end.again_button.text = t("ИГРАТЬ СНОВА")
        unlock_name = ""
        if newly_unlocked and index + 1 < len(LEVELS):
            unlock_name = LEVELS[index + 1].name
        self.end.open(
            win, stats, stars, unlock_name, t(level.name), new_achievements
        )

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
        self.hud.set_music_state(music.enabled)
        self.build_bar.set_state(stats, self.arena.build_mode)
        overlays = (
            self.pause.visible
            or self.upgrades.visible
            or self.shop.visible
            or self.building_panel.visible
            or self.end.visible
        )
        can_call = stats.get("wave_state") == "prep" and not overlays
        self.wave_prompt.visible = can_call and not self.arena.ended
        if can_call:
            self.wave_prompt.set_state(stats)
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
        if key == 27:
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
        if self.end.visible or self.arena.ended:
            return False
        if 49 <= key <= 52:
            kinds = list(BUILD_TYPES)
            index = key - 49
            if index < len(kinds):
                self._select_build(kinds[index])
                return True
        if key == ord("u"):
            self._open_upgrades()
            return True
        if key == ord("m"):
            self._open_shop()
            return True
        if key == ord("t"):
            self._toggle_speed()
            return True
        if key == ord("f"):
            self._call_wave()
            return True
        if key == 32:
            self._toggle_pause(None)
            return True
        return False

    def _toggle_speed(self, *_args) -> None:
        if self.arena.ended or self.end.visible:
            return
        self.arena.toggle_speed()
        self._sync_hud()

    def _toggle_music(self, *_args) -> None:
        enabled = music.toggle()
        PROGRESS.set_music(enabled)
        self.hud.set_music_state(enabled)

    def _call_wave(self, *_args) -> None:
        if self.arena.ended or self.end.visible:
            return
        ok, message = self.arena.call_wave_now()
        if not ok:
            return
        self.toast.show(message, "gold", 2.2)
        self._sync_hud()

    # ------------------------------------------------------------------
    def _select_build(self, kind: str) -> None:
        if self.arena.ended:
            return
        mode = self.arena.set_build_mode(kind)
        self.build_bar.set_state(self.arena.stats(), mode)
        if mode:
            self.toast.show(
                t("{name}: нажми на свободную площадку").format(
                    name=t(BUILD_TYPES[mode]["name"]).upper()
                ),
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
        self.wave_prompt.visible = False

    def _restart(self, *_args) -> None:
        self._close_all()
        if self.mode == "daily" and PROGRESS.daily_done():
            self.screen_manager.current = "levels"
            return
        if self._tutorial_finished:
            # Обучение пройдено: сразу ведём на первую настоящую карту.
            self.start_level(0)
            self._load_current()
            return
        self.arena.start_new()
        self.arena.resume()
        self._sync_hud()
        self.toast.show(t("Новая оборона началась"), "gold", 2.0)

    def _to_levels(self, *_args) -> None:
        self._close_all()
        self.arena.stop()
        self.screen_manager.current = "levels"

    def _menu(self, *_args) -> None:
        self._close_all()
        self.arena.stop()
        self.screen_manager.current = "menu"

    def dispose(self) -> None:
        event = getattr(self, "_sync", None)
        if event is not None:
            event.cancel()
            self._sync = None
        try:
            Window.unbind(on_key_down=self._on_key_down)
        except Exception:
            pass
        self._cancel_hints()
        self.arena.dispose()
