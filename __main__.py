from PyQt6.QtWidgets import QApplication
from twitch_bot.ui import MainWindow
import asyncio


async def qt_loop():
    while app.isOpen:
        app.processEvents()
        await asyncio.sleep(0)


def close():
    app.isOpen = False


app = QApplication([])
app.isOpen = True
window = MainWindow()
loop = asyncio.get_event_loop()
app.aboutToQuit.connect(close)
loop.run_until_complete(qt_loop())
