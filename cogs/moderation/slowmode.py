## -- IMPORTING -- ##

# MODULES
import disnake
import os
import random
import asyncio
import datetime
import certifi
import time
import json

from disnake.ext import commands
from disnake.errors import Forbidden, HTTPException
from disnake.ext.commands import errors
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# FILES
import extra.config as config
import extra.functions as functions
from extra.checks import is_moderator

## -- VARIABLES -- ##

mongo_login = os.environ.get("MONGO_LOGIN")
client = MongoClient(f"{mongo_login}",tlsCAFile=certifi.where())
db = client["db2"]

server_data_col = db["server_data"]
warns_col = db["warns"]


class Slowmode(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @commands.command()
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    @is_moderator(manage_channels=True)
    async def slowmode(self, ctx: commands.Context, seconds: int, channel: disnake.TextChannel = None):
        """Change the slowmode of a channel."""
        
        if not channel:
            channel = ctx.channel
        if seconds > 21600:
            embed = disnake.Embed(description=f"{config.no} The slowmode can't be higher than 21600 seconds. (6 hours)", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
        
        if channel == ctx.channel:
            embed = disnake.Embed(description=f"{config.yes} The slowmode has been set to `{seconds}` seconds.", color=config.success_embed_color)
        else:
            embed = disnake.Embed(description=f"{config.yes} The slowmode for {channel.mention} has been set to `{seconds}` seconds.", color=config.success_embed_color)
        
        await channel.edit(slowmode_delay=seconds)
        await ctx.send(embed=embed)
        
    
    @slowmode.error
    async def slowmode_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `Manage Channels` permission.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == "seconds":
                embed = disnake.Embed(description=f"{config.no} Please provide what the slowmode should be set to.", color=config.error_embed_color)
                await ctx.send(embed=embed)
                
    
    @commands.slash_command(name="slowmode", description="Change the slowmode of a channel.")
    @is_moderator(manage_channels=True)
    async def slash_slowmode(self, inter: disnake.ApplicationCommandInteraction, seconds: int, channel: disnake.TextChannel = None):
        """Change the slowmode of a channel.
        Parameters
        ----------
        seconds: How many seconds the slowmode should be set to.
        channel: What channel to change slowmode of. Defaults to current channel.
        """
        
        if not channel:
            channel = inter.channel
        if seconds > 21600:
            embed = disnake.Embed(description=f"{config.no} The slowmode can't be higher than 21600 seconds. (6 hours)", color=config.error_embed_color)
            await inter.send(embed=embed)
            return
        
        if channel == inter.channel:
            embed = disnake.Embed(description=f"{config.yes} The slowmode has been set to `{seconds}` seconds.", color=config.success_embed_color)
        else:
            embed = disnake.Embed(description=f"{config.yes} The slowmode for {channel.mention} has been set to `{seconds}` seconds.", color=config.success_embed_color)
        
        await channel.edit(slowmode_delay=seconds)
        await inter.send(embed=embed)


    @slash_slowmode.error 
    async def slash_slowmode_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `Manage Channels` permission.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == "seconds":
                embed = disnake.Embed(description=f"{config.no} Please provide what the slowmode should be set to.", color=config.error_embed_color)
                await inter.response.send_message(embed=embed)
    
        
    
def setup(bot):
    bot.add_cog(Slowmode(bot))