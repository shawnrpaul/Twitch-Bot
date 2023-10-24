import sys
import logging
from PyQt6.QtWidgets import QApplication

from PyQt6.QtWidgets import QApplication
from ui import MainWindow

logging.basicConfig(
    filename="twitch-bot.log",
    format="%(levelname)s:%(asctime)s:%(message)s",
    level=logging.ERROR,
)

sys.stderr = open("twitch-bot.log", "a")

app = QApplication([])
window = MainWindow()
app.exec()
