from twitchio.ext import commands
from .client import Client
import twitchio
import asyncio
import random
import json


class Fight(commands.Cog):
    def __init__(self, client: Client) -> None:
        self.client = client
        self.scores = self.load_scores()
        self.battle_royale_scores = self.load_br_scores()

    def load_scores(self) -> dict[str, dict[str, int]]:
        with open("data/scores.json") as f:
            return json.load(f)

    def load_br_scores(self) -> dict[str, dict[str, dict[str, int]]]:
        with open("data/br_scores.json") as f:
            return json.load(f)

    def unload(self) -> None:
        with open("data/scores.json", "w") as f:
            json.dump(self.scores, f, indent=4)
        with open("data/br_scores.json", "w") as f:
            json.dump(self.battle_royale_scores, f, indent=4)

    @commands.Cog.event()
    async def event_on_close(self) -> None:
        self.unload()

    def create_fighter(self) -> dict[str, int]:
        return {"wins": 0, "loses": 0, "matches": 0}

    def create_channel_br(self, channel: twitchio.User):
        return {str(channel.id): 0}

    def update_scores(self, winner: twitchio.User, loser: twitchio.User):
        if str(winner.id) not in self.scores:
            self.scores[str(winner.id)] = self.create_fighter()
        self.scores[str(winner.id)]["wins"] += 1
        self.scores[str(winner.id)]["matches"] += 1
        if str(loser.id) not in self.scores:
            self.scores[str(loser.id)] = self.create_fighter()
        self.scores[str(loser.id)]["loses"] += 1
        self.scores[str(loser.id)]["matches"] += 1

    @commands.command()
    async def fight(self, ctx: commands.Context, user: twitchio.User):
        streamer = await ctx.channel.user()
        if user == streamer:
            chatter = streamer.channel
        elif not (chatter := ctx.channel.get_chatter(user.name)):
            return
        if chatter == ctx.author:
            return
        author, chatter = await asyncio.gather(ctx.author.user(), chatter.user())
        timeout = random.randint(1, 300)
        if random.randint(0, 1):
            winner, loser = author, chatter
        else:
            winner, loser = chatter, author
        self.update_scores(winner, loser)
        return await asyncio.gather(
            streamer.timeout_user(
                self.client._token,
                self.client.user_id,
                int(loser.id),
                timeout,
                "Lost a duel",
            ),
            ctx.send(
                f"{loser.display_name} lost to {winner.display_name}. They will be muted for {timeout}s."
            ),
        )

    @commands.command(name="scores", aliases=["score"])
    async def get_scores(self, ctx: commands.Context, fighter: twitchio.User = None):
        user = await ctx.author.user() if not fighter else fighter
        if not (scores := self.scores.get(str(user.id))):
            scores = self.create_fighter()
            self.scores[str(user.id)] = scores
        streamer = await ctx.channel.user()
        if not (channel_scores := self.battle_royale_scores.get(str(streamer.id))):
            channel_scores = self.create_channel_br(streamer)
        if not (user_br_scores := channel_scores.get(str(user.id))):
            channel_scores[str(user.id)] = 0
            user_br_scores = 0
        await ctx.send(
            f"{user.display_name} won {scores['wins']} matches, won {user_br_scores} battle royale matches, and lost {scores['loses']} matches"
        )

    @commands.command()
    async def duelwinner(
        self, ctx: commands.Context, winner: twitchio.User, loser: twitchio.User
    ):
        if not ctx.author.is_mod:
            return
        self.update_scores(winner, loser)
        await ctx.send(
            f"Congratulations to {winner.display_name} for winning the duel!"
        )

    @commands.command()
    async def brwinner(self, ctx: commands.Context, winner: twitchio.User) -> None:
        if not ctx.author.is_mod:
            return
        streamer = await ctx.channel.user()
        if not self.battle_royale_scores.get(str(streamer.id)):
            self.battle_royale_scores[str(streamer.id)] = self.create_channel_br(
                streamer
            )
        if str(winner.id) not in self.battle_royale_scores[str(streamer.id)]:
            self.battle_royale_scores[str(streamer.id)][str(winner.id)] = 0
        self.battle_royale_scores[str(streamer.id)][str(winner.id)] += 1
        await ctx.send(f"{winner.display_name} has won the Battle Royale!")

    @commands.command()
    async def leaderboard(self, ctx: commands.Context):
        streamer = await ctx.author.user()
        if not (scores := self.battle_royale_scores.get(str(streamer.id))):
            scores = self.create_channel_br(streamer)
            self.battle_royale_scores[str(streamer.id)] = scores
        scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        text = []
        for score in scores:
            user = await self.client.fetch_users(ids=[int(score[0])])
            text.append(f"{user[0].display_name}: {score[1]}")
        message = ",\n".join(text)
        await ctx.send(message)


def setup(client: Client) -> None:
    client.add_cog(Fight(client))
