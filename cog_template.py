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
db = client["db"]

server_data_col = db["server_data"]
warns_col = db["warns"]


class Command(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @commands.command()
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    @is_moderator()
    async def command(self, ctx: commands.Context):
        """Description"""
        
    
    @command.error
    async def command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `` permission.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
        
    
    @commands.slash_command(name="command", description="Description")
    @is_moderator()
    async def slash_command(self, inter: disnake.ApplicationCommandInteraction):
        """Description
        Parameters
        ----------
        member: The member you want to warn.
        reason: The reason for the warn.
        """


    @slash_command.error 
    async def slash_command_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `` permission.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error, commands.MissingRequiredArgument):
                        
    
        
    
def setup(bot):
    bot.add_cog(Command(bot))