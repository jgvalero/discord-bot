import discord
from discord.ext import commands
from collections import defaultdict

import random
import asyncio
import json


class User:
    def __init__(self, name):
        self.name = name
        self.cookies = 0

    def to_json(self):
        return {"name": self.name, "cookies": self.cookies}

    @classmethod
    def from_json(cls, data):
        user = cls(data["name"])
        user.cookies = data["cookies"]
        return user


class Cookies(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.users = defaultdict(lambda: User("Unknown"))
        try:
            with open("data/users.json", "r") as f:
                data = json.load(f)
                self.users = defaultdict(
                    lambda: User("Unknown"),
                    {
                        user_id: User.from_json(user_data)
                        for user_id, user_data in data.items()
                    },
                )
        except FileNotFoundError:
            pass

    def save_users(self):
        with open("data/users.json", "w") as f:
            json.dump(
                {user_id: user.to_json() for user_id, user in self.users.items()}, f
            )

    @commands.command()
    async def fish(self, ctx):
        user_id = str(ctx.author.id)
        num = random.randint(0, 9)
        print(num)
        if num == 0:
            self.users[user_id].cookies += 1
            await ctx.send("You caught a fish!")
        else:
            await ctx.send("Tough luck!")
        self.save_users()

    @commands.command()
    async def cookies(self, ctx):
        user_id = str(ctx.author.id)
        await ctx.send(
            f"{ctx.author.mention} has {self.users[user_id].cookies} cookies!"
        )

    @commands.command()
    async def mute(self, ctx, member: discord.Member):
        user_id = str(ctx.author.id)
        if self.users[user_id].cookies < 1:
            await ctx.send("You don't have enough cookies!")
            return
        self.users[user_id].cookies -= 1
        await member.edit(mute=True)
        await asyncio.sleep(10)
        await member.edit(mute=False)
        self.save_users()

    @commands.command()
    async def deafen(self, ctx, member: discord.Member):
        user_id = str(ctx.author.id)
        if self.users[user_id].cookies < 1:
            await ctx.send("You don't have enough cookies!")
            return
        self.users[user_id].cookies -= 1
        await member.edit(deafen=True)
        await asyncio.sleep(10)
        await member.edit(deafen=False)
        self.save_users()

    @commands.command()
    async def rps(self, ctx, member: discord.Member, wager: int):
        if (
            self.users[str(ctx.author.id)].cookies < wager
            or self.users[str(member.id)].cookies < wager
        ):
            await ctx.send(
                "One or both users do not have enough cookies to make this wager."
            )
            return

        await ctx.author.send("Please reply with 'rock', 'paper', or 'scissors'.")
        await member.send("Please reply with 'rock', 'paper', or 'scissors'.")

        def check(m, member):
            return m.author == member and m.content in ["rock", "paper", "scissors"]

        async def get_choice(member):
            try:
                msg = await self.bot.wait_for(
                    "message", check=lambda m: check(m, member), timeout=60.0
                )
                return msg.content
            except asyncio.TimeoutError:
                await ctx.send(f"{member.mention} did not respond in time.")
                return None

        choice1, choice2 = await asyncio.gather(
            get_choice(ctx.author), get_choice(member)
        )

        if choice1 is None or choice2 is None:
            return

        choices = {"rock": "scissors", "paper": "rock", "scissors": "paper"}
        if choices[choice1] == choice2:
            winner = ctx.author
            loser = member
        elif choices[choice2] == choice1:
            winner = member
            loser = ctx.author
        else:
            await ctx.send("It's a draw!")
            return

        self.users[str(winner.id)].cookies += wager
        self.users[str(loser.id)].cookies -= wager
        self.save_users()

        await ctx.send(
            f"{winner.mention} wins and receives {wager} cookies from {loser.mention}!"
        )

    @commands.command()
    async def give(self, ctx, recipient: discord.Member, amount: int):
        sender_id = str(ctx.author.id)
        if self.users[sender_id].cookies < amount:
            await ctx.send("You do not have enough cookies to make this transfer.")
            return

        recipient_id = str(recipient.id)
        self.users[sender_id].cookies -= amount
        self.users[recipient_id].cookies += amount
        self.save_users()

        await ctx.send(
            f"{ctx.author.mention} has given {amount} cookies to {recipient.mention}!"
        )


async def setup(bot):
    await bot.add_cog(Cookies(bot))
