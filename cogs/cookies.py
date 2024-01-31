import discord
from discord.ext import commands

import sqlite3


class Cookies(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = sqlite3.connect("data/users.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER,
                guild_id INTEGER,
                cookies INTEGER,
                PRIMARY KEY (user_id, guild_id)
            )
            """
        )

    @commands.Cog.listener()
    async def on_ready(self):
        """Event that runs when the bot has connected to the Discord API"""
        for guild in self.bot.guilds:
            for member in guild.members:
                self.cursor.execute(
                    """
                    INSERT OR IGNORE INTO users (user_id, guild_id, cookies)
                    VALUES (?, ?, ?)
                    """,
                    (member.id, guild.id, 0),
                )
        self.conn.commit()

    @commands.command()
    async def cookies(self, ctx, member: discord.Member = None):
        """Check how many cookies you or another user have!"""
        if member is None:
            member = ctx.author

        self.cursor.execute(
            """
            SELECT cookies FROM users WHERE user_id = ? AND guild_id = ?
            """,
            (member.id, ctx.guild.id),
        )
        cookies = self.cursor.fetchone()[0]
        await ctx.send(f"{member.name} has {cookies} cookies!")

    @commands.command()
    async def leaderboard(self, ctx):
        """Check the leaderboard for the guild!"""
        self.cursor.execute(
            """
            SELECT user_id, cookies FROM users WHERE guild_id = ?
            ORDER BY cookies DESC
            """,
            (ctx.guild.id,),
        )
        rows = self.cursor.fetchall()
        if not rows:
            return await ctx.send("No one has any cookies yet!")

        leaderboard = "Leaderboard:\n"
        for index, row in enumerate(rows, start=1):
            member = ctx.guild.get_member(row[0])
            leaderboard += f"{index}. {member.name} - {row[1]} cookies\n"

        await ctx.send(leaderboard)

    @commands.command()
    async def give(self, ctx, member: discord.Member, amount: int):
        """Give your cookies to someone else!"""
        if amount <= 0:
            return await ctx.send(
                "You can't give someone a negative amount of cookies!"
            )

        self.cursor.execute(
            """
            SELECT cookies FROM users WHERE user_id = ? AND guild_id = ?
            """,
            (ctx.author.id, ctx.guild.id),
        )
        author_cookies = self.cursor.fetchone()[0]

        if author_cookies < amount:
            return await ctx.send("You do not have enough cookies to give!")

        self.cursor.execute(
            """
            UPDATE users SET cookies = cookies - ? WHERE user_id = ? AND guild_id = ?
            """,
            (amount, ctx.author.id, ctx.guild.id),
        )

        self.cursor.execute(
            """
            UPDATE users SET cookies = cookies + ? WHERE user_id = ? AND guild_id = ?
            """,
            (amount, member.id, ctx.guild.id),
        )

        await ctx.send(f"You gave {amount} cookies to {member.mention}!")

    # @commands.command()
    # async def fish(self, ctx):
    #     user_id = str(ctx.author.id)
    #     num = random.randint(0, 9)
    #     if num == 0:
    #         self.users[user_id].cookies += 1
    #         await ctx.send(f"You caught a fish ({ctx.author.mention})!")
    #     else:
    #         await ctx.send("Tough luck!")
    #     self.save_users()

    # @commands.command()
    # async def mute(self, ctx, member: discord.Member):
    #     """Mutes a user for 10 seconds! Costs 1 cookie!"""
    #     user_id = str(ctx.author.id)
    #     if self.users[user_id].cookies < 1:
    #         await ctx.send(f"You don't have enough cookies ({ctx.author.mention})!")
    #         return
    #     self.users[user_id].cookies -= 1
    #     await member.edit(mute=True)
    #     await asyncio.sleep(10)
    #     await member.edit(mute=False)
    #     self.save_users()

    # @commands.command()
    # async def deafen(self, ctx, member: discord.Member):
    #     """Deafens a user for 10 seconds! Costs 1 cookie!"""
    #     user_id = str(ctx.author.id)
    #     if self.users[user_id].cookies < 1:
    #         await ctx.send(f"You don't have enough cookies ({ctx.author.mention})!")
    #         return
    #     self.users[user_id].cookies -= 1
    #     await member.edit(deafen=True)
    #     await asyncio.sleep(10)
    #     await member.edit(deafen=False)
    #     self.save_users()

    # @commands.command()
    # async def rps(self, ctx, member: discord.Member, wager: int):
    #     """Play rock-paper-scissors with another user!"""
    #     if (
    #         self.users[str(ctx.author.id)].cookies < wager
    #         or self.users[str(member.id)].cookies < wager
    #     ):
    #         await ctx.send(
    #             "One or both users do not have enough cookies to make this wager!"
    #         )
    #         return

    #     await ctx.author.send("Please reply with 'rock', 'paper', or 'scissors'.")
    #     await member.send("Please reply with 'rock', 'paper', or 'scissors'.")

    #     def check(m, member):
    #         return m.author == member and m.content in ["rock", "paper", "scissors"]

    #     async def get_choice(member):
    #         try:
    #             msg = await self.bot.wait_for(
    #                 "message", check=lambda m: check(m, member), timeout=60.0
    #             )
    #             return msg.content
    #         except asyncio.TimeoutError:
    #             await ctx.send(f"{member.mention} did not respond in time!")
    #             return None

    #     choice1, choice2 = await asyncio.gather(
    #         get_choice(ctx.author), get_choice(member)
    #     )

    #     if choice1 is None or choice2 is None:
    #         return

    #     choices = {"rock": "scissors", "paper": "rock", "scissors": "paper"}
    #     if choices[choice1] == choice2:
    #         winner = ctx.author
    #         loser = member
    #     elif choices[choice2] == choice1:
    #         winner = member
    #         loser = ctx.author
    #     else:
    #         await ctx.send("It's a draw!")
    #         return

    #     self.users[str(winner.id)].cookies += wager
    #     self.users[str(loser.id)].cookies -= wager
    #     self.save_users()

    #     await ctx.send(
    #         f"{winner.mention} wins and receives {wager} cookies from {loser.mention}!"
    #     )


async def setup(bot):
    await bot.add_cog(Cookies(bot))
