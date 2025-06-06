import random
from typing import Dict, Literal

import discord
import tomllib
from discord import app_commands
from discord.ext import commands

from main import DiscordBot
from models.fishing import Fish, FishingSettings, FishingStats
from utils.money import Money


@app_commands.guild_only()
class Fishing(commands.GroupCog, group_name="fish"):
    def __init__(self, bot: DiscordBot) -> None:
        self.bot: DiscordBot = bot
        self.money: Money = Money(bot.database)
        self.settings: FishingSettings = self._load_settings()

    def _load_settings(self) -> FishingSettings:
        with open("config.toml", "rb") as f:
            raw: Dict = tomllib.load(f)["fishing"]
            return FishingSettings(**raw)

    @app_commands.command()
    async def stats(self, interaction: discord.Interaction, member: discord.User):
        """Check a member's fishing stats!"""

        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server!", ephemeral=True
            )
            return

        user_id: int = member.id
        guild_id: int = interaction.guild.id
        user_stats: FishingStats = FishingStats(user_id, guild_id, self.bot.database)

        embed: discord.Embed = discord.Embed(
            title=f"{member.display_name}'s Fishing Stats!",
            color=discord.Color.blue(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(
            name="Total Fish Caught", value=user_stats.total_fish_caught, inline=False
        )
        embed.add_field(
            name="Total Weight", value=user_stats.total_weight, inline=False
        )
        embed.add_field(name="Total Value", value=user_stats.total_value, inline=False)
        embed.add_field(name="Level", value=user_stats.level, inline=False)
        embed.add_field(name="Experience", value=user_stats.experience, inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.describe(use_bait="Use bait to guarantee a catch")
    async def cast(self, interaction: discord.Interaction) -> None:
        """CAST! CAST! CAST!"""

        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server!", ephemeral=True
            )
            return

        user_id: int = interaction.user.id
        guild_id: int = interaction.guild.id
        user_stats: FishingStats = FishingStats(user_id, guild_id, self.bot.database)

        # Calculate catch chance
        attempt: float = random.random()
        catch_chance: float = self.settings.base_catch_chance
        attempt_successful: bool = attempt <= catch_chance
        # TO-DO: Integrate experience

        if attempt_successful:
            # Select random fish
            fish: Fish = random.choices(
                self.settings.fish, weights=[fish.chance for fish in self.settings.fish]
            )[0]

            # Update stats
            user_stats.total_fish_caught += 1
            user_stats.total_weight += fish.weight
            user_stats.total_value += fish.price
            # TO-DO: Integrate level and experience

            # Create success embed message
            embed: discord.Embed = discord.Embed(
                title="You caught a fish!", color=discord.Color.green()
            )
            embed.add_field(name="Type", value=fish.name, inline=False)
            embed.add_field(
                name="Weight",
                value=f"{fish.weight} pounds",
                inline=True,
            )
            embed.add_field(
                name="Price",
                value=f"{fish.price} cookies",
                inline=True,
            )

            await interaction.response.send_message(embed=embed)
        else:
            # Create failure embed message
            embed: discord.Embed = discord.Embed(
                title="Tough luck!", color=discord.Color.red()
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
    await bot.add_cog(Fishing(bot))
