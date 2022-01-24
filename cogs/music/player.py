## -- IMPORTING -- ##

# MODULES
import disnake
import os
import random
import asyncio
import datetime
import certifi

from disnake.ext import commands
from disnake.errors import Forbidden, HTTPException
from disnake.ext.commands import errors
from disnake import utils
from pymongo import MongoClient
from dotenv import load_dotenv
from DiscordUtils import Music

# FILES
import config
import modules

## -- VARIABLES -- ##

load_dotenv()

## -- COG -- ##

class Player(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.music = Music()
        
    ## -- TEXT COMMANDS -- ##

    @commands.command()
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    async def play(self, ctx: commands.Context, *, url: str):
        """Play some music!"""
        voice_client = ctx.voice_client
        user_voice = ctx.author.voice
        player = self.music.get_player(guild_id=ctx.guild.id)

        if not user_voice:
            embed = disnake.Embed(description=f"{config.no} You're not connected to a voice channel!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
        user_vc = user_voice.channel

        if voice_client and not voice_client.is_connected():
            await user_vc.connect()
        elif not voice_client:
            await user_vc.connect()

        voice_client = ctx.voice_client
        
        if not player:
            player = self.music.create_player(ctx, ffmpeg_error_betterfix=True)
        
        if voice_client and voice_client.is_connected():
            if voice_client.channel != user_vc:
                embed = disnake.Embed(description=f"{config.no} I'm already playing music in {voice_client.channel.mention}!", color=config.error_embed_color)
                await ctx.send(embed=embed)
                return
        
        if not voice_client.is_playing():
            embed = disnake.Embed(description=f"{config.loading} Retreiving video..", color=config.embed_color)
            message = await ctx.send(embed=embed)

            song = await player.queue(url, bettersearch=True)
            await player.play()
            
            embed = disnake.Embed(description=f":notes: Playing **[{song.name}]({song.url})** now.", color=config.embed_color)
            embed.set_image(url=song.thumbnail)

            await message.edit(embed=embed)
        else:
            embed = disnake.Embed(description=f"{config.loading} Retreiving video..", color=config.embed_color)
            message = await ctx.send(embed=embed)

            song = await player.queue(url, bettersearch=True)
            
            embed = disnake.Embed(description=f":notes: Queued **[{song.name}]({song.url})** successfully.", color=config.embed_color)
            embed.set_image(url=song.thumbnail)
            
            await message.edit(embed=embed)

    @commands.command()
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    async def pause(self, ctx: commands.Context):
        """Pauses the playing music."""

        voice_client = utils.get(ctx.bot.voice_clients, guild=ctx.guild)
        user_voice = ctx.author.voice
        player = self.music.get_player(guild_id=ctx.guild.id)
        
        if not user_voice:
            embed = disnake.Embed(description=f"{config.no} You're not connected to a voice channel!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
        
        user_vc = user_voice.channel
        embed = disnake.Embed(description=f"{config.yes} The music was paused.", color=config.success_embed_color)
        
        if voice_client and not voice_client.channel == user_vc:
            embed = disnake.Embed(description=f"{config.no} You're not connected to my voice channel!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
        elif not voice_client.is_playing() or not player:
            embed = disnake.Embed(description=f"{config.no} I'm not playing anything!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
        elif not voice_client or not voice_client.is_connected():
            embed = disnake.Embed(description=f"{config.no} I'm not connected to a voice channel!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
            
        await player.pause()
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    async def resume(self, ctx: commands.Context):
        """Resumes the paused music."""

        voice_client = utils.get(ctx.bot.voice_clients, guild=ctx.guild)
        user_voice = ctx.author.voice
        player = self.music.get_player(guild_id=ctx.guild.id)
        
        if not user_voice:
            embed = disnake.Embed(description=f"{config.no} You're not connected to a voice channel!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
        
        user_vc = user_voice.channel
        embed = disnake.Embed(description=f"{config.yes} The music was resumed.", color=config.success_embed_color)
        
        if voice_client and not voice_client.channel == user_vc:
            embed = disnake.Embed(description=f"{config.no} You're not connected to my voice channel!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
        elif voice_client.is_playing() or not player:
            embed = disnake.Embed(description=f"{config.no} The music isn't paused!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
        elif not voice_client or not voice_client.is_connected():
            embed = disnake.Embed(description=f"{config.no} I'm not connected to a voice channel!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
            
        await player.resume()
        await ctx.send(embed=embed)
          
    @commands.command()
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    async def stop(self, ctx: commands.Context):
        """Stops the playing music."""
        voice_client = ctx.voice_client
        user_voice = ctx.author.voice
        player = self.music.get_player(guild_id=ctx.guild.id)
        
        if not user_voice:
            embed = disnake.Embed(description=f"{config.no} You're not connected to a voice channel!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
        
        user_vc = user_voice.channel
        embed = disnake.Embed(description=f"{config.yes} The music have been stopped.", color=config.success_embed_color)
        
        if voice_client and not voice_client.channel == user_vc:
            embed = disnake.Embed(description=f"{config.no} You're not connected to my voice channel!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
        elif not player:
            embed = disnake.Embed(description=f"{config.no} I'm not playing any music!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
        elif not voice_client or not voice_client.is_connected():
            embed = disnake.Embed(description=f"{config.no} I'm not connected to a voice channel!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
        
        await player.stop()
        await voice_client.disconnect()
        await ctx.send(embed=embed)

    @commands.command(aliases=["repeat"])
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    async def loop(self, ctx: commands.Context):
        """Put the playing song on repeat."""

        voice_client = utils.get(ctx.bot.voice_clients, guild=ctx.guild)
        user_voice = ctx.author.voice
        player = self.music.get_player(guild_id=ctx.guild.id)
        
        if not user_voice:
            embed = disnake.Embed(description=f"{config.no} You're not connected to a voice channel!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
        
        user_vc = user_voice.channel
        embed = disnake.Embed(description=f"{config.yes} The music has been put on loop.", color=config.success_embed_color)
        embed2 = disnake.Embed(description=f"{config.yes} The music loop has been disabled.", color=config.success_embed_color)
        
        if voice_client and not voice_client.channel == user_vc:
            embed = disnake.Embed(description=f"{config.no} You're not connected to my voice channel!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
        elif not voice_client.is_playing() or not player:
            embed = disnake.Embed(description=f"{config.no} I'm not playing anything!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
        elif not voice_client or not voice_client.is_connected():
            embed = disnake.Embed(description=f"{config.no} I'm not connected to a voice channel!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return

        song = await player.toggle_song_loop()
        if song.is_looping:
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=embed2)


    
    
    ## -- TEXT COMMAND HANDLERS -- ##
    
    @play.error
    async def command_error(self, ctx: commands.Context, error):
        if isinstance(error, Forbidden):
            embed = disnake.Embed(description=f"{config.no} I don't have permission to play your voice channel!", color=config.error_embed_color)
            await ctx.send(embed=embed)
     
    ## -- SLASH COMMANDS -- ##   
    
    @commands.slash_command(name="play", description="Play some music!")
    async def slash_play(self, inter: disnake.ApplicationCommandInteraction):
        """Play some music!"""
        voice_client = utils.get(inter.bot.voice_clients, guild=inter.guild)
        user_voice = inter.author.voice
        
        if not user_voice:
            embed = disnake.Embed(description=f"{config.no} You're not connected to a voice channel!", color=config.error_embed_color)
            await inter.send(embed=embed)
            return
        if not voice_client or not voice_client.is_connected():
            embed = disnake.Embed(description=f"{config.no} I'm not connected to a voice channel!", color=config.error_embed_color)
        
        user_vc = user_voice.channel
        embed = disnake.Embed(description=f"{config.yes} Left {user_vc.mention} successfully.", color=config.success_embed_color)
        
        if voice_client and voice_client.is_connected():
            await voice_client.disconnect()
        else:
            embed = disnake.Embed(description=f"{config.no} I'm not connected to a voice channel!", color=config.error_embed_color)
            await inter.send(embed=embed)
            return
            
        await user_vc.connect()
        await inter.send(embed=embed)
     
    ## -- SLASH COMMAND HANDLERS -- ##   
    
    @slash_play.error 
    async def slash_play_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, ):
            embed = disnake.Embed()
            await inter.response.send_message(embed=embed, ephemeral=True)
        
    
def setup(bot):
    bot.add_cog(Player(bot))