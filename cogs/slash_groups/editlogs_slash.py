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

load_dotenv()

## -- VARIABLES -- ##

mongo_login = os.environ.get("MONGO_LOGIN")
client = MongoClient(f"{mongo_login}",tlsCAFile=certifi.where())
db = client["db"]

server_data_col = db["server_data"]
muted_users_col = db["muted_users"]
privacy_settings_col = db["privacy_settings"]

type_list = commands.option_enum({"message delete": "message_delete", "message bulk delete": "message_bulk_delete", "message edit": "message_edit", "member join": "member_join"})
category_list = commands.option_enum({"messages": "messages", "members": "members", "channels": "channels"})

categories = {
    "messages": {
        "message_delete_logs_webhook": "Message deletion",
        "message_bulk_delete_logs_webhook": "Bulk message deletion",
        "message_edit_logs_webhook": "Message edit",
    },
    "members": {
        "member_join_logs_webhook": "Member join",
        "member_remove_logs_webook": "Member leave",
        "member_update_logs_webhook": "Member update",
        "user_update_logs_webhook": "User update",
    },
    "channels": {
        "guild_channel_delete_logs_webhook": "Channel deletion",
        "guild_channel_create_logs_webhook": "Channel creation",
        "guild_channel_update_logs_webhook": "Channel update",
    },
}

## -- FUNCTIONS -- ##

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

async def get_update_dictionary(bot, category_name: str, channel_id: str):

    category = categories.get(category_name)
    dictionary = dict()

    for i, v in enumerate(category):
        webhook = await get_webhook(bot, bot.get_channel(int(channel_id)))
        insert_value = {str(v): str(webhook.url)}
        dictionary.update(insert_value)

    return dictionary

async def find_log_type(log_type: str):

    for i in categories:
        for v in categories[i]:
            if v == log_type:
                return v, categories[i][v]

    return None

## -- COG -- ##

class EditLogsSlash(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.slash_command(name="logs")
    async def slash_logs(self, inter):
        pass

    @slash_logs.sub_command_group()
    async def edit(self, inter):
        pass
    
    @edit.sub_command(name="category", description="Edit log categories, changing channel for each log type in the category.")
    @commands.has_permissions(manage_guild=True)
    async def slash_editlogcategory(self, inter: disnake.ApplicationCommandInteraction, category: category_list, channel: disnake.TextChannel = None):
        """Edit log categories, changing channel for each log type in the category..
        Parameters
        ----------
        category: The category you want to edit logs for.
        channel: The channel to send the logs to. If none, the log types will be disabled.
        """
        
        data = await functions.get_db_data(inter.guild.id)
        query = {"guild_id": str(inter.guild.id)}
        result = server_data_col.find_one(query)
        if not result:
            server_data_col.insert_one(data)
            return
        if not channel:
            update_dict = await get_update_dictionary(self.bot, category, "None")
            update = {"$set": update_dict}
            embed = disnake.Embed(description=f"{config.yes} All {category.lower()[:-1]} logs have been disabled", color=config.success_embed_color)
        
        update_dict = await get_update_dictionary(self.bot, category, str(channel.id))
        update = {"$set": update_dict}
        server_data_col.update_one(query, update)

        embed = disnake.Embed(description=f"{config.yes} All {category.lower()[:-1]} logs will now be sent in {channel.mention}.", color=config.success_embed_color)
        await inter.send(embed=embed)

    @edit.sub_command(name="channel", description="Change where a log type should be sent.")
    @commands.has_permissions(manage_guild=True)
    async def slash_editlogchannel(self, inter: disnake.ApplicationCommandInteraction, type: type_list, channel: disnake.TextChannel = None):
        """Change where a log type should be sent.
        Parameters
        ----------
        type: What you want to edit. Example: "message_delete" would edit where deleted messages should be sent.
        channel: Where the selected log type should be sent. If none, the log type will be disabled.
        """
        
        data = {
            "guild_id": str(inter.guild.id),
            "message_delete_logs_webhook": "None",
            "message_edit_logs_webhook": "None",
            "message_bulk_delete_logs_webhook": "None"
        }
        query = {"guild_id": str(inter.guild.id)}
        result = server_data_col.find_one(query)
        log_type, log_description = await find_log_type(f"{type.lower()}_logs_webhook")
        
        if not result:
            server_data_col.insert_one(data)
            return
        if not channel:
            update = {"$set": {log_type: "None"}}
            server_data_col.update_one(query, update)
            embed = disnake.Embed(description=f"{config.yes} {log_description} logs have now been disabled.", color=config.success_embed_color)
            await inter.send(embed=embed)
            return
            
        webhook = await get_webhook(self.bot, channel)
        update = {"$set": {str(log_type): str(webhook.url)}}
        embed = disnake.Embed(description=f"{config.yes} {log_description} logs will now be sent in {channel.mention}.", color=config.success_embed_color)

        server_data_col.update_one(query, update)
        await inter.send(embed=embed)

        
    @slash_editlogchannel.error 
    async def slash_editlogchannel_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `Manage Guild` permission.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error, commands.MissingRequiredArgument):
            missing_argument = error.param.name
            if missing_argument == "type":
                embed = disnake.Embed(description=f"{config.no} Please provide a type!\nTypes: ```message_delete: The channel where deleted messages will be logged."
                                      "\nmessage_bulk_delete: The channel where bulk deleted messages will be logged."
                                      "\nmessage_edit: The channel where edited messages will be logged.```", color=config.error_embed_color)
                await inter.response.send_message(embed=embed, ephemeral=True)
            elif missing_argument == "channel":
                embed = disnake.Embed(description=f"{config.no} Please provide a channel!",
                                      color=config.error_embed_color)
                await inter.response.send_message(embed=embed, ephemeral=True)
        
    
def setup(bot):
    bot.add_cog(EditLogsSlash(bot))