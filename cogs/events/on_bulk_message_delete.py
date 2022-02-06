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
user_data_col = db["user_data"]

## -- COG -- ##

class OnBulkMessageDelete(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages):

        query = {
            "guild_id": str(messages[0].guild.id)
        }
        data = {
            "guild_id": str(messages[0].guild.id),
            "message_bulk_delete_logs_webhook": "None"
        }
        update = { "$set": { "message_bulk_delete_logs_webhook": "None" } }
        server_data = server_data_col.find_one(query)
        if not server_data:
            server_data_col.insert_one(data)
            await self.on_bulk_message_delete(messages)
            return
            
        webhook_url = server_data.get("message_bulk_delete_logs_webhook")
        if webhook_url == "None" or not webhook_url:
            if not webhook_url:
                server_data_col.update_one(query, update)
                return
            return
        
        webhook = Webhook(url=webhook_url, username="OutDash Logging", avatar_url=str(self.bot.user.avatar))
        embed = disnake.Embed(description=f"**Bulk delete in <#{messages[0].channel.id}>, {len(messages)} messages deleted**", color=config.logs_embed_color)
        
        embed.set_author(name=messages[0].guild.name, icon_url=messages[0].guild.icon or "https://cdn.discordapp.com/embed/avatars/1.png")
        embed.timestamp = datetime.datetime.utcnow()
        
        webhook.add_embed(embed)
        webhook.post()
    
    
def setup(bot):
    bot.add_cog(OnBulkMessageDelete(bot))