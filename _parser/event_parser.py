from __future__ import annotations
from typing import Any, TYPE_CHECKING

from models.eventsub import (
    StreamOnline,
    StreamOffline,
    FollowEvent,
    RewardEvent,
    SubscribeEvent,
    GiftSubEvent,
    ReSubscribeEvent,
    RaidEvent,
    CheersEvent,
    BanEvent,
)

if TYPE_CHECKING:
    from network import HTTP
    from models.eventsub import BaseEvent


TYPES: dict[str, BaseEvent] = {
    "stream.online": StreamOnline,
    "stream.offline": StreamOffline,
    "channel.follow": FollowEvent,
    "channel.subscribe": SubscribeEvent,
    "channel.subscription.gift": GiftSubEvent,
    "channel.subscription.message": ReSubscribeEvent,
    "channel.cheer": CheersEvent,
    "channel.raid": RaidEvent,
    "channel.ban": BanEvent,
    "channel.channel_points_custom_reward_redemption.add": RewardEvent,
}


def parse_event(payload: dict[str, Any], http: HTTP) -> BaseEvent | None:
    if cls := TYPES.get(payload["subscription"]["type"]):
        return cls(payload["event"], http)
