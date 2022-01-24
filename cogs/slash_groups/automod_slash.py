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
import config
import modules

load_dotenv()

## -- VARIABLES -- ##

mongo_login = os.environ.get("MONGO_LOGIN")
client = MongoClient(f"{mongo_login}",tlsCAFile=certifi.where())
db = client["db2"]

server_data_col = db["server_data"]
muted_users_col = db["muted_users"]
privacy_settings_col = db["privacy_settings"]

## -- COG -- ##

class AutomodSlash(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(name="automod")
    @commands.has_permissions(manage_guild=True)
    async def slash_automod(self, inter):
        pass
    

    @slash_automod.error
    async def slash_automod_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, errors.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `Manage Guild` permission.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed)
        
    
def setup(bot):
    bot.add_cog(AutomodSlash(bot))