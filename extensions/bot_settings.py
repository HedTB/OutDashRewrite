## -- IMPORTING -- ##

# MODULES
from discord import Sticker
import disnake
import os
import certifi

from disnake.ext import commands
from pymongo import MongoClient
from dotenv import load_dotenv

# FILES
from utils import config
from utils import functions
from utils.checks import *
from utils.classes import *

## -- VARIABLES -- ##

load_dotenv()

# SECRETS
mongo_login = os.environ.get("MONGO_LOGIN")

# DATABASE
client = MongoClient(mongo_login, tlsCAFile=certifi.where())
db = client[config.database_collection]

server_data_col = db["server_data"]
warns_col = db["warns"]

# OTHER
categories = {
    "messages": {
        "message_delete": "Message deletion",
        "message_edit": "Bulk message deletion",
        "message_bulk_delete": "Message edit"
    },
    "members": {
        "member_join": "Member join",
        "member_remove": "Member leave",
        "member_update": "Member update",
        "user_update": "User update",
        "member_ban": "Member ban",
        "member_unban": "Member unban",
    },
    "channels": {
        "guild_channel_delete": "Channel deletion",
        "guild_channel_create": "Channel creation",
        "guild_channel_update": "Channel update",
    },
    "roles": {
        "guild_role_create": "Role creation",
        "guild_role_delete": "Role deletion",
        "guild_role_update": "Role update",
    },
    "guilds": {
        "guild_update": "Guild update",
        "guild_emojis_update": "Guild emojis update",
        "guild_stickers_update": "Guild stickers update",
    },
    "voice_channels": {
        "voice_channel_join": "Voice channel join",
        "voice_channel_leave": "Voice channel leave",
    },
}
embed_values = [
    "title", "description", "author_name",
    "author_icon", "footer_text", "footer_icon",
    "timestamp", "thumbnail", "color"
]

## -- FUNCTIONS -- ##

def find_log_type(log_type_search: str):
    for category in categories:
        for log_type in categories[category]:
            if log_type == log_type_search:
                return log_type + "_logs_webhook", categories[category][log_type]

    return None

async def get_update_dictionary(bot, category_name: str, channel_id: int):
    category = categories.get(category_name)
    dictionary = dict()

    for log_type in category:
        webhook = await get_webhook(bot, bot.get_channel(channel_id))
        insert_value = {str(log_type) + "_logs_webhook": str(webhook.url)}
        dictionary.update(insert_value)

    return dictionary

async def get_webhook(bot: commands.Bot, channel: disnake.TextChannel, can_create: bool = True):
    webhooks = await channel.webhooks()
    
    for webhook in webhooks:
        if webhook.name == "OutDash Logging":
            return webhook

    if can_create == True:
        return await channel.create_webhook(name="OutDash Logging", avatar=bot.avatar)
    return

## -- COG -- ##

class BotSettings(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

## -- TEXT COMMANDS -- ##
    
    """
    ! SETTING LOCKING
    
    These commands locks/unlocks the settings for the server.
    """
    
    @commands.group(name="settings")
    async def settings(self, ctx: commands.Context):
        if ctx.invoked_subcommand == self.settings or None:
            return

    @settings.command()
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    @commands.has_permissions(administrator=True)
    async def lock(self, ctx: commands.Context):
        """Locks the server's settings."""
        
        guild_data_obj = GuildData(ctx.guild)
        guild_data = guild_data_obj.get_data()
        
        if guild_data.get("settings_locked") == "true":
            embed = disnake.Embed(description=f"{config.no} The server's settings are already locked!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
            
        embed = disnake.Embed(description=f"{config.yes} The server's settings are now locked.", color=config.success_embed_color)
        
        guild_data_obj.update_data({ "settings_locked": "false" })
        await ctx.send(embed=embed)

    @settings.command()
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    @commands.has_permissions(administrator=True)
    async def unlock(self, ctx: commands.Context):
        """Unlocks the server's settings."""
        
        guild_data_obj = GuildData(ctx.guild)
        guild_data = guild_data_obj.get_data()
        
        if guild_data.get("settings_locked") == "false":
            embed = disnake.Embed(description=f"{config.no} The server's settings aren't locked!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
            
        embed = disnake.Embed(description=f"{config.yes} The server's settings are now unlocked.", color=config.success_embed_color)
        
        guild_data_obj.update_data({ "settings_locked": "true" })
        await ctx.send(embed=embed)
        
    
    """
    ! SERVER SETTING COMMANDS
    
    These commands changes the way OutDash behaves in servers.
    """
    
    @commands.command(aliases=["changeprefix", "prefix"])
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    @is_moderator(manage_guild=True)
    @server_setting()
    async def setprefix(self, ctx: commands.Context, new_prefix: str):
        """Changes the server prefix."""
        
        guild_data_obj = GuildData(ctx.guild)
        guild_data = guild_data_obj.get_data()

        if guild_data.get("prefix") == new_prefix:
            embed = disnake.Embed(description=f"{config.no} The prefix is already set to `{new_prefix}`.", color=config.error_embed_color)
            return await ctx.send(embed=embed)

        embed = disnake.Embed(description=f"{config.yes} Changed the prefix to `{new_prefix}` successfully.", color=config.success_embed_color)
        
        guild_data_obj.update_data({ "prefix": new_prefix })
        await ctx.send(embed=embed)
        
    ## -- SLASH COMMANDS -- ##
    
    """
    ! SETTING LOCKING
    
    These commands locks/unlocks the settings for the server.
    """
    
    @commands.slash_command(name="settings")
    @commands.has_permissions(administrator=True)
    async def slash_settings(self, inter):
        pass
    
    @slash_settings.sub_command(name="lock", description="Locks the server's settings.")
    async def slash_settings_lock(self, inter: disnake.ApplicationCommandInteraction):
        """Locks the server's settings."""
        
        guild_data_obj = GuildData(inter.guild)
        guild_data = guild_data_obj.get_data()
        
        if guild_data.get("settings_locked") == "true":
            embed = disnake.Embed(description=f"{config.no} The server's settings are already locked!", color=config.error_embed_color)
            return await inter.send(embed=embed, ephemeral=True)
            
        embed = disnake.Embed(description=f"{config.yes} The server's settings are now locked.", color=config.success_embed_color)
        
        guild_data_obj.update_data({ "settings_locked": "true" })
        await inter.send(embed=embed)


    @slash_settings.sub_command(name="unlock", description="Unlocks the server's settings.")
    async def slash_settings_unlock(self, inter: disnake.ApplicationCommandInteraction):
        """Unlocks the server's settings."""
        
        guild_data_obj = GuildData(inter.guild)
        guild_data = guild_data_obj.get_data()
        
        if guild_data.get("settings_locked") == "false":
            embed = disnake.Embed(description=f"{config.no} The server's settings aren't locked!", color=config.error_embed_color)
            return await inter.send(embed=embed, ephemeral=True)
            
        embed = disnake.Embed(description=f"{config.yes} The server's settings are now unlocked.", color=config.success_embed_color)
        
        guild_data_obj.update_data({ "settings_locked": "false" })
        await inter.send(embed=embed)



    """
    ! SERVER SETTING COMMANDS
    
    These commands changes the way OutDash behaves in servers.
    """

    @commands.slash_command(name="setprefix", description="Change the prefix for text commands.")
    @is_moderator(manage_guild=True)
    @server_setting()
    async def slash_setprefix(self, inter: disnake.ApplicationCommandInteraction, new_prefix: str):
        """Change the prefix for text commands.
        Parameters
        ----------
        new_prefix: What you want your new prefix to be.
        """

        guild_data_obj = GuildData(inter.guild)
        guild_data = guild_data_obj.get_data()

        if guild_data.get("prefix") == new_prefix:
            embed = disnake.Embed(description=f"{config.no} The prefix is already set to `{new_prefix}`.", color=config.error_embed_color)
            return await inter.send(embed=embed, ephemeral=True)

        embed = disnake.Embed(description=f"{config.yes} Changed the prefix to `{new_prefix}` successfully.", color=config.success_embed_color)
        
        guild_data_obj.update_data({ "prefix": new_prefix })
        await inter.send(embed=embed)
            
            
    
    """
    ! LOGS SETTING COMMANDS
    
    These commands edits how OutDash logs events in servers.
    """
    
    @commands.group(name="editlogs")
    async def editlogs(self, ctx: commands.Context):
        if not ctx.invoked_subcommand:
            return
        
    @editlogs.command(name="channel")
    @is_moderator(manage_guild=True)
    @server_setting()
    async def editlogs_channel(self, ctx: commands.Context, log_type: str, channel: disnake.TextChannel = None):
        """Edit the log channels, AKA where the logs will be sent."""

        guild_data_obj = GuildData(ctx.guild)
        log_type, log_description = find_log_type(f"{type.lower()}_logs_webhook")
            
        webhook = await get_webhook(self.bot, channel)
        embed = disnake.Embed(description=f"{config.yes} {log_description} logs will now be sent in {channel.mention}.", color=config.success_embed_color)

        guild_data_obj.update_data({ str(log_type): str(webhook.url) })
        await ctx.send(embed=embed)
        
    @editlogs.command(name="category")
    @is_moderator(manage_guild=True)
    @server_setting()
    async def editlogs_category(self, ctx: commands.Context, category: str, channel: disnake.TextChannel = None):
        """Edit log categories, changing channel for each log type in the category."""

        guild_data_obj = GuildData(ctx.guild)

        if not categories[category.lower()]:
            embed = disnake.Embed(description=f"{config.no} Please provide a valid category!\nCategories:\n```messages, members, channels```", color=config.error_embed_color)
            await ctx.send(embed=embed)
        if not channel:
            update_dict = await get_update_dictionary(category, "None")
            embed = disnake.Embed(description=f"{config.yes} All {category.lower()[:-1]} logs have been disabled", color=config.success_embed_color)
        
        update_dict = await get_update_dictionary(category, str(channel.id))
        embed = disnake.Embed(description=f"{config.yes} All {category.lower()[:-1]} logs will now be sent in {channel.mention}.", color=config.success_embed_color)

        guild_data_obj.update_data(update_dict)
        await ctx.send(embed=embed)
        
    
    """
    ! WELCOME/GOODBYE SETTING COMMANDS
    
    These commands manages the welcome/goodbye features
    """
    
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

        guild_data_obj = GuildData(ctx.guild)

        if toggle.lower() == "on" or toggle.lower() == "true" or toggle.lower() == "yes" or toggle.lower() == "enabled":
            update = { "welcome_toggle": "true" }
            
            embed = disnake.Embed(description=f"{config.yes} Welcome messages have been enabled.", color=config.success_embed_color)
        elif toggle.lower() == "off" or toggle.lower() == "false" or toggle.lower() == "no" or toggle.lower() == "disabled":
            update = { "welcome_toggle": "false" }
            
            embed = disnake.Embed(description=f"{config.yes} Welcome messages have been disabled.", color=config.success_embed_color)
        else:
            embed = disnake.Embed(description=f"{config.no} Please give a valid toggle value!\nToggles:\n```on, yes, true, enabled - welcome messages enabled\noff, no, false, disabled - welcome messages disabled```", color=config.error_embed_color)
            
        guild_data_obj.update_data(update)
        await ctx.send(embed=embed)
    
    @editwelcome.command(name="content")
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    @is_moderator(manage_guild=True)
    @server_setting()
    async def editwelcomecontent(self, ctx: commands.Context, *, content: str):
        """Edit the welcome message content."""

        guild_data_obj = GuildData(ctx.guild)
        embed = disnake.Embed(description=f"{config.yes} The welcome message content has been set to:\n`{content}`", color=config.success_embed_color)
        
        guild_data_obj.update_data({ "welcome_message_content": content })
        await ctx.send(embed=embed)
    
    @editwelcome.command(name="embed")
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    @is_moderator(manage_guild=True)
    @server_setting()
    async def editwelcomeembed(self, ctx: commands.Context, embed_part: str, *, value: str):
        """Edit the welcome message embed."""
        
        embed_part = embed_part.lower()
        guild_data_obj = GuildData(ctx.guild)
        
        if not embed_part in embed_values:
            embed = disnake.Embed(description=f"{config.no} Please specify a valid part of the embed!\nEmbed parts:\n```{', '.join(e for e in embed_values)}```", color=config.error_embed_color)
            return await ctx.send(embed=embed)
        
        embed = disnake.Embed()
        
        guild_data_obj.update_data({
            "welcome_embed_{}".format(embed_part): value
        })
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
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions[0].capitalize()}` permission.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = disnake.Embed(description=f"{config.no} You need to specify the new prefix.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, SettingsLocked):
            embed = disnake.Embed(description=f"{config.no} The server's settings are locked.", color=config.error_embed_color)
            await ctx.send(embed=embed)

    
    ## -- SLASH COMMAND ERRORS -- ##
    
    @slash_settings.error
    async def slash_settings_lock_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions[0].capitalize()}` permission.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed)
    
    @slash_setprefix.error
    async def prefix_error(self, inter, error):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions[0].capitalize()}` permission.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = disnake.Embed(description=f"{config.no} You need to specify the new prefix.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error, SettingsLocked):
            embed = disnake.Embed(description=f"{config.no} The server's settings are locked.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(BotSettings(bot))