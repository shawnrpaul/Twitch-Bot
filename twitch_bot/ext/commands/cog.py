from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt6.QtCore import QObject
from twitchio.ext import commands

if TYPE_CHECKING:
    from twitch_bot import Client

__all__ = ("Cog",)


class CogMeta(type(commands.Cog), type(QObject)):
    ...


class Cog(commands.Cog, QObject, metaclass=CogMeta):
    def __init__(self, client: Client) -> None:
        super().__init__()
        self.client = client
