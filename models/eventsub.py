from __future__ import annotations
from typing import TYPE_CHECKING

from .user import User

from dateutil.parser import parse

if TYPE_CHECKING:
    from network import HTTP


class BaseEvent:
    def __init__(self, payload: dict[str, str], http: HTTP) -> None:
        self.event_name = "base_event"
        self.chatter = http.client.streamer.get_chatter(int(payload["user_id"]))
        if not self.chatter:
            self.chatter = User.from_user_id(payload["user_id"], http)


class FollowEvent(BaseEvent):
    def __init__(self, payload: dict[str, str], http: HTTP) -> None:
        super().__init__(payload, http)
        self.event_name = "follow_event"


class SubscribeEvent(BaseEvent):
    def __init__(self, payload: dict[str, str], http: HTTP) -> None:
        super().__init__(payload, http)
        self.event_name = "subscribe_event"
        self.tier = payload["tier"]
        self.is_gift = payload["is_gift"]


class GiftSubEvent(SubscribeEvent):
    def __init__(self, payload: dict[str, str], http: HTTP) -> None:
        super().__init__(payload, http)
        self.event_name = "gift_sub_event"
        self.total = payload["total"]


class ReSubscribeEvent(SubscribeEvent):
    def __init__(self, payload: dict[str, str], http: HTTP) -> None:
        super().__init__(payload, http)
        self.event_name = "resub_event"
        self.message = payload["message"]["text"]
        self.consecutive_months = payload["cumulative_months"]
        self.streak_months = payload["streak_months"]
        self.duration_months = payload["duration_months"]


class CheersEvent(BaseEvent):
    def __init__(self, payload: dict[str, str], http: HTTP) -> None:
        super().__init__(payload, http)
        self.event_name = "cheers_event"
        self.message = payload["message"]
        self.bits = int(payload["bits"])


class RaidEvent(BaseEvent):
    def __init__(self, payload: dict[str, str], http: HTTP) -> None:
        payload["broadcaster_user_id"] = payload.pop("to_broadcaster_user_id")
        payload["user_id"] = payload.pop("from_broadcaster_user_id")
        super().__init__(payload, http)
        self.event_name = "raid_event"
        self.viewers = int(payload["viewers"])


class BanEvent(BaseEvent):
    def __init__(self, payload: dict[str, str], http: HTTP) -> None:
        super().__init__(payload, http)
        self.event_name = "ban_event"
        id = int(payload["moderator_user_id"])
        self.moderator = http.client.streamer.chatters.get(id)
        if not self.moderator:
            self.moderator = User.from_user_id(id, http)
        self.reason = payload["reason"]
        self.timeout = (
            (parse(payload["ends_at"]) - parse(payload["banned_at"])).seconds
            if not payload["is_permanent"]
            else 0
        )


class RewardEvent(BaseEvent):
    class Reward:
        def __init__(self, id: str, title: str, cost: int, prompt: str = None) -> None:
            self.id = id
            self.title = title
            self.cost = int(cost)
            self.prompt = prompt

    def __init__(self, payload: dict[str, str], http: HTTP) -> None:
        super().__init__(payload, http)
        self.event_name = "reward_event"
        self.reward = self.Reward(**payload["reward"])
