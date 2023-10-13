from __future__ import annotations
from typing import TYPE_CHECKING
import commands, models
import random
import json

if TYPE_CHECKING:
    from network.client import Client


class Fight(commands.Cog):
    def __init__(self, client: Client) -> None:
        self.client = client
        self.load_json()

    def load_json(self) -> None:
        with open("data/scores.json", encoding="utf-8") as f:
            self.scores = json.load(f)
        with open("data/br_scores.json", encoding="utf-8") as f:
            self.br_scores = json.load(f)

    def create_fighter(self) -> dict[str, int]:
        return {"wins": 0, "loses": 0, "matches": 0}

    def update_scores(self, winner: models.User, loser: models.User):
        if str(winner.id) not in self.scores:
            self.scores[str(winner.id)] = self.create_fighter()
        self.scores[str(winner.id)]["wins"] += 1
        self.scores[str(winner.id)]["matches"] += 1
        if str(loser.id) not in self.scores:
            self.scores[str(loser.id)] = self.create_fighter()
        self.scores[str(loser.id)]["loses"] += 1
        self.scores[str(loser.id)]["matches"] += 1
        with open("data/scores.json", "w") as f:
            json.dump(self.scores, f, indent=4)

    def create_channel_br(self, channel: models.User):
        return {str(channel.id): 0}

    def update_br_scores(self, winner: models.User):
        if str(winner.id) not in self.br_scores:
            self.br_scores[str(winner.id)] = 0
        self.br_scores[str(winner.id)] += 1
        with open("data/br_scores.json", "w") as f:
            json.dump(self.br_scores, f, indent=4)

    @commands.command()
    def fight(self, ctx: commands.Context, chatter: models.Chatter):
        timeout = random.randint(1, 300)
        if ctx.author == chatter:
            return
        winner, loser = (
            (ctx.author, chatter) if random.randint(0, 1) else (chatter, ctx.author)
        )
        self.update_scores(winner, loser)
        ctx.streamer.timeout_user(chatter, reason="git good nerd", duration=60),
        ctx.send(
            f"{loser.display_name} lost to {winner.display_name}. They will be muted for {timeout}s."
        )

    @commands.command()
    def duelwinner(
        self, ctx: commands.Context, winner: models.User, loser: models.User
    ):
        if not ctx.author.is_mod:
            return
        self.update_scores(winner, loser)
        ctx.streamer.timeout_user(loser, reason="git good nerd", duration=60),
        ctx.send(f"Congratulations to {winner.display_name} for winning the duel!")

    @commands.command(name="scores")
    def get_scores(self, ctx: commands.Context, fighter: models.User = None):
        if not fighter:
            fighter = ctx.author
        if not (scores := self.scores.get(str(fighter.id))):
            scores = self.create_fighter()
        if not (user_br_scores := self.br_scores.get(str(fighter.id))):
            user_br_scores = 0
        ctx.send(
            f"{fighter.display_name} won {scores['wins']} matches, lost {scores['loses']} matches, and won {user_br_scores} battle royale matches"
        )

    @commands.command()
    def brwinner(self, ctx: commands.Context, winner: models.User) -> None:
        if not ctx.author.is_mod:
            return
        self.update_br_scores(winner)
        ctx.send(f"{winner.display_name} has won the Battle Royale!")

    @commands.command()
    def leaderboard(self, ctx: commands.Context):
        scores = sorted(self.br_scores.items(), key=lambda x: x[1], reverse=True)
        text = []
        users = self.client.fetch_users([int(user) for user, _ in scores])
        users_dict = {}
        for user in users:
            users_dict[user.id] = user.display_name
        for id, score in scores:
            text.append(f"{users_dict.get(int(id))}: {score}")
        message = ", ".join(text)
        ctx.send(message)


def setup(client: Client) -> Fight:
    return client.add_cog(Fight(client))
