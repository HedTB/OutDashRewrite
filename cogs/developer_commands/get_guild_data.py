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

class GetGuildData(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def getguilddata(self, ctx: commands.Context, guild_id: int = 836495137651294258):
        if ctx.author.id not in config.owners:
            return

        guild = self.bot.get_guild(guild_id)
        embed = disnake.Embed(title=guild.name, description="")

        embed.set_thumbnail(guild.icon or "https://cdn.discordapp.com/embed/avatars/1.png")
        embed.add_field("Member Count", len(guild.members))

        await ctx.send(embed=embed)
        
    
def setup(bot):
    bot.add_cog(GetGuildData(bot))