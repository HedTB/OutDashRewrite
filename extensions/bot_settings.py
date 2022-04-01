## -- IMPORTING -- ##

# MODULES
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
    "guild": {
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
message_settings_description = {
    "message_content": "message content"
}

embed_parts_choices = commands.option_enum({
    "Title": "title", "Description": "description",
    "Timestamp": "timestamp", "Thumbnail": "thumbnail", "Color": "color",
    
    "Author name": "author_name", "Author url": "author_url", "Author icon": "author_icon",
    "Footer text": "footer_text", "Footer icon": "footer_icon",
})
message_settings_types = commands.option_enum({"message content": "message_content"})
type_list = commands.option_enum({
    "Message deletion": "message_delete", "Message bulk deletion": "message_bulk_delete", "Message edit": "message_edit", "Member join": "member_join", "Member leave": "member_remove",
    "User update": "user_update", "Member ban": "member_ban", "Member unban": "member_unban",
    "Channel creation": "guild_channel_create", "Channel deletion": "guild_channel_delete", "Channel update": "guild_channel_update",
    "Role creation": "guild_role_create", "Role deletion": "guild_role_delete", "Role update": "guild_role_update",
    "Server update": "guild_update", "Voice channel join": "voice_channel_join", "Voice leave": "voice_channel_leave"
})
category_list = commands.option_enum({"messages": "messages", "members": "members", "channels": "channels", "server": "guild"})

## -- FUNCTIONS -- ##

def find_log_type(log_type_search: str):
    for category in categories:
        for log_type in categories[category]:
            if log_type == log_type_search:
                return log_type, categories[category][log_type]

    return None

def get_embed_update(current_embed: dict, embed_part: str, value: str):
    if embed_part.startswith("author") or embed_part.startswith("footer"):
        top_part = embed_part[0:6]
        sub_part = embed_part[:7]
        
        current_embed[top_part][sub_part] = value
    else:
        current_embed[embed_part] = value
        
    return current_embed

async def get_update_dictionary(bot, category_name: str, channel: disnake.TextChannel | None) -> dict:
    category = categories.get(category_name)
    dictionary = dict()

    for log_type in category:
        if channel:
            webhook = await get_webhook(bot, channel)
            dictionary.update({ log_type: { "url": webhook.url, "toggle": True } })
        else:
            dictionary.update({ log_type: { "url": None, "toggle": False } })

    return dictionary

async def get_webhook(bot: commands.Bot, channel: disnake.TextChannel, can_create: bool = True) -> disnake.Webhook:
    webhooks = await channel.webhooks()
    
    for webhook in webhooks:
        if webhook.name == f"{bot.user.name} Logging":
            return webhook

    if can_create:
        return await channel.create_webhook(name=f"{bot.user.name} Logging", avatar=bot.avatar)
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
    @commands.cooldown(1, config.cooldown_time, commands.BucketType.member)
    @commands.has_permissions(administrator=True)
    async def lock(self, ctx: commands.Context):
        """Locks the server's settings."""
        
        data_obj = GuildData(ctx.guild)
        data = data_obj.get_data()
        
        if data["settings_locked"]:
            embed = disnake.Embed(description=f"{config.no} The server's settings are already locked!", color=config.error_embed_color)
            return await ctx.send(embed=embed)
            
        embed = disnake.Embed(description=f"{config.yes} The server's settings are now locked.", color=config.success_embed_color)
        
        data_obj.update_data({ "settings_locked": "false" })
        await ctx.send(embed=embed)

    @settings.command()
    @commands.cooldown(1, config.cooldown_time, commands.BucketType.member)
    @commands.has_permissions(administrator=True)
    async def unlock(self, ctx: commands.Context):
        """Unlocks the server's settings."""
        
        data_obj = GuildData(ctx.guild)
        data = data_obj.get_data()
        
        if not data["settings_locked"]:
            embed = disnake.Embed(description=f"{config.no} The server's settings aren't locked!", color=config.error_embed_color)
            return await ctx.send(embed=embed)
            
        embed = disnake.Embed(description=f"{config.yes} The server's settings are now unlocked.", color=config.success_embed_color)
        
        data_obj.update_data({ "settings_locked": "true" })
        await ctx.send(embed=embed)
        
    
    """
    ! SERVER SETTINGS
    
    These commands changes the way OutDash behaves in servers.
    """
    
    @commands.command(aliases=["changeprefix", "prefix"])
    @commands.cooldown(1, config.cooldown_time, commands.BucketType.member)
    @is_moderator(manage_guild=True)
    @server_setting()
    async def setprefix(self, ctx: commands.Context, new_prefix: str):
        """Changes the server prefix."""
        
        data_obj = GuildData(ctx.guild)
        guild_data = data_obj.get_data()

        if guild_data["prefix"] == new_prefix:
            embed = disnake.Embed(description=f"{config.no} The prefix is already set to `{new_prefix}`.", color=config.error_embed_color)
            return await ctx.send(embed=embed)

        embed = disnake.Embed(description=f"{config.yes} Changed the prefix to `{new_prefix}` successfully.", color=config.success_embed_color)
        
        data_obj.update_data({ "prefix": new_prefix })
        await ctx.send(embed=embed)
        
    
    """
    ! WELCOME/GOODBYE SETTINGS
    
    These commands manages the welcome/goodbye features
    """
    
    @commands.group(name="editwelcome")
    async def editwelcome(self, ctx: commands.Context):
        if ctx.invoked_subcommand == self.editwelcome or None:
            return
    
    @editwelcome.command(name="toggle")
    @commands.cooldown(1, config.cooldown_time, commands.BucketType.member)
    @is_moderator(manage_guild=True)
    @server_setting()
    async def editwelcome_toggle(self, ctx: commands.Context, toggle: str = "on"):
        """Toggles if welcome messages should be sent."""

        data_obj = GuildData(ctx.guild)

        if toggle.lower() == "on" or toggle.lower() == "true":
            update = { "welcome_toggle": "true" }
            embed = disnake.Embed(description=f"{config.yes} Welcome messages have been enabled.", color=config.success_embed_color)
            
        elif toggle.lower() == "off" or toggle.lower() == "false":
            update = { "welcome_toggle": "false" }
            embed = disnake.Embed(description=f"{config.yes} Welcome messages have been disabled.", color=config.success_embed_color)
        else:
            embed = disnake.Embed(description=f"{config.no} Please give a valid toggle value!\nToggles:\n```on, true - welcome messages enabled\noff, false - welcome messages disabled```", color=config.error_embed_color)
            
        data_obj.update_data(update)
        await ctx.send(embed=embed)
    
    @editwelcome.command(name="content")
    @commands.cooldown(1, config.cooldown_time, commands.BucketType.member)
    @is_moderator(manage_guild=True)
    @server_setting()
    async def editwelcome_content(self, ctx: commands.Context, *, content: str):
        """Edit the welcome message content."""

        data_obj = GuildData(ctx.guild)
        data = data_obj.get_data()
        
        welcome_message = data["welcome_message"]
        welcome_message["content"] = content
        
        embed = disnake.Embed(description=f"{config.yes} The welcome message content has been set to:\n`{content}`", color=config.success_embed_color)
        
        data_obj.update_data({ "welcome_message": welcome_message })
        await ctx.send(embed=embed)
    
    @editwelcome.command(name="embed")
    @commands.cooldown(1, config.cooldown_time, commands.BucketType.member)
    @is_moderator(manage_guild=True)
    @server_setting()
    async def editwelcome_embed(self, ctx: commands.Context, embed_part: str, *, value: str):
        """Edit the welcome message embed."""
        
        embed_part = embed_part.lower()
        data_obj = GuildData(ctx.guild)
        data = data_obj.get_data()
        
        embed_update = get_embed_update(data["welcome_message"]["embed"], embed_part, value)
        data["welcome_message"]["embed"] = embed_update
        
        if not embed_part in embed_values:
            embed = disnake.Embed(description=f"{config.no} Please specify a valid part of the embed!\nEmbed parts:\n```{', '.join(e for e in embed_values)}```", color=config.error_embed_color)
            return await ctx.send(embed=embed)
        
        embed = disnake.Embed(description=f"{config.yes} ", color=config.success_embed_color)
        
        if embed_part.startswith("author") or embed_part.startswith("footer"):
            top_part = embed_part[0:6]
            sub_part = embed_part[:7]
            
            embed.description += f"The {top_part} {sub_part} has been changed to `{value}`"
        else:
            embed.description += f"The {embed_part} has been changed to `{value}`"
        
        data_obj.update_data({ "welcome_message": data })
        await ctx.send(embed=embed)

    @editwelcome.command(name="channel")
    @commands.cooldown(1, config.cooldown_time, commands.BucketType.member)
    @is_moderator(manage_guild=True)
    @server_setting()
    async def editwelcome_channel(self, ctx: commands.Context, channel: disnake.TextChannel):
        """Set the channel where welcome messages should be sent."""
        
        data_obj = GuildData(ctx.guild)
        embed_part = embed_part.lower()

        embed = disnake.Embed(description=f"{config.yes} Welcome messages will now be sent in <#{channel.id}>.", color=config.success_embed_color)
        
        data_obj.update_data({ "welcome_channel": channel.id, "welcome_toggle": True })
        await ctx.send(embed=embed)
        
    @editwelcome.command(name="trigger")
    @commands.cooldown(1, 10, commands.BucketType.member)
    @is_moderator(manage_guild=True)
    async def editwelcome_trigger(self, ctx: commands.Context):
        """Trigger the welcome message for testing."""
        
        data_obj = GuildData(ctx.guild)
        data = data_obj.get_data()
        
        if not data["welcome_toggle"]:
            embed = disnake.Embed(description=f"{config.no} Welcome messages have been disabled for this guild.", color=config.error_embed_color)
            return await ctx.send(embed=embed)
        
        await self.bot.dispatch("welcome_member", ctx.author, kwargs={ "channel": ctx.channel })
        
    """
    ! LOGS SETTINGS
    
    These commands changes how OutDash logs events in servers.
    """
    
    @commands.group(name="editlogs", aliases=["editlogging"])
    async def editlogs(self, ctx: commands.Context):
        if not ctx.invoked_subcommand:
            return
        
    @editlogs.command(name="channel")
    @is_moderator(manage_guild=True)
    @server_setting()
    async def editlogs_channel(self, ctx: commands.Context, log_type: str, channel: disnake.TextChannel = None):
        """Edit the log channels, AKA where the logs will be sent."""

        data_obj = GuildData(ctx.guild)
        log_type, log_description = find_log_type(type.lower())
            
        webhook = await get_webhook(self.bot, channel)
        embed = disnake.Embed(description=f"{config.yes} {log_description} logs will now be sent in {channel.mention}.", color=config.success_embed_color)

        data_obj.update_data({ str(log_type): str(webhook.url) })
        await ctx.send(embed=embed)
        
    @editlogs.command(name="category")
    @is_moderator(manage_guild=True)
    @server_setting()
    async def editlogs_category(self, ctx: commands.Context, category: str, channel: disnake.TextChannel = None):
        """Edit log categories, changing channel for each log type in the category."""

        data_obj = GuildData(ctx.guild)

        if not categories[category.lower()]:
            embed = disnake.Embed(description=f"{config.no} Please provide a valid category!\nCategories:\n```messages, members, channels, roles, guild```", color=config.error_embed_color)
            await ctx.send(embed=embed)
        if not channel:
            update_dict = await get_update_dictionary(category, "None")
            embed = disnake.Embed(description=f"{config.yes} All {category.lower()[:-1]} logs have been disabled", color=config.success_embed_color)
        
        update_dict = await get_update_dictionary(category, str(channel.id))
        embed = disnake.Embed(description=f"{config.yes} All {category.lower()[:-1]} logs will now be sent in {channel.mention}.", color=config.success_embed_color)

        data_obj.update_data(update_dict)
        await ctx.send(embed=embed)
       
        
    """
    ! CHATBOT SETTINGS
    
    These settings manages the chatbot feature.
    """
    
    @commands.group(name="chatbot")
    async def chatbot(self, ctx: commands.Context):
        if ctx.invoked_subcommand == self.chatbot or None:
            return
        
    @chatbot.command(name="channel")
    @commands.cooldown(1, config.cooldown_time, commands.BucketType.member)
    @is_moderator(manage_guild=True)
    @server_setting()
    async def chatbot_channel(self, ctx: commands.Context, channel: disnake.TextChannel):
        """Set where the chat bot should respond to messages."""
        
        data_obj = GuildData(ctx.guild)
        embed = disnake.Embed(description=f"{config.yes} The chat bot will now respond to messages in {channel.mention}.", color=config.success_embed_color)
        
        data_obj.update_data({ "chat_bot_channel": channel.id, "chat_bot_toggle": True })
        await ctx.send(embed=embed)
        
    @chatbot.command(name="enable")
    @commands.cooldown(1, config.cooldown_time, commands.BucketType.member)
    @is_moderator(manage_guild=True)
    @server_setting()
    async def chatbot_enable(self, ctx: commands.Context):
        """Enable the chat bot feature."""
        
        data_obj = GuildData(ctx.guild)
        data = data_obj.get_data()
        
        embed = disnake.Embed(description=f"{config.yes} The chat bot feature has been enabled.", color=config.success_embed_color)

        if data["chat_bot_toggle"] == True:
            embed = disnake.Embed(description=f"{config.no} The chat bot feature is already enabled!", color=config.error_embed_color)
        else:
            data_obj.update_data({ "chat_bot_toggle": True })
        
        await ctx.send(embed=embed)
        
    @chatbot.command(name="disable")
    @commands.cooldown(1, config.cooldown_time, commands.BucketType.member)
    @is_moderator(manage_guild=True)
    @server_setting()
    async def chatbot_disable(self, ctx: commands.Context):
        """Disable the chat bot feature."""
        
        data_obj = GuildData(ctx.guild)
        data = data_obj.get_data()
        
        embed = disnake.Embed(description=f"{config.yes} The chat bot feature has been disabled.", color=config.success_embed_color)

        if data["chat_bot_toggle"] == False:
            embed = disnake.Embed(description=f"{config.no} The chat bot feature is already disabled!", color=config.error_embed_color)
        else:
            data_obj.update_data({ "chat_bot_toggle": False })
        
        await ctx.send(embed=embed)
        
    """
    ! USER SETTINGS
    
    These settings manages user's settings.
    """
    
    @commands.group(name="privacy")
    async def privacy(self, inter):
        """Manage your privacy settings."""
        pass

    @privacy.command(name="messages")
    async def privacy_messages(self, ctx: commands.Context, type: str, toggle: bool):
        """Edit your message privacy settings."""
        
        if not type in message_settings_description:
            embed = disnake.Embed(description=f"{config.no} Please provide a valid privacy setting."
                                  f"\nTo view all privacy settings, run `{self.bot.get_bot_prefix(ctx.guild)}privacy settings`.",
                                  color=config.error_embed_color)
            return await ctx.send(embed=embed)
        
        data_obj = UserData(ctx.author)
        embed = disnake.Embed(description=f"{config.yes} The {message_settings_description[type]} privacy setting has been {'enabled' if toggle else 'disabled'}.", color=config.success_embed_color)
        
        data_obj.update({ "message_content_privacy": str(toggle).lower()})
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
        
        data_obj = GuildData(inter.guild)
        guild_data = data_obj.get_data()
        
        if guild_data.get("settings_locked") == True:
            embed = disnake.Embed(description=f"{config.no} The server's settings are already locked!", color=config.error_embed_color)
            return await inter.send(embed=embed, ephemeral=True)
            
        embed = disnake.Embed(description=f"{config.yes} The server's settings are now locked.", color=config.success_embed_color)
        
        data_obj.update_data({ "settings_locked": True })
        await inter.send(embed=embed)

    @slash_settings.sub_command(name="unlock", description="Unlocks the server's settings.")
    async def slash_settings_unlock(self, inter: disnake.ApplicationCommandInteraction):
        """Unlocks the server's settings."""
        
        data_obj = GuildData(inter.guild)
        guild_data = data_obj.get_data()
        
        if guild_data.get("settings_locked") == False:
            embed = disnake.Embed(description=f"{config.no} The server's settings aren't locked!", color=config.error_embed_color)
            return await inter.send(embed=embed, ephemeral=True)
            
        embed = disnake.Embed(description=f"{config.yes} The server's settings are now unlocked.", color=config.success_embed_color)
        
        data_obj.update_data({ "settings_locked": False })
        await inter.send(embed=embed)


    """
    ! SERVER SETTINGS
    
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

        data_obj = GuildData(inter.guild)
        guild_data = data_obj.get_data()

        if guild_data.get("prefix") == new_prefix:
            embed = disnake.Embed(description=f"{config.no} The prefix is already set to `{new_prefix}`.", color=config.error_embed_color)
            return await inter.send(embed=embed, ephemeral=True)

        embed = disnake.Embed(description=f"{config.yes} Changed the prefix to `{new_prefix}` successfully.", color=config.success_embed_color)
        
        data_obj.update_data({ "prefix": new_prefix })
        await inter.send(embed=embed)

    
    """
    ! LOGS SETTINGS
    
    These commands changes how OutDash logs events in servers.
    """
 
    @commands.slash_command(name="logs")
    async def slash_logs(self, inter):
        pass

    @slash_logs.sub_command_group(name="edit")
    async def slash_logs_edit(self, inter):
        pass
    
    @slash_logs_edit.sub_command(name="category", description="Edit log categories, changing channel for each log type in the category.")
    @is_moderator(manage_guild=True)
    @server_setting()
    async def slash_edit_logs_category(self, inter: disnake.ApplicationCommandInteraction, category: category_list, channel: disnake.TextChannel = None):
        """Edit log categories, changing channel for each log type in the category..
        Parameters
        ----------
        category: The category you want to edit logs for.
        channel: The channel to send the logs to. If none, the log types will be disabled.
        """
        
        data_obj = GuildData(inter.guild)
        if not channel:
            update = await get_update_dictionary(self.bot, category, None)
            embed = disnake.Embed(description=f"{config.yes} All {category.lower()[:-1]} logs have been disabled", color=config.success_embed_color)
        else:
            update = await get_update_dictionary(self.bot, category, str(channel.id))
            embed = disnake.Embed(description=f"{config.yes} All {category.lower()[:-1]} logs will now be sent in {channel.mention}.", color=config.success_embed_color)

        data_obj.update_log_webhooks(update)
        await inter.send(embed=embed)

    @slash_logs_edit.sub_command(name="channel", description="Change where a log type should be sent.")
    @is_moderator(manage_guild=True)
    @server_setting()
    async def slash_edit_logs_channel(self, inter: disnake.ApplicationCommandInteraction, type: type_list, channel: disnake.TextChannel = None):
        """Change where a log type should be sent.
        Parameters
        ----------
        type: What you want to edit. Example: "message_delete" would edit where deleted messages should be sent.
        channel: Where the selected log type should be sent. If none, the log type will be disabled.
        """
        
        data_obj = GuildData(inter.guild)
        log_type, log_description = find_log_type(type.lower())
        
        if not channel:
            embed = disnake.Embed(description=f"{config.yes} {log_description} logs have now been disabled.", color=config.success_embed_color)
            
            data_obj.update_data({ log_type: None })
            return await inter.send(embed=embed)
            
        webhook = await get_webhook(self.bot, channel)
        embed = disnake.Embed(description=f"{config.yes} {log_description} logs will now be sent in {channel.mention}.", color=config.success_embed_color)

        data_obj.update_log_webhook(log_type, { "url": webhook.url, "toggle": True })
        await inter.send(embed=embed)
    
    """
    ! WELCOME/GOODBYE SETTINGS
    
    These commands manages the welcome/goodbye features
    """
    
    @commands.slash_command(name="editwelcome")
    async def slash_editwelcome(self, inter: disnake.ApplicationCommandInteraction):
        pass
    
    @slash_editwelcome.sub_command(name="toggle")
    @is_moderator(manage_guild=True)
    @server_setting()
    async def slash_editwelcome_toggle(self, inter: disnake.ApplicationCommandInteraction, toggle: bool):
        """Toggles if welcome messages should be sent."""

        data_obj = GuildData(inter.guild)
        embed = disnake.Embed(description=f"{config.yes} Welcome messages have been {'disabled' if not toggle else 'enabled'}.", color=config.success_embed_color)

        data_obj.update_data({ "welcome_toggle": toggle })
        await inter.send(embed=embed)
    
    @slash_editwelcome.sub_command(name="content")
    @is_moderator(manage_guild=True)
    @server_setting()
    async def slash_editwelcome_content(self, inter: disnake.ApplicationCommandInteraction, *, content: str):
        """Edit the welcome message content."""

        data_obj = GuildData(inter.guild)
        data = data_obj.get_data()
        
        welcome_message = data["welcome_message"]
        welcome_message["content"] = content
        
        embed = disnake.Embed(description=f"{config.yes} The welcome message content has been set to:\n`{content}`", color=config.success_embed_color)
        
        data_obj.update_data({ "welcome_message": welcome_message })
        await inter.send(embed=embed)
    
    @slash_editwelcome.sub_command(name="embed")
    @is_moderator(manage_guild=True)
    @server_setting()
    async def slash_editwelcome_embed(self, inter: disnake.ApplicationCommandInteraction, embed_part: embed_parts_choices, *, value: str):
        """Edit the welcome message embed."""
        
        embed_part = embed_part.lower()
        data_obj = GuildData(inter.guild)
        data = data_obj.get_data()
        
        embed_update = get_embed_update(data["welcome_message"]["embed"], embed_part, value)
        data["welcome_message"]["embed"] = embed_update
        
        embed = disnake.Embed(description=f"{config.yes} ", color=config.success_embed_color)
        
        if embed_part.startswith("author") or embed_part.startswith("footer"):
            top_part = embed_part[0:6]
            sub_part = embed_part[:7]
            
            embed.description += f"The {top_part} {sub_part} has been changed to `{value}`"
        else:
            embed.description += f"The {embed_part} has been changed to `{value}`"
        
        data_obj.update_data({ "welcome_message": data })
        await inter.send(embed=embed)

    @slash_editwelcome.sub_command(name="channel")
    @is_moderator(manage_guild=True)
    @server_setting()
    async def slash_editwelcome_channel(self, inter: disnake.ApplicationCommandInteraction, channel: disnake.TextChannel):
        """Set the channel where welcome messages should be sent."""
        
        data_obj = GuildData(inter.guild)
        embed_part = embed_part.lower()

        embed = disnake.Embed(description=f"{config.yes} Welcome messages will now be sent in <#{channel.id}>.", color=config.success_embed_color)
        
        data_obj.update_data({ "welcome_channel": str(channel.id), "welcome_toggle": True })
        await inter.send(embed=embed)
        
    @slash_editwelcome.sub_command(name="trigger", description="Trigger the welcome message for testing.")
    @is_moderator(manage_guild=True)
    async def editwelcome_trigger(self, inter: disnake.ApplicationCommandInteraction):
        """Trigger the welcome message for testing."""
        
        data_obj = GuildData(inter.guild)
        data = data_obj.get_data()
        
        if not data["welcome_toggle"]:
            embed = disnake.Embed(description=f"{config.no} Welcome messages have been disabled for this guild.", color=config.error_embed_color)
            return await inter.send(embed=embed)
        
        await self.bot.dispatch("welcome_member", inter.author, kwargs={ "channel": inter.channel })
        await inter.send("The welcome message has been triggered.", ephemeral=True)
    
    """
    ! CHATBOT SETTINGS
    
    These settings manages the chatbot feature.
    """
    
    @commands.slash_command(name="chatbot")
    async def slash_chatbot(self, inter):
        pass
    
    @slash_chatbot.sub_command(name="channel", description="Set where the chat bot should respond to messages.")
    @is_moderator(manage_guild=True)
    @server_setting()
    async def slash_chatbot_channel(self, inter: disnake.ApplicationCommandInteraction, channel: disnake.TextChannel):
        """Set where the chat bot should respond to messages.
        Parameters
        ----------
        channel: The channel where the bot should respond to messages.
        ----------
        """
        
        data_obj = GuildData(inter.guild)
        embed = disnake.Embed(description=f"{config.yes} The chat bot will now respond to messages in {channel.mention}.", color=config.success_embed_color)
        
        data_obj.update_data({ "chat_bot_channel": channel.id, "chat_bot_toggle": True })
        await inter.send(embed=embed)
        
    @slash_chatbot.sub_command(name="toggle", description="Toggle the chat bot feature.")
    @is_moderator(manage_guild=True)
    @server_setting()
    async def slash_chatbot_toggle(self, inter: disnake.ApplicationCommandInteraction, toggle: bool):
        """Toggle the chat bot feature.
        Parameters
        ----------
        toggle: Whether the chat bot should be enabled or not.
        """
        
        data_obj = GuildData(inter.guild)
        data = data_obj.get_data()
        
        embed = disnake.Embed(description=f"{config.yes} The chat bot feature has been " + "enabled" if toggle else "disabled" + ".", color=config.success_embed_color)

        if data["chat_bot_toggle"] == toggle:
            embed = disnake.Embed(description=f"{config.no} The chat bot feature is already " + "enabled" if toggle else "disabled" + "!", color=config.error_embed_color)
        else:
            data_obj.update_data({ "chat_bot_toggle": toggle })
        
        await inter.send(embed=embed)
    
      
    """
    ! USER SETTINGS

    These settings manages user's settings.
    """
    
    @commands.slash_command(name="privacy", description="Manage your privacy settings.")
    async def slash_privacy(self, inter):
        """Manage your privacy settings."""
        pass

    @slash_privacy.sub_command(name="messages", description="Edit you message privacy settings.")
    async def slash_privacymessages(self, inter: disnake.ApplicationCommandInteraction, type: message_settings_types, toggle: bool):
        """Edit your message privacy settings.
        Parameters
        ----------
        type: The message privacy setting you want to edit.
        toggle: Whether the privacy setting should be on or not.
        """
        
        data_obj = UserData(inter.author)
        embed = disnake.Embed(description=f"{config.yes} The {message_settings_description[type]} privacy setting has been {'enabled' if toggle else 'disabled'}.", color=config.success_embed_color)
        
        data_obj.update({ "message_content_privacy": str(toggle).lower()})
        await inter.send(embed=embed)
        
    ## -- TEXT COMMAND ERRORS -- ##
    
    # SETTING LOCKING
    @lock.error 
    async def lock_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description="{emoji} You're missing the `{permission}` permission.".format(emoji=config.no, permission=error.missing_permissions[0].title().replace("_", " ")), color=config.error_embed_color)
            await ctx.send(embed=embed)
    
    @unlock.error 
    async def unlock_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description="{emoji} You're missing the `{permission}` permission.".format(emoji=config.no, permission=error.missing_permissions[0].title().replace("_", " ")), color=config.error_embed_color)
            await ctx.send(embed=embed)
    
    # SERVER SETTINGS
    @setprefix.error
    async def prefix_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description="{emoji} You're missing the `{permission}` permission.".format(emoji=config.no, permission=error.missing_permissions[0].title().replace("_", " ")), color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = disnake.Embed(description=f"{config.no} You need to specify the new prefix.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, SettingsLocked):
            embed = disnake.Embed(description=f"{config.no} The server's settings are locked.", color=config.error_embed_color)
            await ctx.send(embed=embed)
            
    # WELCOME/GOODBYE SETTINGS
    # @editwelcome_toggle.error
    # async def editwelcome_toggle_error(self, ctx: commands.Context, error: commands.CommandError):
    #     if isinstance(error, commands.MissingPermissions):
    #         embed = disnake.Embed(description="{emoji} You're missing the `{permission}` permission.".format(emoji=config.no, permission=error.missing_permissions[0].title().replace("_", " ")), color=config.error_embed_color)
    #         await ctx.send(embed=embed)
    #     elif isinstance(error, SettingsLocked):
    #         embed = disnake.Embed(description=f"{config.no} The server's settings are locked.", color=config.error_embed_color)
    #         await ctx.send(embed=embed)
            
    # @editwelcome_content.error
    # async def editwelcome_content_error(self, ctx: commands.Context, error: commands.CommandError):
    #     if isinstance(error, commands.MissingPermissions):
    #         embed = disnake.Embed(description="{emoji} You're missing the `{permission}` permission.".format(emoji=config.no, permission=error.missing_permissions[0].title().replace("_", " ")), color=config.error_embed_color)
    #         await ctx.send(embed=embed)
    #     elif isinstance(error, commands.MissingRequiredArgument):
    #         missing_argument = error.param.name
    #         embed = disnake.Embed(description=f"{config.no} ", color=config.error_embed_color)
    
    #         if missing_argument == "content":
    #             embed.description = "Please specify what the welcome message content should be set to!"
    
    #         await ctx.send(embed=embed)
    #     elif isinstance(error, SettingsLocked):
    #         embed = disnake.Embed(description=f"{config.no} The server's settings are locked.", color=config.error_embed_color)
    #         await ctx.send(embed=embed)

    # CHATBOT SETTINGS
    @chatbot_channel.error 
    async def chatbot_channel_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description="{emoji} You're missing the `{permission}` permission.".format(emoji=config.no, permission=error.missing_permissions[0].title().replace("_", " ")), color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = disnake.Embed(description=f"{config.no} Please provide a channel!", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, SettingsLocked):
            embed = disnake.Embed(description=f"{config.no} The server's settings are locked.", color=config.error_embed_color)
            await ctx.send(embed=embed)
            
    @chatbot_enable.error
    async def chatbot_enable_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description="{emoji} You're missing the `{permission}` permission.".format(emoji=config.no, permission=error.missing_permissions[0].title().replace("_", " ")), color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, SettingsLocked):
            embed = disnake.Embed(description=f"{config.no} The server's settings are locked.", color=config.error_embed_color)
            await ctx.send(embed=embed)
            
    @chatbot_disable.error
    async def chatbot_disable_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description="{emoji} You're missing the `{permission}` permission.".format(emoji=config.no, permission=error.missing_permissions[0].title().replace("_", " ")), color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, SettingsLocked):
            embed = disnake.Embed(description=f"{config.no} The server's settings are locked.", color=config.error_embed_color)
            await ctx.send(embed=embed)
    
    ## -- SLASH COMMAND ERRORS -- ##
    
    # SETTING LOCKING
    @slash_settings.error
    async def slash_settings_lock_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description="{emoji} You're missing the `{permission}` permission.".format(emoji=config.no, permission=error.missing_permissions[0].title().replace("_", " ")), color=config.error_embed_color)
            await inter.response.send_message(embed=embed)
    
    # SERVER SETTING
    @slash_setprefix.error
    async def prefix_error(self, inter, error):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description="{emoji} You're missing the `{permission}` permission.".format(emoji=config.no, permission=error.missing_permissions[0].title().replace("_", " ")), color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = disnake.Embed(description=f"{config.no} You need to specify the new prefix.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error, SettingsLocked):
            embed = disnake.Embed(description=f"{config.no} The server's settings are locked.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)

    # CHATBOT SETTINGS
    @slash_chatbot_channel.error
    async def slash_chatbot_channel_error(self, inter: disnake.ApplicationCommandInteraction, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description="{emoji} You're missing the `{permission}` permission.".format(emoji=config.no, permission=error.missing_permissions[0].title().replace("_", " ")), color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error, SettingsLocked):
            embed = disnake.Embed(description=f"{config.no} The server's settings are locked.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        
    @slash_chatbot_toggle.error
    async def slash_chatbot_toggle_error(self, inter: disnake.ApplicationCommandInteraction, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description="{emoji} You're missing the `{permission}` permission.".format(emoji=config.no, permission=error.missing_permissions[0].title().replace("_", " ")), color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error, SettingsLocked):
            embed = disnake.Embed(description=f"{config.no} The server's settings are locked.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)

    # LOGS SETTINGS
    @slash_edit_logs_channel.error 
    async def slash_edit_logs_channel_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description="{emoji} You're missing the `{permission}` permission.".format(emoji=config.no, permission=error.missing_permissions[0].title().replace("_", " ")), color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error, SettingsLocked):
            embed = disnake.Embed(description=f"{config.no} The server's settings are locked.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)

    @slash_edit_logs_category.error
    async def slash_edit_logs_category_error(self, inter: disnake.ApplicationCommandInteraction, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description="{emoji} You're missing the `{permission}` permission.".format(emoji=config.no, permission=error.missing_permissions[0].title().replace("_", " ")), color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error, SettingsLocked):
            embed = disnake.Embed(description=f"{config.no} The server's settings are locked.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
            

def setup(bot):
    bot.add_cog(BotSettings(bot))