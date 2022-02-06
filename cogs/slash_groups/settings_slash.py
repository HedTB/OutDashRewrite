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
import extra.config as config
import extra.functions as functions

load_dotenv()

## -- VARIABLES -- ##

mongo_login = os.environ.get("MONGO_LOGIN")
client = MongoClient(f"{mongo_login}",tlsCAFile=certifi.where())
db = client["db"]

server_data_col = db["server_data"]
muted_users_col = db["muted_users"]
user_data_col = db["user_data"]

toggle_list = commands.option_enum({"enabled": "enabled", "disabled": "disabled"})

## -- COG -- ##

class SettingsSlash(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(name="settings")
    @commands.has_permissions(administrator=True)
    async def slash_settings(self, inter):
        pass
    
    @slash_settings.sub_command(name="lock", description="The normal text message that should be sent.")
    async def slash_settings_lock(self, inter: disnake.ApplicationCommandInteraction):
        """Locks the server's settings."""
        
        data = functions.get_db_data(str(inter.guild.id))
        query = {"guild_id": str(inter.guild.id)}
        result = server_data_col.find_one(query)
        update = {"$set": {
            "settings_locked": "true"
        }}

        if not result:
            server_data_col.insert_one(data)
            self.slash_settings_lock(inter)
            
        server_data_col.update_one(query, update)
        embed = disnake.Embed(description=f"{config.yes} The server's settings are now locked.", color=config.success_embed_color)
        await inter.send(embed=embed)


    @slash_settings.sub_command(name="unlock", description="Unlocks the server's settings.")
    async def slash_settings_unlock(self, inter: disnake.ApplicationCommandInteraction):
        """Unlocks the server's settings."""
        
        data = functions.get_db_data(str(inter.guild.id))
        query = {"guild_id": str(inter.guild.id)}
        result = server_data_col.find_one(query)
        update = {"$set": {
            "settings_locked": "false"
        }}

        if not result:
            server_data_col.insert_one(data)
            self.slash_settings_unlock(inter)
            
        server_data_col.update_one(query, update)
        embed = disnake.Embed(description=f"{config.yes} The server's settings are now unlocked.", color=config.success_embed_color)
        await inter.send(embed=embed)

    @slash_settings.error
    async def slash_settings_lock_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, errors.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `Administrator` permission.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed)
        
    
def setup(bot):
    bot.add_cog(SettingsSlash(bot))