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
db = client["db2"]

server_data_col = db["server_data"]
muted_users_col = db["muted_users"]
privacy_settings_col = db["privacy_settings"]

## -- COG -- ##

class OnMemberEdit(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_edit(self, message):

        query = {
            "guild_id": str(message.guild.id)
        }
        data = {
            "guild_id": str(message.guild.id),
            "event_logs_webhook": "None"
        }
        update = { "set": { "member_edit_logs_webhook": "None" } }
        server_data = server_data_col.find_one(query)
        if not server_data:
            server_data_col.insert_one(data)
            await self.on_event(message)
            return
            
        webhook_url = server_data.get("member_edit_logs_webhook")
        if webhook_url == "None" or not webhook_url:
            if not webhook_url:
                server_data_col.update_one(query, update)
                return
            return
        
        webhook = Webhook(url=webhook_url, username="OutDash Logging", avatar_url=str(self.bot.user.avatar))
        embed = disnake.Embed(description=f"", color=config.logs_embed_color)
        
        embed.set_author(name=message.guild.name, icon_url=message.guild.icon or "https://cdn.discordapp.com/embed/avatars/1.png")
        embed.timestamp = datetime.datetime.utcnow()
        
        webhook.add_embed(embed)
        webhook.post()
    
    
def setup(bot):
    bot.add_cog(OnMemberEdit(bot))