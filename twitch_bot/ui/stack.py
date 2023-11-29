from __future__ import annotations
from typing import TYPE_CHECKING
import importlib
import traceback
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


if TYPE_CHECKING:
    from PyQt6.QtWidgets import QWidget
    from .window import MainWindow
    from twitchio.ext import commands

__all__ = ("Stack",)


class CogLabel(QLabel):
    def __init__(self, window: MainWindow, cog: commands.Cog):
        super().__init__(window)
        self._window = window
        self.client = window.client
        self.cog = cog
        self.setText(cog.name.capitalize())
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(50, 150)
        self.setMaximumHeight(150)
        self.setMargin(23)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.setContentsMargins(0, 0, 30, 0)

        self.unload = QPushButton(self)
        self.unload.setText("Unload")
        self.unload.setMinimumSize(91, 31)
        self.unload.setMaximumSize(91, 31)
        self.unload.pressed.connect(lambda: self.client.remove_cog(self.cog))
        layout.addWidget(self.unload)

        self.setLayout(layout)

    @property
    def window(self) -> MainWindow:
        return self._window


class CogsPage(QScrollArea):
    def __init__(self, window: MainWindow) -> None:
        super().__init__(window)
        self._window = window
        self.setObjectName("Cogs")
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

    def addCog(self, cog: commands.Cog) -> None:
        self._layout.addWidget(CogLabel(self.window, cog))

    def removeCog(self, cog: commands.Cog) -> None:
        for index in self._layout.count():
            label: CogLabel = self._layout.itemAt(index).widget()
            if label.cog == cog:
                self._layout.removeWidget(label)
                return label.deleteLater()


class Stack(QStackedWidget):
    def __init__(self, window: MainWindow) -> None:
        super().__init__(window)
        self._window = window
        self.cogsPage = CogsPage(self.window)
        self.addWidget(self.cogsPage)

    @property
    def window(self) -> MainWindow:
        return self._window

    def addCog(self, cog: commands.Cog) -> None:
        self.cogsPage.addCog(cog)

    def removeCog(self, cog: commands.Cog) -> None:
        self.cogsPage.removeCog(cog)

    def addWidget(self, w: QWidget) -> None:
        self.window.sidebar.createLabel(w)
        return super().addWidget(w)

    def removeWidget(self, w: QWidget | None) -> None:
        self.window.sidebar.removeLabel(w)
        return super().removeWidget(w)

    @property
    def window(self) -> MainWindow:
        return self._window
