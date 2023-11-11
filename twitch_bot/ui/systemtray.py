from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon

if TYPE_CHECKING:
    from .window import MainWindow


class SystemTray(QSystemTrayIcon):
    def __init__(self, window: MainWindow):
        super().__init__(QIcon("icons/twitch.png"), window)
        self._window = window
        self.createMenu()

    def createMenu(self):
        self.menu = QMenu(self._window)
        show_hide = self.menu.addAction("Show")
        show_hide.triggered.connect(
            lambda: self._window.show() if self._window.isHidden() else ...
        )
        exit = self.menu.addAction("Exit")
        exit.triggered.connect(self._window.close)
        self.setContextMenu(self.menu)

    def showMessage(self, msg: str, time: int = 3000):
        return super().showMessage("Twitch Bot", msg, self.icon(), time)
