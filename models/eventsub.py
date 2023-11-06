from __future__ import annotations
from typing import TYPE_CHECKING

from .user import User

from dateutil.parser import parse

if TYPE_CHECKING:
    from network import HTTP


class BaseEvent:
    def __init__(self, event_name: str) -> None:
        self.event_name = event_name


class _Event(BaseEvent):
    def __init__(self, event_name: str, payload: dict[str, str], http: HTTP) -> None:
        super().__init__(event_name)
        streamer = http.client.streamer
        self.chatter = streamer.get_chatter(int(payload["user_id"]))
        if not self.chatter:
            self.chatter = User.from_user_id(payload["user_id"], streamer, http)
            streamer.add_chatter(self.chatter)
            http.client.dispatch("on_chatter_join", self.chatter)


class StreamOnline(BaseEvent):
    def __init__(self, payload: dict[str, str], _) -> None:
        super().__init__("on_stream_online")
        self.type = payload["type"]


class StreamOffline(BaseEvent):
    def __init__(self, _, __) -> None:
        super().__init__("on_stream_offline")


class FollowEvent(_Event):
    def __init__(self, payload: dict[str, str], http: HTTP) -> None:
        super().__init__("follow_event", payload, http)


class BanEvent(_Event):
    def __init__(self, payload: dict[str, str], http: HTTP) -> None:
        super().__init__("ban_event", payload, http)
        id = int(payload["moderator_user_id"])
        self.moderator = http.client.streamer.get_chatter(id)
        if not self.moderator:
            self.moderator = User.from_user_id(id, http.client.streamer, http)
        self.reason = payload["reason"]
        self.timeout = (
            (parse(payload["ends_at"]) - parse(payload["banned_at"])).seconds
            if not payload["is_permanent"]
            else 0
        )


class RaidEvent(_Event):
    def __init__(self, payload: dict[str, str], http: HTTP) -> None:
        payload["broadcaster_user_id"] = payload.pop("to_broadcaster_user_id")
        payload["user_id"] = payload.pop("from_broadcaster_user_id")
        super().__init__("raid_event", payload, http)
        self.viewers = int(payload["viewers"])


class SubscribeEvent(_Event):
    def __init__(self, payload: dict[str, str], http: HTTP) -> None:
        super().__init__("subscribe_event", payload, http)
        self.tier = payload["tier"]
        self.is_gift = payload.get("is_gift", False)


class GiftSubEvent(SubscribeEvent):
    def __init__(self, payload: dict[str, str], http: HTTP) -> None:
        super().__init__(payload, http)
        self.event_name = "gift_sub_event"
        self.total = payload["total"]
        self.cummulative_total = (
            payload["cumulative_total"] if not payload["is_anonymous"] else 0
        )
        self.is_gift = True


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
        super().__init__("cheers_event")
        if not payload["is_anonymous"]:
            streamer = http.client.streamer
            self.chatter = streamer.get_chatter(int(payload["user_id"]))
            if not self.chatter:
                self.chatter = User.from_user_id(payload["user_id"], streamer, http)
                streamer.add_chatter(self.chatter)
                http.client.dispatch("on_chatter_join", self.chatter)
        else:
            self.chatter = None
        self.message = payload["message"]
        self.bits = int(payload["bits"])


class RewardEvent(_Event):
    class Reward:
        def __init__(
            self,
            id: str,
            reward_id: str,
            title: str,
            prompt: str,
            cost: int,
            user_input: str,
        ) -> None:
            self.id = id
            self.reward_id = reward_id
            self.title = title
            self.prompt = prompt
            self.cost = int(cost)
            self.user_input = user_input

    def __init__(self, payload: dict[str, str], http: HTTP) -> None:
        super().__init__("reward_event", payload, http)
        self.reward = self.Reward(
            **payload["reward"],
            reward_id=payload["id"],
            user_input=payload["user_input"],
        )
