from __future__ import annotations
from typing import TYPE_CHECKING
from functools import singledispatchmethod

from .chatter import Chatter

if TYPE_CHECKING:
    from .user import User
    from .message import Message
    from network import HTTP


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
