from discord.ext import commands

import random


class Cookies(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def fish(self, ctx):
        num = random.randint(0, 9)
        if num == 0:
            await ctx.send("You caught a fish!")
        else:
            await ctx.send("Tough luck!")


async def setup(bot):
    await bot.add_cog(Cookies(bot))
