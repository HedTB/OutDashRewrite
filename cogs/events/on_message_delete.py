## -- IMPORTING -- ##

# MODULES
import disnake
import os
import random
import asyncio
import datetime
import certifi
import time

from disnake.ext import commands
from disnake.errors import Forbidden, HTTPException
from disnake.ext.commands import errors
from pymongo import MongoClient
from webhooks import Webhook

# FILES
import extra.config as config
from extra import functions

## -- VARIABLES -- ##

mongo_login = os.environ.get("MONGO_LOGIN")
client = MongoClient(f"{mongo_login}",tlsCAFile=certifi.where())
db = client[config.database_collection]

server_data_col = db["server_data"]
muted_users_col = db["muted_users"]
user_data_col = db["user_data"]

## -- COG -- ##

class OnMessageDelete(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_delete(self, message: disnake.Message):
        if message.author.bot:
            return

        query = {"guild_id": str(message.guild.id)}
        data = functions.get_db_data(message.guild.id)
        update = { "$set": { "message_delete_logs_webhook": "None" } }
        
        server_data = server_data_col.find_one(query)
        user_data = user_data_col.find_one({"user_id": str(message.author.id)})
        
        if not server_data:
            server_data_col.insert_one(data)
            await self.on_message_delete(message)
            return
        elif not user_data:
            user_data_col.insert_one(functions.get_user_data(message.author.id))
            await self.on_message_delete(message)
            return
            
        webhook_url = server_data.get("message_delete_logs_webhook")
        message_content_privacy = user_data.get("message_content_privacy")

        if webhook_url == "None" or not webhook_url:
            if not webhook_url:
                server_data_col.update_one(query, update)
                await self.on_message_delete(message)
                return
            return
        
        message_text = message.content if len(message.content) < 3750 else f"{message.content[:3750]}..."
        if len(message.embeds) >= 1:
            message_text = f"{message_text}\n**[EMBED]**" if len(message.embeds) == 1 else f"{message_text}\n**[EMBEDS]**"
        if message_content_privacy == "true":
            message_text = "`This user has message content privacy enabled.`"

        webhook = Webhook(url=webhook_url, username="OutDash Logging", avatar_url=str(self.bot.user.avatar))

        embed = disnake.Embed(description=f"**Message deleted in {message.channel.mention}**"
                              f"\n{message_text}", color=config.logs_delete_embed_color)

        embed.set_author(name=f"{message.author.name}#{message.author.discriminator}", icon_url=message.author.avatar or "https://cdn.discordapp.com/embed/avatars/1.png")
        embed.set_footer(text=f"Message ID: {message.id}")
        embed.timestamp = datetime.datetime.utcnow()

        webhook.add_embed(embed)
        webhook.post()
    
    
def setup(bot):
    bot.add_cog(OnMessageDelete(bot))