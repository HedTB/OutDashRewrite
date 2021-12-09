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

class AppFunctions(commands.Cog):

    def __init__(self, bot):
        global selff
        selff = self
        selff["bot"] = bot
        
    def check_for_bot_in_server(guild_id: int):
        guild = selff.bot.get_guild(859482895009579039)
        print(guild)
        if guild:
            return guild
        else:
            return None


def setup(bot):
    bot.add_cog(AppFunctions(bot))
