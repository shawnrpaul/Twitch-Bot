from __future__ import annotations
from typing import Any, overload, TYPE_CHECKING
import json

from PyQt6.QtCore import QUrl, QEventLoop
from PyQt6.QtNetwork import QNetworkRequest, QNetworkReply, QNetworkAccessManager
from .exceptions import HTTPError, RequestError

if TYPE_CHECKING:
    from twitch_bot.models import Message, User
    from .client import Client


class HTTP(QNetworkAccessManager):
    URL = "https://api.twitch.tv/helix"

    def __init__(self, client: Client) -> None:
        super().__init__(client)
        self.client = client

    @property
    def window(self):
        return self.client.window

    @overload
    def fetch_users(self, id: int) -> dict:
        ...

    @overload
    def fetch_users(self, ids: list[int]) -> dict:
        ...

    @overload
    def fetch_users(self, name: str) -> dict:
        ...

    @overload
    def fetch_users(self, names: list[str]) -> dict:
        ...

    def fetch_users(self, users) -> User:
        users_list = []
        if isinstance(users, list):
            if isinstance(users[0], int):
                for id in users:
                    users_list.append(f"id={id}")
            elif isinstance(users[0], str):
                for name in users:
                    users_list.append(f"login={name}")
        elif isinstance(users, int):
            users_list.append(f"id={users}")
        elif isinstance(users, str):
            users_list.append(f"login={users}")
        else:
            raise TypeError("You need to give names or ids")
        if len(users_list) > 100:
            raise TypeError("Too many users to find")
        req = QNetworkRequest(QUrl(f"{self.URL}/users?{'&'.join(users_list)}"))
        req.setHeader(
            QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json"
        )
        req.setRawHeader(
            "Authorization".encode(), f"Bearer {self.client._token}".encode()
        )
        req.setRawHeader("Client-Id".encode(), self.client._client_id.encode())
        resp = self.get(req)
        if not resp:
            raise RequestError
        loop = QEventLoop(self)
        resp.finished.connect(lambda: loop.quit())
        loop.exec()
        status_code = resp.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        if status_code == 400:
            raise HTTPError(
                status_code,
                "The request exceeded the maximum allowed number of user query parameters.",
            )
        if status_code == 401:
            raise HTTPError(status_code, "Invalid or unauthorized Access Token passed.")
        return json.loads(resp.readAll().data().decode()).get("data")

    def fetch_mods(self):
        req = QNetworkRequest(
            QUrl(
                f"{self.URL}/moderation/moderators?broadcaster_id={self.client._user_id}"
            )
        )
        req.setHeader(
            QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json"
        )
        req.setRawHeader(
            "Authorization".encode(), f"Bearer {self.client._token}".encode()
        )
        req.setRawHeader("Client-Id".encode(), self.client._client_id.encode())
        resp = self.get(req)
        if not resp:
            raise RequestError
        loop = QEventLoop(self)
        resp.finished.connect(lambda: loop.quit())
        loop.exec()
        status_code = resp.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        if status_code == 400:
            raise HTTPError(
                status_code,
                "The request exceeded the maximum allowed number of user query parameters.",
            )
        if status_code == 401:
            raise HTTPError(status_code, "Invalid or unauthorized Access Token passed.")
        return json.loads(resp.readAll().data().decode()).get("data")

    def fetch_user_color(self, id: int):
        req = QNetworkRequest(QUrl(f"{self.URL}/chat/color?user_id={id}"))
        req.setHeader(
            QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json"
        )
        req.setRawHeader(
            "Authorization".encode(), f"Bearer {self.client._token}".encode()
        )
        req.setRawHeader("Client-Id".encode(), self.client._client_id.encode())
        resp = self.get(req)
        if not resp:
            raise RequestError
        loop = QEventLoop(self)
        resp.finished.connect(lambda: loop.quit())
        loop.exec()
        status_code = resp.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        if status_code == 400:
            raise HTTPError(
                status_code,
                "The request exceeded the maximum allowed number of user query parameters.",
            )
        if status_code == 401:
            raise HTTPError(status_code, "Invalid or unauthorized Access Token passed.")
        return (
            json.loads(resp.readAll().data().decode()).get("data")[0].get("color", "")
        )

    def ban_user(self, user: int, moderator: User, reason: str, duration: int = 0):
        if not moderator:
            moderator = self.client.streamer
        req = QNetworkRequest(
            QUrl(
                f"{self.URL}/moderation/bans?broadcaster_id={self.client._user_id}&moderator_id={moderator.id}"
            )
        )
        req.setHeader(
            QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json"
        )
        req.setRawHeader(
            "Authorization".encode(), f"Bearer {self.client._token}".encode()
        )
        req.setRawHeader("Client-Id".encode(), self.client._client_id.encode())
        data = {"data": {"user_id": str(user), "reason": reason}}
        if 1 < duration < 1_209_600:
            data["data"]["duration"] = duration
        resp = self.post(req, json.dumps(data).encode())
        status_code = resp.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        if status_code == 400:
            raise HTTPError(status_code, "Unable to ban the user.")
        if status_code == 401:
            raise HTTPError(status_code, "You are not authorized to ban the user.")
        if status_code == 403:
            raise HTTPError(status_code, "The given moderator isn't a moderator.")
        if status_code == 409:
            raise HTTPError(status_code, "Someone else is modifying the user")
        if status_code == 423:
            raise HTTPError(
                status_code, "You have made too many requests in the given channel"
            )

    def delete_message(self, message: Message, moderator: User = None):
        if not moderator:
            moderator = self.client.streamer
        req = QNetworkRequest(
            QUrl(
                f"{self.URL}/moderation/chat?broadcaster_id={self.client._user_id}&moderator_id={moderator.id}&message_id={message.id}"
            )
        )
        req.setHeader(
            QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json"
        )
        req.setRawHeader(
            "Authorization".encode(), f"Bearer {self.client._token}".encode()
        )
        req.setRawHeader("Client-Id".encode(), self.client._client_id.encode())
        resp = self.deleteResource(req)
        status_code = resp.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        if status_code == 400:
            raise HTTPError(status_code, "Unable to delete message.")
        if status_code == 401:
            raise HTTPError(
                status_code, "You are not authorized to delete the message."
            )
        if status_code == 403:
            raise HTTPError(status_code, "The given moderator isn't a moderator.")
        if status_code == 404:
            raise HTTPError(
                status_code, "Message not found or was created more than 6 hrs ago"
            )

    def create_prediction(
        self, title: str, options: list[str], length: int = 120
    ) -> None:
        if len(options) < 2:
            raise TypeError("Options is empty")
        req = QNetworkRequest(QUrl(f"{self.URL}/predictions"))
        req.setHeader(
            QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json"
        )
        req.setRawHeader(
            "Authorization".encode(), f"Bearer {self.client._token}".encode()
        )
        req.setRawHeader("Client-Id".encode(), self.client._client_id.encode())
        data = {
            "broadcaster_id": self.client._user_id,
            "title": title,
            "options": [],
            "prediction_window": length,
        }
        for option in options:
            data["options"].append({"title": option})
        resp = self.post(req, json.dumps(data).encode())
        status_code = resp.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        if status_code == 400:
            raise HTTPError(status_code, "Bad Request")
        if status_code == 401:
            raise HTTPError(
                status_code, "You are not authorized to create a prediction."
            )
        if status_code == 429:
            raise HTTPError(status_code, "You have been rate-limited.")
        print(resp.readAll().data())

    def subscribe_event(self, token: str, data: dict[str, Any]):
        req = QNetworkRequest(QUrl(f"{self.URL}/eventsub/subscriptions"))
        req.setHeader(
            QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json"
        )
        req.setRawHeader("Authorization".encode(), f"Bearer {token}".encode())
        req.setRawHeader("Client-Id".encode(), self.client._client_id.encode())
        resp = self.post(req, json.dumps(data).encode())
        status_code = resp.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        if status_code == 400:
            raise HTTPError(status_code, "Bad Request")
        if status_code == 401:
            raise HTTPError(
                status_code, "You are not authorized to subscribe to this event."
            )
        if status_code == 403:
            raise HTTPError(
                status_code, "Your access token is missing the required scope."
            )
        if status_code == 409:
            raise HTTPError(status_code, "You're already subscribed to this event.")
        if status_code == 429:
            raise HTTPError(status_code, "You have been rate-limited.")

    def validate(self) -> QNetworkReply:
        req = QNetworkRequest(QUrl("https://id.twitch.tv/oauth2/validate"))
        req.setHeader(
            QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json"
        )
        req.setRawHeader(
            "Authorization".encode(), f"OAuth {self.client._token}".encode()
        )
        resp = self.get(req)
        if not resp:
            raise RequestError
        loop = QEventLoop(self)
        resp.finished.connect(lambda: loop.quit())
        loop.exec()
        status_code = resp.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        if 200 > status_code < 300:
            raise HTTPError(
                status_code, "Unable to validate Access Token: {resp.errorString()}"
            )
        if status_code == 401:
            raise HTTPError(status_code, "Invalid or unauthorized Access Token passed.")
        return json.loads(resp.readAll().data().decode())
