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
import config

load_dotenv()

## -- VARIABLES -- ##

mongo_login = os.environ.get("MONGO_LOGIN")
client = MongoClient(f"{mongo_login}",tlsCAFile=certifi.where())
db = client["db2"]

server_data_col = db["server_data"]
muted_users_col = db["muted_users"]
privacy_settings_col = db["privacy_settings"]

type_list = commands.option_enum({"message delete": "message_delete", "message bulk delete": "message_bulk_delete", "message edit": "message_edit"})
category_list = commands.option_enum({"messages": "messages", "members": "members", "channels": "channels"})

categories = {
    "messages": {
        "message_delete_logs_channel": "Message deletion",
        "message_bulk_delete_logs_channel": "Bulk message deletion",
        "message_edit_logs_channel": "Message edit",
    },
    "members": {
        "member_join_logs_channel": "Member join",
        "member_remove_logs_channel": "Member leave",
        "member_update_logs_channel": "Member update",
        "user_update_logs_channel": "User update",
    },
    "channels": {
        "guild_channel_delete_logs_channel": "Channel deletion",
        "guild_channel_create_logs_channel": "Channel creation",
        "guild_channel_update_logs_channel": "Channel update",
    },
}

## -- FUNCTIONS -- ##

async def get_update_dictionary(category_name: str, channel_id: int):

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

## -- COG -- ##

class EditLogCategory(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    @commands.has_permissions(manage_guild=True)
    async def editlogcategory(self, ctx, category: str, channel: disnake.TextChannel):
        """Edit log categories, changing channel for each log type in the category."""
        
        data = {
            "guild_id": str(ctx.guild.id),
            "message_delete_logs_channel": "None",
            "message_edit_logs_channel": "None",
            "message_bulk_delete_logs_channel": "None"
        }
        query = {"guild_id": str(ctx.guild.id)}
        result = server_data_col.find_one(query)
        if not result:
            server_data_col.insert_one(data)
            return

        if result["settings_locked"] == "true":
            embed = disnake.Embed(description=f"{config.no} The server's settings are locked.", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
        elif not result["settings_locked"]:
            update = {"$set": {
                "settings_locked": "false"
            }}
            server_data_col.update_one(query, update)

        if not categories[category.lower()]:
            embed = disnake.Embed(description=f"{config.no} Please provide a valid category!\nCategories:\n```messages, members, channels```", color=config.error_embed_color)
            await ctx.send(embed=embed)
        if not channel:
            update_dict = await get_update_dictionary(category, "None")
            update = {"$set": update_dict}
            embed = disnake.Embed(description=f"{config.yes} All {category.lower()[:-1]} logs have been disabled", color=config.success_embed_color)
        
        update_dict = await get_update_dictionary(category, str(channel.id))
        update = {"$set": update_dict}
        server_data_col.update_one(query, update)

        embed = disnake.Embed(description=f"{config.yes} All {category.lower()[:-1]} logs will now be sent in {channel.mention}.", color=config.success_embed_color)
        await ctx.send(embed=embed)
    
    @editlogcategory.error 
    async def editlogchannel_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `Manage Guild` permission.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            missing_argument = error.param.name
            if missing_argument == "category":
                embed = disnake.Embed(description=f"{config.no} Please provide a category!\nCategories: ```messages, members, channels```", color=config.error_embed_color)
                await ctx.send(embed=embed)
            elif missing_argument == "channel":
                embed = disnake.Embed(description=f"{config.no} Please provide a channel!",
                                      color=config.error_embed_color)
                await ctx.send(embed=embed)
        
    
def setup(bot):
    bot.add_cog(EditLogCategory(bot))