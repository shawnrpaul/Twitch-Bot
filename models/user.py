from __future__ import annotations
from functools import singledispatchmethod
from typing import Any, TYPE_CHECKING
import datetime

from dateutil.parser import parser

if TYPE_CHECKING:
    from .message import Message
    from network import HTTP


class User:
    __slots__ = (
        "id",
        "login",
        "display_name",
        "color",
        "type",
        "broadcaster_type",
        "description",
        "profile_image_url",
        "offline_image_url",
        "created_at",
        "_http",
    )

    def __init__(
        self,
        id: str,
        login: str,
        display_name: str,
        type: str,
        broadcaster_type: str,
        description: str,
        profile_image_url: str,
        offline_image_url: str,
        created_at: str | datetime.datetime,
        http: HTTP,
        **_,
    ) -> None:
        self.id = int(id)
        self.login = login
        self.display_name = display_name
        self.color = color if (color := http.fetch_user_color(self.id)) else "#FFFFFF"
        self.type = type
        self.broadcaster_type = broadcaster_type
        self.description = description
        self.profile_image_url = profile_image_url
        self.offline_image_url = offline_image_url
        self.created_at = (
            parser().parse(created_at) if isinstance(created_at, str) else created_at
        )
        self._http = http

    @property
    def name(self):
        return self.login

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return False
        return self.id == other.id

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, User):
            return True
        return self.id != other.id

    def __repr__(self) -> str:
        return (
            f"<User id={self.id} name={self.name} display_name={self.display_name} color={self.color} "
            f'description="{self.description}" created_at={self.created_at}>'
        )

    def __eq__(self, obj: object) -> bool:
        if not isinstance(obj, User):
            return False
        return self.id == obj.id

    @classmethod
    def from_user_id(cls, user_id: str, http: HTTP) -> User:
        data = http.fetch_users(int(user_id))[0]
        return cls(**data, http=http)

    @classmethod
    def from_name(cls, name: str, http: HTTP):
        data = http.fetch_users(name)[0]
        return cls(**data, http=http)


class Chatter(User):
    __slots__ = ("streamer", "mod", "subscriber", "turbo", "color")

    def __init__(
        self,
        streamer: Streamer,
        mod: int,
        subscriber: str,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.mod = bool(mod)
        self.streamer = streamer
        self.subscriber = subscriber

    def __repr__(self) -> str:
        return (
            f'<Chatter id={self.id} name={self.name} display_name={self.display_name} description="{self.description}" '
            f"mod={self.mod} subscriber={self.subscriber} created_at={self.created_at}>"
        )

    @property
    def is_mod(self) -> bool:
        return self.mod

    @classmethod
    def from_dict(cls, data: dict[str, Any], streamer: Streamer, http: HTTP):
        user_data = http.fetch_users(int(data["user-id"]))[0]
        chatter_data = {}
        for key in cls.__slots__[1:]:
            chatter_data[key] = data.get(key)
        return cls(streamer, **chatter_data, **user_data, http=http)


class Streamer(Chatter):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(self, *args, **kwargs)
        self.chatters: dict[int, User] = {self.id: self}
        self.messages: dict[str, Message] = {}

    def __repr__(self) -> str:
        return (
            f'<Streamer id={self.id} name={self.name} display_name={self.display_name} description="{self.description}" '
            f"mod={self.mod} subscriber={self.subscriber} created_at={self.created_at}>"
        )

    @property
    def mods(self) -> list[Chatter | User]:
        return [
            chatter
            if (chatter := self.get_chatter(mod["user_id"]))
            else User.from_user_id(mod["user_id"], self._http)
            for mod in self._http.fetch_mods()
        ]

    def append_message(self, message: Message):
        self.messages[message.id] = message

    def pop_message(self, id: str):
        return self.messages.pop(id, None)

    @classmethod
    def from_user_id(cls, user_id: str, http: HTTP) -> Streamer:
        data = http.fetch_users(int(user_id))[0]
        return cls(mod=True, subscriber=True, **data, http=http)

    @classmethod
    def from_name(cls, name: str, http: HTTP) -> Streamer:
        data = http.fetch_users(name)[0]
        return cls(mod=True, subscriber=True, http=http, **data)

    @singledispatchmethod
    def get_chatter(self, id: int) -> User | None:
        return self.chatters.get(id)

    @get_chatter.register
    def _(self, name: str) -> Chatter | None:
        for chatter in self.chatters.values():
            if name in (chatter.display_name, chatter.name):
                return chatter
        return None

    def add_chatter(self, chatter: Chatter):
        self.chatters[chatter.id] = chatter

    def remove_chatter(self, chatter: Chatter):
        self.chatters.pop(chatter.id, None)

    def ban_user(self, user: User, moderator: User = None, reason: str = None):
        if not isinstance(user, User):
            raise TypeError("A User object is required")
        if isinstance(reason, str) and len(reason) > 500:
            raise Exception("Reason must a be a max of 500 characters")
        self._http.ban_user(user.id, moderator, reason)

    def timeout_user(
        self,
        user: User,
        *,
        moderator: User = None,
        reason: str = None,
        duration: int = 0,
    ):
        if not isinstance(user, User):
            raise TypeError("A User object is required")
        if isinstance(reason, str) and len(reason) > 500:
            raise Exception("Reason must a be a max of 500 characters")
        self._http.ban_user(user.id, moderator, reason, duration)
