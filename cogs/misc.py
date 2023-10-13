from __future__ import annotations
from typing import TYPE_CHECKING
import commands
import json

if TYPE_CHECKING:
    from network.client import Client


class Misc(commands.Cog):
    def __init__(self, client: Client) -> None:
        self.client = client
        self.load_json()

    def load_json(self) -> None:
        with open("data/death_counter.json") as f:
            self.deaths = json.load(f)
        with open("data/raid.json", encoding="utf-8") as f:
            self.raid_messages = json.load(f)

    def dump_death_counter(self):
        with open("data/death_counter.json", "w") as f:
            json.dump(self.deaths, f, indent=4)

    @commands.command()
    def death(self, ctx: commands.Context):
        total = self.deaths("total", 0)
        ctx.send(f"{self.client.streamer.display_name} had died a total of {total}.")

    @commands.command()
    def bdeath(self, ctx: commands.Context):
        total = self.deaths("boss", 0)
        ctx.send(
            f"{self.client.streamer.display_name} had died a total of {total} to the boss."
        )

    @commands.command(name="death++")
    def increment_death(self, ctx: commands.Context):
        if not ctx.author.is_mod:
            return
        self.deaths["total"] += 1
        self.dump_death_counter()
        return ctx.send(
            f"{self.client.streamer.display_name} has died a total of {self.deaths['total']} times."
        )

    @commands.command(name="bdeath++")
    def increment_bdeath(self, ctx: commands.Context):
        if not ctx.author.is_mod:
            return
        self.deaths["boss"] += 1
        self.deaths["total"] += 1
        self.dump_death_counter()
        return ctx.send(
            f"{self.client.streamer.display_name} has died to the boss {self.deaths['boss']} times. They have died a total of {self.deaths['total']} times."
        )

    @commands.command()
    def setdeath(self, ctx: commands.Context, type: str, num: int = 0):
        if not ctx.author.is_mod:
            return
        type = type.lower()
        if type == "boss":
            self.deaths["boss"] = num
            self.dump_death_counter()
            return ctx.send(f"Boss Death counter set to {num}.")
        elif type == "total":
            self.deaths["total"] = num
            self.dump_death_counter()
            return ctx.send(f"Death counter set to {num}.")
        else:
            return ctx.send(f"Couldn't set {type} counter.")

    @commands.command()
    def raid(self, ctx: commands.Context):
        free, sub = self.raid_messages.get("free"), self.raid_messages.get("sub")
        if not bool(free) and not bool(sub):
            return ctx.send(
                "You don't have a raid message use *setraid <free or sub> <message> to set a message"
            )
        if free:
            ctx.send(free)
        if sub:
            ctx.send(sub)

    @commands.command()
    def setraid(self, ctx: commands.Context, type: str, *, message: str):
        type = type.lower()
        self.raid_messages[type] = message
        with open("data/raid.json", "w", encoding="utf-8") as f:
            json.dump(self.raid_messages, f, indent=4)
        ctx.send(message)

    @commands.command()
    def cmds(self, ctx: commands.Context):
        ctx.send(
            "*fight <user>, *scores (user), *duelwinner <winner> <loser>, *brwinner <winner>, *leaderboard, *death, *death++, *bdeath, *bdeath++, *setdeath <type> <num>, *raid, *setraid <free or sub> <message>"
        )


def setup(client: Client) -> Misc:
    return client.add_cog(Misc(client))
