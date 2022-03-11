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
from extra import config
from extra import functions
from extra.checks import *

## -- VARIABLES -- ##

load_dotenv()

mongo_login = os.environ.get("MONGO_LOGIN")

client = MongoClient(f"{mongo_login}",tlsCAFile=certifi.where())
db = client["db2"]

server_data_col = db["server_data"]
warns_col = db["warns"]


class Settings(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        
    ## -- TEXT COMMANDS -- ##
    
    # SETTING LOCKING
    @commands.group(name="settings")
    async def settings(self, ctx: commands.Context):
        if ctx.invoked_subcommand == self.settings or None:
            return

    @settings.command()
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    @commands.has_permissions(administrator=True)
    async def lock(self, ctx: commands.Context):
        """Locks the server's settings."""
        
        query = {"guild_id": str(ctx.guild.id)}
        result = server_data_col.find_one(query)
        update = {"$set": {
            "settings_locked": "true"
        }}

        if not result:
            server_data_col.insert_one(functions.get_db_data(str(ctx.guild.id)))
            await self.locksettings(ctx)
            return
        
        elif result.get("settings_locked") == "true":
            embed = disnake.Embed(description=f"{config.no} The server's settings are already locked!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
            
        server_data_col.update_one(query, update)
        embed = disnake.Embed(description=f"{config.yes} The server's settings are now locked.", color=config.success_embed_color)
        await ctx.send(embed=embed)

    @settings.command()
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    @commands.has_permissions(administrator=True)
    async def unlock(self, ctx: commands.Context):
        """Unlocks the server's settings."""
        
        query = {"guild_id": str(ctx.guild.id)}
        result = server_data_col.find_one(query)
        update = {"$set": {
            "settings_locked": "false"
        }}

        if not result:
            server_data_col.insert_one(functions.get_db_data(str(ctx.guild.id)))
            await self.unlocksettings(ctx)
            return
        
        elif result.get("settings_locked") == "false":
            embed = disnake.Embed(description=f"{config.no} The server's settings aren't locked!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
            
        server_data_col.update_one(query, update)
        embed = disnake.Embed(description=f"{config.yes} The server's settings are now unlocked.", color=config.success_embed_color)
        await ctx.send(embed=embed)
        
    
    
    # SERVER SETTINGS
    @commands.command(aliases=["changeprefix", "prefix"])
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    @is_moderator(manage_guild=True)
    @server_setting()
    async def setprefix(self, ctx: commands.Context,new_prefix: str):
        """Changes the server prefix."""

        data = functions.get_db_data(str(ctx.guild.id))
        query = {"guild_id": str(ctx.guild.id)}
        result = server_data_col.find_one(query)

        if not result:
            server_data_col.insert_one(data)
            self.setprefix(ctx, new_prefix)
            return

        if self.bot.get_bot_prefix(ctx.guild.id) == new_prefix:
            embed = disnake.Embed(description=f"{config.no} The prefix is already set to `{new_prefix}`.", color=config.error_embed_color)
            await ctx.send(embed=embed)

        else:
            self.bot.change_prefix(ctx.guild.id, new_prefix)
            embed = disnake.Embed(description=f"{config.yes} Changed the prefix to `{new_prefix}` successfully.", color=config.success_embed_color)
            await ctx.send(embed=embed)
        
    ## -- SLASH COMMANDS -- ##
    
    @commands.slash_command(name="settings")
    @commands.has_permissions(administrator=True)
    async def slash_settings(self, inter):
        pass
    
    @slash_settings.sub_command(name="lock", description="Locks the server's settings.")
    async def slash_settings_lock(self, inter: disnake.ApplicationCommandInteraction):
        """Locks the server's settings."""
        
        query = {"guild_id": str(inter.guild.id)}
        result = server_data_col.find_one(query)
        update = {"$set": {
            "settings_locked": "true"
        }}

        if not result:
            server_data_col.insert_one(functions.get_db_data(str(inter.guild.id)))
            await self.locksettings(inter)
            return
        
        elif result.get("settings_locked") == "true":
            embed = disnake.Embed(description=f"{config.no} The server's settings are already locked!", color=config.error_embed_color)
            await inter.send(embed=embed, ephemeral=True)
            return
            
        server_data_col.update_one(query, update)
        embed = disnake.Embed(description=f"{config.yes} The server's settings are now locked.", color=config.success_embed_color)
        await inter.send(embed=embed)


    @slash_settings.sub_command(name="unlock", description="Unlocks the server's settings.")
    async def slash_settings_unlock(self, inter: disnake.ApplicationCommandInteraction):
        """Unlocks the server's settings."""
        
        query = {"guild_id": str(inter.guild.id)}
        result = server_data_col.find_one(query)
        update = {"$set": {
            "settings_locked": "false"
        }}

        if not result:
            server_data_col.insert_one(functions.get_db_data(str(inter.guild.id)))
            await self.unlocksettings(inter)
            return
        
        elif result.get("settings_locked") == "false":
            embed = disnake.Embed(description=f"{config.no} The server's settings aren't locked!", color=config.error_embed_color)
            await inter.send(embed=embed, ephemeral=True)
            return
            
        server_data_col.update_one(query, update)
        embed = disnake.Embed(description=f"{config.yes} The server's settings are now unlocked.", color=config.success_embed_color)
        await inter.send(embed=embed)


    @commands.slash_command(name="setprefix", description="Change the prefix for text commands.")
    @is_moderator(manage_guild=True)
    @server_setting()
    async def slash_setprefix(self, inter: disnake.ApplicationCommandInteraction, new_prefix: str):
        """Change the prefix for text commands.
        Parameters
        ----------
        new_prefix: What you want your new prefix to be.
        """

        data = functions.get_db_data(str(inter.guild_id))
        query = {"guild_id": str(inter.guild.id)}
        result = server_data_col.find_one(query)
        if not result:
            server_data_col.insert_one(data)
            self.slash_setprefix(inter, new_prefix)
            return

        if self.bot.get_bot_prefix(inter.guild.id) == new_prefix:
            embed = disnake.Embed(description=f"{config.no} The prefix is already set to `{new_prefix}`.", color=config.error_embed_color)
            await inter.send(embed=embed, ephemeral=True)
        else:
            self.bot.change_prefix(inter.guild.id, new_prefix)
            embed = disnake.Embed(description=f"{config.yes} Changed the prefix to `{new_prefix}` successfully.", color=config.success_embed_color)
            await inter.send(embed=embed)
        
        
    ## -- TEXT COMMAND ERRORS -- ##
    
    @lock.error 
    async def lock_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions[0].capitalize()}` permission.", color=config.error_embed_color)
            await ctx.send(embed=embed)
    
    @unlock.error 
    async def unlock_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions[0].capitalize()}` permission.", color=config.error_embed_color)
            await ctx.send(embed=embed)
    
    @setprefix.error 
    async def prefix_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, errors.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions[0].capitalize()}` permission.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, errors.MissingRequiredArgument):
            embed = disnake.Embed(description=f"{config.no} You need to specify the new prefix.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, SettingsLocked):
            embed = disnake.Embed(description=f"{config.no} The server's settings are locked.", color=config.error_embed_color)
            await ctx.send(embed=embed)

    
    ## -- SLASH COMMAND ERRORS -- ##
    
    @slash_settings.error
    async def slash_settings_lock_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, errors.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions[0].capitalize()}` permission.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed)
    
    @slash_setprefix.error 
    async def prefix_error(self, inter, error):
        if isinstance(error, errors.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions[0].capitalize()}` permission.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error, errors.MissingRequiredArgument):
            embed = disnake.Embed(description=f"{config.no} You need to specify the new prefix.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error, SettingsLocked):
            embed = disnake.Embed(description=f"{config.no} The server's settings are locked.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)

    
def setup(bot):
    bot.add_cog(Settings(bot))