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

class SetChatBotChannel(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    @commands.has_permissions(manage_guild=True)
    @server_setting()
    async def setchatbotchannel(self, ctx, channel: disnake.TextChannel):
        """Set where the chat bot should respond to messages."""
        
        data = functions.get_db_data(str(ctx.guild.id))
        query = {"guild_id": str(ctx.guild.id)}
        update = {"$set": {
            "chat_bot_channel": str(channel.id),
            "chat_bot_toggle": "true"
        }}
        result = server_data_col.find_one(query)

        if not result:
            server_data_col.insert_one(data)
            self.setchatbotchannel(ctx, channel)
            return
        
        server_data_col.update_one(query, update)
        embed = disnake.Embed(description=f"{config.yes} The chat bot will now respond to messages in {channel.mention}.", color=config.success_embed_color)
        
        await ctx.send(embed=embed)

    
    @setchatbotchannel.error 
    async def editlogchannel_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions}` permission.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            missing_argument = error.param.name
            if missing_argument == "type":
                embed = disnake.Embed(description=f"{config.no} Please provide a type!\nTypes: ```message_delete: The channel where deleted messages will be logged."
                                      "\nmessage_bulk_delete: The channel where bulk deleted messages will be logged."
                                      "\nmessage_edit: The channel where edited messages will be logged.```", color=config.error_embed_color)
                await ctx.send(embed=embed)
            elif missing_argument == "channel":
                embed = disnake.Embed(description=f"{config.no} Please provide a channel!",
                                      color=config.error_embed_color)
                await ctx.send(embed=embed)
        elif isinstance(error, SettingsLocked):
            embed = disnake.Embed(description=f"{config.no} The server's settings are locked.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        
    
def setup(bot):
    bot.add_cog(SetChatBotChannel(bot))