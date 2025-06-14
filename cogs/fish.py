import random
from typing import Dict, List, Optional, Tuple

import discord
import tomllib
from discord import app_commands
from discord.ext import commands

from main import DiscordBot
from models.fishing import (
    Fish,
    FishingSettings,
    FishingStats,
    FishingStatsItems,
    Rarity,
    Rod,
)
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

    def _calculate_catch_chance(
        self, user_stats: FishingStats, rod: Optional[Rod] = None
    ) -> float:
        catch_chance: float = self.settings.base_catch_chance * (
            1 + (user_stats.level * self.settings.level_modifier)
        )

        if rod:
            catch_chance *= 1 + rod.modifier

        return catch_chance

    def _choose_fish(self) -> Tuple[Fish, Rarity]:
        rarity: Rarity = random.choices(
            self.settings.rarity,
            weights=[rarity.probability for rarity in self.settings.rarity],
        )[0]

        fishes: List[Fish] = []
        for fish in self.settings.fish:
            if fish.rarity == rarity.name:
                fishes.append(fish)

        return (random.choice(fishes), rarity)

    def _get_current_rod(self, user_id: int, guild_id: int) -> Rod:
        for rod in self.settings.rod:
            item: FishingStatsItems = FishingStatsItems(
                user_id,
                guild_id,
                self.bot.database,
                "rod",
                rod.name,
                "owned",
            )

            if item.value == 2:
                return rod

        item: FishingStatsItems = FishingStatsItems(
            user_id,
            guild_id,
            self.bot.database,
            "rod",
            self.settings.rod[0].name,
            "owned",
        )
        item.value = 2
        return self.settings.rod[0]

    @app_commands.command()
    async def rarity(self, interaction: discord.Interaction):
        """Shows the rarity types!"""

        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server!", ephemeral=True
            )
            return

        embed: discord.Embed = discord.Embed(
            title="Fish Rarity", color=discord.Color.blue()
        )

        for rarity in self.settings.rarity:
            value = f"Price: {rarity.price}\n"
            value += f"Probability: {rarity.probability:.0%}"
            embed.add_field(name=rarity.name, value=value, inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    async def fish(self, interaction: discord.Interaction):
        """Shows the fishes!"""

        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server!", ephemeral=True
            )
            return

        embed: discord.Embed = discord.Embed(title="Fish", color=discord.Color.blue())

        for fish in self.settings.fish:
            value = f"Weight: {fish.weight} pounds\n"
            value += f"Rarity: {fish.rarity}"
            embed.add_field(name=fish.name, value=value, inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    async def rod(self, interaction: discord.Interaction, select: Optional[int] = None):
        """Shows the rods! You can also equip or buy them here!"""

        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server!", ephemeral=True
            )
            return

        user_id: int = interaction.user.id
        guild_id: int = interaction.guild.id

        if select:
            for rod in self.settings.rod:
                item: FishingStatsItems = FishingStatsItems(
                    user_id,
                    guild_id,
                    self.bot.database,
                    "rod",
                    rod.name,
                    "owned",
                )

                if item.value == 2:
                    item.value = 1

            selected_rod: Rod = self.settings.rod[select - 1]
            item: FishingStatsItems = FishingStatsItems(
                user_id, guild_id, self.bot.database, "rod", selected_rod.name, "owned"
            )

            if item.value == 0:
                if not self.money.lose(user_id, guild_id, selected_rod.price):
                    return await interaction.response.send_message(
                        f"You don't have enough cookies to buy the {selected_rod.name}!"
                    )
                else:
                    item.value = 2
                    return await interaction.response.send_message(
                        f"You have purchased and equipped the {selected_rod.name} for {selected_rod.price} cookies!"
                    )
            else:
                item.value = 2
                return await interaction.response.send_message(
                    f"You have equipped the {selected_rod.name}!"
                )

        else:
            embed: discord.Embed = discord.Embed(
                title="Rods", color=discord.Color.blue()
            )

            for i, rod in enumerate(self.settings.rod):
                value = f"Price: {rod.price} cookies\n"
                value += f"Effect: Increases catch chance by {rod.modifier:.0%}"
                field_name = f"{i + 1}. {rod.name}"

                if i == 0:
                    field_name += " [Default]"

                item: FishingStatsItems = FishingStatsItems(
                    user_id, guild_id, self.bot.database, "rod", rod.name, "owned"
                )

                if item.value == 2:
                    field_name += " [Equipped]"
                elif item.value == 1:
                    field_name += " [Owned]"

                embed.add_field(name=field_name, value=value, inline=False)

            await interaction.response.send_message(embed=embed)

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
        rod: Rod = self._get_current_rod(user_id, guild_id)

        embed: discord.Embed = discord.Embed(
            title=f"{member.display_name}'s Fishing Stats!",
            color=discord.Color.blue(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(
            name="Total Fish Caught",
            value=f"{user_stats.total_fish_caught} fish",
            inline=False,
        )
        embed.add_field(
            name="Total Weight", value=f"{user_stats.total_weight} pounds", inline=False
        )
        embed.add_field(
            name="Total Value", value=f"{user_stats.total_value} cookies", inline=False
        )
        embed.add_field(name="Level", value=user_stats.level, inline=False)
        embed.add_field(
            name="Experience",
            value=f"{user_stats.experience}/{self.settings.experience}",
            inline=False,
        )
        embed.add_field(
            name="Catch Chance",
            value=f"{self._calculate_catch_chance(user_stats, rod) * 100:.2f}%",
        )

        fish_stats: str = ""
        for fish in self.settings.fish:
            fish_item: FishingStatsItems = FishingStatsItems(
                user_id, guild_id, self.bot.database, "fish", fish.name, "caught"
            )
            fish_stats += f"{fish.name}: {fish_item.value}\n"
        embed.add_field(name="Fish Caught", value=fish_stats, inline=False)

        embed.add_field(name="Current Rod", value=rod.name, inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.guild_id, i.user.id))
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
        attempt_successful: bool = attempt <= self._calculate_catch_chance(
            user_stats, self._get_current_rod(user_id, guild_id)
        )

        if attempt_successful:
            # Choose random fish
            fish: Tuple[Fish, Rarity] = self._choose_fish()

            fish_stats: FishingStatsItems = FishingStatsItems(
                user_id, guild_id, self.bot.database, "fish", fish[0].name, "caught"
            )

            # Update stats
            user_stats.total_fish_caught += 1
            user_stats.total_weight += fish[0].weight
            user_stats.total_value += fish[1].price
            user_stats.experience += 1
            fish_stats.value += 1
            self.money.earn(user_id, guild_id, fish[1].price)

            # Create success embed message
            embed: discord.Embed = discord.Embed(
                title=f"{interaction.user.display_name} caught a fish!",
                color=discord.Color.green(),
            )
            embed.add_field(name="Type", value=fish[0].name, inline=False)
            embed.add_field(
                name="Weight",
                value=f"{fish[0].weight} pounds",
                inline=False,
            )
            embed.add_field(
                name="Price",
                value=f"{fish[1].price} cookies",
                inline=False,
            )
            embed.add_field(
                name="Rarity",
                value=f"{fish[1].name}",
                inline=False,
            )

            if user_stats.experience == self.settings.experience:
                user_stats.level += 1
                user_stats.experience = 0
                embed.add_field(
                    name="Status",
                    value=f"Leveled up! [{user_stats.level}]",
                    inline=False,
                )

            await interaction.response.send_message(embed=embed)
        else:
            # Create failure embed message
            embed: discord.Embed = discord.Embed(
                title="Tough luck!", color=discord.Color.red()
            )

            await interaction.response.send_message(embed=embed)

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
