import json
import os
import random

import discord
from discord import app_commands
from discord.ext import commands

from main import DiscordBot


class Fish(commands.GroupCog):
    def __init__(self, bot: DiscordBot, catch_chance: float) -> None:
        self.bot = bot
        self.catch_chance = catch_chance
        if os.path.exists("data/fishes.json"):
            with open("data/fishes.json", "r") as f:
                self.fishes = json.load(f)
        else:
            self.fishes = [{"name": "Joel", "price": 10, "chance": 100}]

    @app_commands.command()
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.guild_id, i.user.id))
    async def cast(self, interaction: discord.Interaction) -> None:
        """CAST! CAST! CAST!"""
        # Ensure command is used in a server context
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server!", ephemeral=True
            )
            return

        # Get user and guild IDs for database operations
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild.id)

        # Increment the total fishing attempts counter
        attempts = self.bot.database.get_value(
            user_id, guild_id, "fishing", "attempts"
        )[0]
        self.bot.database.set_value(
            user_id, guild_id, "fishing", "attempts", attempts + 1
        )

        # Determine if the cast was successful based on catch chance
        if random.random() < self.catch_chance:
            # Reset dry streak on successful catch
            self.bot.database.set_value(
                user_id, guild_id, "fishing", "streak", 0
            )

            # Select a random fish based on their chance weights
            random_fish = random.choices(
                self.fishes, weights=[fish["chance"] for fish in self.fishes]
            )[0]

            # Update fishing statistics
            caught = self.bot.database.get_value(
                user_id, guild_id, "fishing", "caught"
            )[0]
            revenue = self.bot.database.get_value(
                user_id, guild_id, "fishing", "revenue"
            )[0]

            # Calculate new fishing stats
            new_caught = caught + 1
            new_revenue = revenue + random_fish["price"]

            # Update fishing stats in database
            self.bot.database.set_value(
                user_id, guild_id, "fishing", "caught", new_caught
            )
            self.bot.database.set_value(
                user_id, guild_id, "fishing", "revenue", new_revenue
            )

            # Get current cookie stats
            cookies_result = self.bot.database.get_value(
                user_id, guild_id, "cookies", "cookies, total, max"
            )
            current_cookies, total_cookies, max_cookies = cookies_result

            # Calculate new cookie values
            new_cookies = current_cookies + random_fish["price"]
            new_total = total_cookies + random_fish["price"]
            new_max = max(max_cookies, new_cookies)

            # Update cookie stats in database
            self.bot.database.set_value(
                user_id, guild_id, "cookies", "cookies", new_cookies
            )
            self.bot.database.set_value(
                user_id, guild_id, "cookies", "total", new_total
            )
            self.bot.database.set_value(
                user_id, guild_id, "cookies", "max", new_max
            )

            # Create success embed message
            embed = discord.Embed(
                title="You caught a fish!", color=discord.Color.green()
            )
            embed.set_image(
                url="https://media1.tenor.com/m/ZHze27YyLIkAAAAC/joel-spinning.gif"
            )
            embed.add_field(name="Type", value=random_fish["name"], inline=True)
            embed.add_field(
                name="Price",
                value=f"{random_fish['price']} cookies",
                inline=True,
            )

            await interaction.response.send_message(embed=embed)
        else:
            # Get current dry streak stats
            current_streak = self.bot.database.get_value(
                user_id, guild_id, "fishing", "streak"
            )[0]
            longest_streak = self.bot.database.get_value(
                user_id, guild_id, "fishing", "longest_streak"
            )[0]

            # Calculate new streak values
            new_streak = current_streak + 1
            new_longest_streak = max(longest_streak, new_streak)

            # Update streak stats in database
            self.bot.database.set_value(
                user_id, guild_id, "fishing", "streak", new_streak
            )
            self.bot.database.set_value(
                user_id,
                guild_id,
                "fishing",
                "longest_streak",
                new_longest_streak,
            )

            # Create failure embed message
            embed = discord.Embed(
                title="Tough luck!", color=discord.Color.red()
            )
            embed.add_field(
                name="Current dry streak",
                value=f"{new_streak} failed catches",
                inline=True,
            )
            embed.add_field(
                name="Longest dry streak",
                value=f"{new_longest_streak} failed catches",
                inline=True,
            )
            await interaction.response.send_message(embed=embed)

    @app_commands.command()
    async def shop(self, interaction: discord.Interaction) -> None:
        """Check shop prices!"""
        await interaction.response.send_message("Shop not implemented")

    @app_commands.command()
    async def buy(self, interaction: discord.Interaction) -> None:
        """Buy from the shop!"""
        await interaction.response.send_message("Buy not implemented")

    @cast.error
    async def on_cast_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ) -> None:
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(str(error), ephemeral=True)


async def setup(bot: DiscordBot) -> None:
    await bot.add_cog(Fish(bot, catch_chance=0.25))
