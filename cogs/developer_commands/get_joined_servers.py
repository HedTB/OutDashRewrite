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
import extra.config as config
import extra.functions as functions
import app

## -- VARIABLES -- ##

load_dotenv()

## -- COG -- ##

class GetJoinedServers(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def getjoinedservers(self, ctx: commands.Context):
        if ctx.author.id not in config.owners:
            return

        guilds = self.bot.guilds
        message = ""
        
        for guild in guilds:
            message += f"**{guild.name}**\n`{guild.id}`\n\n"

        await ctx.send(message)
        
    
def setup(bot):
    bot.add_cog(GetJoinedServers(bot))