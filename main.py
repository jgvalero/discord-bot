import discord
from discord.ext import commands
from discord import app_commands
import random
import os
import asyncio
import json

description = """Discord bot made by jgvalero! Work in progress..."""

with open("config.json") as config_file:
    config = json.load(config_file)


class MyBot(commands.Bot):
    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=discord.Object(id=config["guild_id"]))
        await self.tree.sync(guild=discord.Object(id=config["guild_id"]))


intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = MyBot(command_prefix="$", description=description, intents=intents)


# Load all cogs in cogs folder
async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")
            print(f"Loaded cogs.{filename[:-3]}")


@bot.event
async def on_ready():
    if bot.user:
        print(f"Logged in as {bot.user} (ID: {bot.user.id})")
        print("------")


# New Commands
@bot.command()
async def reload(ctx, extension):
    """Reloads cogs"""
    await bot.reload_extension(f"cogs.{extension}")
    await ctx.send(f"Reloaded {extension}!")


async def main():
    async with bot:
        await load_cogs()
        await bot.start(config["discord_token"])


asyncio.run(main())
