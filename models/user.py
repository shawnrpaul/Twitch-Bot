from __future__ import annotations
from typing import TYPE_CHECKING
import datetime

from dateutil.parser import parser

if TYPE_CHECKING:
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
