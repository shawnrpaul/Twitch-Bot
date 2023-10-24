from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models import Message, Streamer
    from network import Client
    from commands import Command


class Context:
    def __init__(
        self, client: Client, message: Message, command: Command, args: list[str]
    ) -> None:
        self.client = client
        self.message = message
        self.command = command
        self.args = args

    @property
    def streamer(self) -> Streamer:
        return self.client.streamer

    @property
    def author(self):
        return self.message.author

    def send(self, message: str):
        self.client.send_message(message)

    def reply(self, message: str):
        self.client.reply(self.message.id, message)
