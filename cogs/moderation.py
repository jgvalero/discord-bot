import discord
import tomllib
from discord import app_commands
from discord.ext import commands


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        with open("config.toml", "rb") as f:
            self.config = tomllib.load(f)["moderation"]
            self.blacklisted_words = self.config["blacklisted_words"]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        content = message.content.lower()
        if any(word in content for word in self.blacklisted_words):
            await message.delete()
            await message.channel.send(
                f"{message.author.display_name}, that word is not allowed!"
            )

    # Ban command
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None, alert=True):
        """Bans a member from the server"""
        await member.ban(reason=reason)

        if alert:
            await ctx.send(f"Banned {member.display_name}")

    # Kick command
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None, alert=True):
        """Kicks a member from the server"""
        await member.kick(reason=reason)

        if alert:
            await ctx.send(f"Kicked {member.display_name}")

    # Clear command
    @app_commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, amount: int = 5):
        """Clears a number of messages from the channel"""
        await interaction.response.send_message(content="Purging!", ephemeral=True)
        await interaction.channel.purge(limit=amount)

    # Change nickname command
    @commands.command()
    @commands.has_permissions(manage_nicknames=True)
    async def nick(self, ctx, member: discord.Member, *, name=None, alert=True):
        """Changes a member's nickname"""
        await member.edit(nick=name)

        if alert:
            await ctx.send(f"Changed {member.display_name}'s nickname to {name}")


async def setup(bot):
    await bot.add_cog(Moderation(bot))
