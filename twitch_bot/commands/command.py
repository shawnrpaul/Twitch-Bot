from __future__ import annotations
from typing import Any, Callable, TYPE_CHECKING
from types import FunctionType
import traceback
import inspect
import asyncio

from .abc import Base
from twitch_bot.models import User, Streamer, UserNotFound

if TYPE_CHECKING:
    from .context import Context
    from .cooldowns import CooldownMapping


class Command(Base):
    __cooldown__: CooldownMapping | None

    def __init__(self, name: str, func: Callable[..., Any]) -> None:
        super().__init__(name, func)
        self.__cooldown__ = getattr(func, "__cooldown__", None)
        self.params = inspect.signature(self.func).parameters.copy()
        for key, value in self.params.items():
            if isinstance(value.annotation, str):
                self.params[key] = value.replace(
                    annotation=eval(value.annotation, func.__globals__)
                )

    def has_cooldown(self) -> bool:
        return bool(self.__cooldown__)

    def _convert_types(self, ctx: Context, param: inspect.Parameter, arg: str):
        converter = param.annotation
        if converter is param.empty:
            return arg

        if converter is User:
            if not (chatter := ctx.streamer.get_chatter(arg.lstrip("@").lower())):
                chatter = (
                    User.from_user_id(arg, ctx.streamer, ctx.client._http)
                    if arg.isdigit()
                    else User.from_name(
                        arg.lstrip("@").lower(), ctx.streamer, ctx.client._http
                    )
                )
                if not chatter:
                    raise UserNotFound(f"User {arg} not Found")
            return chatter
        if converter is Streamer:
            return ctx.streamer
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

    def _run(self, ctx: Context):
        try:
            self._parse_args(ctx)
        except Exception as e:
            return self._send_error_message(ctx, e)
        try:
            if self.has_cooldown():
                self.__cooldown__.update_cooldown(ctx)
            return self.func(self._instance, ctx, *ctx.args, **ctx.kwargs)
        except Exception as e:
            self._send_error_message(ctx, e)

    async def _arun(self, ctx: Context):
        try:
            self._parse_args(ctx)
        except Exception as e:
            return self._send_error_message(ctx, e)
        try:
            if self.has_cooldown():
                self.__cooldown__.update_cooldown(ctx)
            return await self.func(self._instance, ctx, *ctx.args, **ctx.kwargs)
        except Exception as e:
            self._send_error_message(ctx, e)

    def __call__(self, ctx: Context) -> Any:
        if inspect.iscoroutinefunction(self.func):
            asyncio.create_task(self._run(ctx))
        else:
            self._run()

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
        return Command(name, func)

    return decorator
