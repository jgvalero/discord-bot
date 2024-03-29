import random
import discord
from discord.ext import commands

import asyncio

from utils.database import Database


class Cookies(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database("data/users.db")

    @commands.Cog.listener()
    async def on_ready(self):
        """Event that runs when the bot has connected to the Discord API"""
        for guild in self.bot.guilds:
            for member in guild.members:
                self.db.create_user(member.id, guild.id)

    @commands.command()
    async def cookies(self, ctx, member: discord.Member = None):
        """Check how many cookies you or another user have!"""
        if member is None:
            member = ctx.author

        cookies = self.db.get_value(member.id, ctx.guild.id, "cookies")
        await ctx.send(f"{member.display_name} has {cookies} cookies!")

    @commands.command()
    async def leaderboard(self, ctx):
        """Check the leaderboard for the guild!"""
        rows = self.db.get_leaderboard(ctx.guild.id)
        if not rows:
            return await ctx.send("No one has any cookies yet!")

        leaderboard = "Leaderboard:\n"
        for index, row in enumerate(rows, start=1):
            member = ctx.guild.get_member(row[0])
            leaderboard += f"{index}. {member.display_name} - {row[1]} cookies\n"

        await ctx.send(leaderboard)

    @commands.command()
    async def give(self, ctx, member: discord.Member, amount: int):
        """Give your cookies to someone else!"""
        if amount <= 0:
            return await ctx.send(
                "You can't give someone a negative amount of cookies!"
            )

        author_cookies = self.db.get_value(ctx.author.id, ctx.guild.id, "cookies")

        if author_cookies < amount:
            return await ctx.send("You do not have enough cookies to give!")

        self.db.set_value(
            ctx.author.id, ctx.guild.id, "cookies", author_cookies - amount
        )

        member_cookies = self.db.get_value(member.id, ctx.guild.id, "cookies")
        self.db.set_value(member.id, ctx.guild.id, "cookies", member_cookies + amount)

        await ctx.send(f"You gave {amount} cookies to {member.display_name}!")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def set(self, ctx, member: discord.Member, amount: int):
        """Set the amount of cookies someone has!"""
        self.db.set_value(member.id, ctx.guild.id, "cookies", amount)
        await ctx.send(f"{member.display_name} now has {amount} cookies!")

    @commands.command()
    async def mute(self, ctx, member: discord.Member):
        """Mutes a user for 10 seconds! Costs 10 cookies!"""
        user_cookies = self.db.get_value(ctx.author.id, ctx.guild.id, "cookies")
        if user_cookies < 10:
            await ctx.send(
                f"You don't have enough cookies ({ctx.author.display_name})!"
            )
            return
        self.db.set_value(ctx.author.id, ctx.guild.id, "cookies", user_cookies - 10)
        await member.edit(mute=True)
        await ctx.send(
            f"{member.display_name} has been muted for 10 seconds! Enjoy the silence!"
        )
        await asyncio.sleep(10)
        await member.edit(mute=False)

    @commands.command()
    async def deafen(self, ctx, member: discord.Member):
        """Deafens a user for 10 seconds! Costs 10 cookies!"""
        user_cookies = self.db.get_value(ctx.author.id, ctx.guild.id, "cookies")
        if user_cookies < 10:
            await ctx.send(
                f"You don't have enough cookies ({ctx.author.display_name})!"
            )
            return
        self.db.set_value(ctx.author.id, ctx.guild.id, "cookies", user_cookies - 10)
        await member.edit(deafen=True)
        await ctx.send(
            f"{member.display_name} has been deafened for 10 seconds! We're having so much fun without you!"
        )
        await asyncio.sleep(10)
        await member.edit(deafen=False)

    @commands.command()
    async def rps(self, ctx, member: discord.Member, wager: int = None):
        """Play rock-paper-scissors with another user!"""
        if wager is None:
            return await ctx.send("Please specify a wager!")

        author_cookies = self.db.get_value(ctx.author.id, ctx.guild.id, "cookies")
        member_cookies = self.db.get_value(member.id, ctx.guild.id, "cookies")
        if author_cookies < wager or member_cookies < wager:
            return await ctx.send(
                "One or both users do not have enough cookies to make this wager!"
            )

        await ctx.author.send("Please reply with 'rock', 'paper', or 'scissors'.")
        await member.send(
            f"You have been challenged to rock-paper-scissors by {ctx.author.display_name}! Please reply with 'rock', 'paper', or 'scissors'."
        )

        async def get_choice(player):
            def check(m, player):
                return m.author == player and m.content.lower in [
                    "rock",
                    "paper",
                    "scissors",
                ]

            try:
                msg = await self.bot.wait_for(
                    "message", check=lambda m: check(m, player), timeout=60.0
                )
                await player.send(f"You chose {msg.content.lower}! Good luck!")
                return msg.content.lower
            except asyncio.TimeoutError:
                await ctx.send(f"{player.display_name} did not respond in time!")
                return None

        choice1, choice2 = await asyncio.gather(
            get_choice(ctx.author), get_choice(member)
        )

        if choice1 is None or choice2 is None:
            return

        await ctx.send(f"{ctx.author.display_name} chose {choice1}!")
        await ctx.send(f"{member.display_name} chose {choice2}!")

        choices = {"rock": "scissors", "paper": "rock", "scissors": "paper"}
        if choices[choice1] == choice2:
            winner = ctx.author
            loser = member
        elif choices[choice2] == choice1:
            winner = member
            loser = ctx.author
        else:
            await ctx.send(f"It's a draw!")
            return

        winner_cookies = self.db.get_value(winner.id, ctx.guild.id, "cookies")
        self.db.set_value(winner.id, ctx.guild.id, "cookies", winner_cookies + wager)

        loser_cookies = self.db.get_value(loser.id, ctx.guild.id, "cookies")
        self.db.set_value(loser.id, ctx.guild.id, "cookies", loser_cookies - wager)

        await ctx.send(
            f"{winner.display_name} wins and receives {wager} cookies from {loser.display_name}!"
        )

    @commands.command()
    async def stats(self, ctx):
        """Check your stats!"""
        cookies = self.db.get_value(ctx.author.id, ctx.guild.id, "cookies")
        most_valuable_fish = self.db.get_value(
            ctx.author.id, ctx.guild.id, "most_valuable_fish"
        )
        baits = self.db.get_value(ctx.author.id, ctx.guild.id, "bait")
        await ctx.send(
            f"{ctx.author.display_name}'s stats:\nCookies: {cookies}\nMost valuable fish: {most_valuable_fish} cookies\nBaits: {baits}"
        )

    @commands.command()
    async def blackjack(self, ctx, wager: int):
        """Starts a game of blackjack with a wager!"""

        user_cookies = self.db.get_value(ctx.author.id, ctx.guild.id, "cookies")
        if user_cookies < wager:
            return await ctx.send(f"You don't have enough cookies to make this wager!")

        DECK = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11]
        DEALER_HIT_THRESHOLD = 17

        random.shuffle(DECK)

        player_hand = [DECK.pop(), DECK.pop()]
        dealer_hand = [DECK.pop(), DECK.pop()]

        await ctx.send(f"Your hand: {player_hand} ({sum(player_hand)})")
        await ctx.send(f"Dealer's hand: {dealer_hand[0]} _")

        while sum(player_hand) < 21:
            await ctx.send("Would you like to hit or stand? [hit/stand]")

            def check(m):
                return m.author == ctx.author and m.content.lower() in ["hit", "stand"]

            try:
                message = await self.bot.wait_for("message", check=check, timeout=60.0)
            except asyncio.TimeoutError:
                await ctx.send(
                    "Sorry, you took too long to respond! Because of that, you lose your cookies!"
                )
                self.db.set_value(
                    ctx.author.id, ctx.guild.id, "cookies", user_cookies - wager
                )
                return

            if message.content.lower() == "hit":
                player_hand.append(DECK.pop())
                await ctx.send(f"Your hand: {player_hand} ({sum(player_hand)})")
            else:
                break

        if sum(player_hand) > 21:
            await ctx.send("Bust! You lose!")
            self.db.set_value(
                ctx.author.id, ctx.guild.id, "cookies", user_cookies - wager
            )
        elif sum(player_hand) == 21:
            await ctx.send("Blackjack! You win!")
            self.db.set_value(
                ctx.author.id, ctx.guild.id, "cookies", user_cookies + wager
            )
        else:
            while sum(dealer_hand) < DEALER_HIT_THRESHOLD:
                dealer_hand.append(DECK.pop())
            await ctx.send(f"Dealer's hand: {dealer_hand} ({sum(dealer_hand)})")

            if sum(dealer_hand) > 21:
                await ctx.send("Dealer busts! You win!")
                self.db.set_value(
                    ctx.author.id, ctx.guild.id, "cookies", user_cookies + wager
                )
            elif sum(dealer_hand) < sum(player_hand):
                await ctx.send("You win!")
                self.db.set_value(
                    ctx.author.id, ctx.guild.id, "cookies", user_cookies + wager
                )
            elif sum(dealer_hand) > sum(player_hand):
                await ctx.send("You lose!")
                self.db.set_value(
                    ctx.author.id, ctx.guild.id, "cookies", user_cookies - wager
                )
            else:
                await ctx.send("It's a tie! Zoo wee mama!")


async def setup(bot):
    await bot.add_cog(Cookies(bot))
