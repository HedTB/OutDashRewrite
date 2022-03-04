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
from extra.checks import *

load_dotenv()

## -- VARIABLES -- ##

mongo_login = os.environ.get("MONGO_LOGIN")
client = MongoClient(f"{mongo_login}",tlsCAFile=certifi.where())
db = client[config.database_collection]

server_data_col = db["server_data"]
muted_users_col = db["muted_users"]
user_data_col = db["user_data"]

type_list = commands.option_enum({"message delete": "message_delete", "message bulk delete": "message_bulk_delete", "message edit": "message_edit"})
category_list = commands.option_enum({"messages": "messages", "members": "members", "channels": "channels"})

categories = {
    "messages": {
        "message_delete_logs_webhook": "Message deletion",
        "message_bulk_delete_logs_webhook": "Bulk message deletion",
        "message_edit_logs_webhook": "Message edit",
    },
    "members": {
        "member_join_logs_webhook": "Member join",
        "member_remove_logs_webhook": "Member leave",
        "member_update_loga": "Member update",
        "user_update_logs_webhook": "User update",
    },
    "channels": {
        "guild_channel_delete_logs_webhook": "Channel deletion",
        "guild_channel_create_logs_webhook": "Channel creation",
        "guild_channel_update_logs_webhook": "Channel update",
    },
}

## -- FUNCTIONS -- ##

async def get_update_dictionary(category_name: str, channel_id: str):

    category = categories.get(category_name)
    dictionary = dict()

    for i, v in enumerate(category):
        insert_value = {str(v): str(channel_id)}
        dictionary.update(insert_value)

    return dictionary

async def find_log_type(log_type: str):

    for i in categories:
        for v in categories[i]:
            if v == log_type:
                return v, categories[i][v]

    return None

async def get_webhook(bot: commands.Bot, channel: disnake.TextChannel, can_create: bool=True):
    webhooks = await channel.webhooks()
    for i in webhooks:
        if i.name == "OutDash Logging":
            return i

    if can_create == True:
        webhook = await channel.create_webhook(name="OutDash Logging", avatar=bot.avatar)
        return webhook
    else:
        return None

## -- COG -- ##

class EditLogChannel(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    @commands.has_permissions(manage_guild=True)
    async def editlogchannel(self, ctx, type: str, channel: disnake.TextChannel = None):
        """Edit log channels, AKA where the logs should be sent."""
        
        data = functions.get_db_data(str(ctx.guild.id))
        query = {"guild_id": str(ctx.guild.id)}
        result = server_data_col.find_one(query)
        log_type, log_description = await find_log_type(f"{type.lower()}_logs_webhook")
        
        if not result:
            server_data_col.insert_one(data)
            await self.editlogchannel(ctx, type, channel)
            return
            
        if not channel:
            update = {"$set": {log_type: "None"}}
            server_data_col.update_one(query, update)
            embed = disnake.Embed(description=f"{config.yes} {log_description} logs have now been disabled.", color=config.success_embed_color)
            await ctx.send(embed=embed)
            return
            
        webhook = await get_webhook(self.bot, channel)
        update = {"$set": {str(log_type): str(webhook.url)}}
        embed = disnake.Embed(description=f"{config.yes} {log_description} logs will now be sent in {channel.mention}.", color=config.success_embed_color)

        server_data_col.update_one(query, update)
        await ctx.send(embed=embed)
    
    @editlogchannel.error 
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
    bot.add_cog(EditLogChannel(bot))