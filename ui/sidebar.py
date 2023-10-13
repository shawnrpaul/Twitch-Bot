from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QEnterEvent, QMouseEvent
from PyQt6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout, QWidget

if TYPE_CHECKING:
    from .window import MainWindow


class SidebarLabel(QLabel):
    def __init__(self, sidebar: Sidebar, widget: QWidget):
        super().__init__(sidebar)
        self._window = sidebar.window
        self.widget = widget
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    @property
    def window(self) -> MainWindow:
        return self._window

    def enterEvent(self, event: QEnterEvent | None) -> None:
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        event.accept()

    def leaveEvent(self, a0: QEvent | None) -> None:
        self.setCursor(Qt.CursorShape.ArrowCursor)
        a0.accept()

    def mousePressEvent(self, ev: QMouseEvent | None) -> None:
        self.window.stack.setCurrentWidget(self.widget)
        return super().mousePressEvent(ev)


class Sidebar(QFrame):
    def __init__(self, window: MainWindow) -> None:
        super().__init__(window)
        self._window = window
        self.setObjectName("Sidebar")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Plain)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumWidth(25)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(5, 10, 5, 0)
        self._layout.setSpacing(0)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self._layout)

    def addWidget(self, widget: QWidget) -> None:
        self._layout.addWidget(widget, alignment=Qt.AlignmentFlag.AlignTop)

    def removeWidget(self, widget: QWidget) -> None:
        self._layout.removeWidget(widget)
        widget.deleteLater()

    @property
    def window(self) -> MainWindow:
        return self._window

    @property
    def layout(self) -> QVBoxLayout:
        return self._layout
