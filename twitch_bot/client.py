from typing import Coroutine
import traceback
import importlib
import asyncio
import inspect
import json
import sys
import os
import re

from PyQt6.QtWidgets import QApplication
from twitch_bot import MainWindow, Message, Channel
from twitch_bot.ext import commands, eventsub, routines

__all__ = ("Client",)

sys.path.append(os.path.join(sys.path[0], "site-packages"))


class Client(commands.Bot):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._es = eventsub.EventSubWSClient(self)
        self._token: str = kwargs.get("token") or args[0]
        self._messages: dict[str, Message] = {}
        self.routines: dict[str, tuple[routines.Routine]] = {}
        self.application = QApplication([])
        self.window = MainWindow(self)
        self.streamer = None
        self._tasks: list[asyncio.Task] = []

    @staticmethod
    def load_settings() -> None:
        with open("data/settings.json") as f:
            return json.load(f)

    def create_task(self, coro: Coroutine) -> asyncio.Task:
        if not inspect.iscoroutine(coro):
            raise TypeError("The function must be a coroutine")
        task = self.loop.create_task(coro)
        task.add_done_callback(self._tasks.remove)
        self._tasks.append(task)
        return task

    def add_cogs(self) -> None:
        for path in os.listdir("cogs"):
            if os.path.isfile(f"cogs/{path}"):
                if not path.endswith(".py"):
                    continue
            else:
                if "__init__.py" not in os.listdir(f"cogs/{path}"):
                    continue
            path = path.replace(".py", "")
            try:
                mod = importlib.import_module(f"cogs.{path}")
                mod.setup(self.window.client)
            except Exception as e:
                print(f"Unable to load cog: {path.capitalize()}")
                traceback.print_exception(type(e), e, e.__traceback__)

    def add_cog(self, cog: commands.Cog) -> None:
        super().add_cog(cog)
        task_list = tuple(
            getattr(cog, attr)
            for attr in dir(cog)
            if isinstance(getattr(cog, attr, None), routines.Routine)
        )
        if task_list:
            self.routines[cog.name] = task_list
        self.window.stack.addCog(cog)

    def remove_cog(self, cog: commands.Cog) -> None:
        tasks = self.routines.pop(cog.name, ())
        for task in tasks:
            task.stop()
        self._cogs.pop(cog.name)
        cog._unload_methods(self)
        self.window.stack.removeCog(cog)

    async def event_raw_data(self, data: str):
        match = re.match(r"[\S\s]+target-msg-id=([\S\s]+);[\S\s]+CLEARMSG[\S\s]+", data)
        if match and (message := self._messages.pop(match.groups()[0], None)):
            self.run_event("message_delete", message)

    async def event_ready(self):
        print(f"Logged in as {self.nick}")
        await self.join_channels([self.nick])
        self.process_events.start()
        self.window.systemTray.show()
        self.add_cogs()
        self.window.showMaximized()

    async def event_error(self, error: Exception, data: str = None):
        return await super().event_error(error, data)

    async def event_command_error(
        self, ctx: commands.Context, error: Exception
    ) -> None:
        command = ctx.command
        if isinstance(error, commands.errors.CommandNotFound):
            return
        if isinstance(command, commands.Command) and command.has_error_handler():
            return
        return await super().event_command_error(ctx.command, error)

    async def event_message(self, message: Message) -> None:
        if message.echo:
            message._author = self.streamer.channel.get_chatter(self.streamer.name)
        self._messages[message.id] = message
        return await super().event_message(message)

    async def event_channel_joined(self, channel: Channel):
        self.channel = channel
        self.streamer = await channel.user()
        chatter = channel.get_chatter(self.streamer.name)
        chatter._id = str(self.streamer.id)

        # fmt: off
        tasks = {
            channel.send("Srpbotz has joined the chat"),
            self._es.subscribe_channel_stream_start(self.streamer, self._token),
            self._es.subscribe_channel_stream_end(self.streamer, self._token),
            self._es.subscribe_channel_bans(self.streamer, self._token),
            self._es.subscribe_channel_raid(self._token, to_broadcaster=self.streamer),
            self._es.subscribe_channel_follows_v2(self.streamer, self.streamer, self._token),
            self._es.subscribe_channel_subscriptions(self.streamer, self._token),
            self._es.subscribe_channel_subscription_messages(self.streamer, self._token),
            self._es.subscribe_channel_subscription_gifts(self.streamer, self._token),
            self._es.subscribe_channel_cheers(self.streamer, self._token),
            self._es.subscribe_channel_points_redeemed(self.streamer, self._token),
            self._es.subscribe_channel_prediction_begin(self.streamer, self._token),
            self._es.subscribe_channel_prediction_progress(self.streamer, self._token),
            self._es.subscribe_channel_prediction_lock(self.streamer, self._token),
            self._es.subscribe_channel_prediction_end(self.streamer, self._token),
            self._es.subscribe_channel_poll_begin(self.streamer, self._token),
            self._es.subscribe_channel_poll_progress(self.streamer, self._token),
            self._es.subscribe_channel_poll_end(self.streamer, self._token),
            self._es.subscribe_channel_hypetrain_begin(self.streamer, self._token),
            self._es.subscribe_channel_hypetrain_progress(self.streamer, self._token),
            self._es.subscribe_channel_hypetrain_end(self.streamer, self._token)
        }
        # fmt: on

        async with asyncio.TaskGroup() as tg:
            for task in tasks:
                tg.create_task(task)

    @routines.routine(seconds=1e-4)
    async def process_events(self) -> None:
        self.application.processEvents()

    def run(self) -> None:
        return super().run()

    async def close(self) -> None:
        await self.streamer.channel.send("Srpbotz has left the chat")
        await asyncio.sleep(0.5)
        self.process_events.stop()
        self.run_event("close")
        return await super().close()
