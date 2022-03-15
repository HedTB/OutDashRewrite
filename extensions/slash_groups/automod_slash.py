## -- IMPORTING -- ##

# MODULES
import disnake
import os
import random
import asyncio
import datetime
import certifi

from disnake.ext import commands
from disnake.errors import Forbidden, HTTPException
from disnake.ext.commands import errors
from disnake.utils import get
from pymongo import MongoClient
from dotenv import load_dotenv

# FILES
from extra import config
from extra import functions
from extra.checks import *

load_dotenv()

## -- VARIABLES -- ##

mongo_login = os.environ.get("MONGO_LOGIN")
client = MongoClient(f"{mongo_login}",tlsCAFile=certifi.where())
db = client[config.database_collection]

server_data_col = db["server_data"]
muted_users_col = db["muted_users"]
user_data_col = db["user_data"]

type_list = commands.option_enum({"wildcard": "wildcard", "normal": "normal"})

## -- COG -- ##

class AutomodSlash(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(name="automod")
    @is_moderator(manage_guild=True)
    async def slash_automod(self, inter):
        pass

    @slash_automod.sub_command_group(name="filter")
    @is_moderator(manage_guild=True)
    async def slash_filter(self, inter):
        pass

    @slash_filter.sub_command(name="add")
    async def slash_filteradd(self, inter: disnake.ApplicationCommandInteraction, type: type_list, word: str):
        await inter.send("wip")
    

    @slash_automod.error
    async def slash_automod_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, errors.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions[0].capitalize()}` permission.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed)
        
    
def setup(bot):
    bot.add_cog(AutomodSlash(bot))