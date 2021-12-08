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

class Cog(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(rate=1, per=bot_info.cooldown_time, type=commands.BucketType.member)
    @commands.has_permissions(ban_members=True)
    async def command(self, ctx):
                
    
    @command.error 
    async def command_error(self, ctx, error):
            
        
    
    @commands.slash_command(name="command", description="", guild_ids=[bot_info.bot_server])
    @commands.has_permissions(ban_members=True)
    async def slash_command(self, ctx):
                
    
    @slash_command.error 
    async def slash_command_error(self, ctx, error):
        
    
        
    
def setup(bot):
    bot.add_cog(Cog(bot))