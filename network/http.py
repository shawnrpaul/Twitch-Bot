from __future__ import annotations
from typing import Any, overload, TYPE_CHECKING
import json

from PyQt6.QtCore import QUrl, QEventLoop
from PyQt6.QtNetwork import QNetworkRequest, QNetworkReply, QNetworkAccessManager

from models import User

if TYPE_CHECKING:
    from .client import Client


class HTTP(QNetworkAccessManager):
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
            raise Exception("Too many users to find")
        url = "https://api.twitch.tv/helix/users?"
        url += "&".join(users_list)
        req = QNetworkRequest(QUrl(url))
        req.setHeader(
            QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json"
        )
        req.setRawHeader(
            "Authorization".encode(), f"Bearer {self.client._token}".encode()
        )
        req.setRawHeader("Client-Id".encode(), self.client._client_id.encode())
        resp = self.get(req)
        if not resp:
            raise Exception("Failed to create request")
        loop = QEventLoop(self)
        resp.finished.connect(lambda: loop.quit())
        loop.exec()
        status_code = resp.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        if status_code == 400:
            raise Exception(
                f"The request exceeded the maximum allowed number of user query parameters."
            )
        if status_code == 401:
            raise Exception("Invalid or unauthorized Access Token passed.")
        return json.loads(resp.readAll().data().decode()).get("data")

    def fetch_mods(self, streamer: int):
        req = QNetworkRequest(
            QUrl(
                f"https://api.twitch.tv/helix/moderation/moderators?broadcaster_id={streamer}"
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
            raise Exception("Failed to create request")
        loop = QEventLoop(self)
        resp.finished.connect(lambda: loop.quit())
        loop.exec()
        status_code = resp.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        if status_code == 400:
            raise Exception(
                f"The request exceeded the maximum allowed number of user query parameters."
            )
        if status_code == 401:
            raise Exception("Invalid or unauthorized Access Token passed.")
        return json.loads(resp.readAll().data().decode()).get("data")

    def fetch_user_color(self, id: int):
        req = QNetworkRequest(
            QUrl(f"https://api.twitch.tv/helix/chat/color?user_id={id}")
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
            raise Exception("Failed to create request")
        loop = QEventLoop(self)
        resp.finished.connect(lambda: loop.quit())
        loop.exec()
        status_code = resp.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        if status_code == 400:
            raise Exception(
                f"The request exceeded the maximum allowed number of user query parameters."
            )
        if status_code == 401:
            raise Exception("Invalid or unauthorized Access Token passed.")
        return (
            json.loads(resp.readAll().data().decode()).get("data")[0].get("color", "")
        )

    def ban_user(
        self, streamer: int, user: int, moderator: User, reason: str, duration: int = 0
    ):
        if not moderator:
            moderator = self.client.streamer
        req = QNetworkRequest(
            QUrl(
                f"https://api.twitch.tv/helix/moderation/bans?broadcaster_id={streamer}&moderator_id={moderator.id}"
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
            raise Exception(f"Unable to ban the user.")
        if status_code == 401:
            raise Exception("You are not authorized to ban the user.")
        if status_code == 403:
            raise Exception(f"The given moderator isn't a moderator.")
        if status_code == 409:
            raise Exception(f"Someone else is modifying the user")
        if status_code == 423:
            raise Exception(f"You have made too many requests in the given channel")

    def create_prediction(
        self, broadcaster_id: int, title: str, options: list[str], length: int = 120
    ) -> None:
        if len(options) < 2:
            raise TypeError("Options is empty")
        req = QNetworkRequest(QUrl(f"https://api.twitch.tv/helix/predictions"))
        req.setHeader(
            QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json"
        )
        req.setRawHeader(
            "Authorization".encode(), f"Bearer {self.client._token}".encode()
        )
        req.setRawHeader("Client-Id".encode(), self.client._client_id.encode())
        data = {
            "broadcaster_id": broadcaster_id,
            "title": title,
            "options": [],
            "prediction_window": length,
        }
        for option in options:
            data["options"].append({"title": option})
        resp = self.post(req, json.dumps(data).encode())
        status_code = resp.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        if status_code == 400:
            raise Exception("Bad Request")
        if status_code == 401:
            raise Exception("You are not authorized to create a prediction.")
        if status_code == 429:
            raise Exception("You have been rate-limited.")
        print(resp.readAll().data())

    def subscribe_event(self, token: str, data: dict[str, Any]):
        req = QNetworkRequest(
            QUrl("https://api.twitch.tv/helix/eventsub/subscriptions")
        )
        req.setHeader(
            QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json"
        )
        req.setRawHeader("Authorization".encode(), f"Bearer {token}".encode())
        req.setRawHeader("Client-Id".encode(), self.client._client_id.encode())
        resp = self.post(req, json.dumps(data).encode())
        status_code = resp.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        if status_code == 400:
            raise Exception("Bad Request")
        if status_code == 401:
            raise Exception("You are not authorized to subscribe to this event.")
        if status_code == 403:
            raise Exception("Your access token is missing the required scope.")
        if status_code == 409:
            raise Exception("You're already subscribed to this event.")
        if status_code == 429:
            raise Exception("You have been rate-limited.")

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
            raise Exception("Failed to create request")
        loop = QEventLoop(self)
        resp.finished.connect(lambda: loop.quit())
        loop.exec()
        return resp
