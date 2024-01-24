from typing import Coroutine
import traceback
import importlib
import asyncio
import inspect
import json
import sys
import os
import re

from twitch_bot import MainWindow, Message, Channel
from twitch_bot.QtGui import QIcon
from twitch_bot.QtWidgets import QApplication
from twitch_bot.ext import commands, eventsub, routines

__all__ = ("Client",)

sys.path.append(os.path.join(sys.path[0], "site-packages"))


class Client(commands.Bot):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._token: str = kwargs.get("token") or args[0]
        self._es = eventsub.EventSubWSClient(self)
        self._messages: dict[str, Message] = {}
        self.routines: dict[str, tuple[routines.Routine]] = {}
        self.application = QApplication([])
        self.application.setWindowIcon(QIcon("icons/twitch.ico"))
        self.window = MainWindow(self)
        self.streamer = None
        self._tasks: set[asyncio.Task] = set()

    @staticmethod
    def load_settings() -> None:
        with open("data/settings.json") as f:
            return json.load(f)

    def create_task(self, coro: Coroutine) -> asyncio.Task:
        if not inspect.iscoroutine(coro):
            raise TypeError("The function must be a coroutine")
        task = self.loop.create_task(coro)
        task.add_done_callback(self._tasks.discard)
        self._tasks.add(task)
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
        if not isinstance(cog, commands.Cog):
            raise TypeError("Cog must be of type twitchio.ext.commands.Cog")
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
        try:
            cog.unload()
        except Exception as e:
            traceback.print_exception(type(e), e, e.__traceback__)
        self.window.stack.removeCog(cog)
        return super().remove_cog(cog.name)

    async def event_raw_data(self, data: str):
        match = re.match(r"[\S\s]+target-msg-id=([\S\s]+);[\S\s]+CLEARMSG[\S\s]+", data)
        if match and (message := self._messages.pop(match.groups()[0], None)):
            return self.run_event("message_delete", message)
        if "CLEARCHAT" in data:
            return self.run_event("message_clear")

    async def event_ready(self):
        print(f"Logged in as {self.nick}")
        await self.join_channels([self.nick])
        self.add_cogs()
        self.window.showMaximized()

    async def event_message(self, message: Message) -> None:
        if message.echo:
            message._author = self.channel.get_chatter(self.streamer.name)
        self._messages[message.id] = message
        return await super().event_message(message)

    async def event_channel_joined(self, channel: Channel):
        self.streamer = await channel.user()
        self.channel = channel

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

    @routines.routine(seconds=1e-4)
    async def process_events(self) -> None:
        self.application.processEvents()

    def run(self) -> None:
        self.window.systemTray.show()
        self.process_events.start()
        return super().run()

    async def close(self) -> None:
        await self.channel.send("Srpbotz has left the chat")
        self.run_event("close")
        self.process_events.stop()
        await asyncio.sleep(0.5)
        return await super().close()

    @commands.command()
    async def cmds(self, ctx: commands.Context, name: str):
        if not (cog := self.cogs.get(name)):
            return await ctx.reply(f"Cog {name} couldn't be found")

        cmds = []
        commands = list(cog._commands.values())
        if not commands:
            return await ctx.send(f"Cog {name} doesn't have any commands")

        for command in commands:
            cmd = f"*{command.name}"
            params = list(command.params.values())
            if len(params) > 2:
                for param in params[2:]:
                    if param.default == param.empty:
                        cmd += f" <{param.name}>"
                    else:
                        cmd += f"({param.name})"
            cmds.append(cmd)

        msg = f"{', '.join(cmds)}. <> = required, () = optional"
        await ctx.send(msg)

    @cmds.error
    async def cmds_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, commands.MissingRequiredArgument):
            cogs = [cog.name for cog in self.cogs.values() if cog.commands.values()]
            return await ctx.reply(
                f"Format: `*cmds <cog>`. Available cogs: {', '.join(cogs)}. Note: Case Sensitive"
            )
