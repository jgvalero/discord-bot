import asyncio
from collections import deque
from typing import Any, Dict, Optional, cast

import discord
import yt_dlp
from discord import app_commands
from discord.ext import commands

# Suppress noise about console usage from errors
yt_dlp.utils.bug_reports_message = lambda **kwargs: ""


ytdl_format_options: Dict[str, Any] = {
    "format": "bestaudio/best",
    "outtmpl": "./data/music/%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options: Dict[str, str] = {
    "options": "-vn",
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(
        self, source: discord.AudioSource, *, data: Dict[str, Any], volume: float = 0.2
    ):
        super().__init__(source, volume)
        self.data = data
        self.title: Optional[str] = data.get("title")
        self.url: Optional[str] = data.get("url")

    @classmethod
    async def from_url(
        cls,
        url: str,
        *,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        stream: bool = False,
    ) -> "YTDLSource":
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(url, download=not stream)
        )

        if data is None:
            raise ValueError("Could not extract info from URL")

        if "entries" in data and data["entries"]:
            # take first item from a playlist
            data = data["entries"][0]

        filename = data["url"] if stream else ytdl.prepare_filename(data)
        return cls(
            discord.FFmpegPCMAudio(filename, before_options=ffmpeg_options["options"]),
            data=data,
        )


class Voice(commands.GroupCog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_queue: deque[YTDLSource] = deque()

    @app_commands.command()
    async def join(
        self, interaction: discord.Interaction, channel: discord.VoiceChannel
    ) -> None:
        """Joins a voice channel!"""

        if not interaction.guild:
            await interaction.response.send_message(
                "This command can only be used in a server!", ephemeral=True
            )
            return

        if interaction.guild.voice_client is not None:
            voice_client = cast(discord.VoiceClient, interaction.guild.voice_client)
            await voice_client.move_to(channel)
            await interaction.response.send_message(f"Moved to {channel.name}!")
        else:
            await channel.connect()
            await interaction.response.send_message(f"Joined {channel.name}!")

    # @app_commands.command()
    async def play_file(self, interaction: discord.Interaction, query: str) -> None:
        """Plays a file from the local filesystem!"""

        if not interaction.guild:
            await interaction.response.send_message(
                "This command can only be used in a server!", ephemeral=True
            )
            return

        await self.ensure_voice(interaction)

        if interaction.guild.voice_client is None:
            return

        voice_client = cast(discord.VoiceClient, interaction.guild.voice_client)
        source = discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(query, before_options=ffmpeg_options["options"])
        )
        voice_client.play(
            source,
            after=lambda e: (
                self.play_next(interaction.guild) if interaction.guild else None
            ),
        )

        if not interaction.response.is_done():
            await interaction.response.send_message(f"Now playing: {query}!")

    @app_commands.command()
    async def play(self, interaction: discord.Interaction, query: str) -> None:
        """Plays from a url or search query!"""

        if not interaction.guild:
            await interaction.response.send_message(
                "This command can only be used in a server!", ephemeral=True
            )
            return

        await self.ensure_voice(interaction)

        if interaction.guild.voice_client is None:
            return

        await interaction.response.defer()

        try:
            player = await YTDLSource.from_url(query, loop=self.bot.loop)
            voice_client = cast(discord.VoiceClient, interaction.guild.voice_client)

            if voice_client.is_playing() or voice_client.is_paused():
                self.voice_queue.append(player)
                await interaction.followup.send(
                    f"Added to queue: {player.title}! (Position: {len(self.voice_queue)})"
                )
            else:
                voice_client.play(
                    player,
                    after=lambda e: (
                        self.play_next(interaction.guild) if interaction.guild else None
                    ),
                )
                await interaction.followup.send(f"Now playing: {player.title}!")
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}!")

    # @app_commands.command()
    async def stream(self, interaction: discord.Interaction, url: str) -> None:
        """Streams from a url or search query!"""

        if not interaction.guild:
            await interaction.response.send_message(
                "This command can only be used in a server!", ephemeral=True
            )
            return

        await self.ensure_voice(interaction)

        if interaction.guild.voice_client is None:
            return

        await interaction.response.defer()

        try:
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            voice_client = cast(discord.VoiceClient, interaction.guild.voice_client)
            voice_client.play(
                player,
                after=lambda e: (
                    self.play_next(interaction.guild) if interaction.guild else None
                ),
            )
            await interaction.followup.send(f"Now playing: {player.title}!")
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}!")

    @app_commands.command()
    @app_commands.describe(volume="Volume percentage (0-100)")
    async def volume(self, interaction: discord.Interaction, volume: int) -> None:
        """Changes the player's volume!"""

        if not interaction.guild:
            await interaction.response.send_message(
                "This command can only be used in a server!", ephemeral=True
            )
            return

        if interaction.guild.voice_client is None:
            await interaction.response.send_message("Not connected to a voice channel!")
            return

        if not (0 <= volume <= 100):
            await interaction.response.send_message("Volume must be between 0 and 100!")
            return

        voice_client = cast(discord.VoiceClient, interaction.guild.voice_client)
        if (
            hasattr(voice_client, "source")
            and voice_client.source
            and isinstance(voice_client.source, discord.PCMVolumeTransformer)
        ):
            voice_client.source.volume = volume / 100
            await interaction.response.send_message(f"Changed volume to {volume}%!")
        else:
            await interaction.response.send_message(
                "No audio source is currently playing or volume control not available!"
            )

    @app_commands.command()
    async def stop(self, interaction: discord.Interaction) -> None:
        """Stops playing and disconnects from voice!"""

        if not interaction.guild:
            await interaction.response.send_message(
                "This command can only be used in a server!", ephemeral=True
            )
            return

        if interaction.guild.voice_client is None:
            await interaction.response.send_message("Not connected to a voice channel!")
            return

        voice_client = cast(discord.VoiceClient, interaction.guild.voice_client)
        await voice_client.disconnect()
        await interaction.response.send_message("Disconnected from voice channel!")

    @app_commands.command()
    async def pause(self, interaction: discord.Interaction) -> None:
        """Pauses the current audio!"""

        if not interaction.guild:
            await interaction.response.send_message(
                "This command can only be used in a server!", ephemeral=True
            )
            return

        if interaction.guild.voice_client is None:
            await interaction.response.send_message("Not connected to a voice channel!")
            return

        voice_client = cast(discord.VoiceClient, interaction.guild.voice_client)
        if voice_client.is_playing():
            voice_client.pause()
            await interaction.response.send_message("Paused audio!")
        else:
            await interaction.response.send_message("Nothing is currently playing!")

    @app_commands.command()
    async def resume(self, interaction: discord.Interaction) -> None:
        """Resumes the paused audio!"""

        if not interaction.guild:
            await interaction.response.send_message(
                "This command can only be used in a server!", ephemeral=True
            )
            return

        if interaction.guild.voice_client is None:
            await interaction.response.send_message("Not connected to a voice channel!")
            return

        voice_client = cast(discord.VoiceClient, interaction.guild.voice_client)
        if voice_client.is_paused():
            voice_client.resume()
            await interaction.response.send_message("Resumed audio!")
        else:
            await interaction.response.send_message("Audio is not paused!")

    def play_next(self, guild: discord.Guild) -> None:
        """Plays the next song in the queue."""
        if not guild.voice_client:
            return

        voice_client = cast(discord.VoiceClient, guild.voice_client)

        if self.voice_queue:
            next_player = self.voice_queue.popleft()
            voice_client.play(next_player, after=lambda e: self.play_next(guild))

    @app_commands.command()
    async def skip(self, interaction: discord.Interaction) -> None:
        """Skips the current song!"""

        if not interaction.guild:
            await interaction.response.send_message(
                "This command can only be used in a server!", ephemeral=True
            )
            return

        if interaction.guild.voice_client is None:
            await interaction.response.send_message("Not connected to a voice channel!")
            return

        voice_client = cast(discord.VoiceClient, interaction.guild.voice_client)
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()
            await interaction.response.send_message("Skipped current song!")
        else:
            await interaction.response.send_message("Nothing is currently playing!")

    @app_commands.command(name="queue")
    async def show_queue(self, interaction: discord.Interaction) -> None:
        """Shows the current queue!"""

        if not interaction.guild:
            await interaction.response.send_message(
                "This command can only be used in a server!", ephemeral=True
            )
            return

        if not self.voice_queue:
            await interaction.response.send_message("The queue is empty!")
            return

        queue_list = []
        for i, player in enumerate(self.voice_queue, 1):
            queue_list.append(f"{i}. {player.title}")

        queue_text = "\n".join(queue_list[:10])
        if len(self.voice_queue) > 10:
            queue_text += f"\n... and {len(self.voice_queue) - 10} more"

        embed = discord.Embed(
            title="Music Queue", description=queue_text, color=0x89CD00
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    async def clear(self, interaction: discord.Interaction) -> None:
        """Clears the music queue!"""

        if not interaction.guild:
            await interaction.response.send_message(
                "This command can only be used in a server!", ephemeral=True
            )
            return

        if not self.voice_queue:
            await interaction.response.send_message("The queue is already empty!")
            return

        queue_size = len(self.voice_queue)
        self.voice_queue.clear()
        await interaction.response.send_message(
            f"Cleared {queue_size} songs from the queue!"
        )

    async def ensure_voice(self, interaction: discord.Interaction) -> None:
        if not interaction.guild:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "This command can only be used in a server!", ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "This command can only be used in a server!"
                )
            raise commands.CommandError("Command not used in a guild!")

        if interaction.guild.voice_client is None:
            member = cast(discord.Member, interaction.user)
            if member.voice and member.voice.channel:
                await member.voice.channel.connect()
            else:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "You are not connected to a voice channel!"
                    )
                else:
                    await interaction.followup.send(
                        "You are not connected to a voice channel!"
                    )
                raise commands.CommandError("Author not connected to a voice channel!")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Voice(bot))
