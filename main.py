"""Точка входа игры «Золотой рейд»."""

from __future__ import annotations

import os

# Android увеличивает sp() по системной настройке «размер шрифта», но не
# трогает отступы в dp(). Из-за этого подписи вырастали и вылезали из кнопок
# и панелей — «шрифт разлетался». Интерфейс игры рассчитан на один размер,
# поэтому фиксируем масштаб шрифта до импорта Kivy.
os.environ["KIVY_METRICS_FONTSCALE"] = "1.0"

from kivy.config import Config

# p4a выставляет эти переменные — значит, мы внутри APK на Android.
ANDROID = "ANDROID_ARGUMENT" in os.environ or "ANDROID_PRIVATE" in os.environ

# Настройки окна должны задаваться до создания Window.
if ANDROID:
    # На телефоне/ТВ размер задаёт сам Android, окно на весь экран.
    Config.set("graphics", "fullscreen", "auto")
else:
    Config.set("graphics", "width", "430")
    Config.set("graphics", "height", "860")
    Config.set("graphics", "resizable", "1")
    Config.set("graphics", "fullscreen", "0")
Config.set("input", "mouse", "mouse,multitouch_on_demand")
Config.set("kivy", "exit_on_escape", "0")

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import FadeTransition, ScreenManager

from game.core.i18n import set_language
from game.core.progress import PROGRESS
from game.ui.screens import GameScreen, LevelsScreen, MenuScreen


class GoldRaidApp(App):
    def _build_screens(self, manager) -> None:
        manager.add_widget(MenuScreen(self, manager))
        manager.add_widget(LevelsScreen(self, manager))
        manager.add_widget(GameScreen(self, manager))

    def build(self):
        # Язык нужен до создания экранов: подписи переводятся один раз.
        set_language(PROGRESS.language)
        manager = ScreenManager(transition=FadeTransition(duration=0.18))
        self._build_screens(manager)
        manager.current = "menu"
        return manager

    def rebuild_ui(self) -> None:
        """Пересобирает экраны заново (после смены языка).

        Правит существующий ScreenManager, чтобы ``app.root`` остался тем же
        объектом: на него завязаны переходы и внешние тесты.
        """
        manager = self.root
        if manager is None:
            return
        current = manager.current
        for screen in list(manager.screens):
            dispose = getattr(screen, "dispose", None)
            if callable(dispose):
                try:
                    dispose()
                except Exception:
                    pass
            manager.remove_widget(screen)
        self._build_screens(manager)
        manager.current = current

    def on_start(self) -> None:
        Window.clearcolor = (0.02, 0.06, 0.04, 1)
        # Страховка: если Kivy успел подхватить системный масштаб шрифта,
        # возвращаем его к 1.0 — иначе вёрстка поплывёт на части телефонов.
        try:
            from kivy.metrics import Metrics

            Metrics.fontscale = 1.0
        except Exception:
            pass


if __name__ == "__main__":
    GoldRaidApp().run()
