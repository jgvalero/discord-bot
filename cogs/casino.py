import random

import discord
from discord import app_commands
from discord.ext import commands

from utils.money import Money


class Casino(commands.GroupCog):
    def __init__(self, bot):
        self.bot = bot
        self.money = Money(bot.database)

    @app_commands.command()
    async def slots(self, interaction: discord.Interaction, wager: int = 1):
        """Play some slots!"""

        # Ensure command is used in a server context
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server!", ephemeral=True
            )
            return

        # Get user and guild IDs for database operations
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild.id)

        if not self.money.lose(user_id, guild_id, wager):
            return await interaction.response.send_message(
                "You don't have enough cookies to make this wager!"
            )

        SYMBOLS = ["🍉", "🍊", "🍋", "🍌", "🍒"]
        wheel1 = random.choice(SYMBOLS)
        wheel2 = random.choice(SYMBOLS)
        wheel3 = random.choice(SYMBOLS)

        def evaluate_slots(wheel1, wheel2, wheel3):
            if wheel1 == wheel2 == wheel3:
                if interaction.guild:
                    payout = wager * 100
                    self.money.earn(user_id, guild_id, payout)
                    return f"You won! Payout: {payout}"
            else:
                return "Tough luck!"

        await interaction.response.send_message(
            f"{wheel1} | {wheel2} | {wheel3}... {evaluate_slots(wheel1, wheel2, wheel3)}"
        )


async def setup(bot):
    await bot.add_cog(Casino(bot))
