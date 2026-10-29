"""Точка входа игры «Золотой рейд»."""

from __future__ import annotations

import os

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

from game.screens import GameScreen, MenuScreen


class GoldRaidApp(App):
    def build(self):
        manager = ScreenManager(transition=FadeTransition(duration=0.18))
        manager.add_widget(MenuScreen(self, manager))
        manager.add_widget(GameScreen(self, manager))
        manager.current = "menu"
        return manager

    def on_start(self) -> None:
        Window.clearcolor = (0.02, 0.06, 0.04, 1)


if __name__ == "__main__":
    GoldRaidApp().run()
