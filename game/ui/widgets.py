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

from ..core.config import BUILD_TYPES, SAFE_BOTTOM, SAFE_SIDE, SAFE_TOP, TOTAL_WAVES
from ..core.i18n import t
from ..core.sfx import sfx
from ..render.gfx import star
from ..render.icons import draw_icon
from .fonts import DISPLAY_FONT


# Максимальная ширина интерфейса на широких экранах. На ПК в большом окне
# кнопки не должны растягиваться на всю ширину — держим «телефонную» форму
# и центрируем её.
MAX_CONTENT_WIDTH = 470.0  # в dp


def content_width(screen_w: float) -> float:
    """Ширина рабочей колонки: не шире телефона, но не больше экрана."""
    return min(screen_w, dp(MAX_CONTENT_WIDTH))


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
        # Высоту задаём только если её не задали явно и не передали size:
        # иначе setdefault перетирал height и кнопки с size=(...) вытягивались
        # по вертикали (например, круглые кнопки HUD становились 46x58).
        if "height" not in kwargs and "size" not in kwargs:
            kwargs.setdefault("height", dp(58))
        # Единый «игровой» шрифт для всех кнопок. Он шире Roboto, поэтому
        # базовый размер чуть меньше — длинные подписи остаются в кнопке.
        kwargs.setdefault("font_name", DISPLAY_FONT)
        super().__init__(
            text=text,
            bold=True,
            font_size=font_size if font_size is not None else sp(16),
            background_normal="",
            background_down="",
            background_color=(0, 0, 0, 0),
            color=text_color,
            disabled_color=(text_color[0], text_color[1], text_color[2], 0.55),
            outline_color=(0, 0, 0, 0.42),
            outline_width=dp(0.8),
            # У Button в Kivy по умолчанию halign='auto', valign='bottom':
            # подпись «прилипала» к нижнему левому углу. Центрируем явно.
            halign="center",
            valign="middle",
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
        # Лёгкий щелчок на любую кнопку интерфейса. Не мешает тем, кто вешает
        # свой on_press: Kivy-привязки складываются, а не заменяют друг друга.
        self.bind(on_press=self._play_click)
        self._refresh_style()

    def _play_click(self, *_args) -> None:
        sfx.play("click")

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
        self.text_size = self.size

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


class _ModeIcon(Widget):
    """Маленький виджет-иконка: рисует себя в собственном canvas.

    Именно дочерний виджет, а не инструкции в ``canvas.after``: так иконка
    гарантированно попадает в первый же кадр, даже если карточка создана
    ещё до подключения окна.
    """

    def __init__(self, icon: str, color, **kwargs):
        kwargs.setdefault("size_hint", (None, None))
        super().__init__(**kwargs)
        self._icon = icon
        self._color = list(color)
        self._group = InstructionGroup()
        self.canvas.add(self._group)
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def set_color(self, color) -> None:
        self._color = list(color)
        self._redraw()

    def _redraw(self, *_args) -> None:
        self._group.clear()
        if not self._icon or self.width <= 1 or self.height <= 1:
            return
        draw_icon(
            self._group,
            self._icon,
            self.x + self.width * 0.5,
            self.y + self.height * 0.5,
            min(self.width, self.height),
            self._color,
        )


class ModeCard(GameButton):
    """Крупная карточка режима: иконка сверху, заголовок и подпись по центру.

    Обычная кнопка рисует одну строку одним размером, поэтому длинные
    подписи вроде «БЕСКОНЕЧНЫЙ / рекорд: волна 24» съезжали и выглядели
    неопрятно. Здесь заголовок и подпись — два отдельных Label с разными
    размерами и цветом: строки всегда стоят ровно друг под другом.
    """

    def __init__(
        self,
        title: str,
        subtitle: str = "",
        icon: str | None = None,
        color=(0.20, 0.34, 0.30, 1),
        text_color=(0.96, 1.0, 0.97, 1),
        sub_color=(0.70, 0.86, 0.78, 1),
        **kwargs,
    ):
        kwargs.setdefault("height", dp(106))
        kwargs.setdefault("radius", 16)
        super().__init__(
            text=title,
            color=color,
            # Сам Button подпись не рисует: её заменяют две аккуратные строки.
            text_color=(0, 0, 0, 0),
            **kwargs,
        )
        self._title_color = list(text_color)
        self._sub_color = list(sub_color)
        self._icon = icon
        self._icon_color = list(text_color)

        self._title_label = Label(
            text=title,
            font_name=DISPLAY_FONT,
            bold=True,
            font_size=sp(13.5),
            color=self._title_color,
            halign="center",
            valign="middle",
        )
        self._subtitle_label = Label(
            text=subtitle,
            font_size=sp(9.5),
            color=self._sub_color,
            halign="center",
            valign="middle",
        )
        for label in (self._title_label, self._subtitle_label):
            label.size_hint = (None, None)
            self.add_widget(label)

        self._icon_widget = _ModeIcon(icon, self._icon_color)
        self.add_widget(self._icon_widget)

        self.bind(pos=self._layout_content, size=self._layout_content)
        self._layout_content()

    # ------------------------------------------------------------------
    def _layout_content(self, *_args) -> None:
        if not hasattr(self, "_title_label"):
            return
        pad = dp(8)
        width = max(1.0, self.width - pad * 2)
        title_h = dp(22)
        sub_h = dp(17)
        # Иконка сверху, ниже — ровный блок из двух строк.
        self._title_label.size = (width, title_h)
        self._title_label.pos = (
            self.x + pad,
            self.y + (dp(38) if self._subtitle_label.text else dp(26)),
        )
        self._title_label.text_size = self._title_label.size
        self._subtitle_label.size = (width, sub_h)
        self._subtitle_label.pos = (self.x + pad, self.y + dp(17))
        self._subtitle_label.text_size = self._subtitle_label.size

        icon_size = min(self.width * 0.30, dp(26))
        self._icon_widget.size = (icon_size, icon_size)
        self._icon_widget.pos = (
            self.x + self.width * 0.5 - icon_size * 0.5,
            self.y + self.height - dp(30) - icon_size * 0.5,
        )

    def _refresh_style(self, *_args) -> None:
        super()._refresh_style(*_args)
        if not hasattr(self, "_title_label"):
            return
        if self.disabled:
            self._title_label.color = (*self._title_color[:3], 0.55)
            self._subtitle_label.color = (*self._sub_color[:3], 0.45)
            self._icon_widget.set_color((*self._icon_color[:3], 0.55))
        else:
            self._title_label.color = self._title_color
            self._subtitle_label.color = self._sub_color
            self._icon_widget.set_color(self._icon_color)

    def set_text(self, title: str, subtitle: str | None = None) -> None:
        """Меняет подписи, не пересоздавая карточку."""
        self.text = title
        self._title_label.text = title
        if subtitle is not None:
            self._subtitle_label.text = subtitle
        self._layout_content()


class RibbonLabel(Label):
    """Подпись на золотой «ленточке»: тёмная плашка со скруглением."""

    def __init__(self, **kwargs):
        kwargs.setdefault("font_name", DISPLAY_FONT)
        kwargs.setdefault("bold", True)
        kwargs.setdefault("halign", "center")
        kwargs.setdefault("valign", "middle")
        super().__init__(**kwargs)
        with self.canvas.before:
            self._ribbon_color = Color(0.06, 0.14, 0.11, 0.72)
            self._ribbon = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(9)]
            )
            self._ribbon_edge_color = Color(1.0, 0.84, 0.40, 0.36)
            self._ribbon_edge = Line(
                rounded_rectangle=(0, 0, 0, 0, dp(9)), width=dp(1.1)
            )
        self.bind(
            pos=self._sync_ribbon,
            size=self._sync_ribbon,
            text=self._sync_ribbon,
        )
        self._sync_ribbon()

    def _sync_ribbon(self, *_args) -> None:
        if not hasattr(self, "_ribbon"):
            return
        pad_x = dp(10)
        pad_y = dp(2)
        x = self.x + pad_x
        y = self.y + pad_y
        w = max(1.0, self.width - pad_x * 2)
        h = max(1.0, self.height - pad_y * 2)
        self._ribbon.pos = (x, y)
        self._ribbon.size = (w, h)
        self._ribbon_edge.rounded_rectangle = (x, y, w, h, dp(8))
        self.text_size = (max(1.0, self.width - dp(8)), self.height)


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
        # center_y/center_x в Kivy кэшируются и внутри наблюдателя свойства
        # могут отдать ещё старое значение — считаем центр напрямую.
        cy = self.y + self.height * 0.5
        for index in range(int(self.total)):
            cx = self.x + step * (index + 0.5)
            filled = index < self.count
            color = (
                (1.0, 0.84, 0.30, 1)
                if filled
                else (0.24, 0.33, 0.27, 0.85)
            )
            star(self._group, cx, cy, radius, color, radius * 0.46)


class IconView(Widget):
    """Иконка, нарисованная примитивами."""

    def __init__(self, kind: str, color=(1, 1, 1, 1), **kwargs):
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("size", (dp(26), dp(26)))
        super().__init__(**kwargs)
        self.kind = kind
        self.icon_color = list(color)
        self._group = InstructionGroup()
        self.canvas.add(self._group)
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def set_color(self, color) -> None:
        if list(self.icon_color) != list(color):
            self.icon_color = list(color)
            self._redraw()

    def _redraw(self, *_args) -> None:
        self._group.clear()
        if self.width <= 1 or self.height <= 1:
            return
        cx = self.x + self.width * 0.5
        cy = self.y + self.height * 0.5
        draw_icon(
            self._group, self.kind, cx, cy,
            min(self.width, self.height) * 0.94, self.icon_color,
        )


class StatPill(BoxLayout):
    """Компактная плашка-показатель: иконка, подпись и значение."""

    def __init__(self, icon: str, title: str, value: str = "—",
                 accent=(1, 1, 1, 1), **kwargs):
        kwargs.setdefault("orientation", "horizontal")
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(50))
        kwargs.setdefault("padding", (dp(7), dp(3)))
        kwargs.setdefault("spacing", dp(6))
        super().__init__(**kwargs)
        with self.canvas.before:
            self._glow_color = Color(1.0, 0.84, 0.36, 0.06)
            self._glow = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(15)])
            self._fill_color = Color(0.045, 0.105, 0.080, 0.88)
            self._fill = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(14)])
            self._top_color = Color(1, 1, 1, 0.05)
            self._top = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(14)])
        with self.canvas.after:
            self._edge_color = Color(1.0, 0.85, 0.40, 0.16)
            self._edge = Line(rounded_rectangle=(0, 0, 0, 0, dp(13)), width=dp(1.0))

        self.icon = IconView(icon, accent)
        self.icon.size = (dp(28), dp(28))
        self.icon.pos_hint = {"center_y": 0.5}
        self.add_widget(self.icon)

        column = BoxLayout(orientation="vertical", spacing=dp(-1))
        self.title_label = Label(
            text=title, font_size=sp(8.5), bold=True,
            color=(0.66, 0.79, 0.70, 1), halign="left", valign="middle",
            shorten=True, max_lines=1,
        )
        self.title_label.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        self.value_label = Label(
            text=value, font_size=sp(14.5), bold=True, color=accent,
            halign="left", valign="middle", shorten=True, max_lines=1,
        )
        self.value_label.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        column.add_widget(self.title_label)
        column.add_widget(self.value_label)
        self.add_widget(column)
        self.bind(pos=self._sync, size=self._sync)
        self._sync()

    def _sync(self, *_args) -> None:
        pad = dp(1)
        self._glow.pos = (self.x - pad, self.y - pad)
        self._glow.size = (self.width + pad * 2, self.height + pad * 2)
        self._fill.pos = self.pos
        self._fill.size = self.size
        gloss_h = max(0.0, self.height * 0.5)
        self._top.pos = (self.x + pad, self.y + self.height - gloss_h)
        self._top.size = (max(0, self.width - pad * 2), max(0, gloss_h - pad))
        self._top.radius = [dp(14), dp(14), 0, 0]
        self._edge.rounded_rectangle = (
            self.x + pad, self.y + pad,
            max(0, self.width - pad * 2), max(0, self.height - pad * 2), dp(13),
        )

    def set_value(self, text: str, color=None) -> None:
        _set_text(self.value_label, text)
        if color is not None and list(self.value_label.color) != list(color):
            self.value_label.color = color
            self.icon.set_color(color)


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


class IconButton(GameButton):
    """Круглая кнопка с нарисованным значком."""

    def __init__(self, icon: str, color=(0.10, 0.28, 0.34, 1),
                 text_color=(0.9, 0.96, 1.0, 1), size: float = 46,
                 icon_scale: float = 0.46, **kwargs):
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("size", (dp(size), dp(size)))
        super().__init__(
            text="", color=color, text_color=text_color,
            radius=size / 2.0, gloss=True, **kwargs,
        )
        self._icon = icon
        self._icon_color = list(text_color)
        self._icon_scale = icon_scale
        self._glyph = InstructionGroup()
        self.canvas.after.add(self._glyph)
        self.bind(pos=self._draw_glyph, size=self._draw_glyph)
        self._draw_glyph()

    def _draw_glyph(self, *_args) -> None:
        self._glyph.clear()
        if self.width <= 1:
            return
        cx = self.x + self.width * 0.5
        cy = self.y + self.height * 0.5
        draw_icon(
            self._glyph, self._icon, cx, cy,
            min(self.width, self.height) * self._icon_scale, self._icon_color,
        )

    def set_icon(self, icon: str, color=None) -> None:
        """Меняет значок (и, при желании, его цвет) и перерисовывает."""
        self._icon = icon
        if color is not None:
            self._icon_color = list(color)
        self._draw_glyph()


class HUD(FloatLayout):
    """Верхняя панель: база, золото, волна, герой и кнопки."""

    def __init__(self, on_pause=None, on_shop=None, on_speed=None, on_music=None,
                 **kwargs):
        super().__init__(size_hint=(1, 1), **kwargs)
        self.on_pause = on_pause or (lambda *args: None)
        self.on_shop = on_shop or (lambda *args: None)
        self.on_speed = on_speed or (lambda *args: None)
        self.on_music = on_music or (lambda *args: None)

        self.panel = BoxLayout(
            orientation="vertical",
            size_hint=(1, None),
            height=dp(158) + dp(SAFE_TOP),
            pos_hint={"top": 1},
            padding=(dp(9) + dp(SAFE_SIDE), dp(7) + dp(SAFE_TOP)),
            spacing=dp(5),
        )
        # Полупрозрачная подложка: текст не теряется на фоне замка.
        with self.panel.canvas.before:
            self._panel_glow = Color(1.0, 0.84, 0.36, 0.05)
            self._panel_glow_bg = RoundedRectangle(
                pos=self.panel.pos, size=self.panel.size, radius=[dp(20)]
            )
            self._panel_color = Color(0.03, 0.07, 0.05, 0.82)
            self._panel_bg = RoundedRectangle(
                pos=self.panel.pos, size=self.panel.size, radius=[dp(18)]
            )
            self._panel_top_color = Color(1, 1, 1, 0.04)
            self._panel_top = RoundedRectangle(
                pos=self.panel.pos, size=self.panel.size, radius=[dp(18)]
            )
        self.panel.bind(pos=self._sync_panel, size=self._sync_panel)

        row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(50),
            spacing=dp(6),
        )
        self.base_chip = StatPill("base", t("БАЗА"), "600", (0.48, 0.92, 0.58, 1))
        self.gold_chip = StatPill("coin", t("ЗОЛОТО"), "0", (1.0, 0.86, 0.38, 1))
        self.wave_chip = StatPill("wave", t("ВОЛНА"), f"1/{TOTAL_WAVES}", (0.86, 0.92, 1.0, 1))
        row.add_widget(self.base_chip)
        row.add_widget(self.gold_chip)
        row.add_widget(self.wave_chip)
        self.panel.add_widget(row)

        self.base_meter = Meter(size_hint_y=None, height=dp(6))
        self.panel.add_widget(self.base_meter)

        row2 = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(50),
            spacing=dp(6),
        )
        self.hero_chip = StatPill("hero", t("ГЕРОЙ"), "100 / 100", (0.72, 0.95, 0.78, 1))
        self.hero_chip.size_hint_x = 1
        row2.add_widget(self.hero_chip)

        self.speed_button = IconButton(
            "speed", color=(0.10, 0.28, 0.34, 1),
            text_color=(0.84, 0.96, 1.0, 1), size=46,
        )
        self.speed_button.bind(on_release=lambda *_a: self.on_speed())
        row2.add_widget(self.speed_button)

        self.shop_button = IconButton(
            "shop", color=(0.32, 0.20, 0.46, 1),
            text_color=(1.0, 0.92, 1.0, 1), size=46,
        )
        self.shop_button.bind(on_release=lambda *_a: self.on_shop())
        row2.add_widget(self.shop_button)

        self.music_button = IconButton(
            "sound", color=(0.16, 0.34, 0.28, 1),
            text_color=(0.90, 0.98, 0.92, 1), size=46,
        )
        self.music_button.bind(on_release=lambda *_a: self.on_music())
        row2.add_widget(self.music_button)

        self.pause_button = IconButton(
            "pause", color=(0.05, 0.13, 0.10, 0.92),
            text_color=(1, 1, 1, 1), size=46,
        )
        self.pause_button.bind(on_release=lambda *_a: self.on_pause())
        row2.add_widget(self.pause_button)
        self.panel.add_widget(row2)

        self.boss_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=0,
            spacing=dp(6),
            opacity=0,
        )
        self.boss_label = Label(
            text="", font_size=sp(9.5), bold=True, color=(1.0, 0.58, 0.46, 1),
            size_hint_x=None, width=dp(110), halign="left", valign="middle",
            shorten=True, max_lines=1,
        )
        self.boss_label.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        self.boss_meter = Meter(color=(0.92, 0.24, 0.20, 1), size_hint_y=None, height=dp(10))
        self.boss_row.add_widget(self.boss_label)
        self.boss_row.add_widget(self.boss_meter)
        self.panel.add_widget(self.boss_row)

        self.status_label = Label(
            text="", font_size=sp(10.5), bold=True, color=(1.0, 0.88, 0.50, 1),
            halign="center", valign="middle", size_hint_y=None, height=dp(18),
            shorten=True, max_lines=1,
        )
        self.status_label.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        self.panel.add_widget(self.status_label)

        self.add_widget(self.panel)

    def _sync_panel(self, *_args) -> None:
        pad = dp(1.5)
        self._panel_glow_bg.pos = (self.panel.x - pad, self.panel.y - pad)
        self._panel_glow_bg.size = (
            self.panel.width + pad * 2, self.panel.height + pad * 2
        )
        self._panel_bg.pos = self.panel.pos
        self._panel_bg.size = self.panel.size
        gloss_h = max(0.0, self.panel.height * 0.5)
        self._panel_top.pos = (self.panel.x + pad, self.panel.y + self.panel.height - gloss_h)
        self._panel_top.size = (
            max(0, self.panel.width - pad * 2), max(0, gloss_h - pad)
        )
        self._panel_top.radius = [dp(18), dp(18), 0, 0]

    def set_stats(self, stats: dict) -> None:
        hp = int(stats.get("base_hp", 0))
        max_hp = max(1, int(stats.get("base_max_hp", 1)))
        ratio = hp / max_hp
        if ratio > 0.55:
            color = (0.48, 0.92, 0.58, 1)
        elif ratio > 0.25:
            color = (1.0, 0.82, 0.32, 1)
        else:
            color = (1.0, 0.42, 0.34, 1)
        self.base_chip.set_value(f"{hp} / {max_hp}", color)
        self.base_meter.set_ratio(ratio, color)
        self.gold_chip.set_value(str(int(stats.get("gold", 0))))
        if stats.get("endless"):
            self.wave_chip.set_value(str(int(stats.get("wave", 1))))
        else:
            self.wave_chip.set_value(
                f"{int(stats.get('wave', 1))}/{int(stats.get('total_waves', TOTAL_WAVES))}"
            )
        speed = float(stats.get("time_scale", 1.0))
        _set_text(self.speed_button, "")
        self.speed_button.set_active(speed > 1.0)

        hero_hp = int(stats.get("hero_hp", 0))
        hero_max = max(1, int(stats.get("hero_max_hp", 1)))
        if stats.get("respawn", 0) > 0:
            self.hero_chip.set_value(
                t("возрождение {n} с").format(
                    n=math.ceil(stats.get("respawn", 0))
                ),
                (1.0, 0.80, 0.42, 1),
            )
        else:
            hero_ratio = hero_hp / hero_max
            hero_color = (
                (0.72, 0.95, 0.78, 1) if hero_ratio > 0.35 else (1.0, 0.62, 0.48, 1)
            )
            rage = ""
            if stats.get("rage", 0) > 0:
                rage = t(" · ярость {n}с").format(
                    n=math.ceil(stats.get("rage", 0))
                )
            self.hero_chip.set_value(f"{hero_hp} / {hero_max}{rage}", hero_color)

        if stats.get("wave_state") == "prep":
            status = t(
                "{level} · волна {wave} через {left} с · {preview}"
            ).format(
                level=stats.get("level_name", ""),
                wave=int(stats.get("wave", 1)),
                left=int(math.ceil(stats.get("wave_timer", 0))),
                preview=stats.get("preview", ""),
            )
        else:
            status = t(
                "{level} · волна {wave} · врагов: {enemies}"
            ).format(
                level=stats.get("level_name", ""),
                wave=int(stats.get("wave", 1)),
                enemies=int(stats.get("enemies", 0)),
            )
        roam = ""
        if stats.get("base_distance", 0) > 430:
            arrow = {
                "севернее": "↑", "южнее": "↓",
                "западнее": "←", "восточнее": "→",
            }.get(stats.get("base_dir", ""), "•")
            roam = t(" · база {arrow}{dist}").format(
                arrow=arrow, dist=int(stats.get("base_distance", 0))
            )
        if speed > 1.0:
            roam += f" · x{int(speed)}"
        _set_text(self.status_label, status + roam)

        if stats.get("boss"):
            boss_max = max(1.0, float(stats.get("boss_max", 1)))
            boss_hp = max(0.0, float(stats.get("boss_hp", 0)))
            self.boss_row.opacity = 1
            self.boss_row.height = dp(20)
            _set_text(
                self.boss_label,
                t("{name}: {hp}").format(
                    name=stats.get("boss_name") or t("БОСС"),
                    hp=int(boss_hp),
                ),
            )
            self.boss_meter.set_ratio(boss_hp / boss_max, (1.0, 0.35, 0.28, 1))
        else:
            self.boss_row.opacity = 0
            self.boss_row.height = 0
        # Строка босса добавляет высоту: панель чуть подрастает,
        # чтобы подпись волны не вылезала за подложку.
        target = dp(178 if stats.get("boss") else 158) + dp(SAFE_TOP)
        if abs(self.panel.height - target) > 0.5:
            self.panel.height = target

    def set_music_state(self, enabled: bool) -> None:
        """Показывает на кнопке динамика, включена ли музыка."""
        if enabled:
            self.music_button.set_icon("sound", (0.90, 0.98, 0.92, 1))
            self.music_button.bg = [0.16, 0.34, 0.28, 1]
        else:
            self.music_button.set_icon("mute", (0.96, 0.72, 0.66, 1))
            self.music_button.bg = [0.26, 0.20, 0.20, 1]
        self.music_button._normal_bg = list(self.music_button.bg)
        self.music_button._refresh_style()

    def update_stats(self, stats: dict) -> None:
        self.set_stats(stats)


class BuildCard(GameButton):
    """Карточка постройки: значок сверху, название и цена внизу."""

    def __init__(self, kind: str, icon: str, color=(0.13, 0.45, 0.28, 1),
                 text_color=(1, 1, 1, 1), text: str = "", **kwargs):
        kwargs.setdefault("height", dp(76))
        super().__init__(text=text, color=color, text_color=text_color,
                         radius=14, **kwargs)
        self.kind = kind
        self._icon = icon
        self._icon_color = list(text_color)
        self.valign = "bottom"
        self._glyph = InstructionGroup()
        self.canvas.after.add(self._glyph)
        self.bind(pos=self._draw_glyph, size=self._draw_glyph)
        self.bind(pos=self._sync_text, size=self._sync_text)
        self._sync_text()

    def _sync_text(self, *_args) -> None:
        self.text_size = (self.width, self.height)

    def _draw_glyph(self, *_args) -> None:
        self._glyph.clear()
        if self.width <= 1:
            return
        # Не берём self.center_x: кэш алиаса может быть ещё не сброшен.
        draw_icon(
            self._glyph, self._icon, self.x + self.width * 0.5,
            self.y + self.height - dp(19),
            min(self.width * 0.5, dp(24)), self._icon_color,
        )


class _GlyphButton(GameButton):
    """Квадратная кнопка с нарисованной иконкой вместо текста.

    Нужна там, где Unicode-глиф (стрелка, крестик) может не найтись в шрифте
    телефона — рисуем значок сами, как в HUD.
    """

    def __init__(self, icon: str, color=(0.16, 0.30, 0.22, 1),
                 icon_color=(1, 1, 1, 1), icon_scale: float = 0.42, **kwargs):
        super().__init__(text="", color=color, text_color=icon_color,
                         radius=14, **kwargs)
        self._icon = icon
        self._icon_scale = icon_scale
        self._icon_color = list(icon_color)
        self._glyph = InstructionGroup()
        self.canvas.after.add(self._glyph)
        self.bind(pos=self._draw_glyph, size=self._draw_glyph)

    def _draw_glyph(self, *_args) -> None:
        self._glyph.clear()
        if self.width <= 1:
            return
        color = self._icon_color if not self.disabled else [1, 1, 1, 0.55]
        draw_icon(
            self._glyph, self._icon, self.center_x, self.center_y,
            min(self.width, self.height) * self._icon_scale, color,
        )


class BuildBar(FloatLayout):
    """Нижняя панель строительства и улучшений."""

    def __init__(self, on_build=None, on_upgrades=None, on_confirm=None,
                 on_cycle=None, on_cancel=None, **kwargs):
        super().__init__(size_hint=(1, 1), **kwargs)
        self.on_build = on_build or (lambda *args: None)
        self.on_upgrades = on_upgrades or (lambda *args: None)
        self.on_confirm = on_confirm or (lambda *args: None)
        self.on_cycle = on_cycle or (lambda *args: None)
        self.on_cancel = on_cancel or (lambda *args: None)
        self._mode = None

        panel = BoxLayout(
            orientation="vertical",
            size_hint=(1, None),
            height=dp(112) + dp(SAFE_BOTTOM) * 2,
            pos_hint={"x": 0, "y": 0},
            padding=(dp(7) + dp(SAFE_SIDE), dp(6) + dp(SAFE_BOTTOM)),
            spacing=dp(3),
        )
        with panel.canvas.before:
            self._glow_color = Color(1.0, 0.84, 0.36, 0.05)
            self._glow = RoundedRectangle(pos=panel.pos, size=panel.size, radius=[dp(22)])
            self._bg_color = Color(0.03, 0.07, 0.05, 0.88)
            self._bg = RoundedRectangle(pos=panel.pos, size=panel.size, radius=[dp(20)])
            self._top_color = Color(1, 1, 1, 0.04)
            self._top = RoundedRectangle(pos=panel.pos, size=panel.size, radius=[dp(20)])
        panel.bind(pos=self._sync_panel, size=self._sync_panel)
        self.panel_ref = panel

        self.hint = Label(
            text=t("Строй и защищай базу"),
            font_size=sp(10),
            color=(0.78, 0.90, 0.82, 1),
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=dp(15),
            shorten=True,
            max_lines=1,
        )
        self.hint.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        panel.add_widget(self.hint)

        # Ряд кнопок меняется местами: обычные карточки построек или крупные
        # кнопки режима стройки. Оба ряда живут в контейнере одной высоты,
        # поэтому панель не «прыгает».
        self.row_host = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(76),
        )
        panel.add_widget(self.row_host)

        # --- обычный ряд: карточки построек + улучшения ---------------
        self.normal_row = BoxLayout(orientation="horizontal", spacing=dp(5))
        icons = {"mine": "mine", "tower": "tower", "barracks": "barracks", "totem": "totem"}
        self.buttons = {}
        for kind, data in BUILD_TYPES.items():
            button = BuildCard(
                kind,
                icons.get(kind, kind),
                color=data["color"],
                text=t("{short}\n{cost} з.").format(
                    short=t(data["short"]), cost=data["cost"]
                ),
                font_size=sp(10),
            )
            button.bind(on_release=lambda _inst, k=kind: self.on_build(k))
            self.normal_row.add_widget(button)
            self.buttons[kind] = button

        self.upgrade_button = GameButton(
            text=t("УЛУЧШ.\n+"),
            color=(0.30, 0.20, 0.52, 1),
            text_color=(1.0, 0.92, 1.0, 1),
            height=dp(76),
            radius=14,
            font_size=sp(10),
        )
        self.upgrade_button.bind(on_release=lambda *_a: self.on_upgrades())
        self._upgrade_glyph = InstructionGroup()
        self.upgrade_button.canvas.after.add(self._upgrade_glyph)
        self.upgrade_button.valign = "bottom"
        self.upgrade_button.bind(
            pos=lambda w, _v: self._draw_upgrade_glyph(w),
            size=lambda w, _v: self._draw_upgrade_glyph(w),
        )
        self.normal_row.add_widget(self.upgrade_button)

        # --- ряд режима стройки: ◀ / Построить / ▶ / ✕ ---------------
        # Крупная кнопка подтверждения избавляет от необходимости целиться
        # пальцем: площадку выбираем стрелками, строим одной кнопкой.
        self.mode_row = BoxLayout(orientation="horizontal", spacing=dp(5))
        self.prev_button = _GlyphButton(
            "arrow_left",
            color=(0.16, 0.34, 0.24, 1),
            height=dp(76),
            size_hint_x=None,
            width=dp(54),
        )
        self.prev_button.bind(on_release=lambda *_a: self.on_cycle(-1))
        self.mode_row.add_widget(self.prev_button)

        self.confirm_button = GameButton(
            text=t("ПОСТРОИТЬ"),
            color=(0.14, 0.50, 0.29, 1),
            text_color=(1.0, 0.98, 0.90, 1),
            height=dp(76),
            radius=14,
            font_size=sp(14),
        )
        self.confirm_button.bind(on_release=lambda *_a: self.on_confirm())
        self.mode_row.add_widget(self.confirm_button)

        self.next_button = _GlyphButton(
            "arrow_right",
            color=(0.16, 0.34, 0.24, 1),
            height=dp(76),
            size_hint_x=None,
            width=dp(54),
        )
        self.next_button.bind(on_release=lambda *_a: self.on_cycle(1))
        self.mode_row.add_widget(self.next_button)

        self.cancel_button = _GlyphButton(
            "close",
            color=(0.40, 0.15, 0.15, 1),
            height=dp(76),
            size_hint_x=None,
            width=dp(54),
        )
        self.cancel_button.bind(on_release=lambda *_a: self.on_cancel())
        self.mode_row.add_widget(self.cancel_button)

        self.add_widget(panel)
        self._row_mode = None
        self._set_row(False)

    def _sync_panel(self, *_args) -> None:
        pad = dp(1.5)
        self._glow.pos = (self.panel_ref.x - pad, self.panel_ref.y - pad)
        self._glow.size = (self.panel_ref.width + pad * 2, self.panel_ref.height + pad * 2)
        self._bg.pos = self.panel_ref.pos
        self._bg.size = self.panel_ref.size
        gloss_h = max(0.0, self.panel_ref.height * 0.45)
        self._top.pos = (self.panel_ref.x + pad, self.panel_ref.y + self.panel_ref.height - gloss_h)
        self._top.size = (max(0, self.panel_ref.width - pad * 2), max(0, gloss_h - pad))
        self._top.radius = [dp(20), dp(20), 0, 0]

    def _draw_upgrade_glyph(self, button) -> None:
        self._upgrade_glyph.clear()
        if button.width <= 1:
            return
        draw_icon(
            self._upgrade_glyph, "upgrade", button.x + button.width * 0.5,
            button.y + button.height - dp(19),
            min(button.width * 0.5, dp(24)), list(button.text_color),
        )

    def _set_row(self, mode_row: bool) -> None:
        """Показывает либо обычные карточки, либо ряд режима стройки."""
        if self._row_mode == mode_row:
            return
        self._row_mode = mode_row
        self.row_host.clear_widgets()
        self.row_host.add_widget(self.mode_row if mode_row else self.normal_row)

    def set_state(self, stats: dict, mode: str | None) -> None:
        gold = int(stats.get("gold", 0))
        for kind, button in self.buttons.items():
            cost = int(BUILD_TYPES[kind]["cost"])
            active = mode == kind
            button.set_active(active)
            button.disabled = (not active) and gold < cost

        if mode is None:
            _set_text(self.hint, t("Строй и защищай базу"))
            self._set_row(False)
            return

        data = BUILD_TYPES[mode]
        cost = int(data["cost"])
        self.confirm_button.disabled = gold < cost
        _set_text(
            self.confirm_button,
            t("ПОСТРОИТЬ") + "\n" + t("{cost} з.").format(cost=cost),
        )
        _set_text(
            self.hint,
            "{name}: {pick}".format(
                name=t(data["name"]),
                pick=t("выбери площадку и жми «Построить»"),
            ),
        )
        self._set_row(True)


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
        # Панель не должна растягиваться на всю ширину большого окна:
        # запоминаем исходную долю и ограничиваем реальную ширину.
        try:
            self._panel_ratio = float(panel.size_hint_x or 1.0)
        except (TypeError, ValueError):
            self._panel_ratio = 0.9
        panel.size_hint_x = None
        self.add_widget(panel)
        self.bind(size=self._fit_panel, pos=self._fit_panel)
        self._fit_panel()

    def _fit_panel(self, *_args) -> None:
        if self.panel is None:
            return
        width = min(self.width * self._panel_ratio, dp(MAX_CONTENT_WIDTH))
        self.panel.width = max(dp(220), width)

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
            pos_hint={"center_x": 0.5, "y": 0.145},
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
        if stats.get("endless"):
            caption = t("ВОЛНА {wave} ЧЕРЕЗ {left} С").format(
                wave=wave, left=left
            )
        elif wave >= total:
            caption = t("ПОСЛЕДНЯЯ ВОЛНА")
        else:
            caption = t("ВОЛНА {wave} ЧЕРЕЗ {left} С").format(
                wave=wave, left=left
            )
        _set_text(
            self.button,
            t("{caption}\nВЫЗВАТЬ РАНЬШЕ · +{bonus} З.").format(
                caption=caption, bonus=bonus
            ),
        )

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
