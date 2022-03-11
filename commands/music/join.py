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
from extra import config
from extra import functions

## -- VARIABLES -- ##

load_dotenv()

## -- COG -- ##

class Join(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    async def join(self, ctx: commands.Context):
        """Makes me join your voice channel."""
        voice_client = utils.get(ctx.bot.voice_clients, guild=ctx.guild)
        user_voice = ctx.author.voice
        
        if not user_voice:
            embed = disnake.Embed(description=f"{config.no} You're not connected to a voice channel!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
        
        user_vc = user_voice.channel
        embed = disnake.Embed(description=f"{config.yes} Joined {user_vc.mention} successfully.", color=config.success_embed_color)
        
        if voice_client and voice_client.is_connected():
            await voice_client.disconnect()
            
        await user_vc.connect()
        await ctx.send(embed=embed)
            
    
    @join.error
    async def join_error(self, ctx: commands.Context, error):
        if isinstance(error, Forbidden):
            embed = disnake.Embed(description=f"{config.no} I don't have permission to join your voice channel!", color=config.error_embed_color)
            await ctx.send(embed=embed)
        
    
    @commands.slash_command(name="join", description="Makes me join your voice channel.")
    async def slash_join(self, inter: disnake.ApplicationCommandInteraction):
        """Makes me join your voice channel."""
        voice_client = utils.get(inter.bot.voice_clients, guild=inter.guild)
        user_voice = inter.author.voice
        
        if not user_voice:
            embed = disnake.Embed(description=f"{config.no} You're not connected to a voice channel!", color=config.error_embed_color)
            await inter.send(embed=embed)
            return
        
        user_vc = user_voice.channel
        embed = disnake.Embed(description=f"{config.yes} Joined {user_vc.mention} successfully.", color=config.success_embed_color)
        
        if voice_client and voice_client.is_connected():
            await voice_client.disconnect()
            
        await user_vc.connect()
        await inter.send(embed=embed)
        
    
    @slash_join.error 
    async def slash_join_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, ):
            embed = disnake.Embed()
            await inter.response.send_message(embed=embed, ephemeral=True)
        
    
def setup(bot):
    bot.add_cog(Join(bot))