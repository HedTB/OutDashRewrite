## -- IMPORTING -- ##

# MODULES
import disnake
import os
import certifi

from disnake import utils
from disnake.ext import commands
from pymongo import MongoClient
from dotenv import load_dotenv
from utils.DiscordUtils import Music as MusicManager

# FILES
from utils import config, functions, colors, enums, converters

from utils.checks import *
from utils.data import *
from utils.emojis import *

## -- VARIABLES -- ##

load_dotenv()

## -- COG -- ##


class Music(commands.Cog):
    name = ":notes: Music"
    description = "Want to listen to some music? This module is for you!"
    emoji = "🎶"

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.music = MusicManager()

    ## -- SLASH COMMANDS -- ##

    @commands.slash_command(name="play")
    async def play(
        self, inter: disnake.ApplicationCommandInteraction, query: str
    ):
        """Play some music!
        Parameters
        ----------
        query: The song you want to play. This can be a URL or a search term.
        """

        voice_client = inter.guild.voice_client
        user_voice = inter.author.voice
        player = self.music.get_player(guild_id=inter.guild.id)

        if not user_voice:
            embed = disnake.Embed(
                description=f"{no} You're not connected to a voice channel!",
                color=colors.error_embed_color,
            )
            return await inter.send(embed=embed, ephemeral=True)

        user_vc = user_voice.channel

        if voice_client and not voice_client.is_connected():
            await user_vc.connect()
        elif not voice_client:
            await user_vc.connect()

        voice_client = inter.guild.voice_client
        if not player:
            player = self.music.create_player(inter, ffmpeg_error_betterfix=True)

        if voice_client and voice_client.is_connected():
            if voice_client.channel != user_vc:
                embed = disnake.Embed(
                    description=f"{no} I'm already playing music in {voice_client.channel.mention}!",
                    color=colors.error_embed_color,
                )
                return await inter.send(embed=embed, ephemeral=True)

        if not voice_client.is_playing():
            embed = disnake.Embed(
                description=f"{loading} Retreiving video..", color=colors.embed_color
            )
            await inter.send(embed=embed)

            song = await player.queue(query, bettersearch=True)
            await player.play()

            embed = disnake.Embed(
                description=f":notes: Playing **[{song.name}]({song.url})** now.",
                color=colors.embed_color,
            )
            embed.set_image(url=song.thumbnail)

            await inter.edit_original_message(embed=embed)
        else:
            embed = disnake.Embed(
                description=f"{loading} Retreiving video..", color=colors.embed_color
            )
            await inter.send(embed=embed)

            song = await player.queue(query, bettersearch=True)

            embed = disnake.Embed(
                description=f":notes: Queued **[{song.name}]({song.url})** successfully.",
                color=colors.embed_color,
            )
            embed.set_image(url=song.thumbnail)

            await inter.edit_original_message(embed=embed)

    @commands.slash_command(name="pause")
    async def pause(self, inter: disnake.ApplicationCommandInteraction):
        """Pauses your music."""

        voice_client = utils.get(inter.bot.voice_clients, guild=inter.guild)
        user_voice = inter.author.voice
        player = self.music.get_player(guild_id=inter.guild.id)

        if not user_voice:
            embed = disnake.Embed(
                description=f"{no} You're not connected to a voice channel!",
                color=colors.error_embed_color,
            )
            return await inter.send(embed=embed, ephemeral=True)

        user_vc = user_voice.channel
        embed = disnake.Embed(
            description=f"{yes} The music have been paused.",
            color=colors.success_embed_color,
        )

        if voice_client and not voice_client.channel == user_vc:
            embed = disnake.Embed(
                description=f"{no} You're not connected to my voice channel!",
                color=colors.error_embed_color,
            )
            return await inter.send(embed=embed, ephemeral=True)

        elif not voice_client.is_playing() or not player:
            embed = disnake.Embed(
                description=f"{no} I'm not playing anything!",
                color=colors.error_embed_color,
            )
            return await inter.send(embed=embed, ephemeral=True)

        elif not voice_client or not voice_client.is_connected():
            embed = disnake.Embed(
                description=f"{no} I'm not connected to a voice channel!",
                color=colors.error_embed_color,
            )
            return await inter.send(embed=embed, ephemeral=True)

        await player.pause()
        await inter.send(embed=embed)

    @commands.slash_command(name="resume")
    async def resume(self, inter: disnake.ApplicationCommandInteraction):
        """Resumes your music."""

        voice_client = utils.get(inter.bot.voice_clients, guild=inter.guild)
        user_voice = inter.author.voice
        player = self.music.get_player(guild_id=inter.guild.id)

        if not user_voice:
            embed = disnake.Embed(
                description=f"{no} You're not connected to a voice channel!",
                color=colors.error_embed_color,
            )
            return await inter.send(embed=embed, ephemeral=True)

        user_vc = user_voice.channel
        embed = disnake.Embed(
            description=f"{yes} The music have been resumed.",
            color=colors.success_embed_color,
        )

        if voice_client and not voice_client.channel == user_vc:
            embed = disnake.Embed(
                description=f"{no} You're not connected to my voice channel!",
                color=colors.error_embed_color,
            )
            return await inter.send(embed=embed, ephemeral=True)

        elif voice_client.is_playing() or not player:
            embed = disnake.Embed(
                description=f"{no} The music isn't paused!",
                color=colors.error_embed_color,
            )
            return await inter.send(embed=embed, ephemeral=True)

        elif not voice_client or not voice_client.is_connected():
            embed = disnake.Embed(
                description=f"{no} I'm not connected to a voice channel!",
                color=colors.error_embed_color,
            )
            return await inter.send(embed=embed, ephemeral=True)

        await player.resume()
        await inter.send(embed=embed)

    @commands.slash_command(name="stop")
    async def stop(self, inter: disnake.ApplicationCommandInteraction):
        """Stops the playing music."""

        voice_client = inter.guild.voice_client
        user_voice = inter.author.voice
        player = self.music.get_player(guild_id=inter.guild.id)

        if not user_voice:
            embed = disnake.Embed(
                description=f"{no} You're not connected to a voice channel!",
                color=colors.error_embed_color,
            )
            return await inter.send(embed=embed, ephemeral=True)

        user_vc = user_voice.channel
        embed = disnake.Embed(
            description=f"{yes} The music have been stopped.",
            color=colors.success_embed_color,
        )

        if voice_client and not voice_client.channel == user_vc:
            embed = disnake.Embed(
                description=f"{no} You're not connected to my voice channel!",
                color=colors.error_embed_color,
            )
            return await inter.send(embed=embed, ephemeral=True)

        elif not player:
            embed = disnake.Embed(
                description=f"{no} I'm not playing any music!",
                color=colors.error_embed_color,
            )
            return await inter.send(embed=embed, ephemeral=True)

        elif not voice_client or not voice_client.is_connected():
            embed = disnake.Embed(
                description=f"{no} I'm not connected to a voice channel!",
                color=colors.error_embed_color,
            )
            return await inter.send(embed=embed, ephemeral=True)

        await player.stop()
        await voice_client.disconnect()
        await inter.send(embed=embed)

    @commands.slash_command(aliases=["repeat"])
    async def loop(self, inter: disnake.ApplicationCommandInteraction):
        """Put the playing song on repeat!"""

        voice_client = utils.get(inter.bot.voice_clients, guild=inter.guild)
        user_voice = inter.author.voice
        player = self.music.get_player(guild_id=inter.guild.id)

        if not user_voice:
            embed = disnake.Embed(
                description=f"{no} You're not connected to a voice channel!",
                color=colors.error_embed_color,
            )
            return await inter.send(embed=embed, ephemeral=True)

        user_vc = user_voice.channel
        embed = disnake.Embed(
            description=f"{yes} The music has been put on loop.",
            color=colors.success_embed_color,
        )
        embed2 = disnake.Embed(
            description=f"{yes} The music loop has been disabled.",
            color=colors.success_embed_color,
        )

        if voice_client and not voice_client.channel == user_vc:
            embed = disnake.Embed(
                description=f"{no} You're not connected to my voice channel!",
                color=colors.error_embed_color,
            )
            return await inter.send(embed=embed, ephemeral=True)

        elif not voice_client.is_playing() or not player:
            embed = disnake.Embed(
                description=f"{no} I'm not playing anything!",
                color=colors.error_embed_color,
            )
            return await inter.send(embed=embed, ephemeral=True)

        elif not voice_client or not voice_client.is_connected():
            embed = disnake.Embed(
                description=f"{no} I'm not connected to a voice channel!",
                color=colors.error_embed_color,
            )
            return await inter.send(embed=embed, ephemeral=True)

        song = await player.toggle_song_loop()
        if song.is_looping:
            await inter.send(embed=embed)
        else:
            await inter.send(embed=embed2)

    @commands.slash_command(name="join")
    async def join(self, inter: disnake.ApplicationCommandInteraction):
        """Makes me join your voice channel."""

        voice_client = utils.get(inter.bot.voice_clients, guild=inter.guild)
        user_voice = inter.author.voice

        if not user_voice:
            embed = disnake.Embed(
                description=f"{no} You're not connected to a voice channel!",
                color=colors.error_embed_color,
            )
            return await inter.send(embed=embed, ephemeral=True)

        user_vc = user_voice.channel
        embed = disnake.Embed(
            description=f"{yes} Joined {user_vc.mention} successfully.",
            color=colors.success_embed_color,
        )

        if voice_client and voice_client.is_connected():
            await voice_client.disconnect()

        await user_vc.connect()
        await inter.send(embed=embed)

    ## -- TEXT COMMAND HANDLERS -- ##

    @join.error
    @play.error
    async def command_error(self, ctx: commands.Context, error):
        if isinstance(error, disnake.errors.Forbidden):
            embed = disnake.Embed(
                description=f"{no} I don't have permission to join your voice channel!",
                color=colors.error_embed_color,
            )
            await ctx.send(embed=embed)

    ## -- SLASH COMMAND HANDLERS -- ##

    @join
    @play.error
    async def play_error(
        self, inter: disnake.ApplicationCommandInteraction, error: commands.CommandError
    ):
        if isinstance(error, disnake.errors.Forbidden):
            embed = disnake.Embed(
                description=f"{no} I don't have permission to join your voice channel!",
                color=colors.error_embed_color,
            )
            await inter.response.send_message(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(Music(bot))
