## -- IMPORTING -- ##

# MODULES
import disnake
import os
import random
import asyncio
import datetime
import certifi
import json
import requests

from disnake.ext import commands
from disnake.errors import Forbidden, HTTPException
from disnake.ext.commands import errors
from pymongo import MongoClient
from dotenv import load_dotenv

# FILES
from extra import config
from extra import functions
import app

## -- VARIABLES -- ##

load_dotenv()

## -- COG -- ##

class Test(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(hidden=True)
    async def test(self, ctx: commands.Context):
        if ctx.author.id not in config.owners:
            return

        await ctx.send(random.choice([69 ** 420, 420 ** 69, 69 * 420]))
        
    
def setup(bot):
    bot.add_cog(Test(bot))