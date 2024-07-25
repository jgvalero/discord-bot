import asyncio
import random

import discord
from discord import app_commands
from discord.ext import commands

from utils.database import Database

COOLDOWN_TIME = 10
BAIT_PRICE = 50


class Fish(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database("data/users.db")

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def fish(self, ctx, bait: str = None):
        """Fish! If you use bait, you're guaranteed to catch a fish."""
        message_content = f"{ctx.author.display_name} is fishing"

        if bait is not None and bait.lower() == "bait":
            user_bait = self.db.get_value(ctx.author.id, ctx.guild.id, "bait")
            if user_bait < 1:
                return await ctx.send("You don't have any bait!")
            else:
                self.db.set_value(ctx.author.id, ctx.guild.id, "bait", user_bait - 1)
                message_content += " (with bait)"

        message = await ctx.send(message_content)
        for i in range(7):
            await asyncio.sleep(1)
            message_content += "."
            await message.edit(content=message_content)
        await asyncio.sleep(1)

        if bait is not None and bait.lower() == "bait" or random.randint(1, 10) == 1:
            fish_value = int((random.random() ** 2) * 100) + 1
            user_cookies = self.db.get_value(ctx.author.id, ctx.guild.id, "cookies")
            self.db.set_value(
                ctx.author.id, ctx.guild.id, "cookies", user_cookies + fish_value
            )

            most_valuable_fish = self.db.get_value(
                ctx.author.id, ctx.guild.id, "most_valuable_fish"
            )
            if fish_value > most_valuable_fish:
                self.db.set_value(
                    ctx.author.id, ctx.guild.id, "most_valuable_fish", fish_value
                )
                await ctx.send(
                    f"{ctx.author.display_name} caught a fish worth {fish_value} cookies! This is your most valuable catch!"
                )
            else:
                await ctx.send(
                    f"{ctx.author.display_name} caught a fish worth {fish_value} cookies!"
                )
        else:
            await ctx.send(f"Tough luck, {ctx.author.display_name}!")

    @app_commands.command()
    async def bait(self, interaction: discord.Interaction, amount: int = 1):
        f"""Buy bait! Costs {BAIT_PRICE} cookies per bait."""
        try:
            amount = int(amount)
        except ValueError:
            return await interaction.response.send_message("Invalid amount, enter a number!")

        amount = int(amount)
        cost = amount * BAIT_PRICE
        user_cookies = self.db.get_value(interaction.user.id, interaction.guild.id, "cookies")
        user_bait = self.db.get_value(interaction.user.id, interaction.guild.id, "bait")
        if user_cookies < cost:
            await interaction.response.send_message(
                f"You do not have enough cookies, {interaction.user.display_name}!"
            )
            return
        self.db.set_value(interaction.user.id, interaction.guild.id, "cookies", user_cookies - cost)
        self.db.set_value(interaction.user.id, interaction.guild.id, "bait", user_bait + amount)
        await interaction.response.send_message(
            f"{interaction.user.display_name} bought {amount} bait (${cost})! You now have {user_bait + amount} bait. New balance: {user_cookies - cost} cookies."
        )


async def setup(bot):
    await bot.add_cog(Fish(bot))
