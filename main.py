import os
import sys
import traceback
import logging
from PyQt6.QtWidgets import QApplication
from pathlib import Path
from types import TracebackType
from typing import Any, Optional, Type

from PyQt6.QtWidgets import QApplication
from ui import MainWindow

logging.basicConfig(
    filename="twitch-bot.log",
    format="%(levelname)s:%(asctime)s:%(message)s",
    level=logging.ERROR,
)


def excepthook(
    exc_type: Type[BaseException],
    exc_value: Optional[BaseException],
    exc_tb: TracebackType,
) -> Any:
    tb = traceback.TracebackException(exc_type, exc_value, exc_tb)
    cwd = Path(os.path.dirname(os.path.dirname(__file__))).absolute()
    try:
        for frame in tb.stack[::-1]:
            file = Path(frame.filename).absolute()
            if file.is_relative_to(cwd):
                line = frame.lineno
                break
        logging.error(f"{file.name}({line}) - {exc_type.__name__}: {exc_value}")
    except Exception:
        logging.error(f"{exc_type.__name__}: {exc_value}")
    app.quit()
    return sys.__excepthook__(exc_type, exc_value, exc_tb)


sys.excepthook = excepthook

app = QApplication([])
window = MainWindow()
app.exec()
