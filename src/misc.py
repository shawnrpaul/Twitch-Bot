from __future__ import annotations
from twitchio.ext import commands
from typing import TYPE_CHECKING
import json

if TYPE_CHECKING:
    from ..client import Client


class Misc(commands.Cog):
    def __init__(self, client: Client) -> None:
        self.client = client
        self.deaths = self.load_deaths()

    def load_deaths(self) -> dict[str, dict[str, int]]:
        with open("data/death_counter.json") as f:
            return json.load(f)

    def unload(self) -> None:
        with open("data/death_counter.json", "w") as f:
            return json.dump(self.deaths, f, indent=4)

    @commands.Cog.event()
    async def event_on_close(self) -> None:
        self.unload()

    @commands.command()
    async def death(self, ctx: commands.Context):
        streamer = await ctx.channel.user()
        await ctx.send(
            f"{streamer.display_name} had died a total of {self.deaths[str(streamer.id)]['total']}."
        )

    @commands.command()
    async def bdeath(self, ctx: commands.Context):
        streamer = await ctx.channel.user()
        await ctx.send(
            f"{streamer.display_name} had died a total of {self.deaths[str(streamer.id)]['boss']} to the boss."
        )

    @commands.command(name="death++")
    async def increment_death(self, ctx: commands.Context):
        if not ctx.author.is_mod:
            return
        streamer = await ctx.channel.user()
        if self.deaths.get(str(streamer.id)) is None:
            self.deaths[str(streamer.id)] = {}
            self.deaths[str(streamer.id)]["boss"] = 0
            self.deaths[str(streamer.id)]["total"] = 0
        self.deaths[str(streamer.id)]["total"] += 1
        return await ctx.send(
            f"{streamer.display_name} has died a total of {self.deaths[str(streamer.id)]['total']} times."
        )

    @commands.command(name="bdeath++")
    async def increment_bdeath(self, ctx: commands.Context):
        if not ctx.author.is_mod:
            return
        streamer = await ctx.channel.user()
        if self.deaths.get(str(streamer.id)) is None:
            self.deaths[str(streamer.id)] = {}
            self.deaths[str(streamer.id)]["boss"] = 0
            self.deaths[str(streamer.id)]["total"] = 0
        self.deaths[str(streamer.id)]["boss"] += 1
        self.deaths[str(streamer.id)]["total"] += 1
        return await ctx.send(
            f"{streamer.display_name} has died to the boss {self.deaths[str(streamer.id)]['boss']} times. They have died a total of {self.deaths[str(streamer.id)]['total']} times."
        )

    @commands.command()
    async def setdeath(self, ctx: commands.Context, type: str, num: int = 0):
        if not ctx.author.is_mod:
            return
        type = type.lower()
        streamer = await ctx.channel.user()
        if self.deaths.get(str(streamer.id)) is None:
            self.deaths[str(streamer.id)] = {}
            self.deaths[str(streamer.id)]["boss"] = 0
            self.deaths[str(streamer.id)]["total"] = 0
        if type == "boss":
            self.deaths[str(streamer.id)]["boss"] = num
            return await ctx.send(f"Boss Death counter set to {num}.")
        elif type == "total":
            self.deaths[str(streamer.id)]["total"] = num
            return await ctx.send(f"Death counter set to {num}.")
        else:
            return await ctx.send(f"Couldn't set {type} counter.")

    @commands.command()
    async def cmds(self, ctx: commands.Context):
        await ctx.send(
            "*fight <user>, *scores (user), *duelwinner <winner> <loser>, *brwinner <winner>, *leaderboard, *death, *death++, *bdeath, *bdeath++, *setdeath <type> <num>"
        )


def setup(client: Client) -> None:
    client.add_cog(Misc(client))
