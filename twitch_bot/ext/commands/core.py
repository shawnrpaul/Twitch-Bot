from __future__ import annotations
from typing import Any, Callable, Sequence, TypeVar

from twitchio.ext import commands

__all__ = ("Command", "command")


class Command(commands.Command):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def has_error_handler(self) -> bool:
        return bool(self.event_error)

    def error(self, func: Callable[..., Any]) -> Callable[..., Any]:
        self.event_error = func
        return func


C = TypeVar("C", bound="Command")


def command(
    *,
    name: str = None,
    aliases: Sequence = None,
    cls: type[C] = Command,
    no_global_checks=False,
) -> C:
    return commands.command(
        name=name, aliases=aliases, cls=cls, no_global_checks=no_global_checks
    )
