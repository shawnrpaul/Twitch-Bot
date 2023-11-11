from __future__ import annotations
from typing import TYPE_CHECKING
from functools import singledispatchmethod

from .user import User

if TYPE_CHECKING:
    from .message import Message
    from network import HTTP


class Streamer(User):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs, streamer=self)
        self._messages: dict[str, Message] = {}
        self._chatters: dict[int, User] = {self.id: self}
        self._mods = [int(mod["user_id"]) for mod in self._http.fetch_mods()]

    def __repr__(self) -> str:
        return (
            f'<Streamer id={self.id} name={self.name} display_name={self.display_name} description="{self.description}" '
            f"color={self.color} created_at={self.created_at}>"
        )

    @property
    def mods(self) -> list[User]:
        mods = []
        fetch_users = []
        for mod in self._mods:
            if user := self._chatters.get(mod):
                mods.append(user)
            else:
                fetch_users.append(mod)
        if fetch_users:
            for data in self._http.fetch_users(fetch_users):
                mods.append(User(**data, streamer=self, http=self._http))
        return mods

    @property
    def is_mod(self) -> bool:
        return True

    def append_message(self, message: Message):
        self._messages[message.id] = message

    def pop_message(self, id: str):
        return self._messages.pop(id, None)

    @classmethod
    def from_user_id(cls, user_id: str, http: HTTP) -> Streamer:
        data = http.fetch_users(int(user_id))[0]
        return cls(**data, http=http)

    @classmethod
    def from_name(cls, name: str, http: HTTP) -> Streamer:
        data = http.fetch_users(name)[0]
        return cls(**data, http=http)

    @singledispatchmethod
    def get_chatter(self, id: int) -> User | None:
        return self._chatters.get(id)

    @get_chatter.register
    def _(self, name: str) -> User | None:
        for chatter in self._chatters.values():
            if name in (chatter.display_name, chatter.name):
                return chatter
        return None

    def add_chatter(self, chatter: User):
        self._chatters[chatter.id] = chatter

    def remove_chatter(self, chatter: User):
        self._chatters.pop(chatter.id, None)

    def ban_user(self, user: User, moderator: User = None, reason: str = None):
        if not isinstance(user, User):
            raise TypeError("A User object is required")
        if isinstance(reason, str) and len(reason) > 500:
            raise TypeError("Reason must a be a max of 500 characters")
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
            raise TypeError("Reason must a be a max of 500 characters")
        self._http.ban_user(user.id, moderator, reason, duration)
