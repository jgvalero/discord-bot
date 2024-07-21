import random

import discord
from discord import app_commands
from discord.ext import commands

from utils.database import Database


class Casino(commands.GroupCog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database("data/users.db")

    @app_commands.command()
    async def slots(self, interaction: discord.Interaction, amount: int = 1):
        """Play some slots!"""

        user_cookies = 0
        if interaction.guild:
            user_cookies = self.db.get_value(
                interaction.user.id, interaction.guild.id, "cookies"
            )
            if user_cookies < amount:
                return await interaction.response.send_message(
                    f"You don't have enough cookies to make this wager!"
                )
            else:
                self.db.set_value(
                    interaction.user.id,
                    interaction.guild.id,
                    "cookies",
                    user_cookies - amount,
                )

        SYMBOLS = ["🍉", "🍊", "🍋", "🍌", "🍒"]
        wheel1 = random.choice(SYMBOLS)
        wheel2 = random.choice(SYMBOLS)
        wheel3 = random.choice(SYMBOLS)

        def evaluate_slots(wheel1, wheel2, wheel3):
            if wheel1 == wheel2 == wheel3:
                if interaction.guild:
                    payout = amount * 10
                    self.db.set_value(
                        interaction.user.id,
                        interaction.guild.id,
                        "cookies",
                        payout * 10,
                    )
                    return f"You won! Payout: {payout}"
            else:
                return "Tough luck!"

        await interaction.response.send_message(
            f"{wheel1} | {wheel2} | {wheel3}... {evaluate_slots(wheel1, wheel2, wheel3)}"
        )


async def setup(bot):
    await bot.add_cog(Casino(bot))
