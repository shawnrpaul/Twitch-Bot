from __future__ import annotations
from typing import Any, TYPE_CHECKING

from .user import User

if TYPE_CHECKING:
    from .streamer import Streamer
    from network import HTTP


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
