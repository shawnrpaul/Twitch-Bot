from __future__ import annotations
from typing import Any, Callable, TYPE_CHECKING
from abc import abstractmethod
import inspect

if TYPE_CHECKING:
    from .cog import Cog


class Base:
    def __init__(self, name: str, func: Callable[..., Any]) -> None:
        self.name = name if name else func.__name__
        self._instance: Cog = None
        self.func = func
        self._error = None

    @abstractmethod
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        ...

    def has_error_handler(self):
        return bool(self._error)

    def error(self, func: Callable[..., Any]):
        if inspect.iscoroutine(func):
            raise TypeError("The function can't be asynchronous.")
        self._error = func
        return func
