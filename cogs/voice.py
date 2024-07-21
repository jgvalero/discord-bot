# TAKEN FROM https://github.com/Rapptz/discord.py/blob/v2.3.2/examples/basic_voice.py TO USE AS EXAMPLE (UNDER MIT LICENSE)

import asyncio
import json

import discord
import lyricsgenius
import yt_dlp
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import sys
import os

from utils.voting import Voting

if not load_dotenv():
    print("Could not locate .env!")
    sys.exit(1)

genius_token = os.getenv("GENIUS_TOKEN")


# Suppress noise about console usage from errors
yt_dlp.utils.bug_reports_message = lambda: ""
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

if genius_token:
    genius = lyricsgenius.Genius(genius_token)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.2):
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
        self.voting = Voting()
        self.song_queue = []

    @app_commands.command()
    async def join(self, interaction: discord.Interaction):
        # TO-DO: ADD ABILITY TO SPECIFY CHANNEL
        # TO-DO: FIX UNKNOWN

        """Joins a voice channel"""

        voice = interaction.guild

        if interaction.user.voice is None or interaction.user.voice.channel is None:
            return await interaction.response.send_message("You are not connected to a voice channel!")
        else:
            user_channel = interaction.user.voice.channel

        if voice is not None and voice.voice_client is not None:
            await voice.change_voice_state(channel=user_channel)
        else:
            await user_channel.connect()

        await interaction.response.send_message(f"Joined {user_channel}!")

    @commands.command()
    async def play_file(self, ctx, *, query):
        """Plays a file from the local filesystem"""

        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(query))
        ctx.voice_client.play(
            source, after=lambda e: print(f"Player error: {e}") if e else None
        )

        await ctx.send(f"Now playing: {query}")

    @commands.command()
    async def play(self, ctx, *, url):
        """Plays from a url (almost anything yt_dlp supports)"""

        async with ctx.typing():
            # Get the song
            player = await YTDLSource.from_url(url, loop=self.bot.loop)
            player.author = ctx.author
            self.song_queue.append(player)

            # Check if there is a song playing
            if ctx.voice_client.is_playing():
                return await ctx.send(f"Added {player.title} to queue!")

            # Play the song and check queue after
            ctx.voice_client.play(
                self.song_queue[0],
                after=lambda e: (
                    print(f"Player error: {e}") if e else self.check_queue(ctx)
                ),
            )

        await ctx.send(f"Now playing: {self.song_queue[0].title}!")

    @commands.command()
    async def stream(self, ctx, *, url):
        """Streams from a url (same as yt, but doesn't predownload)"""

        async with ctx.typing():
            # Get the song
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            self.song_queue.append(player)

            # Check if there is a song playing
            if ctx.voice_client.is_playing():
                return await ctx.send(f"Added {player.title} to queue!")

            # Play the song and check queue after
            ctx.voice_client.play(
                self.song_queue[0],
                after=lambda e: (
                    print(f"Player error: {e}") if e else self.check_queue(ctx)
                ),
            )

        await ctx.send(f"Now playing: {self.song_queue[0].title}!")

    @commands.command()
    async def volume(self, ctx, volume: int):
        """Changes the player's volume"""

        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        ctx.voice_client.source.volume = volume / 100
        await ctx.send(f"Changed volume to {volume}%")

    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""

        await ctx.voice_client.disconnect()

    @play_file.before_invoke
    @play.before_invoke
    @stream.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        # elif ctx.voice_client.is_playing():
        #     ctx.voice_client.stop()

    # New Commands
    @commands.command()
    async def skip(self, ctx):
        """Skips currently playing song"""
        if not ctx.voice_client.is_playing():
            return await ctx.send(f"There is no song playing!")

        # Get number of people in the voice channel
        num_people = len(ctx.voice_client.channel.members)
        self.voting.requiredVotes = num_people // 2

        # Check if the user is the one who requested the song
        if ctx.author == self.song_queue[0].author:
            ctx.voice_client.stop()
            await ctx.send(f"Skipped [by requester]!")
            self.voting.reset()
        else:
            # Check if the user has already voted
            if self.voting.addVote(ctx.author):
                await ctx.send(
                    f"Current votes: {self.voting.currentVotes}/{self.voting.requiredVotes}"
                )
            else:
                await ctx.send(f"You already voted!")

            # Check if the vote is done
            if self.voting.isDone():
                ctx.voice_client.stop()
                await ctx.send(f"Skipped [by vote]!")
                self.voting.reset()

    @commands.command()
    async def pause(self, ctx):
        """Pauses currently playing song"""
        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send(f"Paused")

    @commands.command()
    async def resume(self, ctx):
        """Resumes currently paused song"""
        if ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send(f"Resumed")

    @commands.command()
    async def queue(self, ctx):
        """Shows the music queue"""
        if not self.song_queue:
            return await ctx.send("The queue is empty!")

        queue_str = f"#1: {self.song_queue[0].title} requested by {self.song_queue[0].author} [Currently playing!]"

        for i in range(1, len(self.song_queue)):
            queue_str += f"\n#{i+1}: {self.song_queue[i].title} requested by {self.song_queue[i].author}"

        await ctx.send(queue_str)

    @commands.command()
    async def lyrics(self, ctx, *, query):
        if genius_token:
            [artist, song] = query.split(" - ")
            await ctx.send(genius.search_song(song, artist).lyrics)
        else:
            await ctx.send("You don't have a genius token! If you want to use this command make sure to add the genius token in the .env file!")

    # Functions
    def check_queue(self, ctx):
        self.song_queue.pop(0)

        if self.song_queue:
            ctx.voice_client.play(
                self.song_queue[0],
                after=lambda e: (
                    print(f"Player error: {e}") if e else self.check_queue(ctx)
                ),
            )


async def setup(bot):
    await bot.add_cog(Music(bot))
