import asyncio
import os

import discord
import lyricsgenius
import yt_dlp
from discord import app_commands
from discord.ext import commands

import utils.tts
from utils.money import Money
from utils.voting import Voting

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

        if data is None:
            raise TypeError()

        if "entries" in data:
            # take first item from a playlist
            data = data["entries"][0]

        filename = data["url"] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.song_queue = []
        self.money = Money(bot.database)

    @app_commands.command()
    async def join(self, interaction: discord.Interaction):
        # TO-DO: ADD ABILITY TO SPECIFY CHANNEL
        # TO-DO: FIX UNKNOWN
        # To-DO: REFINE THIS (MAYBE YOU DON'T EVEN NEED IT!)

        """Joins a voice channel"""

        user_channel = await self.ensure_voice(interaction)
        await interaction.response.send_message(f"Joined {user_channel}!")

    # @commands.command()
    # async def play_file(self, ctx, *, query):
    #     """Plays a file from the local filesystem"""

    #     source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(query))
    #     ctx.voice_client.play(
    #         source, after=lambda e: print(f"Player error: {e}") if e else None
    #     )

    #     await ctx.send(f"Now playing: {query}")

    @app_commands.command()
    async def play(self, interaction: discord.Interaction, query: str):
        # TO-DO: COMPLETE IMPLEMENTATION AND BEFORE INVOKE
        # TO-DO: THIS IS MESSY, MAYBE TAKE A GANDER
        """Plays a song!"""

        await self.ensure_voice(interaction)

        voice = interaction.client.voice_clients[0]

        async with interaction.channel.typing():
            await interaction.response.send_message("Fetching song...")
            # Get the song
            player = await YTDLSource.from_url(query, loop=self.bot.loop)
            player.author = interaction.user
            player.voting = Voting()
            self.song_queue.append(player)

            # Check if there is a song playing
            if voice.is_playing():
                return await interaction.followup.send(
                    f"Added {player.title} to queue!"
                )

            # Play the song and check queue after
            voice.play(
                self.song_queue[0],
                after=lambda e: (
                    print(f"Player error: {e}") if e else self.check_queue(interaction)
                ),
            )

        msg = await interaction.original_response()
        await msg.edit(content=f"Now playing: {self.song_queue[0].title}!")

    # @commands.command()
    # async def stream(self, ctx, *, url):
    #     """Streams from a url (same as yt, but doesn't predownload)"""

    #     async with ctx.typing():
    #         # Get the song
    #         player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
    #         self.song_queue.append(player)

    #         # Check if there is a song playing
    #         if ctx.voice_client.is_playing():
    #             return await ctx.send(f"Added {player.title} to queue!")

    #         # Play the song and check queue after
    #         ctx.voice_client.play(
    #             self.song_queue[0],
    #             after=lambda e: (
    #                 print(f"Player error: {e}") if e else self.check_queue(ctx)
    #             ),
    #         )

    #     await ctx.send(f"Now playing: {self.song_queue[0].title}!")

    @app_commands.command()
    async def volume(self, interaction: discord.Interaction, volume: int):
        """Changes the player's volume"""

        voice_client = interaction.client.voice_clients[0]

        if voice_client is None:
            return await interaction.response.send_message(
                "Not connected to a voice channel."
            )

        voice_client.source.volume = volume / 100
        await interaction.response.send_message(f"Changed volume to {volume}%")

    # @app_commands.command()
    # async def stop(self, interaction: discord.Interaction):
    #     """Stops and disconnects the bot from voice"""

    #     voice_client = interaction.client.voice_clients[0]

    #     await voice_client.disconnect()

    #     await interaction.response.send_message(f"We outta here!")

    #     # TO-DO: CLEAR QUEUE

    # TO-DO: FIX THIS!!!
    # @play_file.before_invoke
    # @play.before_invoke
    # @stream.before_invoke
    async def ensure_voice(self, interaction: discord.Interaction) -> str | None:
        voice = interaction.guild

        if interaction.user.voice is None or interaction.user.voice.channel is None:
            return await interaction.response.send_message(
                "You are not connected to a voice channel!"
            )
        else:
            user_channel = interaction.user.voice.channel

        if voice is not None and voice.voice_client is not None:
            await voice.change_voice_state(channel=user_channel)
        else:
            await user_channel.connect()

        return user_channel.name

        # voice_client = interaction.client.voice_clients[0]

        # if voice_client is None:
        #     if (
        #         isinstance(interaction.user, discord.Member)
        #         and interaction.user.voice
        #         and interaction.user.voice.channel
        #     ):
        #         await interaction.user.voice.channel.connect()
        #     else:
        #         await interaction.response.send_message(
        #             "You are not connected to a voice channel."
        #         )
        #         raise commands.CommandError("Author not connected to a voice channel.")
        # elif voice_client and voice_client.is_playing():
        #     voice_client.stop()

    @app_commands.command()
    async def skip(self, interaction: discord.Interaction):
        """Skips currently playing song"""

        voice_client = interaction.client.voice_clients[0]

        if not voice_client.is_playing():
            return await interaction.response.send_message("There is no song playing!")

        # Get number of people in the voice channel
        num_people = len(voice_client.channel.members)
        self.song_queue[0].voting.requiredVotes = num_people // 2

        # Check if the user is the one who requested the song
        if interaction.user == self.song_queue[0].author:
            voice_client.stop()
            await interaction.response.send_message("Skipped [by requester]!")
            self.song_queue[0].voting.reset()
        else:
            # Check if the user has already voted
            if self.song_queue[0].voting.addVote(interaction.user):
                await interaction.response.send_message(
                    f"Current votes: {self.song_queue[0].voting.currentVotes}/{self.song_queue[0].voting.requiredVotes}"
                )
            else:
                await interaction.response.send_message("You already voted!")

            # Check if the vote is done
            if self.song_queue[0].voting.isDone():
                voice_client.stop()
                await interaction.response.send_message("Skipped [by vote]!")

    @app_commands.command()
    async def pause(self, interaction: discord.Interaction):
        """Pauses currently playing song"""

        voice_client = interaction.client.voice_clients[0]

        if voice_client.is_playing():
            voice_client.pause()
            await interaction.response.send_message("Paused")

    @app_commands.command()
    async def resume(self, interaction: discord.Interaction):
        """Resumes currently paused song"""

        voice_client = interaction.client.voice_clients[0]

        if voice_client.is_paused():
            voice_client.resume()
            await interaction.response.send_message("Resumed")

    @app_commands.command()
    async def queue(self, interaction: discord.Interaction):
        """Shows the music queue"""

        if not self.song_queue:
            return await interaction.response.send_message("The queue is empty!")

        queue_str = f"#1: {self.song_queue[0].title} requested by {self.song_queue[0].author} [Currently playing!]"

        for i in range(1, len(self.song_queue)):
            queue_str += f"\n#{i + 1}: {self.song_queue[i].title} requested by {self.song_queue[i].author}"

        await interaction.response.send_message(queue_str)

    @app_commands.command()
    async def lyrics(self, interaction: discord.Interaction, artist: str, song: str):
        """Get lyrics to your favorite song"""

        if genius_token:
            await interaction.response.send_message("Searching for song...")
            msg = await interaction.original_response()
            await msg.edit(content=genius.search_song(song, artist).lyrics)
        else:
            await interaction.response.send_message(
                "You don't have a genius token! If you want to use this command make sure to add the genius token in the .env file!"
            )

    @app_commands.command()
    async def tts(self, interaction: discord.Interaction, message: str = ""):
        """Play a TTS message! Costs 10 cookies!"""

        user_id = interaction.user.id
        guild_id = interaction.guild.id

        if not self.money.lose(user_id, guild_id, 10):
            return await interaction.response.send_message(
                "You don't have enough cookies to use TTS!"
            )

        if message == "":
            return await interaction.response.send_message(
                f"Current voices: {utils.tts.get_voices()}"
            )

        await self.ensure_voice(interaction)

        voice = interaction.client.voice_clients[0]

        async with interaction.channel.typing():
            await interaction.response.send_message("Generating TTS...")
            urls = await utils.tts.generate_tts(message)

            if urls is None:
                return await interaction.followup.send(
                    "Woah there! You have exceeded past 100 characters!"
                )

            for url in urls:
                # Get the TTS
                player = await YTDLSource.from_url(url, loop=self.bot.loop)
                player.volume = 1.0
                player.author = interaction.user
                player.voting = Voting()
                self.song_queue.append(player)

            for url in urls:
                # Check if there is anything playing
                if voice.is_playing():
                    return await interaction.followup.send("Added TTS to queue!")

                # Play the song and check queue after
                voice.play(
                    self.song_queue[0],
                    after=lambda e: (
                        print(f"Player error: {e}")
                        if e
                        else self.check_queue(interaction)
                    ),
                )

                msg = await interaction.original_response()
                await msg.edit(content="Now playing TTS!")

    # Functions
    def check_queue(self, interaction: discord.Interaction):
        voice = interaction.client.voice_clients[0]

        self.song_queue.pop(0)

        if self.song_queue:
            voice.play(
                self.song_queue[0],
                after=lambda e: (
                    print(f"Player error: {e}") if e else self.check_queue(interaction)
                ),
            )


async def setup(bot):
    await bot.add_cog(Music(bot))
