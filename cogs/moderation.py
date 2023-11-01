import discord
from discord.ext import commands


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Ban command
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None, alert=True):
        await member.ban(reason=reason)

        if alert:
            await ctx.send(f"Banned {member.mention}")

    # Kick command
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None, alert=True):
        await member.kick(reason=reason)

        if alert:
            await ctx.send(f"Kicked {member.mention}")

    # Clear command
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount=5):
        await ctx.channel.purge(limit=amount)

    # Change nickname command
    @commands.command()
    @commands.has_permissions(manage_nicknames=True)
    async def nick(self, ctx, member: discord.Member, *, name=None, alert=True):
        await member.edit(nick=name)

        if alert:
            await ctx.send(f"Changed {member.mention}'s nickname to {name}")


async def setup(bot):
    await bot.add_cog(Moderation(bot))
