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
from webhooks import Webhook

# FILES
import extra.config as config

## -- VARIABLES -- ##

mongo_login = os.environ.get("MONGO_LOGIN")
client = MongoClient(f"{mongo_login}",tlsCAFile=certifi.where())
db = client["db"]

server_data_col = db["server_data"]
muted_users_col = db["muted_users"]
privacy_settings_col = db["privacy_settings"]

## -- COG -- ##

class OnMessageEdit(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_edit(self, before: disnake.Message, after: disnake.Message):
        if before.content == after.content:
            return
        elif before.author.bot or after.author.bot:
            return
        
        query = {
            "guild_id": str(before.guild.id)
        }
        data = {
            "guild_id": str(before.guild.id),
            "message_edit_logs_channel": "None"
        }
        update = { "$set": { "message_edit_logs_channel": "None" } }
        server_data = server_data_col.find_one(query)
        if not server_data:
            server_data_col.insert_one(data)
            self.on_message_edit(before, after)
            return
            
        webhook_url = server_data.get("message_edit_logs_webhook")
        if webhook_url == "None" or not webhook_url:
            if not webhook_url:
                server_data_col.update_one(query, update)
            return
        
        before_text = before.content if len(before.content) < 1021 else f"{before.content[:1021]}..."
        if len(before.embeds) >= 1:
            before_text = f"{before_text}\n**[EMBED]**" if len(before.embeds) == 1 else f"{before_text}\n**[EMBEDS]**"
        after_text = after.content if len(after.content) < 1021 else f"{after.content[:1021]}..."
        if len(after.embeds) >= 1:
            after_text = f"{after_text}\n**[EMBED]**" if len(after.embeds) == 1 else f"{after_text}\n**[EMBEDS]**"
        
        webhook = Webhook(url=webhook_url, username="OutDash Logging", avatar_url=str(self.bot.user.avatar))

        embed = disnake.Embed(description=f"**Message edited in <#{before.channel.id}>**\n[Jump to message](https://discordapp.com/channels/{after.guild.id}/{after.channel.id}/{after.id})", color=config.logs_embed_color)
        embed.add_field(name="Before", value=before_text, inline=False)
        embed.add_field(name="After", value=after_text, inline=False)

        embed.set_author(name=f"{before.author.name}#{before.author.discriminator}", icon_url=before.author.avatar or "https://cdn.discordapp.com/embed/avatars/1.png")
        embed.set_footer(text=f"Message ID: {before.id}")
        embed.timestamp = datetime.datetime.utcnow()
        
        if not before_text or not after_text:
            return

        webhook.add_embed(embed)
        webhook.post()
    
    
def setup(bot):
    bot.add_cog(OnMessageEdit(bot))