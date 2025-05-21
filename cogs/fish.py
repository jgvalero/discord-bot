import random
from typing import Literal

import discord
import tomllib
from discord import app_commands
from discord.ext import commands

from main import DiscordBot
from utils.money import Money


class Fish(commands.GroupCog):
    def __init__(self, bot: DiscordBot) -> None:
        self.bot = bot
        self.money = Money(bot.database)

        with open("config.toml", "rb") as f:
            self.config = tomllib.load(f)["fishing"]
            self.fishes = self.config["fish"]
            self.catch_chance = self.config["catch_chance"]

    @app_commands.command()
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.describe(use_bait="Use bait to guarantee a catch")
    async def cast(
        self, interaction: discord.Interaction, use_bait: bool = False
    ) -> None:
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

        # Get current bait count
        bait_count = self.bot.database.get_value(user_id, guild_id, "fishing", "bait")[
            0
        ]

        # Check if user wants to use bait and has any
        if use_bait:
            if bait_count <= 0:
                await interaction.response.send_message(
                    "You don't have any bait! Buy some from the shop with `/fish shop`",
                    ephemeral=True,
                )
                return
            # Consume one bait
            new_bait_count = bait_count - 1
            self.bot.database.set_value(
                user_id, guild_id, "fishing", "bait", new_bait_count
            )
        else:
            new_bait_count = bait_count

        # Increment the total fishing attempts counter
        attempts = self.bot.database.get_value(
            user_id, guild_id, "fishing", "attempts"
        )[0]
        self.bot.database.set_value(
            user_id, guild_id, "fishing", "attempts", attempts + 1
        )

        # Determine if the cast was successful based on catch chance or bait
        if use_bait or random.random() < self.catch_chance:
            # Reset dry streak on successful catch
            self.bot.database.set_value(user_id, guild_id, "fishing", "streak", 0)

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
                user_id, guild_id, "cookies", "cookies, total_earned, max"
            )
            current_cookies, total_cookies, max_cookies = cookies_result

            # Calculate new cookie values
            new_cookies = current_cookies + random_fish["price"]
            new_total = total_cookies + random_fish["price"]
            new_max = max(max_cookies, new_cookies)

            # Update cookie stats in database
            self.money.earn(user_id, guild_id, random_fish["price"])

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
            if use_bait:
                embed.add_field(
                    name="Bait Used",
                    value=f"Remaining bait: {new_bait_count}",
                    inline=False,
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
            embed = discord.Embed(title="Tough luck!", color=discord.Color.red())
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
        embed = discord.Embed(
            title="Big Dawg's Fishing Shop",
            description="Buy items to improve your fishing! No refunds!",
            color=discord.Color.blue(),
        )

        embed.add_field(
            name="Big Dawg's Delectable Bait - 50 cookies",
            value="Guarantees a catch on your next cast! Safe for human consumption!",
            inline=False,
        )

        # Get user's current bait count
        if interaction.guild:
            bait_count = self.bot.database.get_value(
                str(interaction.user.id),
                str(interaction.guild.id),
                "fishing",
                "bait",
            )[0]
            embed.add_field(
                name="Your Bait",
                value=f"You currently have {bait_count} bait",
                inline=False,
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.describe(
        item="Choose an item to buy", amount="How many items to buy (1-100)"
    )
    async def buy(
        self,
        interaction: discord.Interaction,
        item: Literal["Big Dawg's Delectable Bait"],
        amount: app_commands.Range[int, 1, 100] = 1,
    ) -> None:
        """Buy items from the shop!"""
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server!", ephemeral=True
            )
            return

        shop_items = {
            "Big Dawg's Delectable Bait": {
                "price": 50,
                "name": "Bait",
                "value": "bait",
            }
        }

        if item not in shop_items:
            await interaction.response.send_message(
                "Invalid item! Use `/fish shop` to see available items.",
                ephemeral=True,
            )
            return

        item_data = shop_items[item]
        total_cost = item_data["price"] * amount

        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild.id)

        if not self.money.lose(user_id, guild_id, total_cost):
            return await interaction.response.send_message(
                f"You don't have enough cookies! You need {total_cost} cookies, but you only have {self.money.get_money(user_id, guild_id)}.",
                ephemeral=True,
            )

        current_bait = self.bot.database.get_value(
            user_id, guild_id, "fishing", "bait"
        )[0]
        self.bot.database.set_value(
            user_id, guild_id, "fishing", "bait", current_bait + amount
        )

        await interaction.response.send_message(
            f"You just bought {amount} {item_data['name']} for {total_cost} cookies! You're not gonna regret it! You now have {self.money.get_money(user_id, guild_id)} cookies and {current_bait + amount} bait!"
        )

    @cast.error
    async def on_cast_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ) -> None:
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(str(error), ephemeral=True)


async def setup(bot: DiscordBot) -> None:
    await bot.add_cog(Fish(bot))
