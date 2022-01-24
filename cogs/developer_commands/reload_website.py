## -- IMPORTING -- ##

# MODULES
import disnake
import os
import random
import asyncio
import datetime
import certifi
import json

from disnake.ext import commands
from disnake.errors import Forbidden, HTTPException
from disnake.ext.commands import errors
from pymongo import MongoClient
from dotenv import load_dotenv

# FILES
import config
import modules
import app

## -- VARIABLES -- ##

load_dotenv()

## -- COG -- ##

class ReloadWebsite(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def reloadwebsite(self, ctx: commands.Context):
        if ctx.author.id not in config.owners:
            return

        guild_dict = dict()
        guild_dict["id"] = ctx.guild.id
        guild_dict["name"] = ctx.guild.name
        guild_dict["icon"] = str(ctx.guild.icon)

        print(json.dumps(guild_dict))
        
    
def setup(bot):
    bot.add_cog(ReloadWebsite(bot))