import asyncio
import logging
import logging.handlers
import os
import sys
from typing import List, Optional

import discord
from aiohttp import ClientSession
from discord.ext import commands
from dotenv import load_dotenv

from utils.database import Database


class DiscordBot(commands.Bot):
    def __init__(
        self,
        *args,
        initial_extensions: List[str],
        database: Database,
        web_client: ClientSession,
        testing_guild_id: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.database = database
        self.web_client = web_client
        self.testing_guild_id = testing_guild_id
        self.initial_extensions = initial_extensions

    async def setup_hook(self) -> None:
        for extension in self.initial_extensions:
            await self.load_extension(f"cogs.{extension}")

        if self.testing_guild_id:
            guild = discord.Object(self.testing_guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)


async def main():
    logger = logging.getLogger("discord")
    logger.setLevel(logging.INFO)

    file_handler = logging.handlers.RotatingFileHandler(
        filename="discord.log",
        encoding="utf-8",
        maxBytes=32 * 1024 * 1024,
        backupCount=5,
    )
    dt_fmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(
        "[{asctime}] [{levelname:<8}] {name}: {message}", dt_fmt, style="{"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if not load_dotenv():
        print("Could not locate .env!")
        sys.exit(1)
    token = os.environ["DISCORD_TOKEN"]
    guild_id = os.environ["GUILD_ID"]

    async with ClientSession() as our_client:
        with Database("data/users.db") as db:
            exts = ["casino", "cookies", "fish", "moderation", "voice"]
            intents = discord.Intents.default()
            intents.message_content = True
            intents.presences = True
            intents.members = True
            async with DiscordBot(
                command_prefix="$",
                database=db,
                web_client=our_client,
                initial_extensions=exts,
                intents=intents,
                testing_guild_id=int(guild_id),
            ) as bot:
                await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
