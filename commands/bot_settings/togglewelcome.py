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
import extra.functions as functions
import extra.config as config
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

class ToggleWelcome(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    @commands.has_permissions(manage_guild=True)
    @server_setting()
    async def togglewelcome(self, ctx, toggle: str = "on"):
        """Toggles if welcome messages should be sent."""
        
        data = {
            "guild_id": str(ctx.guild.id),
            "welcome_channel": "None",
            "welcome_toggle": str(toggle),
        }
        query = {"guild_id": str(ctx.guild.id)}
        result = server_data_col.find_one(query)
        if not result:
            server_data_col.insert_one(data)
            self.togglewelcome(ctx, toggle)
            return

        if toggle.lower() == "on" or toggle.lower() == "true" or toggle.lower() == "yes" or toggle.lower() == "enabled":
            update = { "$set": { "welcome_toggle": "true" } }
            server_data_col.update_one(query, update)
            
            embed = disnake.Embed(description=f"{config.yes} Welcome messages have been enabled.", color=config.success_embed_color)
            await ctx.send(embed=embed)
        elif toggle.lower() == "off" or toggle.lower() == "false" or toggle.lower() == "no" or toggle.lower() == "disabled":
            update = { "$set": { "welcome_toggle": "false" } }
            server_data_col.update_one(query, update)
            
            embed = disnake.Embed(description=f"{config.yes} Welcome messages have been disabled.", color=config.success_embed_color)
            await ctx.send(embed=embed)
        else:
            embed = disnake.Embed(description=f"{config.no} Please give a valid toggle value!\nToggles:\n```on, yes, true, enabled - welcome messages enabled\noff, no, false, disabled - welcome messages disabled```", color=config.error_embed_color)
            await ctx.send(embed=embed)
    
    @togglewelcome.error 
    async def setwelcomechannel_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions}` permission.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = disnake.Embed(description=f"{config.no} Please specify a toggle value!\nToggles:\n```on, yes, true, enabled - welcome messages enabled\noff, no, false, disabled - welcome messages disabled```", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, SettingsLocked):
            embed = disnake.Embed(description=f"{config.no} The server's settings are locked.", color=config.error_embed_color)
            await ctx.send(embed=embed)
            
    
def setup(bot):
    bot.add_cog(ToggleWelcome(bot))