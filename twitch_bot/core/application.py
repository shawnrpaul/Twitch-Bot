from PyQt6.QtWidgets import QApplication
import asyncio


class Application(QApplication):
    def __init__(self, argv: list[str]) -> None:
        super().__init__(argv)
        self.isRunning = False

    async def runEventLoop(self) -> None:
        while self.isRunning:
            self.processEvents()
            await asyncio.sleep(0)

    def start(self) -> None:
        if not self.isRunning:
            self.isRunning = True
            asyncio.get_event_loop().run_until_complete(self.runEventLoop())

    def close(self) -> None:
        self.isRunning = False
