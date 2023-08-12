from twitchio.ext import commands
from typing import Any, Iterable
import importlib
import logging
import os
import sys
import json


class Client(commands.Bot):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._token = kwargs.get("token")

    async def event_ready(self):
        print(f"Logged in as {self.nick}")

    async def event_error(self, error: Exception, data: str = None):
        if isinstance(error, commands.errors.ArgumentParsingFailed):
            return
        if isinstance(error, commands.errors.CommandNotFound):
            return
        logging.error(f"Exception: {error.__class__.__name__} - {error}")

    async def event_command_error(self, ctx: commands.Context, error: Exception):
        logging.error(
            f"Message: {ctx.message.content} - Exception: {error.__class__.__name__} - {error}"
        )

    @staticmethod
    def load_settings() -> dict[str, Any]:
        with open("data/settings.json") as f:
            return json.load(f)

    def add_cogs(self, cogs: Iterable[str]) -> None:
        for cog in cogs:
            try:
                mod = importlib.import_module(f"src.{cog}")
            except ModuleNotFoundError as e:
                logging.error(
                    f"Error while trying loading {cog} - {e.__class__.name}: {e}"
                )
                continue
            mod.setup(self)

    @commands.command()
    async def load(self, ctx: commands.Context, name: str):
        author = await ctx.author.user()
        if int(author.id) != 786971213:
            return
        name = name.capitalize()
        if self.cogs.get(name):
            return await ctx.send(f"Cog {name} already exists.")
        try:
            mod = importlib.import_module(f"src.{name.lower()}")
        except ModuleNotFoundError:
            return await ctx.send(f"Unable to find module {name}")
        except Exception as e:
            logging.error(
                f"Message: {ctx.message.content} - Exception: {e.__class__} - {e}"
            )
            return await ctx.send(f"Error while loading Cog {name}.")
        mod.setup(self)
        return await ctx.send(f"Loaded {name} successfully.")

    @commands.command()
    async def unload(self, ctx: commands.Context, name: str):
        author = await ctx.author.user()
        if int(author.id) != 786971213:
            return
        name = name.capitalize()
        try:
            mod = sys.modules[f"src.{name.lower()}"]
        except KeyError:
            return await ctx.send(f"Unable to find module {name}.")
        except Exception as e:
            logging.error(
                f"Message: {ctx.message.content} - Exception: {e.__class__} - {e}"
            )
            return await ctx.send(f"Error while unloading Cog {name}.")
        cog = self.cogs.get(name)
        if hasattr(cog, "unload"):
            cog.unload()
        self.remove_cog(name)
        del mod
        return await ctx.send(f"Unloaded {name} successfully.")

    @commands.command()
    async def reload(self, ctx: commands.Context, name: str):
        author = await ctx.author.user()
        if int(author.id) != 786971213:
            return
        name = name.capitalize()
        try:
            mod = sys.modules[f"src.{name.lower()}"]
        except KeyError:
            return await ctx.send(f"Unable to find module {name}.")
        except Exception as e:
            logging.error(
                f"Message: {ctx.message.content} - Exception: {e.__class__} - {e}"
            )
            return await ctx.send(f"Error while reloading Cog {name}.")
        cog = self.cogs.get(name)
        if hasattr(cog, "unload"):
            cog.unload()
        self.remove_cog(name)
        mod = importlib.reload(mod)
        mod.setup(self)
        return await ctx.send(f"Updated All Commands")

    async def close(self):
        self.run_event("on_close")
        return await super().close()


logging.basicConfig(
    filename="client.log",
    level=logging.ERROR,
    format="%(levelname)s:%(asctime)s:%(message)s",
)


def main():
    settings = Client.load_settings()
    client = Client(
        token=settings["token"],
        prefix=settings["prefix"],
        initial_channels=settings["initial_channels"],
    )
    client.add_cogs(settings["cogs"])
    client.run()


if __name__ == "__main__":
    sys.path.insert(0, os.getcwd())
    main()
