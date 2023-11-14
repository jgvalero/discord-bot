import discord
from discord.ext import commands
import random
import os
import asyncio
import json

description = """Discord bot made by jgvalero! Work in progress..."""

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="$", description=description, intents=intents)


# Load all cogs in cogs folder
async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")
            print(f"Loaded cogs.{filename[:-3]}")


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")


# New Commands
@bot.command()
async def reload(ctx, extension):
    """Reloads cogs"""
    await bot.reload_extension(f"cogs.{extension}")
    await ctx.send(f"Reloaded {extension}!")


async def main():
    with open("config.json") as config_file:
        parsed_json = json.load(config_file)

    async with bot:
        await load_cogs()
        await bot.start(parsed_json["discord_token"])


asyncio.run(main())
