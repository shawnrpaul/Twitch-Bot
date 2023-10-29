from __future__ import annotations
from typing import Any, Callable, TYPE_CHECKING
from types import FunctionType
import traceback
import inspect

from .abc import Base
from models.user import User, Chatter

if TYPE_CHECKING:
    from .context import Context


class Command(Base):
    def __init__(self, name: str, func: Callable[..., Any]) -> None:
        super().__init__(name, func)
        self.params = inspect.signature(self.func).parameters.copy()
        for key, value in self.params.items():
            if isinstance(value.annotation, str):
                self.params[key] = value.replace(
                    annotation=eval(value.annotation, func.__globals__)
                )

    def _convert_types(self, ctx: Context, param: inspect.Parameter, arg: str):
        converter = param.annotation
        if converter is param.empty:
            return arg

        if converter is User:
            return (
                User.from_user_id(arg, ctx.client._http)
                if arg.isdigit()
                else User.from_name(arg.lstrip("@").lower(), ctx.client._http)
            )
        if converter is Chatter:
            if not (chatter := ctx.streamer.get_chatter(arg.lstrip("@").lower())):
                raise Exception("Chatter not Found")
            return chatter
        return converter(arg)

    def _parse_args(self, ctx: Context):
        iterator = iter(self.params.values())
        arguments = ctx.args
        ctx.args, ctx.kwargs = [], {}

        try:
            next(iterator)
            next(iterator)
        except StopIteration:
            raise TypeError("self or ctx is a required argument which is missing.")
        for param in iterator:
            if param.kind == param.POSITIONAL_OR_KEYWORD:
                try:
                    argument = arguments.pop(0)
                except (KeyError, IndexError):
                    if param.default is param.empty:
                        raise TypeError(f"Missing argument {param.name}")
                    ctx.args.append(param.default)
                else:
                    ctx.args.append(self._convert_types(ctx, param, argument))
            elif param.kind == param.KEYWORD_ONLY:
                rest = " ".join(arguments)
                rest = rest.strip(" ")
                if rest:
                    rest = self._convert_types(ctx, param, rest)
                elif param.default is param.empty:
                    raise TypeError(f"Missing argument {param.name}")
                else:
                    rest = param.default
                ctx.kwargs[param.name] = rest
                break
            elif param.VAR_POSITIONAL:
                ctx.args.extend(
                    [
                        self._convert_types(ctx.client, param, argument)
                        for argument in arguments
                    ]
                )
                break

    def __call__(self, ctx: Context) -> Any:
        try:
            self._parse_args(ctx)
        except Exception as e:
            return self._send_error_message(ctx, e)
        try:
            return self.func(self._instance, ctx, *ctx.args, **ctx.kwargs)
        except Exception as e:
            self._send_error_message(ctx, e)

    def _send_error_message(self, ctx: Context, error: Exception) -> None:
        if self._error:
            try:
                return self._error(self._instance, ctx, error)
            except Exception as e:
                print(
                    f"Ignoring exception in command {self._error.__name__} - {e.__class__.__name__}"
                )
                traceback.print_exception(type(e), e, e.__traceback__)
        ctx.client.on_command_error(ctx, error)


def command(name: str = None):
    def decorator(func: Callable[..., Any]):
        if not isinstance(func, FunctionType):
            raise TypeError(f"The object isn't a function.")
        if inspect.iscoroutine(func):
            raise TypeError("The function can't be asynchronous.")
        return Command(name, func)

    return decorator
