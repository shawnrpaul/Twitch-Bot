from __future__ import annotations
from typing import Optional, Type, TYPE_CHECKING
from pathlib import Path
import traceback
import logging
import sys

from twitch_bot.QtWidgets import QPlainTextEdit, QMessageBox

if TYPE_CHECKING:
    from .window import MainWindow
    from types import TracebackType

logger = logging.getLogger("twitch-bot")
formatter = logging.Formatter("%(levelname)s:%(asctime)s: %(message)s")
file_handler = logging.FileHandler("twitch-bot.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


class Stdout:
    def __init__(self, logs: Logs) -> None:
        self.logs = logs

    def write(self, text: str):
        self.logs.setPlainText(f"{self.logs.toPlainText()}{text}")

    def flush(self) -> None:
        pass


class Logs(QPlainTextEdit):
    def __init__(self, window: MainWindow) -> None:
        super().__init__()
        self._window = window

        action = self.addAction("Hide Logs")
        action.setShortcut("Alt+C")
        action.triggered.connect(
            lambda: self.show() if self.isHidden() else self.hide()
        )

        sys.stdout = sys.stderr = Stdout(self)
        sys.excepthook = self.excepthook

        self.setWindowTitle("Logs")
        self.resize(700, 350)

        self.setContentsMargins(0, 0, 0, 0)
        self.setReadOnly(True)

    @property
    def window(self) -> MainWindow:
        return self._window

    def setPlainText(self, text: str | None) -> None:
        scrollbar = self.verticalScrollBar()
        value = scrollbar.value()
        max = scrollbar.maximum()
        super().setPlainText(text)
        scrollbar.setValue(scrollbar.maximum()) if value == max else ...

    def log(self, text: str, level=logging.ERROR):
        print(text)
        logger.log(msg=text, level=level)

    def excepthook(
        self,
        exc_type: Type[BaseException],
        exc_value: Optional[BaseException],
        exc_tb: TracebackType,
    ):
        try:
            file = Path(exc_tb.tb_frame.f_code.co_filename)
            line = exc_tb.tb_lineno
            logger.error(f"{file.name}({line}) - {exc_type.__name__}: {exc_value}")
            if not file.is_relative_to(Path("cogs").absolute()) and not file.is_relative_to(Path("site-packages").absolute()):  # fmt:skip
                dialog = QMessageBox()
                dialog.setWindowTitle("Twitch-Bot")
                dialog.setText(
                    "Srpbotz crashed. Please restart to continue running the bot."
                )
                return sys.exit(1)
        except Exception:
            logger.error(f"{exc_type.__name__}: {exc_value}")
        traceback.print_exception(exc_type, exc_value, exc_tb)
