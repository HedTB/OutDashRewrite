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

mongo_login = os.environ.get("MONGO_LOGIN")
client = MongoClient(f"{mongo_login}",tlsCAFile=certifi.where())
db = client["db2"]

server_data_col = db["server_data"]
warns_col = db["warns"]

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
embed_values = [
    "title", "description", "author_name",
    "author_icon", "footer_text", "footer_icon",
    "timestamp", "thumbnail", "color"
]

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

def find_log_type(log_type: str):
    for i in categories:
        for v in categories[i]:
            if v == log_type:
                return v, categories[i][v]

    return None

## -- COG -- ##

class Logging(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        
    ## -- TEXT COMMANDS -- ##
    
    @commands.command()
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    @is_moderator(manage_guild=True)
    @server_setting()
    async def editlogcategory(self, ctx: commands.Context, category: str, channel: disnake.TextChannel):
        """Edit log categories, changing channel for each log type in the category."""
        
        data = functions.get_db_data(ctx.guild.id)
        query = {"guild_id": str(ctx.guild.id)}
        result = server_data_col.find_one(query)
        
        if not result:
            server_data_col.insert_one(data)
            await self.editlogcategory(ctx, category, channel)
            return

        if not categories[category.lower()]:
            embed = disnake.Embed(description=f"{config.no} Please provide a valid category!\nCategories:\n```messages, members, channels```", color=config.error_embed_color)
            await ctx.send(embed=embed)
        if not channel:
            update_dict = await get_update_dictionary(category, "None")
            update = {"$set": update_dict}
            embed = disnake.Embed(description=f"{config.yes} All {category.lower()[:-1]} logs have been disabled", color=config.success_embed_color)
        
        update_dict = await get_update_dictionary(category, str(channel.id))
        update = {"$set": update_dict}
        embed = disnake.Embed(description=f"{config.yes} All {category.lower()[:-1]} logs will now be sent in {channel.mention}.", color=config.success_embed_color)

        server_data_col.update_one(query, update)
        await ctx.send(embed=embed)
        
    @commands.command()
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    @is_moderator(manage_guild=True)
    async def editlogchannel(self, ctx: commands.Context,type: str, channel: disnake.TextChannel = None):
        """Edit log channels, AKA where the logs should be sent."""
        
        data = functions.get_db_data(str(ctx.guild.id))
        query = {"guild_id": str(ctx.guild.id)}
        result = server_data_col.find_one(query)
        log_type, log_description = find_log_type(f"{type.lower()}_logs_webhook")
        
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


    @commands.group(name="editwelcome")
    async def editwelcome(self, ctx: commands.Context):
        if ctx.invoked_subcommand == self.editwelcome or None:
            return
    
    @editwelcome.command(name="toggle")
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    @is_moderator(manage_guild=True)
    @server_setting()
    async def editwelcometoggle(self, ctx: commands.Context, toggle: str = "on"):
        """Toggles if welcome messages should be sent."""
        
        query = {"guild_id": str(ctx.guild.id)}
        result = server_data_col.find_one(query)
        
        if not result:
            server_data_col.insert_one(functions.get_db_data(ctx.guild.id))
            self.editwelcometoggle(ctx, toggle)
            return

        if toggle.lower() == "on" or toggle.lower() == "true" or toggle.lower() == "yes" or toggle.lower() == "enabled":
            update = {"$set": {"welcome_toggle": "true"}}
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
    
    @editwelcome.command(name="content")
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    @is_moderator(manage_guild=True)
    @server_setting()
    async def editwelcomecontent(self, ctx: commands.Context, *, content: str):
        """Edit the welcome message content."""
        
        query = {"guild_id": str(ctx.guild.id)}
        result = server_data_col.find_one(query)

        if not result:
            server_data_col.insert_one(functions.get_db_data(ctx.guild.id))
            await self.content(ctx, content)
            return
        
        embed = disnake.Embed(description=f"{config.yes} The welcome message content has been set to:\n`{content}`", color=config.success_embed_color)
        
        server_data_col.update_one(query, {"$set": {"welcome_message_content": content}})
        await ctx.send(embed=embed)
    
    @editwelcome.command(name="embed")
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    @is_moderator(manage_guild=True)
    @server_setting()
    async def editwelcomeembed(self, ctx: commands.Context, embed_part: str, *, value: str):
        """Edit the welcome message embed."""
        
        embed_part = embed_part.lower()
        
        query = {"guild_id": str(ctx.guild.id)}
        result = server_data_col.find_one(query)

        if not result:
            server_data_col.insert_one(functions.get_db_data(ctx.guild.id))
            await self.embed(ctx, embed_part, value)
            return
        if not embed_part in embed_values:
            embed = disnake.Embed(description=f"{config.no} Please specify a valid part of the embed!\nEmbed parts:\n```{', '.join(e for e in embed_values)}```", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
        
        embed = disnake.Embed()
        
        server_data_col.update_one(query, {"$set": {
            "welcome_embed_{}".format(embed_part): value
        }})
        await ctx.send(embed=embed)

    @editwelcome.command(name="channel")
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    @is_moderator(manage_guild=True)
    @server_setting()
    async def editwelcomechannel(self, ctx: commands.Context,channel: disnake.TextChannel = None):
        """Set the channel where welcome messages should be sent."""
        
        query = {"guild_id": str(ctx.guild.id)}
        result = server_data_col.find_one(query)
        update = { "$set": {
            "welcome_channel": str(channel.id)
        }}

        embed = disnake.Embed(description=f"{config.yes} Welcome messages will now be sent in <#{channel.id}>.", color=config.success_embed_color)
        
        if not result:
            server_data_col.insert_one(functions.get_db_data(str(ctx.guild_id)))
            self.setwelcomechannel(ctx, channel)
            return
        
        server_data_col.update_one(query, update)
        await ctx.send(embed=embed)
        
    ## -- SLASH COMMANDS -- ##

    @commands.slash_command(name="logs")
    async def slash_logs(self, inter):
        pass

    @slash_logs.sub_command_group()
    async def edit(self, inter):
        pass
    
    @edit.sub_command(name="category", description="Edit log categories, changing channel for each log type in the category.")
    @is_moderator(manage_guild=True)
    @server_setting()
    async def slash_editlogcategory(self, inter: disnake.ApplicationCommandInteraction, category: category_list, channel: disnake.TextChannel = None):
        """Edit log categories, changing channel for each log type in the category..
        Parameters
        ----------
        category: The category you want to edit logs for.
        channel: The channel to send the logs to. If none, the log types will be disabled.
        """
        
        data = functions.get_db_data(inter.guild.id)
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
    @is_moderator(manage_guild=True)
    @server_setting()
    async def slash_editlogchannel(self, inter: disnake.ApplicationCommandInteraction, type: type_list, channel: disnake.TextChannel = None):
        """Change where a log type should be sent.
        Parameters
        ----------
        type: What you want to edit. Example: "message_delete" would edit where deleted messages should be sent.
        channel: Where the selected log type should be sent. If none, the log type will be disabled.
        """
        
        query = {"guild_id": str(inter.guild.id)}
        result = server_data_col.find_one(query)
        log_type, log_description = find_log_type(f"{type.lower()}_logs_webhook")
        
        if not result:
            server_data_col.insert_one(functions.get_db_data(inter.guild.id))
            return
        if not channel:
            update = {"$set": {log_type: "None"}}
            embed = disnake.Embed(description=f"{config.yes} {log_description} logs have now been disabled.", color=config.success_embed_color)
            
            server_data_col.update_one(query, update)
            await inter.send(embed=embed)
            return
            
        webhook = await get_webhook(self.bot, channel)
        update = {"$set": {str(log_type): str(webhook.url)}}
        embed = disnake.Embed(description=f"{config.yes} {log_description} logs will now be sent in {channel.mention}.", color=config.success_embed_color)

        server_data_col.update_one(query, update)
        await inter.send(embed=embed)

    ## -- TEXT COMMAND ERRORS -- ##
    
    @editlogcategory.error
    async def editlogchannel_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions[0].capitalize()}` permission.", color=config.error_embed_color)
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
        elif isinstance(error, SettingsLocked):
            embed = disnake.Embed(description=f"{config.no} The server's settings are locked.", color=config.error_embed_color)
            await ctx.send(embed=embed)
            
    @editlogchannel.error
    async def editlogchannel_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions[0].capitalize()}` permission.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            missing_argument = error.param.name
            if missing_argument == "type":
                embed = disnake.Embed(description=f"{config.no} Please provide a log type!\nLog types: """"```
                message_delete, message_edit, message_bulk_delete,
                member_join, member_remove, member_update
                """, color=config.error_embed_color)
                await ctx.send(embed=embed)
            elif missing_argument == "channel":
                embed = disnake.Embed(description=f"{config.no} Please provide a channel!",
                                      color=config.error_embed_color)
                await ctx.send(embed=embed)
        elif isinstance(error, SettingsLocked):
            embed = disnake.Embed(description=f"{config.no} The server's settings are locked.", color=config.error_embed_color)
            await ctx.send(embed=embed)
    
    @editwelcomeembed.error 
    async def editwelcomeembed_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions[0].capitalize()}` permission.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = disnake.Embed(description=f"{config.no} Please specify a toggle value!\nToggles:\n```on, yes, true, enabled - welcome messages enabled\noff, no, false, disabled - welcome messages disabled```", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, SettingsLocked):
            embed = disnake.Embed(description=f"{config.no} The server's settings are locked.", color=config.error_embed_color)
            await ctx.send(embed=embed)
            
    @editwelcomecontent.error
    async def editwelcomecontent_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions[0].capitalize()}` permission.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = disnake.Embed(description=f"{config.no} Please specify what the welcome message content should be set to.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, SettingsLocked):
            embed = disnake.Embed(description=f"{config.no} The server's settings are locked.", color=config.error_embed_color)
            await ctx.send(embed=embed)
    
    @editwelcometoggle.error
    async def editwelcometoggle_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions[0].capitalize()}` permission.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = disnake.Embed(description=f"{config.no} Please specify a toggle value!\nToggles:\n```on, yes, true, enabled - welcome messages enabled\noff, no, false, disabled - welcome messages disabled```", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, SettingsLocked):
            embed = disnake.Embed(description=f"{config.no} The server's settings are locked.", color=config.error_embed_color)
            await ctx.send(embed=embed)
    
    @editwelcomechannel.error 
    async def setwelcomechannel_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions[0].capitalize()}` permission.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = disnake.Embed(description=f"{config.no} Please specify a channel!\n If you're looking to disable the welcome message, run `{self.bot.get_prefix}editwelcome toggle off`.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, SettingsLocked):
            embed = disnake.Embed(description=f"{config.no} The server's settings are locked.", color=config.error_embed_color)
            await ctx.send(embed=embed)

    ## -- SLASH COMMAND ERRORS -- ##
        
    @slash_editlogchannel.error 
    async def slash_editlogchannel_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions[0].capitalize()}` permission.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error, SettingsLocked):
            embed = disnake.Embed(description=f"{config.no} The server's settings are locked.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
            
    @slash_editlogcategory.error
    async def slash_editlogcategory_error(self, inter: disnake.ApplicationCommandInteraction, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions[0].capitalize()}` permission.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error, SettingsLocked):
            embed = disnake.Embed(description=f"{config.no} The server's settings are locked.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)

    
def setup(bot):
    bot.add_cog(Logging(bot))