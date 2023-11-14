from __future__ import annotations
from typing import TYPE_CHECKING
import logging

from PyQt6.QtGui import QIcon, QCloseEvent
from PyQt6.QtWidgets import QApplication, QMainWindow

from .body import Body
from .sidebar import Sidebar
from .stack import Stack
from .systemtray import SystemTray
from .logs import Logs
from twitch_bot.network import Client

if TYPE_CHECKING:
    from .sidebar import Sidebar
    from .stack import Stack


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.client = Client(self)

        self.body = Body(self)
        self.systemTray = SystemTray(self)
        self.sidebar = Sidebar(self)
        self.stack = Stack(self)
        self.logs = Logs(self)

        action = self.addAction("Logs")
        action.setShortcut("Alt+C")
        action.triggered.connect(
            lambda: self.logs.show() if self.logs.isHidden() else self.logs.hide()
        )

        self.body.addWidget(self.sidebar, 3)
        self.body.addWidget(self.stack, 10)
        self.setCentralWidget(self.body)

        self.setWindowTitle("Twitch Bot")
        self.setWindowIcon(QIcon("icons/twitch.ico"))
        self.setStyleSheet(open("data/styles.qss").read())

        self.stack.cogsPage.addCogs()
        self.client.start()

    def setWindowIcon(self, icon: QIcon) -> None:
        self.logs.setWindowIcon(icon)
        return super().setWindowIcon(icon)

    def setStyleSheet(self, styleSheet: str | None) -> None:
        self.logs.setStyleSheet(styleSheet)
        return super().setStyleSheet(styleSheet)

    def closeEvent(self, event: QCloseEvent):
        if self.systemTray.isVisible():
            self.hide()
            self.logs.hide() if not self.logs.isHidden() else ...
            return event.ignore()
        return super().closeEvent(event)

    def close(self):
        self.client.dispatch("on_close")
        return QApplication.instance().exit()

    def showMessage(self, message: str, time=3000):
        self.systemTray.showMessage(message, time)

    def log(self, text: str, level=logging.ERROR):
        self.logs.log(text, level)
