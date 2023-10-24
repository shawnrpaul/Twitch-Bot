from __future__ import annotations
from typing import TYPE_CHECKING
import importlib
import logging
import copy
import sys
import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QStackedWidget,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .sidebar import SidebarLabel

if TYPE_CHECKING:
    from .window import MainWindow
    from commands import Cog

__all__ = ("Stack",)


class CogLabel(QLabel):
    def __init__(self, window: MainWindow, path: str, mod, cog: Cog):
        super().__init__(window)
        self._window = window
        self.client = window.client
        self.path = path
        self.cog = cog
        self.setText(cog.__class__.__name__)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(50, 150)
        self.setMaximumHeight(150)
        self.setMargin(23)
        self._mod = mod

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.setContentsMargins(0, 0, 30, 0)

        self.load_unload = QPushButton(self)
        self.load_unload.setText("Unload")
        self.load_unload.setMinimumSize(91, 31)
        self.load_unload.setMaximumSize(91, 31)
        self.load_unload.pressed.connect(self._load_unload)
        layout.addWidget(self.load_unload)

        self.reload = QPushButton(self)
        self.reload.setText("Reload")
        self.reload.setMinimumSize(91, 31)
        self.reload.setMaximumSize(91, 31)
        self.reload.pressed.connect(self._reload)
        layout.addWidget(self.reload)

        self.setLayout(layout)

    @property
    def window(self) -> MainWindow:
        return self._window

    def _remove_modules(self):
        for name in copy.copy(sys.modules).keys():
            mod_name = f"cogs.{self.path}"
            if name.startswith(mod_name) and name != mod_name:
                sys.modules.pop(name)

    def _load_unload(self):
        if self.load_unload.text() == "Unload":
            self.load_unload.setText("Load")
            self.client.remove_cog(self.cog)
            return self._remove_modules()
        self._mod = importlib.import_module(f"cogs.{self.path}")
        try:
            self.cog = self._mod.setup(self.client)
            self.load_unload.setText("Unload")
        except Exception as e:
            self.load_unload.setText("Load")
            logging.error(str(e))

    def _reload(self):
        try:
            self.client.remove_cog(self.cog)
            self._remove_modules()
            self._mod = importlib.reload(self._mod)
            self.cog = self._mod.setup(self.client)
            self.setText(self.cog.__class__.__name__)
        except Exception as e:
            return logging.error(str(e))


class CogsPage(QScrollArea):
    def __init__(self, window: MainWindow) -> None:
        super().__init__(window)
        self._window = window
        self.page = QFrame(self)
        self.page.setFrameShape(QFrame.Shape.StyledPanel)
        self.page.setFrameShadow(QFrame.Shadow.Plain)
        self.page.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.page.setContentsMargins(0, 6, 0, 6)
        self._layout = QVBoxLayout(self.page)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.page.setLayout(self._layout)
        self.page.setMinimumWidth(500)
        self.setWidgetResizable(True)
        self.setWidget(self.page)
        self.page.setParent(self)

    @property
    def window(self) -> MainWindow:
        return self._window

    def addCogs(self):
        for path in os.listdir("cogs"):
            if os.path.isfile(f"cogs/{path}"):
                if not path.endswith(".py"):
                    continue
            else:
                if "__init__.py" not in os.listdir(f"cogs/{path}"):
                    continue
            path = path.replace(".py", "")
            try:
                mod = importlib.import_module(f"cogs.{path}")
                cog = mod.setup(self.window.client)
            except Exception as e:
                logging.error(f"{e.__class__.__name__}: {e}")
                continue
            self._layout.addWidget(CogLabel(self.window, path, mod, cog))


class Stack(QStackedWidget):
    def __init__(self, window: MainWindow) -> None:
        super().__init__(window)
        self._window = window
        self.cogsPage = CogsPage(self.window)
        self.addWidget(self.cogsPage)

        self.cogsLabel = SidebarLabel(self, self.cogsPage)
        self.cogsLabel.setText("Cogs")
        self.window.sidebar.addWidget(self.cogsLabel)

    def removeWidget(self, w: QWidget | None) -> None:
        super().removeWidget(w)
        w.deleteLater()

    @property
    def window(self) -> MainWindow:
        return self._window
