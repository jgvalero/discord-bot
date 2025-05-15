import random

import discord
from discord import app_commands
from discord.ext import commands


class Casino(commands.GroupCog):
    def __init__(self, bot):
        self.bot = bot

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

        user_cookies = self.bot.database.get_value(
            user_id, guild_id, "cookies", "cookies"
        )[0]
        if user_cookies < wager:
            return await interaction.response.send_message(
                "You don't have enough cookies to make this wager!"
            )
        else:
            self.bot.database.set_value(
                interaction.user.id,
                interaction.guild.id,
                "cookies",
                "cookies",
                user_cookies - wager,
            )

        SYMBOLS = ["🍉", "🍊", "🍋", "🍌", "🍒"]
        wheel1 = random.choice(SYMBOLS)
        wheel2 = random.choice(SYMBOLS)
        wheel3 = random.choice(SYMBOLS)

        def evaluate_slots(wheel1, wheel2, wheel3):
            if wheel1 == wheel2 == wheel3:
                if interaction.guild:
                    payout = wager * 100
                    self.bot.database.set_value(
                        interaction.user.id,
                        interaction.guild.id,
                        "cookies",
                        "cookies",
                        user_cookies + payout,
                    )
                    return f"You won! Payout: {payout}"
            else:
                return "Tough luck!"

        await interaction.response.send_message(
            f"{wheel1} | {wheel2} | {wheel3}... {evaluate_slots(wheel1, wheel2, wheel3)}"
        )


async def setup(bot):
    await bot.add_cog(Casino(bot))
