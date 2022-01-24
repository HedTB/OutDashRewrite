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
from disnake.utils import get
from pymongo import MongoClient
from dotenv import load_dotenv

# FILES
import config
import modules

load_dotenv()

## -- VARIABLES -- ##

mongo_login = os.environ.get("MONGO_LOGIN")
client = MongoClient(f"{mongo_login}",tlsCAFile=certifi.where())
db = client["db2"]

server_data_col = db["server_data"]
muted_users_col = db["muted_users"]
privacy_settings_col = db["privacy_settings"]

toggle_list = commands.option_enum({"enabled": "enabled", "disabled": "disabled"})

async def get_data(
    guild_id: int,
    channel: str = "None",
    toggle: str = "false",
    embed_title: str = "None",
    embed_description: str = "**Welcome to __{guild_name}__!**",
    embed_author_name: str = "{member_username}",
    embed_author_icon: str = "{member_icon}",
    embed_footer_text: str = "None",
    embed_footer_icon: str = "None",
    embed_timestamp: str = "true",
    embed_thumbnail: str = "{guild_icon}",
    embed_color: str = str(config.logs_embed_color),
    message_content: str = "{member_mention},"
):
    return {
        "guild_id": str(guild_id),
        "welcome_channel": channel,
        "welcome_toggle": toggle,
        "welcome_embed_title": embed_title,
        "welcome_embed_description": embed_description,
        "welcome_embed_author_name": embed_author_name,
        "welcome_embed_author_icon": embed_author_icon,
        "welcome_embed_footer_text": embed_footer_text,
        "welcome_embed_footer_icon": embed_footer_icon,
        "welcome_embed_timestamp": embed_timestamp,
        "welcome_embed_thumbnail": embed_thumbnail,
        "welcome_embed_color": embed_color,
        "welcome_message_content": message_content,
    }
    
async def update_data(
    guild_id: int,
    channel: str = "None",
    toggle: str = "false",
    embed_title: str = "None",
    embed_description: str = "**Welcome to __{guild_name}__!**",
    embed_author_name: str = "{member_username}",
    embed_author_icon: str = "{member_icon}",
    embed_footer_text: str = "None",
    embed_footer_icon: str = "None",
    embed_timestamp: str = "true",
    embed_thumbnail: str = "{guild_icon}",
    embed_color: str = str(config.logs_embed_color),
    message_content: str = "{member_mention},"
):
    query = {"guild_id": str(guild_id)}
    update = { "$set": {
        "guild_id": str(guild_id),
        "welcome_channel": channel,
        "welcome_toggle": toggle,
        "welcome_embed_title": embed_title,
        "welcome_embed_description": embed_description,
        "welcome_embed_author_name": embed_author_name,
        "welcome_embed_author_icon": embed_author_icon,
        "welcome_embed_footer_text": embed_footer_text,
        "welcome_embed_footer_icon": embed_footer_icon,
        "welcome_embed_timestamp": embed_timestamp,
        "welcome_embed_thumbnail": embed_thumbnail,
        "welcome_embed_color": embed_color,
        "welcome_message_content": message_content,
    }}
    server_data_col.update_one(query, update)

## -- COG -- ##

class EditWelcomeSlash(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(name="welcome")
    @commands.has_permissions(manage_guild=True)
    async def slash_welcome(self, inter):
        query = {"guild_id": str(inter.guild.id)}
        result = server_data_col.find_one(query)
        data = await modules.get_db_data(str(inter.guild.id))

        if not result:
            server_data_col.insert_one(data)
            result = server_data_col.find_one(query)

        if result["settings_locked"] == "true":
            embed = disnake.Embed(description=f"{config.no} The server's settings are locked. Please run `/settings unlock` to change any settings.", color=config.error_embed_color)
            await inter.send(embed=embed)
            return
            
        pass
    
    @slash_welcome.sub_command_group(name="message")
    @commands.has_permissions(manage_guild=True)
    async def slash_welcome_message(self, inter):
        pass
    
    @slash_welcome_message.sub_command(name="content", description="The normal text message that should be sent.")
    async def slash_welcome_message_content(self, inter: disnake.ApplicationCommandInteraction, content: str):
        """The normal text message that should be sent.
        Parameters
        ----------
        content: The text message you want to send.
        """
        
        data = await get_data(guild_id=str(inter.guild.id), message_content=content)
        query = {"guild_id": str(inter.guild.id)}
        result = server_data_col.find_one(query)
        if not result:
            server_data_col.insert_one(data)
            result = server_data_col.find_one(query)
            
        await update_data(guild_id=str(inter.guild.id), message_content=str(content))
        embed = disnake.Embed(description=f"{config.yes} The welcome message content is now set as:\n`{content}`", color=config.success_embed_color)
        await inter.send(embed=embed)
        
    
    @slash_welcome.sub_command(name="channel", description="Set the channel where welcome messages should be sent.")
    async def slash_setwelcomechannel(self, inter: disnake.ApplicationCommandInteraction, channel: disnake.TextChannel):
        """Set the channel where welcome messages should be sent.
        Parameters
        ----------
        channel: The channel where the welcome messages will be sent.
        """
        
        data = await get_data(guild_id=str(inter.guild.id), channel=str(channel.id))
        query = {"guild_id": str(inter.guild.id)}
        result = server_data_col.find_one(query)
        if not result:
            server_data_col.insert_one(data)
            result = server_data_col.find_one(query)
        
        update = { "$set": {
                "welcome_channel": str(channel.id)
            }}
        server_data_col.update_one(query, update)
        embed = disnake.Embed(description=f"{config.yes} Welcome messages will now be sent in <#{channel.id}>.", color=config.success_embed_color)
        await inter.send(embed=embed)

        
    @slash_setwelcomechannel.error 
    async def slash_setwelcomechannel_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `Manage Guild` permission.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = disnake.Embed(description=f"{config.no} Please specify a channel!\n If you're looking to disable the welcome message, run `/welcome toggle off`.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
    
    @slash_welcome.sub_command(name="toggle", description="Toggles if welcome messages should be sent.")
    async def slash_togglewelcome(self, inter: disnake.ApplicationCommandInteraction, toggle: toggle_list):
        """Toggles if welcome messages should be sent.
        Parameters
        ----------
        toggle: Whether welcome messages should be sent or not.
        """
        
        data = await get_data(guild_id=str(inter.guild.id), toggle=str(toggle))
        query = {"guild_id": str(inter.guild.id)}
        result = server_data_col.find_one(query)
        if not result:
            server_data_col.insert_one(data)
            return
        if toggle.lower() == "on" or toggle.lower() == "true" or toggle.lower() == "yes" or toggle.lower() == "enabled":
            update = { "$set": { "welcome_toggle": "true" } }
            server_data_col.update_one(query, update)
            
            embed = disnake.Embed(description=f"{config.yes} Welcome messages have been enabled.", color=config.success_embed_color)
            await inter.send(embed=embed)
        elif toggle.lower() == "off" or toggle.lower() == "false" or toggle.lower() == "no" or toggle.lower() == "disabled":
            update = { "$set": { "welcome_toggle": "false" } }
            server_data_col.update_one(query, update)
            
            embed = disnake.Embed(description=f"{config.yes} Welcome messages have been disabled.", color=config.success_embed_color)
            await inter.send(embed=embed)
        else:
            embed = disnake.Embed(description=f"{config.no} Please give a valid toggle value!\nToggles:\n```on, yes, true, enabled - welcome messages enabled\noff, no, false, disabled - welcome messages disabled```", color=config.error_embed_color)
            await inter.send(embed=embed)

        
    @slash_welcome.error 
    async def slash_welcome_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `Manage Guild` permission.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        
    
def setup(bot):
    bot.add_cog(EditWelcomeSlash(bot))