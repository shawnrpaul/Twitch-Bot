from PyQt6.QtWidgets import QApplication
from twitch_bot.ui import MainWindow


app = QApplication([])
window = MainWindow()
app.exec()
