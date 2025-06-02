import asyncio

import discord
import yt_dlp
from discord import app_commands
from discord.ext import commands

# Suppress noise about console usage from errors
yt_dlp.utils.bug_reports_message = lambda **kwargs: ""


ytdl_format_options = {
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

ffmpeg_options = {
    "options": "-vn",
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get("title")
        self.url = data.get("url")

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(url, download=not stream)
        )

        if "entries" in data:
            # take first item from a playlist
            data = data["entries"][0]

        filename = data["url"] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="join", description="Joins a voice channel")
    async def join(
        self, interaction: discord.Interaction, channel: discord.VoiceChannel
    ):
        """Joins a voice channel"""

        if interaction.guild.voice_client is not None:
            await interaction.guild.voice_client.move_to(channel)
            await interaction.response.send_message(f"Moved to {channel.name}")
        else:
            await channel.connect()
            await interaction.response.send_message(f"Joined {channel.name}")

    @app_commands.command(
        name="play", description="Plays a file from the local filesystem"
    )
    async def play(self, interaction: discord.Interaction, query: str):
        """Plays a file from the local filesystem"""

        await self.ensure_voice(interaction)

        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(query))
        interaction.guild.voice_client.play(
            source, after=lambda e: print(f"Player error: {e}") if e else None
        )

        await interaction.response.send_message(f"Now playing: {query}")

    @app_commands.command(
        name="youtube", description="Plays from a URL (YouTube and other sites)"
    )
    async def yt(self, interaction: discord.Interaction, url: str):
        """Plays from a url (almost anything yt_dlp supports)"""

        await self.ensure_voice(interaction)
        await interaction.response.defer()

        try:
            player = await YTDLSource.from_url(url, loop=self.bot.loop)
            interaction.guild.voice_client.play(
                player, after=lambda e: print(f"Player error: {e}") if e else None
            )
            await interaction.followup.send(f"Now playing: {player.title}")
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}")

    @app_commands.command(
        name="stream", description="Streams from a URL without downloading"
    )
    async def stream(self, interaction: discord.Interaction, url: str):
        """Streams from a url (same as yt, but doesn't predownload)"""

        await self.ensure_voice(interaction)
        await interaction.response.defer()

        try:
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            interaction.guild.voice_client.play(
                player, after=lambda e: print(f"Player error: {e}") if e else None
            )
            await interaction.followup.send(f"Now playing: {player.title}")
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}")

    @app_commands.command(name="volume", description="Changes the player's volume")
    @app_commands.describe(volume="Volume percentage (0-100)")
    async def volume(self, interaction: discord.Interaction, volume: int):
        """Changes the player's volume"""

        if interaction.guild.voice_client is None:
            return await interaction.response.send_message(
                "Not connected to a voice channel."
            )

        if not (0 <= volume <= 100):
            return await interaction.response.send_message(
                "Volume must be between 0 and 100."
            )

        interaction.guild.voice_client.source.volume = volume / 100
        await interaction.response.send_message(f"Changed volume to {volume}%")

    @app_commands.command(
        name="stop", description="Stops playing and disconnects from voice"
    )
    async def stop(self, interaction: discord.Interaction):
        """Stops and disconnects the bot from voice"""

        if interaction.guild.voice_client is None:
            return await interaction.response.send_message(
                "Not connected to a voice channel."
            )

        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("Disconnected from voice channel.")

    @app_commands.command(name="pause", description="Pauses the current audio")
    async def pause(self, interaction: discord.Interaction):
        """Pauses the current audio"""

        if interaction.guild.voice_client is None:
            return await interaction.response.send_message(
                "Not connected to a voice channel."
            )

        if interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.pause()
            await interaction.response.send_message("Paused audio.")
        else:
            await interaction.response.send_message("Nothing is currently playing.")

    @app_commands.command(name="resume", description="Resumes the paused audio")
    async def resume(self, interaction: discord.Interaction):
        """Resumes the paused audio"""

        if interaction.guild.voice_client is None:
            return await interaction.response.send_message(
                "Not connected to a voice channel."
            )

        if interaction.guild.voice_client.is_paused():
            interaction.guild.voice_client.resume()
            await interaction.response.send_message("Resumed audio.")
        else:
            await interaction.response.send_message("Audio is not paused.")

    async def ensure_voice(self, interaction: discord.Interaction):
        if interaction.guild.voice_client is None:
            if interaction.user.voice:
                await interaction.user.voice.channel.connect()
            else:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "You are not connected to a voice channel."
                    )
                else:
                    await interaction.followup.send(
                        "You are not connected to a voice channel."
                    )
                raise commands.CommandError("Author not connected to a voice channel.")
        elif interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.stop()


async def setup(bot):
    await bot.add_cog(Music(bot))
