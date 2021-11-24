## -- IMPORTING -- ##

# MODULES
import discord
import os
import random
import asyncio
import datetime
import certifi

from discord.ext import commands
from discord.commands.commands import Option
from discord.errors import Forbidden, HTTPException
from discord.ext.commands import errors
from pymongo import MongoClient

# FILES
import bot_info

## -- VARIABLES -- ##

mongo_token = os.getenv("MONGO_TOKEN")
client = MongoClient(f"{mongo_token}",tlsCAFile=certifi.where())
db = client["db2"]

prefixes_col = db["prefixes"]
confirmations_col = db["bot_farm_confirmations"]


class SetPrefix(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        

    @commands.command(aliases=["changeprefix", "prefix"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.member)
    @commands.has_permissions(manage_guild=True)
    async def setprefix(self, ctx, newPrefix:str):
        
        query = {'guild_id' : str(ctx.guild.id)}
        replacement = {"guild_id": str(ctx.guild.id), "prefix": str(newPrefix)}
        update = { "$set": { 'guild_id' : str(ctx.guild.id), 'prefix' : str(newPrefix) } }
        
        prefixes_col.replace_one(query, replacement)
        
        embed = discord.Embed(description=f"{bot_info.yes} Changed the prefix to `{newPrefix}` successfully.", color=bot_info.success_embed_color)
        await ctx.send(embed=embed)
    
    @setprefix.error 
    async def prefix_error(self, ctx, error):
        if isinstance(error, errors.MissingPermissions):
            embed = discord.Embed(description=f"{bot_info.no} You're missing the `Manage Guild` permission.", color=bot_info.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, errors.MissingRequiredArgument):
            embed = discord.Embed(description=f"{bot_info.no} You need to specify the new prefix.", color=bot_info.error_embed_color)
            await ctx.send(embed=embed)
    
        
    
def setup(bot):
    bot.add_cog(SetPrefix(bot))