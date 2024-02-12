from __future__ import annotations
from typing import TYPE_CHECKING

from twitch_bot.QtGui import QIcon
from twitch_bot.QtWidgets import QMenu, QSystemTrayIcon

if TYPE_CHECKING:
    from .window import MainWindow


class SystemTray(QSystemTrayIcon):
    def __init__(self, window: MainWindow):
        super().__init__(QIcon("icons/twitch.png"), window)
        self._window = window
        self.createMenu()
        self.activated.connect(
            lambda reason: (
                self.showWindow()
                if reason == self.ActivationReason.DoubleClick
                else ...
            )
        )

    def createMenu(self):
        menu = QMenu(self._window)
        show_hide = menu.addAction("Show")
        show_hide.triggered.connect(self.showWindow)
        exit = menu.addAction("Exit")
        exit.triggered.connect(self._window.close)
        self.setContextMenu(menu)

    def showWindow(self) -> None:
        self._window.show() if self._window.isHidden() else ...

    def showMessage(self, msg: str, time: int = 3000):
        return super().showMessage("Twitch Bot", msg, self.icon(), time)
