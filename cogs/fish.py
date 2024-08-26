import random
import json
import os

import discord
from discord import app_commands
from discord.ext import commands


class Fish(commands.GroupCog):
    def __init__(self, bot, catch_chance: float):
        self.bot = bot
        self.catch_chance = catch_chance
        if os.path.exists("data/fish.json"):
            with open("data/fish.json", "r") as f:
                self.fish = json.load(f)
        else:
            self.fish = {
                "name": "Joel",
                "price": 10,
                "chance": 100
            }

    @app_commands.command()
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.guild_id, i.user.id))
    async def cast(self, interaction: discord.Interaction) -> None:
        """CAST! CAST! CAST!"""
        if random.random() < self.catch_chance:
            embed = discord.Embed(title="You caught a fish!", color=discord.Color.green())
            embed.set_image(url="https://media1.tenor.com/m/ZHze27YyLIkAAAAC/joel-spinning.gif")
            embed.add_field(name="Type", value="Swag", inline=True)
            embed.add_field(name="Price", value="10 cookies", inline=True)

            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Tough luck!")

    @app_commands.command()
    async def shop(self, interaction: discord.Interaction) -> None:
        """Check shop prices!"""
        await interaction.response.send_message("Shop not implemented")

    @app_commands.command()
    async def buy(self, interaction: discord.Interaction) -> None:
        """Buy from the shop!"""
        await interaction.response.send_message("Buy not implemented")

    @cast.error
    async def on_cast_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(str(error), ephemeral=True)

async def setup(bot):
    await bot.add_cog(Fish(bot, catch_chance=1.0))
