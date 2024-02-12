from __future__ import annotations
from typing import Any, TYPE_CHECKING
import traceback
import json

from twitch_bot.QtCore import QObject
from twitchio.ext import commands

if TYPE_CHECKING:
    from twitch_bot import Client


__all__ = ("Cog",)


class CogMeta(type(commands.Cog), type(QObject)): ...


class Cog(commands.Cog, QObject, metaclass=CogMeta):
    def __init__(self, client: Client) -> None:
        super().__init__()
        self.client = client

    @property
    def window(self):
        return self.client.window

    def _load_methods(self, bot) -> None:
        super()._load_methods(bot)
        for callback in self.client.registered_callbacks:
            if callback.args[0] == self:
                name = callback.func
                if name not in self._events:
                    self._events[name] = []
                self._events[name].append(callback)

    def _unload_methods(self, _) -> None:
        for command in self._commands.values():
            command._instance = None
            command.cog = None
        return super()._unload_methods(_)

    def cog_unload(self) -> None:
        try:
            self.unload()
        except Exception as e:
            traceback.print_exception(type(e), e, e.__traceback__)

    def unload(self) -> None: ...

    def load_settings(self) -> Any:
        try:
            with open(f"{__package__}/settings.json") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
