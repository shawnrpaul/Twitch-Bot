from __future__ import annotations
from typing import TYPE_CHECKING
import logging

from twitch_bot.QtCore import QFileSystemWatcher
from twitch_bot.QtGui import QCloseEvent
from twitch_bot.QtWidgets import QMainWindow

from .body import Body
from .menubar import Menubar
from .sidebar import Sidebar
from .stack import Stack
from .systemtray import SystemTray
from .logs import Logs

if TYPE_CHECKING:
    from twitch_bot import Client


class MainWindow(QMainWindow):
    def __init__(self, client: Client) -> None:
        super().__init__()
        self.client = client

        self.body = Body(self)
        self.menubar = Menubar(self)
        self.systemTray = SystemTray(self)
        self.sidebar = Sidebar(self)
        self.stack = Stack(self)
        self.logs = Logs(self)

        action = self.addAction("Logs")
        action.setShortcut("Alt+C")
        action.triggered.connect(
            lambda: self.logs.show() if self.logs.isHidden() else self.logs.hide()
        )
        action = self.addAction("Menubar")
        action.setShortcut("Alt+M")
        action.triggered.connect(
            lambda: self.menubar.show()
            if self.menubar.isHidden()
            else self.menubar.hide()
        )

        styles_path = "data/styles.qss"
        self.application.setStyleSheet(open(styles_path).read())
        self._styles = QFileSystemWatcher()
        self._styles.addPath(styles_path)
        self._styles.fileChanged.connect(
            lambda path: self.application.setStyleSheet(open(path).read())
        )

        self.setMenuBar(self.menubar)
        self.body.addWidget(self.sidebar, 3)
        self.body.addWidget(self.stack, 10)
        self.setCentralWidget(self.body)

        self.setWindowTitle("Twitch Bot")

    @property
    def application(self):
        return self.client.application

    def closeEvent(self, event: QCloseEvent):
        if self.systemTray.isVisible():
            self.hide()
            self.logs.close() if not self.logs.isHidden() else ...
            self.client.run_event("window_close")
            return event.ignore()
        return super().closeEvent(event)

    def close(self) -> None:
        self.logs.close()
        self.client.loop.create_task(self.client.close()).add_done_callback(
            lambda _: self.client.loop.stop()
        )
        return super().close()

    def showMessage(self, message: str, time=3000):
        self.systemTray.showMessage(message, time)

    def log(self, text: str, level=logging.ERROR):
        self.logs.log(text, level)
