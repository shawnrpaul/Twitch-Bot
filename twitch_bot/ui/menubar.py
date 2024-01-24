from __future__ import annotations
from typing import TYPE_CHECKING
from twitch_bot.QtWidgets import QMenuBar, QMenu

if TYPE_CHECKING:
    from .window import MainWindow


class Menubar(QMenuBar):
    def __init__(self, window: MainWindow) -> None:
        super().__init__(window)
        self._window = window
        self._menus: set[QMenu] = set()
        self.hide()

    @property
    def window(self) -> MainWindow:
        return self._window

    def addMenu(self, menu: QMenu) -> None:
        super().addMenu(menu)
        self._menus.add(menu)
        if self.isHidden():
            self.window.addActions(menu.actions())

    def removeMenu(self, menu: QMenu) -> None:
        for action in menu.actions():
            self.removeAction(action)
        self._menus.discard(menu)

    def show(self) -> None:
        super().show()
        for menu in self._menus:
            for action in menu.actions():
                self.window.removeAction(action)

    def hide(self) -> None:
        super().hide()
        for menu in self._menus:
            self.window.addActions(menu.actions())
