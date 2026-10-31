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

from game.ui.screens import GameScreen, LevelsScreen, MenuScreen


class GoldRaidApp(App):
    def build(self):
        manager = ScreenManager(transition=FadeTransition(duration=0.18))
        manager.add_widget(MenuScreen(self, manager))
        manager.add_widget(LevelsScreen(self, manager))
        manager.add_widget(GameScreen(self, manager))
        manager.current = "menu"
        return manager

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
