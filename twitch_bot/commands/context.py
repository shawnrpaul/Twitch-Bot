from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from twitch_bot.models import Message, Streamer
    from twitch_bot.network import Client
    from twitch_bot.commands import Command


class Context:
    def __init__(
        self, client: Client, message: Message, command: Command, args: list[str]
    ) -> None:
        self.client = client
        self.message = message
        self.command = command
        self.args = args
        self.kwargs = {}

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
