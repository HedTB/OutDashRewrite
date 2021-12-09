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
#  from main import bot

# FILES
import bot_info

theBot = "None"

class AppFunctions(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        global theBot
        theBot = self.bot
      
    @staticmethod  
    def check_for_bot_in_server(guild_id: int):
        guild = theBot.get_guild(guild_id)
        print(guild)
        
        if guild:
            return guild
        else:
            return None


def setup(bot):
    bot.add_cog(AppFunctions(bot))
