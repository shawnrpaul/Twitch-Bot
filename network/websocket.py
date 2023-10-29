from __future__ import annotations
from typing import TYPE_CHECKING
from abc import abstractmethod
import json

from PyQt6.QtCore import QUrl
from PyQt6.QtWebSockets import QWebSocket, QWebSocketProtocol

from models import Streamer, Chatter, Message, BanEvent, StreamOffline
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
                    "type": "stream.online",
                    "version": "1",
                    "condition": {"broadcaster_user_id": self.client._user_id},
                },
                {
                    "type": "stream.offline",
                    "version": "1",
                    "condition": {"broadcaster_user_id": self.client._user_id},
                },
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
                if isinstance(event, BanEvent):
                    self.client.streamer.remove_chatter(event.chatter)
                elif isinstance(event, StreamOffline):
                    self.client.on_stream_offline()
                return self.client.dispatch(f"on_{event.event_name}", event)

    def ws_connected(self):
        self.client.dispatch("on_es_connect")

    def ws_disconnected(self):
        self.client.dispatch("on_es_disconnect")
        self.connect()

    def ws_error(self, code):
        self.client.window.log(f"Eventsub WS Error({code}): {self.errorString()}")


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
        data = self._http.validate()
        self.nick = data.get("login")
        self.client._user_id = data.get("user_id")
        return super().connect()

    def ping(self) -> None:
        return self.sendTextMessage("PONG :tmi.twitch.tv")

    def close(self, *args, **kwargs) -> None:
        self.client.send_message(f"Srpbotz has left the chat")
        return super().close(*args, **kwargs)

    def ws_connected(self) -> None:
        for mode in ("commands", "tags"):
            self.sendTextMessage(f"CAP REQ :twitch.tv/{mode}")
        self.sendTextMessage(f"PASS oauth:{self._token}\r\n")
        self.sendTextMessage(f"NICK {self.nick}\r\n")
        self.sendTextMessage(f"JOIN #{self.nick}")
        self.window.systemTray.showMessage(f"Logged in as {self.nick}")
        self.client.dispatch("on_ws_connect")
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
            self.client.send_message("Srpbotz has joined the chat")
            return self.client.dispatch("on_channel_join")
        elif command["command"] == "PART":
            self.client.send_message(f"Srpbotz has left the chat")
            self.client.streamer = None
            return self.client.dispatch("on_channel_leave")
        elif command["command"] == "PRIVMSG":
            streamer = self.client.streamer
            user_id = int(data["tags"]["user-id"])
            if not (author := streamer.get_chatter(user_id)):
                author = Chatter.from_dict(data["tags"], streamer, self._http)
                streamer.add_chatter(author)
                self.client.dispatch("on_chatter_join", author)
            message = Message(
                data["tags"]["id"], self.client, author, data["parameters"]
            )
            self.client.streamer.append_message(message)
            self.client.dispatch("on_message", message)
            self.client.run_command(data, message) if command.get("botCommand") else ...
        elif command["command"] == "CLEARMSG":
            return self.client.dispatch(
                "on_message_delete",
                self.client.streamer.pop_message(data["tags"]["target-msg-id"]),
            )
        elif command["command"] == "PING":
            return self.ping()

    def ws_disconnected(self):
        if self.window.systemTray.isVisible():
            self.window.systemTray.showMessage("Reconnecting...")
            self.client.streamer = None
            return self.connect()
        self.client.dispatch("on_ws_disconnect")

    def ws_error(self, code):
        self.window.systemTray.showMessage(f"WS Error({code}): {self.errorString()}")
