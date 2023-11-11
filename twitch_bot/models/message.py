from __future__ import annotations
from typing import TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from .user import User
    from twitch_bot.network import Client


@dataclass(repr=True, slots=True)
class Message:
    id: str
    client: Client
    author: User
    content: str

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Message) and self.id == other.id

    def __ne__(self, other: object) -> bool:
        return not isinstance(other, Message) or self.id != other.id

    def delete(self):
        self.client._http.delete_message(self)
