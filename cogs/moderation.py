import discord
from discord.ext import commands


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(manage_nicknames=True)
    async def changenick(self, ctx, member: discord.Member, nickname):
        print(f"Changed {str(member)}'s nickname to: {nickname}!")
        await member.edit(nick=nickname)


async def setup(bot):
    await bot.add_cog(Moderation(bot))
