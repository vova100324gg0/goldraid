"""Экраны игры: меню, арена и модальные окна."""

from __future__ import annotations

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget

from .arena import Arena
from .config import GLOBAL_UPGRADES, SHOP_ITEMS, TOTAL_WAVES
from .levels import LEVELS
from .progress import PROGRESS
from .widgets import BuildBar, GameButton, HUD, Overlay, Toast


class Backdrop(FloatLayout):
    """Фон меню: мягкий градиент и золотое свечение."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            self._c1 = Color(0.035, 0.10, 0.06, 1)
            self._r1 = Rectangle()
            self._c2 = Color(0.06, 0.19, 0.11, 1)
            self._r2 = Rectangle()
            self._c3 = Color(0.10, 0.28, 0.16, 1)
            self._r3 = Rectangle()
            self._glow_color = Color(1.0, 0.84, 0.35, 0.07)
            self._glow = Ellipse()
            self._line_color = Color(1.0, 0.84, 0.35, 0.12)
            self._line = Line(width=dp(2))
        self.bind(pos=self._layout, size=self._layout)

    def _layout(self, *_args) -> None:
        w, h = self.size
        self._r1.pos = self.pos
        self._r1.size = (w, h)
        self._r2.pos = self.pos
        self._r2.size = (w, h * 0.55)
        self._r3.pos = self.pos
        self._r3.size = (w, h * 0.22)
        self._glow.pos = (self.x + w * 0.5 - w * 0.62, self.y + h * 0.55)
        self._glow.size = (w * 1.24, h * 0.62)
        self._line.circle = (
            self.x + w * 0.5,
            self.y + h * 0.58,
            min(w, h) * 0.46,
        )


class MenuCard(BoxLayout):
    """Карточка с закруглённым фоном для меню и модальных окон."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            self._fill = Color(0.03, 0.08, 0.05, 0.90)
            self._rect = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(26)]
            )
            self._edge = Color(1.0, 0.84, 0.35, 0.18)
            self._outline = Line(rounded_rectangle=(0, 0, 0, 0, dp(26)), width=dp(1.2))
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *_args) -> None:
        self._rect.pos = self.pos
        self._rect.size = self.size
        pad = dp(1)
        self._outline.rounded_rectangle = (
            self.x + pad,
            self.y + pad,
            max(0, self.width - pad * 2),
            max(0, self.height - pad * 2),
            dp(25),
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


class MenuScreen(Screen):
    def __init__(self, app_ref, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.name = "menu"
        self.app_ref = app_ref
        self.screen_manager = screen_manager
        self.level_buttons = []

        self.backdrop = Backdrop()
        self.add_widget(self.backdrop)

        self.card = MenuCard(
            orientation="vertical",
            size_hint=(0.92, None),
            height=dp(700),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            padding=(dp(20), dp(16)),
            spacing=dp(7),
        )

        title = Label(
            text="ЗОЛОТОЙ РЕЙД",
            font_size=sp(31),
            bold=True,
            color=(1.0, 0.84, 0.35, 1),
            size_hint_y=None,
            height=dp(46),
            halign="center",
            valign="middle",
        )
        title.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        self.card.add_widget(title)

        subtitle = Label(
            text="Выбери карту и защити ворота",
            font_size=sp(13),
            color=(0.78, 0.90, 0.82, 1),
            size_hint_y=None,
            height=dp(26),
            halign="center",
            valign="middle",
        )
        subtitle.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        self.card.add_widget(subtitle)

        self.card.add_widget(Divider())

        self.summary = Label(
            text="",
            font_size=sp(10.5),
            color=(0.86, 0.78, 0.50, 1),
            size_hint_y=None,
            height=dp(20),
            halign="center",
            valign="middle",
        )
        self.summary.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        self.card.add_widget(self.summary)

        for index, level in enumerate(LEVELS):
            button = GameButton(
                text="",
                color=level.accent,
                text_color=(1.0, 0.97, 0.88, 1),
                height=dp(112),
                radius=15,
                font_size=sp(12),
            )
            button.halign = "center"
            button.valign = "middle"
            button.bind(
                size=lambda w, _v: setattr(
                    w, "text_size", (max(1, w.width - dp(18)), None)
                )
            )
            button.text_size = (max(1, button.width - dp(18)), None)
            button.bind(on_release=lambda _inst, i=index: self._play(i))
            self.card.add_widget(button)
            self.level_buttons.append(button)

        self.card.add_widget(Divider())

        rules = Label(
            text=(
                "Враги идут по дорогам из порталов. Боссы и вожаки — "
                "каждую чётную волну.\n"
                "Строй шахты, башни, казармы и тотемы. Собирай золото по карте."
            ),
            font_size=sp(10.5),
            color=(0.70, 0.82, 0.74, 1),
            size_hint_y=None,
            height=dp(48),
            halign="center",
            valign="middle",
        )
        rules.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        self.card.add_widget(rules)

        self.quit = GameButton(
            text="ВЫХОД",
            color=(0.30, 0.13, 0.12, 1),
            text_color=(1.0, 0.86, 0.84, 1),
            height=dp(42),
            radius=13,
            font_size=sp(14),
        )
        self.quit.bind(on_release=self._quit)
        self.card.add_widget(self.quit)

        hint = Label(
            text="ПК: WASD/стрелки · Телефон: палец по экрану",
            font_size=sp(9.5),
            color=(0.55, 0.68, 0.60, 1),
            size_hint_y=None,
            height=dp(18),
            halign="center",
            valign="middle",
        )
        hint.bind(size=lambda w, _v: setattr(w, "text_size", w.size))
        self.card.add_widget(hint)

        self.add_widget(self.card)
        Clock.schedule_once(lambda _dt: self.refresh_levels(), 0)

    # ------------------------------------------------------------------
    def on_enter(self) -> None:
        self.refresh_levels()

    def refresh_levels(self) -> None:
        unlocked = max(1, min(len(LEVELS), PROGRESS.unlocked))
        self.summary.text = f"Открыто карт: {unlocked} из {len(LEVELS)}"
        for index, (level, button) in enumerate(zip(LEVELS, self.level_buttons)):
            available = PROGRESS.is_unlocked(index)
            stars = PROGRESS.stars(level.id) if available else 0
            best_wave = PROGRESS.best_wave(level.id) if available else 0
            if available:
                star_text = f"Звёзд: {stars}/3"
                details = (
                    f"{level.waves} волн · {star_text} · {level.subtitle}"
                )
                if best_wave:
                    details += f" · рекорд: {best_wave}"
                button.text = f"{level.name}\n{details}"
                button.text_color = (1.0, 0.97, 0.88, 1)
            else:
                button.text = (
                    f"{level.name}\n"
                    f"{level.waves} волн · ЗАКРЫТО\n"
                    "Пройди предыдущую карту"
                )
                button.text_color = (0.72, 0.78, 0.72, 1)
            button.disabled = not available

    def _play(self, index: int) -> None:
        if not PROGRESS.is_unlocked(index):
            return
        game = self.screen_manager.get_screen("game")
        game.start_level(index)
        self.screen_manager.current = "game"

    def _quit(self, _instance) -> None:
        self.app_ref.stop()


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
            height=dp(250),
            pos_hint={"center_x": 0.5, "y": 0.135},
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
