import discord
from discord import app_commands
from discord.ext import commands

class Fish(commands.GroupCog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command()
    async def cast(self, interaction: discord.Interaction):
        """CAST! CAST! CAST!"""
        await interaction.response.send_message("Cast not implemented")

    @app_commands.command()
    async def shop(self, interaction: discord.Interaction):
        """Check shop prices!"""
        await interaction.response.send_message("Shop not implemented")

    @app_commands.command()
    async def buy(self, interaction: discord.Interaction):
        """Buy from the shop!"""
        await interaction.response.send_message("Buy not implemented")

async def setup(bot):
    await bot.add_cog(Fish(bot))
