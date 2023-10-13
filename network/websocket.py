from __future__ import annotations
from typing import TYPE_CHECKING
from abc import abstractmethod
import json

from PyQt6.QtCore import QUrl
from PyQt6.QtNetwork import QNetworkRequest
from PyQt6.QtWebSockets import QWebSocket, QWebSocketProtocol

from models import Streamer, Chatter, Message
from _parser import parse_message, parse_event

if TYPE_CHECKING:
    from .client import Client


class BaseWebSocket(QWebSocket):
    URL = ""

    def __init__(self, client: Client) -> None:
        super().__init__("", QWebSocketProtocol.Version.Version13, client)
        self.client = client
        self._http = client._http
        self.connected.connect(self.ws_connected)
        self.textMessageReceived.connect(self.parse_message)
        self.disconnected.connect(self.ws_disconnected)
        self.error.connect(self.ws_error)

    def connect(self) -> None:
        return self.open(QUrl(self.URL))

    @abstractmethod
    def ws_connected(self):
        ...

    @abstractmethod
    def ws_disconnected(self):
        ...

    @abstractmethod
    def ws_error(self, code):
        ...

    @abstractmethod
    def parse_message(self):
        ...


class EventSub(BaseWebSocket):
    URL = "wss://eventsub.wss.twitch.tv/ws"

    def __init__(self, client: Client) -> None:
        super().__init__(client)
        self._session_id: str = None

    def parse_message(self, response: str):
        data = json.loads(response)
        if data["metadata"]["message_type"] == "session_welcome":
            self._session_id = data["payload"]["session"]["id"]
            events = [
                {
                    "type": "channel.follow",
                    "version": "2",
                    "condition": {
                        "broadcaster_user_id": self.client._user_id,
                        "moderator_user_id": self.client._user_id,
                    },
                },
                {
                    "type": "channel.subscribe",
                    "version": "1",
                    "condition": {
                        "broadcaster_user_id": self.client._user_id,
                    },
                },
                {
                    "type": "channel.subscription.gift",
                    "version": "1",
                    "condition": {
                        "broadcaster_user_id": self.client._user_id,
                    },
                },
                {
                    "type": "channel.subscription.message",
                    "version": "1",
                    "condition": {
                        "broadcaster_user_id": self.client._user_id,
                    },
                },
                {
                    "type": "channel.cheer",
                    "version": "1",
                    "condition": {
                        "broadcaster_user_id": self.client._user_id,
                    },
                },
                {
                    "type": "channel.raid",
                    "version": "1",
                    "condition": {
                        "to_broadcaster_user_id": self.client._user_id,
                    },
                },
                {
                    "type": "channel.ban",
                    "version": "1",
                    "condition": {
                        "broadcaster_user_id": self.client._user_id,
                    },
                },
                {
                    "type": "channel.channel_points_custom_reward_redemption.add",
                    "version": "1",
                    "condition": {
                        "broadcaster_user_id": self.client._user_id,
                    },
                },
            ]

            transport = {
                "transport": {
                    "method": "websocket",
                    "session_id": self._session_id,
                }
            }
            for event in events:
                event.update(transport)
                self._http.subscribe_event(self.client._token, event)
        elif data["metadata"]["message_type"] == "notification":
            if event := parse_event(data["payload"], self._http):
                self.client.dispatch(f"on_{event.event_name}", event)

    def ws_disconnected(self):
        self.connect()

    def ws_error(self, code):
        self.client.window.systemTray.showMessage(
            f"WS Error({code}): {self.errorString()}"
        )


class WebSocket(BaseWebSocket):
    URL = "wss://irc-ws.chat.twitch.tv:443"

    def __init__(self, client: Client) -> None:
        super().__init__(client)
        self._token = client._token
        self.nick = None
        self._ready = False

    @property
    def window(self):
        return self.client.window

    def connect(self) -> None:
        response = self._http.validate()
        status_code = response.attribute(
            QNetworkRequest.Attribute.HttpStatusCodeAttribute
        )
        if 200 > status_code < 300:
            raise Exception(
                f"Unable to validate Access Token: {response.errorString()}"
            )
        if status_code == 401:
            raise Exception("Invalid or unauthorized Access Token passed.")
        data = json.loads(response.readAll().data().decode())
        self.nick = data.get("login")
        self.client._user_id = data.get("user_id")
        return super().connect()

    def ping(self) -> None:
        return self.sendTextMessage("PONG :tmi.twitch.tv")

    def ws_connected(self) -> None:
        for mode in ("commands", "tags"):
            self.sendTextMessage(f"CAP REQ :twitch.tv/{mode}")
        self.sendTextMessage(f"PASS oauth:{self._token}\r\n")
        self.sendTextMessage(f"NICK {self.nick}\r\n")
        self.sendTextMessage(f"JOIN #{self.nick}")
        self.window.systemTray.showMessage(f"Logged in as {self.nick}")
        if not self._ready:
            self._ready = True
            self.client._eventsub.connect()
            self.client.window.showMaximized()
            self.window.systemTray.show()
            self.client.dispatch("on_ready")

    def parse_message(self, response: str):
        data = parse_message(response.encode().decode().strip())
        if not (command := data.get("command")):
            return
        if command["command"] == "JOIN":
            self.client.streamer: Streamer = Streamer.from_name(
                command["channel"].lstrip("#"), self._http
            )
            self.sendTextMessage(
                f"PRIVMSG #{self.nick} :Srpbotz has joined the chat\r\n"
            )
            return self.client.dispatch("on_channel_join")
        elif command["command"] == "PART":
            self.sendTextMessage(f"PRIVMSG #{self.nick} :Srpbotz has left the chat\r\n")
            self.client.streamer = None
            return self.client.dispatch("on_channel_leave")
        elif command["command"] == "PRIVMSG":
            streamer = self.client.streamer
            user_id = int(data["tags"]["user-id"])
            if not (author := streamer.get_chatter(user_id)):
                author = Chatter.from_dict(data["tags"], streamer, self._http)
                streamer.chatters[user_id] = author
                self.client.dispatch("on_chatter_join", author)
            message = Message(data["tags"]["id"], author, data["parameters"])
            self.client.dispatch("on_message", message)
            self.client.run_command(data, message) if command.get("botCommand") else ...
        elif command["command"] == "PING":
            return self.ping()

    def ws_disconnected(self):
        if self.window.systemTray.isVisible():
            self.window.systemTray.showMessage("Reconnecting...")
            self.client.dispatch("on_channel_leave")
            self.client.streamer = None
            return self.connect()
        self.window.systemTray.showMessage("Disconnecting...")

    def ws_error(self, code):
        self.window.systemTray.showMessage(f"WS Error({code}): {self.errorString()}")
