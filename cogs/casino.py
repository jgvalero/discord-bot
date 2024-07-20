import discord
from discord.ext import commands
from discord import app_commands

import random

class Casino(commands.GroupCog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command()
    async def slots(self, interaction: discord.Interaction, amount: int = 1):
        """Play some slots!"""
        SYMBOLS = ["🍉", "🍊", "🍋", "🍌", "🍒"]
        wheel1 = random.choice(SYMBOLS)
        wheel2 = random.choice(SYMBOLS)
        wheel3 = random.choice(SYMBOLS)

        if interaction.guild:
            await interaction.response.send_message(f"{wheel1} | {wheel2} | {wheel3}")

async def setup(bot):
    await bot.add_cog(Casino(bot))
