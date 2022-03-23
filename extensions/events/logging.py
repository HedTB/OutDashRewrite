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
from googleapiclient import discovery
from dotenv import load_dotenv

# FILES
from utils import config
from utils import functions
from utils.checks import *
from utils.webhooks import *
from utils.classes import *

## -- VARIABLES -- ##

load_dotenv()

mongo_login = os.environ.get("MONGO_LOGIN")
rapid_api_key = os.environ.get("RAPID_API_KEY")
google_api_key = os.environ.get("GOOGLE_API_KEY")
randomstuff_key = os.environ.get("RANDOMSTUFF_KEY")

client = MongoClient(mongo_login, tlsCAFile=certifi.where())
db = client["db2"]


"""
perspective_client = discovery.build(
    "commentanalyzer",
    "v1alpha1",
    developerKey=google_api_key,
    discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
    static_discovery=False,
)
"""

server_data_col = db["server_data"]
user_data_col = db["user_data"]
privacy_settings_col = db["privacy_settings"]

## -- FUNCTIONS -- ##

def get_response_score(response, attribute: str):
    attribute = attribute.upper()
    attribute_scores = response["attributeScores"]

    if attribute_scores[attribute]:
        return round(attribute_scores[attribute]["summaryScore"]["value"], 3)
    else:
        return None
    
def send_log_message(log_type: str, avatar: disnake.Asset, ctx: commands.Context, embed: disnake.Embed):
    query = {"guild_id": str(ctx.guild.id)}
    update = {"$set": {f"{log_type}_logs_webhook": "None"}}
    server_data = server_data_col.find_one(query)
    
    if not server_data:
        server_data_col.insert_one(functions.get_db_data(ctx.guild.id))
        send_log_message(log_type, ctx, embed)
        return
            
    webhook_url = server_data.get(f"{log_type}_logs_webhook")
    if webhook_url == "None" or not webhook_url:
        if not webhook_url:
            server_data_col.update_one(query, update)
        return
    
    webhook = Webhook(url=webhook_url, username="OutDash Logging", avatar_url=str(avatar))
    
    webhook.add_embed(embed)
    try:
        webhook.post()
    except InvalidWebhook:
        server_data_col.update_one(query, {"$set": {f"{log_type}_logs_webhook": "None"}})


## -- COG -- ##

class LoggingEvents(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages: list[disnake.Message]):
        webhook = LoggingWebhook(self.bot.user.avatar, messages[0].guild, "message_bulk_delete")
        embed = disnake.Embed(description=f"**Bulk delete in <#{messages[0].channel.id}>, {len(messages)} messages deleted**", color=config.logs_embed_color)
        
        embed.set_author(name=messages[0].guild.name, icon_url=messages[0].guild.icon or config.default_avatar_url)
        embed.timestamp = datetime.datetime.utcnow()
        
        webhook.add_embed(embed)
        webhook.post()
        
    @commands.Cog.listener()
    async def on_message_edit(self, before: disnake.Message, after: disnake.Message):
        if before.content == after.content:
            return
        if before.author.bot or after.author.bot:
            return
        
        webhook = LoggingWebhook(self.bot.user.avatar, before.guild, "message_bulk_delete")
        user_data = user_data_col.find_one({"user_id": str(before.author.id)})
        
        if not user_data:
            user_data_col.insert_one(functions.get_user_data(before.author.id, before.guild.id))
            await self.on_message_edit(before, after)
            return
            
        message_content_privacy = user_data.get("message_content_privacy")
        
        before_text = before.content if len(before.content) < 1021 else f"{before.content[:1021]}..."
        if len(before.embeds) >= 1:
            before_text = f"{before_text}\n**[EMBED]**" if len(before.embeds) == 1 else f"{before_text}\n**[EMBEDS]**"
        after_text = after.content if len(after.content) < 1021 else f"{after.content[:1021]}..."
        if len(after.embeds) >= 1:
            after_text = f"{after_text}\n**[EMBED]**" if len(after.embeds) == 1 else f"{after_text}\n**[EMBEDS]**"
        
        if not before_text or not after_text:
            return

        if message_content_privacy != "true":
            embed = disnake.Embed(description=f"**Message edited in <#{before.channel.id}>**\n[Jump to message](https://discordapp.com/channels/{after.guild.id}/{after.channel.id}/{after.id})", color=config.logs_embed_color)
            embed.add_field(name="Before", value=before_text, inline=False)
            embed.add_field(name="After", value=after_text, inline=False)

            embed.set_author(name=f"{before.author.name}#{before.author.discriminator}", icon_url=before.author.avatar or config.default_avatar_url)
            embed.set_footer(text=f"Message ID: {before.id}")
            embed.timestamp = datetime.datetime.utcnow()
        else:
            embed = disnake.Embed(description=f"**Message edited in <#{before.channel.id}>** \n[Jump to message](https://discordapp.com/channels/{after.guild.id}/{after.channel.id}/{after.id})", color=config.logs_embed_color)
            embed.add_field(name="Notice", value="`This user has message content privacy enabled.`")
            
            embed.set_author(name=f"{before.author.name}#{before.author.discriminator}", icon_url=before.author.avatar or config.default_avatar_url)
            embed.set_footer(text=f"Message ID: {before.id}")
            embed.timestamp = datetime.datetime.utcnow()

        webhook.add_embed(embed)
        webhook.post()
        
    @commands.Cog.listener()
    async def on_message_delete(self, message: disnake.Message):
        if message.author.bot:
            return
        
        webhook = LoggingWebhook(self.bot.user.avatar, message.guild, "message_delete")
        user_data = user_data_col.find_one({"user_id": str(message.author.id)})
        
        if not user_data:
            user_data_col.insert_one(functions.get_user_data(message.author.id, message.guild.id))
            await self.on_message_delete(message)
            return
            
        message_content_privacy = user_data.get("message_content_privacy")
        
        message_text = message.content if len(message.content) < 2000 else f"{message.content[:2000]}..."
        
        if len(message.embeds) >= 1:
            message_text = f"{message_text}\n**[EMBED]**" if len(message.embeds) == 1 else f"{message_text}\n**[EMBEDS]**"
        if message_content_privacy == "true":
            message_text = "`This user has message content privacy enabled.`"

        embed = disnake.Embed(description=f"**Message deleted in {message.channel.mention}**"
                              f"\n{message_text}", color=config.logs_delete_embed_color)

        embed.set_author(name=f"{message.author.name}#{message.author.discriminator}", icon_url=message.author.avatar or config.default_avatar_url)
        embed.set_footer(text=f"Message ID: {message.id}")
        embed.timestamp = datetime.datetime.utcnow()

        webhook.add_embed(embed)
        webhook.post()
    
    
def setup(bot):
    bot.add_cog(LoggingEvents(bot))