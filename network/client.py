from __future__ import annotations
from typing import Any, TYPE_CHECKING
from pathlib import Path
import traceback
import sys
import re

from PyQt6.QtCore import QObject

from .http import HTTP
from .websocket import WebSocket, EventSub
from commands import Context
from models import User, Message

if TYPE_CHECKING:
    from ui import MainWindow
    from models import Streamer
    from commands import Command, Cog, Event


class Client(QObject):
    __cogs__: dict[str, Cog]
    __commands__: dict[str, Command]
    __events__: dict[str, list[Event]]

    def __init__(self, window: MainWindow) -> None:
        super().__init__(window)
        self._window = window
        self._client_id = "gp762nuuoqcoxypju8c569th9wz7q5"
        self._token = "2wq5gfgrxlhc618j0jfwaw4do636jq"
        self._user_id = None
        self._http = HTTP(self)
        self._ws = WebSocket(self)
        self._eventsub = EventSub(self)
        self.streamer: Streamer = None
        self.__cogs__ = {}
        self.__commands__ = {}
        self.__events__ = {}

    @property
    def window(self):
        return self._window

    def start(self) -> None:
        return self._ws.connect()

    def is_ready(self) -> bool:
        return self._ws._ready

    def invoke(self, name: str, ctx: Context, *args, **kwargs):
        if not (command := self.__commands__.get(name)):
            return
        command(ctx, *args, **kwargs)

    def run_command(self, data: dict[str, Any], message: Message):
        if not (command := self.__commands__.get(data["command"]["botCommand"])):
            return
        args = (
            re.split(r"\s+", params)
            if (params := data["command"].get("botCommandParams"))
            else []
        )
        if "\U000e0000" in args:
            args.remove("\U000e0000")
        ctx = Context(self, message, command, args)
        command(ctx)

    def send_message(self, message: str) -> None:
        if not self.streamer:
            return
        self._ws.sendTextMessage(f"PRIVMSG #{self._ws.nick} :{message}\r\n")
        message = Message(0, self.streamer, message)
        self.dispatch("on_message", message)

    def reply(self, message_id: int, message: str) -> None:
        if not self.streamer:
            return
        self._ws.sendTextMessage(
            f"@reply-parent-msg-id={message_id} PRIVMSG #{self._ws.nick} :{message}\r\n"
        )
        message = Message(0, self.streamer, message)
        self.dispatch("on_message", message)

    def command_error(self, ctx: Context, error: Exception):
        if ctx.command.has_error_handler():
            return

        path = open("twitch-bot.log", "a", encoding="utf-8")
        print(f"Ignoring exception in command {ctx.command}:", file=path)
        traceback.print_exception(type(error), error, error.__traceback__, file=path)

    def add_cog(self, cog: Cog) -> Cog:
        name = cog.__class__.__name__
        if self.__cogs__.get(name):
            raise Exception(f"Cog {name} already exists")
        self.__cogs__[name] = cog
        for command in cog.__commands__.keys():
            if self.__commands__.get(command):
                self.window.systemTray.showMessage(
                    f"Cannot add command {command} as it already exists"
                )
                cog.__commands__.pop(command)
                continue
        self.__commands__.update(cog.__commands__)
        for name, events in cog.__events__.items():
            if not (lst := self.__events__.get(name, [])):
                self.__events__[name] = lst
            lst.extend(events)
        return cog

    def remove_cog(self, cog: Cog) -> None:
        if not self.__cogs__.pop(cog.__class__.__name__, None):
            raise Exception(f"Cog {cog.__class__.__name__} doesn't exist")
        for key in cog.__commands__:
            self.__commands__.pop(key)
        for name, events in cog.__events__.items():
            evnts = self.__events__.get(name)
            for event in events:
                evnts.remove(event)
        cog.unload()

    def dispatch(self, event: str, *args, **kwargs):
        for evnt in self.__events__.get(event, []):
            evnt(*args, **kwargs)

    def fetch_users(self, users: list[int, str]):
        users_data = self._http.fetch_users(users)
        return [User(**data, http=self._http) for data in users_data]

    def create_prediction(
        self, broadcaster_id: int, title: str, options: list[str], length: int = 120
    ):
        return self._http.create_prediction(broadcaster_id, title, options, length)

    def close(self):
        self._ws.close()
        self._eventsub.close()
