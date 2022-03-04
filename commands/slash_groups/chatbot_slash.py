## -- IMPORTING -- ##

# MODULES
import disnake
import os
import random
import asyncio
import datetime
import certifi
import json

from disnake.ext import commands
from disnake.errors import Forbidden, HTTPException
from disnake.ext.commands import errors
from pymongo import MongoClient
from dotenv import load_dotenv

# FILES
import extra.config as config
import extra.functions as functions
from extra.checks import is_moderator, server_setting, SettingsLocked

load_dotenv()

## -- VARIABLES -- ##

mongo_login = os.environ.get("MONGO_LOGIN")
client = MongoClient(f"{mongo_login}",tlsCAFile=certifi.where())
db = client["db"]

server_data_col = db["server_data"]
muted_users_col = db["muted_users"]
privacy_settings_col = db["privacy_settings"]

## -- FUNCTIONS -- ##



## -- COG -- ##

class ChatbotSlash(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
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

        if not result:
            server_data_col.insert_one(data)
            self.slash_chatbottoggle(inter, toggle)
            return
        
        embed = disnake.Embed(description=f"{config.yes} The chat bot has been " + "enabled" if toggle else "disabled" + ".", color=config.success_embed_color)
        
        server_data_col.update_one(query, update)
        await inter.send(embed=embed)
    
        
    @slash_chatbotchannel.error
    async def slash_chatbotchannel_error(self, inter: disnake.ApplicationCommandInteraction, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions}` permission.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error, SettingsLocked):
            embed = disnake.Embed(description=f"{config.no} The server's settings are locked.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
    
        
    @slash_chatbottoggle.error
    async def slash_chatbotchannel_error(self, inter: disnake.ApplicationCommandInteraction, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions}` permission.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error, SettingsLocked):
            embed = disnake.Embed(description=f"{config.no} The server's settings are locked.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        
    
def setup(bot):
    bot.add_cog(ChatbotSlash(bot))