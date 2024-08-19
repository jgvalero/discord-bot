import random

import discord
from discord import app_commands
from discord.ext import commands

class Fish(commands.GroupCog):
    def __init__(self, bot, catch_chance: float):
        self.bot = bot
        self.catch_chance = catch_chance

    @app_commands.command()
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.guild_id, i.user.id))
    async def cast(self, interaction: discord.Interaction):
        """CAST! CAST! CAST!"""
        if random.random() < self.catch_chance:
            await interaction.response.send_message("You caught a fish!")
        else:
            await interaction.response.send_message("Tough luck!")

    @app_commands.command()
    async def shop(self, interaction: discord.Interaction):
        """Check shop prices!"""
        await interaction.response.send_message("Shop not implemented")

    @app_commands.command()
    async def buy(self, interaction: discord.Interaction):
        """Buy from the shop!"""
        await interaction.response.send_message("Buy not implemented")

    @cast.error
    async def on_cast_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(str(error), ephemeral=True)

async def setup(bot):
    await bot.add_cog(Fish(bot, catch_chance=0.25))
