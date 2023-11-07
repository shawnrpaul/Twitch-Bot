from __future__ import annotations
from typing import Any, Callable, TYPE_CHECKING
from enum import IntEnum
import time

from .exceptions import CommandOnCooldown

if TYPE_CHECKING:
    from .context import Context


class BucketType(IntEnum):
    Global = 0
    User = 1


class Cooldown:
    def __init__(self, rate: int, cooldown: float) -> None:
        self.rate = int(rate)
        self.cooldown = float(cooldown)
        self._current = 0
        self._last = time.time()

    def update_cooldown(self):
        now = time.time()
        if self._current < self.rate:
            self._current += 1
            self._last = now
        elif now >= self._last + self.cooldown:
            self._current = 0
            self._last = now
        else:
            raise CommandOnCooldown(self._last + self.cooldown - now)


class CooldownMapping:
    def __init__(self, rate: int, cooldown: float, type: BucketType) -> None:
        self.rate = int(rate)
        self.cooldown = float(cooldown)
        self._type = type
        self._cache: dict[int, Cooldown] = {}
        if type == BucketType.Global:
            self._cache[0] = Cooldown(rate, cooldown)

    def update_cooldown(self, ctx: Context):
        match self._type:
            case BucketType.Global:
                cooldown = self._cache[0]
            case BucketType.User:
                if not (cooldown := self._cache.get(ctx.author.id)):
                    cooldown = Cooldown(self.rate, self.cooldown)
                    self._cache[ctx.author.id] = cooldown
        cooldown.update_cooldown()


def cooldown(rate: int, cooldown: float, type: BucketType = BucketType.Global):
    def decorator(func: Callable[..., Any]):
        if not isinstance(type, BucketType):
            raise TypeError("Variable type must be a BucketType")
        func.__cooldown__ = CooldownMapping(rate, cooldown, type)
        return func

    return decorator
