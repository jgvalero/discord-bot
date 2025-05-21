import asyncio

import discord
from discord import app_commands
from discord.ext import commands

from main import DiscordBot
from utils.money import Money


class Cookies(commands.GroupCog):
    def __init__(self, bot: DiscordBot) -> None:
        self.bot = bot
        self.money = Money(bot.database)

    @app_commands.command()
    async def amount(self, interaction: discord.Interaction, member: discord.User):
        """Check how many cookies you or another user have!"""
        if interaction.guild is None:
            return

        cookies = self.money.get_money(member.id, interaction.guild.id)
        await interaction.response.send_message(
            f"{member.display_name} has {cookies} cookies!"
        )

    @app_commands.command()
    async def leaderboard(self, interaction: discord.Interaction):
        """Show the cookie leaderboard for this server!"""
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server!", ephemeral=True
            )
            return

        guild_id = str(interaction.guild.id)
        cursor = self.bot.database.cursor
        cursor.execute(
            """
            SELECT user_id, cookies
            FROM cookies
            WHERE guild_id = ?
            ORDER BY cookies DESC
            LIMIT 10
            """,
            (guild_id,),
        )

        rows = cursor.fetchall()

        if not rows:
            await interaction.response.send_message(
                "No one has any cookies yet!", ephemeral=True
            )
            return

        embed = discord.Embed(
            title="🍪 Cookie Leaderboard",
            description="Top 10 Cookie Collectors!",
            color=discord.Color.gold(),
        )

        medals = {1: "🥇", 2: "🥈", 3: "🥉"}

        for index, (user_id, cookies) in enumerate(rows, start=1):
            member = interaction.guild.get_member(int(user_id))
            if member:
                rank = medals.get(index, f"#{index}")
                name = f"{rank} {member.display_name}"
                embed.add_field(name=name, value=f"{cookies:,} cookies", inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    async def give(
        self,
        interaction: discord.Interaction,
        recipient: discord.Member,
        amount: int,
    ):
        """Give your cookies to someone else!"""

        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server!", ephemeral=True
            )
            return

        if amount <= 0:
            return await interaction.response.send_message(
                "You can't give someone a negative amount of cookies!"
            )

        sender_id = interaction.user.id
        recipient_id = recipient.id
        guild_id = interaction.guild.id

        if not self.money.lose(sender_id, guild_id, amount):
            return await interaction.response.send_message(
                "You don't have enough cookies to give!"
            )

        self.money.earn(recipient_id, guild_id, amount)

        await interaction.response.send_message(
            f"Transfer complete. {interaction.user.display_name} gives {recipient.display_name} {amount} cookies!"
        )

    @app_commands.command()
    @commands.has_permissions(administrator=True)
    async def set(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        amount: int,
    ):
        """Set the amount of cookies someone has!"""
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server!", ephemeral=True
            )
            return

        user_id = member.id
        guild_id = interaction.guild.id

        self.money.set_money(user_id, guild_id, amount)
        await interaction.response.send_message(
            f"{member.display_name} now has {amount} cookies!"
        )

    @app_commands.command()
    async def mute(self, interaction: discord.Interaction, member: discord.Member):
        """Mutes a user for 10 seconds! Costs 10 cookies!"""

        # Ensure command is used in a server context
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server!", ephemeral=True
            )
            return

        author_id = interaction.user.id
        guild_id = interaction.guild.id

        if not self.money.lose(author_id, guild_id, 10):
            return await interaction.response.send_message(
                "You don't have enough cookies to mute!"
            )

        await member.edit(mute=True)
        await interaction.response.send_message(
            f"{member.display_name} has been muted for 10 seconds! Enjoy the silence!"
        )
        await asyncio.sleep(10)
        await member.edit(mute=False)

    @app_commands.command()
    async def deafen(self, interaction: discord.Interaction, member: discord.Member):
        """Deafens a user for 10 seconds! Costs 10 cookies!"""

        # Ensure command is used in a server context
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server!", ephemeral=True
            )
            return

        author_id = interaction.user.id
        guild_id = interaction.guild.id

        if not self.money.lose(author_id, guild_id, 10):
            return await interaction.response.send_message(
                "You don't have enough cookies to mute!"
            )

        await member.edit(deafen=True)
        await interaction.response.send_message(
            f"{member.display_name} has been deafened for 10 seconds! We're having so much fun without you!"
        )
        await asyncio.sleep(10)
        await member.edit(deafen=False)

    # @commands.command()
    # async def rps(self, ctx, member: discord.Member, wager: int = 0):
    #     """Play rock-paper-scissors with another user!"""
    #     if wager is None:
    #         return await ctx.send("Please specify a wager!")

    #     # author_cookies = self.db.get_value(ctx.author.id, ctx.guild.id, "cookies")
    #     # member_cookies = self.db.get_value(member.id, ctx.guild.id, "cookies")
    #     if author_cookies < wager or member_cookies < wager:
    #         return await ctx.send(
    #             "One or both users do not have enough cookies to make this wager!"
    #         )

    #     await ctx.author.send("Please reply with 'rock', 'paper', or 'scissors'.")
    #     await member.send(
    #         f"You have been challenged to rock-paper-scissors by {ctx.author.display_name}! Please reply with 'rock', 'paper', or 'scissors'."
    #     )

    #     async def get_choice(player):
    #         def check(m, player):
    #             return m.author == player and m.content.lower in [
    #                 "rock",
    #                 "paper",
    #                 "scissors",
    #             ]

    #         try:
    #             msg = await self.bot.wait_for(
    #                 "message", check=lambda m: check(m, player), timeout=60.0
    #             )
    #             await player.send(f"You chose {msg.content.lower}! Good luck!")
    #             return msg.content.lower
    #         except asyncio.TimeoutError:
    #             await ctx.send(f"{player.display_name} did not respond in time!")
    #             return None

    #     choice1, choice2 = await asyncio.gather(
    #         get_choice(ctx.author), get_choice(member)
    #     )

    #     if choice1 is None or choice2 is None:
    #         return

    #     await ctx.send(f"{ctx.author.display_name} chose {choice1}!")
    #     await ctx.send(f"{member.display_name} chose {choice2}!")

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

    #     # winner_cookies = self.db.get_value(winner.id, ctx.guild.id, "cookies")
    #     # self.db.set_value(winner.id, ctx.guild.id, "cookies", winner_cookies + wager)

    #     # loser_cookies = self.db.get_value(loser.id, ctx.guild.id, "cookies")
    #     # self.db.set_value(loser.id, ctx.guild.id, "cookies", loser_cookies - wager)

    #     await ctx.send(
    #         f"{winner.display_name} wins and receives {wager} cookies from {loser.display_name}!"
    #     )

    @app_commands.command()
    async def stats(self, interaction: discord.Interaction, member: discord.User):
        """Check a member's stats!"""
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server!", ephemeral=True
            )
            return

        user_id = member.id
        guild_id = interaction.guild.id

        current_cookies = self.money.get_money(user_id, guild_id)
        total_earned = self.money.get_total_earned(user_id, guild_id)
        total_lost = self.money.get_total_lost(user_id, guild_id)
        highest_amount = self.money.get_max(user_id, guild_id)

        if not current_cookies:
            await interaction.response.send_message(
                f"{member.display_name} has no cookie stats yet!",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title=f"{member.display_name}'s Cookie Stats",
            color=discord.Color.gold(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        embed.add_field(name="Current Cookies", value=current_cookies, inline=True)
        embed.add_field(name="Total Earned", value=total_earned, inline=True)
        embed.add_field(name="Total Lost", value=total_lost, inline=True)
        embed.add_field(name="Highest Amount", value=highest_amount, inline=True)

        await interaction.response.send_message(embed=embed)


async def setup(bot: DiscordBot) -> None:
    await bot.add_cog(Cookies(bot))
