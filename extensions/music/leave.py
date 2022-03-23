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

# FILES
from utils import config
from utils import functions

## -- VARIABLES -- ##

load_dotenv()

## -- COG -- ##

class Leave(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    async def leave(self, ctx: commands.Context):
        """Makes me leave your voice channel."""
        voice_client = utils.get(ctx.bot.voice_clients, guild=ctx.guild)
        user_voice = ctx.author.voice
        
        if not user_voice:
            embed = disnake.Embed(description=f"{config.no} You're not connected to a voice channel!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
        
        user_vc = user_voice.channel
        embed = disnake.Embed(description=f"{config.yes} Left {user_vc.mention} successfully.", color=config.success_embed_color)
        
        if not voice_client or not voice_client.is_connected():
            embed = disnake.Embed(description=f"{config.no} I'm not connected to a voice channel!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
        elif user_vc != voice_client.channel:
            embed = disnake.Embed(description=f"{config.no} You're not connected to my voice channel!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
            
        await voice_client.disconnect()
        await ctx.send(embed=embed)
            
    
    @leave.error
    async def command_error(self, ctx: commands.Context, error):
        if isinstance(error, Forbidden):
            embed = disnake.Embed(description=f"{config.no} I don't have permission to leave your voice channel!", color=config.error_embed_color)
            await ctx.send(embed=embed)
        
    
    @commands.slash_command(name="leave", description="Makes me leave your voice channel.")
    async def slash_leave(self, inter: disnake.ApplicationCommandInteraction):
        """Makes me leave your voice channel."""
        voice_client = utils.get(inter.bot.voice_clients, guild=inter.guild)
        user_voice = inter.author.voice
        
        if not user_voice:
            embed = disnake.Embed(description=f"{config.no} You're not connected to a voice channel!", color=config.error_embed_color)
            await inter.send(embed=embed)
            return
        
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
        
    
    @slash_leave.error 
    async def slash_leave_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, ):
            embed = disnake.Embed()
            await inter.response.send_message(embed=embed, ephemeral=True)
        
    
def setup(bot):
    bot.add_cog(Leave(bot))