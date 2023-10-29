from __future__ import annotations
from typing import Any, Callable
from types import FunctionType
import traceback
import inspect

from .abc import Base


class Event(Base):
    def __init__(self, event: str, func: Callable[..., Any]) -> None:
        super().__init__(event, func)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        try:
            self.func(self._instance, *args, **kwargs)
        except Exception as e:
            self._send_error_message(e)

    def _send_error_message(self, error: Exception) -> None:
        if self._error:
            try:
                return self._error(self._instance, error)
            except Exception as e:
                print(
                    f"Ignoring exception in command {self._error.__name__} - {e.__class__.__name__}: {e}"
                )
                traceback.print_exception(type(e), e, e.__traceback__)
        self._instance.client.on_event_error(self, error)


def event(event: str = None):
    def decorator(func: Callable[..., Any]):
        if not isinstance(func, FunctionType):
            raise TypeError(f"The object isn't a function.")
        if inspect.iscoroutine(func):
            raise TypeError("The function can't be asynchronous.")
        return Event(event, func)

    return decorator
