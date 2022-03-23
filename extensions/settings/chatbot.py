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
from utils import config
from utils import functions
from utils.checks import *

## -- VARIABLES -- ##

load_dotenv()

mongo_login = os.environ.get("MONGO_LOGIN")

client = MongoClient(mongo_login, tlsCAFile=certifi.where())
db = client["db2"]

server_data_col = db["server_data"]
warns_col = db["warns"]


class Command(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    
    ## -- TEXT COMMANDS -- ##
    
    @commands.group(name="chatbot")
    async def chatbot(self, ctx: commands.Context):
        if ctx.invoked_subcommand == self.chatbot or None:
            return
        
    @chatbot.command(name="channel")
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    @is_moderator(manage_guild=True)
    @server_setting()
    async def chatbotchannel(self, ctx: commands.Context, channel: disnake.TextChannel):
        """Set where the chat bot should respond to messages."""
        
        query = {"guild_id": str(ctx.guild.id)}
        update = {"$set": {
            "chat_bot_channel": str(channel.id),
            "chat_bot_toggle": "true"
        }}
        result = server_data_col.find_one(query)

        if not result:
            server_data_col.insert_one(functions.get_db_data(str(ctx.guild.id)))
            await self.chatbotchannel(ctx, channel)
            return
        
        embed = disnake.Embed(description=f"{config.yes} The chat bot will now respond to messages in {channel.mention}.", color=config.success_embed_color)
        
        server_data_col.update_one(query, update)
        await ctx.send(embed=embed)
        
    @chatbot.command(name="enable")
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    @is_moderator(manage_guild=True)
    @server_setting()
    async def chatbotenable(self, ctx: commands.Context):
        """Enable the chat bot feature."""
        
        query = {"guild_id": str(ctx.guild.id)}
        update = {"$set": {
            "chat_bot_toggle": "true"
        }}
        result = server_data_col.find_one(query)
        
        embed = disnake.Embed(description=f"{config.yes} The chat bot feature has been enabled.", color=config.success_embed_color)

        if not result:
            server_data_col.insert_one(functions.get_db_data(str(ctx.guild.id)))
            await self.chatbotenable(ctx)
            
            return
        elif result.get("chat_bot_toggle") == "true":
            embed = disnake.Embed(description=f"{config.no} The chat bot feature is already enabled!", color=config.error_embed_color)
        else:
            server_data_col.update_one(query, update)
        
        await ctx.send(embed=embed)
        
    @chatbot.command(name="disable")
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    @is_moderator(manage_guild=True)
    @server_setting()
    async def chatbotdisable(self, ctx: commands.Context):
        """Enable the chat bot feature."""
        
        query = {"guild_id": str(ctx.guild.id)}
        update = {"$set": {
            "chat_bot_toggle": "false"
        }}
        result = server_data_col.find_one(query)
        
        embed = disnake.Embed(description=f"{config.yes} The chat bot feature has been disabled.", color=config.success_embed_color)

        if not result:
            server_data_col.insert_one(functions.get_db_data(str(ctx.guild.id)))
            await self.chatbotdisable(ctx)
            
            return
        elif result.get("chat_bot_toggle") == "false":
            embed = disnake.Embed(description=f"{config.no} The chat bot feature is already disabled!", color=config.error_embed_color)
        else:
            server_data_col.update_one(query, update)
        
        await ctx.send(embed=embed)
        
    
    ## -- SLASH COMMANDS -- ##
    
    @commands.slash_command(name="chatbot")
    async def slash_chatbot(self, inter):
        pass
    
    @slash_chatbot.sub_command(name="channel", description="Set where the chat bot should respond to messages.")
    @is_moderator(manage_guild=True)
    @server_setting()
    async def slash_chatbotchannel(self, inter: disnake.ApplicationCommandInteraction, channel: disnake.TextChannel):
        """Set where the chat bot should respond to messages.
        Parameters
        ----------
        channel: The channel where the bot should respond to messages.
        ----------
        """
        
        data = functions.get_db_data(str(inter.guild.id))
        query = {"guild_id": str(inter.guild.id)}
        update = {"$set": {
            "chat_bot_channel": str(channel.id),
            "chat_bot_toggle": "true"
        }}
        result = server_data_col.find_one(query)

        if not result:
            server_data_col.insert_one(data)
            self.setchatbotchannel(inter, channel)
            return
        
        server_data_col.update_one(query, update)
        embed = disnake.Embed(description=f"{config.yes} The chat bot will now respond to messages in {channel.mention}.", color=config.success_embed_color)
        
        await inter.send(embed=embed)
        
    @slash_chatbot.sub_command(name="toggle", description="Toggle the chat bot feature.")
    @is_moderator(manage_guild=True)
    @server_setting()
    async def slash_chatbottoggle(self, inter: disnake.ApplicationCommandInteraction, toggle: bool):
        """Toggle the chat bot feature.
        Parameters
        ----------
        toggle: Whether the chat bot should be enabled or not.
        """
        
        data = functions.get_db_data(str(inter.guild.id))
        query = {"guild_id": str(inter.guild.id)}
        update = {"$set": {
            "chat_bot_toggle": str(toggle).lower()
        }}
        result = server_data_col.find_one(query)
        
        embed = disnake.Embed(description=f"{config.yes} The chat bot feature has been " + "enabled" if toggle else "disabled" + ".", color=config.success_embed_color)

        if not result:
            server_data_col.insert_one(data)
            await self.slash_chatbottoggle(inter, toggle)
            
            return
        elif result.get("chat_bot_toggle") == str(toggle).lower():
            embed = disnake.Embed(description=f"{config.no} The chat bot feature is already " + "enabled" if toggle else "disabled" + "!", color=config.error_embed_color)
        else:
            server_data_col.update_one(query, update)
        
        await inter.send(embed=embed)
    
    
    ## -- TEXT COMMAND ERRORS -- ##
    
    @chatbotchannel.error 
    async def chatbotchannel_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions[0].capitalize()}` permission.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = disnake.Embed(description=f"{config.no} Please provide a channel!", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, SettingsLocked):
            embed = disnake.Embed(description=f"{config.no} The server's settings are locked.", color=config.error_embed_color)
            await ctx.send(embed=embed)
            
    @chatbotenable.error
    async def chatbotenable_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions[0].capitalize()}` permission.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, SettingsLocked):
            embed = disnake.Embed(description=f"{config.no} The server's settings are locked.", color=config.error_embed_color)
            await ctx.send(embed=embed)
            
    @chatbotdisable.error
    async def chatbotdisable_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions[0].capitalize()}` permission.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, SettingsLocked):
            embed = disnake.Embed(description=f"{config.no} The server's settings are locked.", color=config.error_embed_color)
            await ctx.send(embed=embed)
    
    ### -- SLASH COMMAND ERRORS -- ##
    
    @slash_chatbotchannel.error
    async def slash_chatbotchannel_error(self, inter: disnake.ApplicationCommandInteraction, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions[0].capitalize()}` permission.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error, SettingsLocked):
            embed = disnake.Embed(description=f"{config.no} The server's settings are locked.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        
    @slash_chatbottoggle.error
    async def slash_chatbotchannel_error(self, inter: disnake.ApplicationCommandInteraction, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions[0].capitalize()}` permission.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error, SettingsLocked):
            embed = disnake.Embed(description=f"{config.no} The server's settings are locked.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
            
    
def setup(bot):
    bot.add_cog(Command(bot))