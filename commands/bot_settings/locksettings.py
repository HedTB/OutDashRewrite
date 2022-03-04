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
from pymongo import MongoClient
from dotenv import load_dotenv

# FILES
import extra.config as config
import extra.functions as functions
from extra.checks import *

load_dotenv()

## -- VARIABLES -- ##

mongo_login = os.environ.get("MONGO_LOGIN")
client = MongoClient(f"{mongo_login}",tlsCAFile=certifi.where())
db = client[config.database_collection]

server_data_col = db["server_data"]
muted_users_col = db["muted_users"]
user_data_col = db["user_data"]

## -- COG -- ##

class LockSettings(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    @commands.has_permissions(administrator=True)
    async def locksettings(self, ctx: commands.Context):
        """Locks the server's settings."""
        
        data = functions.get_db_data(str(ctx.guild.id))
        query = {"guild_id": str(ctx.guild.id)}
        result = server_data_col.find_one(query)
        update = {"$set": {
            "settings_locked": "true"
        }}

        if not result:
            server_data_col.insert_one(data)
            self.locksettings(ctx)
        elif result.get("settings_locked") == "true":
            embed = disnake.Embed(description=f"{config.no} The server's settings are already locked!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
            
        server_data_col.update_one(query, update)
        embed = disnake.Embed(description=f"{config.yes} The server's settings are now locked.", color=config.success_embed_color)
        await ctx.send(embed=embed)
    
    @locksettings.error 
    async def locksettings_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `Administrator` permission.", color=config.error_embed_color)
            await ctx.send(embed=embed)
            
    
def setup(bot):
    bot.add_cog(LockSettings(bot))