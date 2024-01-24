from __future__ import annotations
from typing import TYPE_CHECKING

from twitch_bot.QtCore import Qt, QEvent
from twitch_bot.QtGui import QEnterEvent, QMouseEvent
from twitch_bot.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout, QWidget

if TYPE_CHECKING:
    from .window import MainWindow


class SidebarLabel(QLabel):
    def __init__(self, window: MainWindow, widget: QWidget | None = None):
        super().__init__()
        self._window = window
        self.setWidget(widget)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)

    @property
    def window(self) -> MainWindow:
        return self._window

    def setWidget(self, widget: QWidget | None = None):
        self._widget = widget
        self.setText(widget.objectName())

    def enterEvent(self, event: QEnterEvent | None) -> None:
        if not self._widget:
            return
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        event.accept()

    def leaveEvent(self, a0: QEvent | None) -> None:
        if not self._widget:
            return
        self.setCursor(Qt.CursorShape.ArrowCursor)
        a0.accept()

    def mousePressEvent(self, ev: QMouseEvent | None) -> None:
        if not self._widget:
            return
        self.window.stack.setCurrentWidget(self._widget)
        return super().mousePressEvent(ev)


class Sidebar(QFrame):
    def __init__(self, window: MainWindow) -> None:
        super().__init__(window)
        self._window = window
        self.setObjectName("Sidebar")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Plain)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumWidth(1)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(5, 10, 5, 0)
        self._layout.setSpacing(0)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self._layout)

    def createLabel(self, widget: QWidget | None = None) -> SidebarLabel:
        label = SidebarLabel(self.window, widget=widget)
        self._layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignTop)
        return label

    def removeLabel(self, widget: QWidget) -> bool:
        for i in range(self._layout.count()):
            label: SidebarLabel = self.layout.itemAt(i).widget()
            if label._widget == widget:
                self._layout.removeWidget(label)
                label.deleteLater()
                return True

        message = f"Couldn't remove {widget.objectName()}"
        self.window.showMessage(message)
        self.window.log(message)
        return False

    @property
    def window(self) -> MainWindow:
        return self._window

    @property
    def layout(self) -> QVBoxLayout:
        return self._layout
