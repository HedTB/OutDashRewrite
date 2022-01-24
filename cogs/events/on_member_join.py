## -- IMPORTING -- ##

# MODULES
import disnake
import os
import random
import asyncio
import datetime
import certifi
import requests

from disnake.ext import commands
from disnake.errors import Forbidden, HTTPException
from disnake.ext.commands import errors
from pymongo import MongoClient
from discord_webhook import DiscordEmbed, DiscordWebhook
from requests.exceptions import Timeout
from webhooks import Webhook

# FILES
import config
import modules

## -- VARIABLES -- ##

mongo_login = os.environ.get("MONGO_LOGIN")
client = MongoClient(f"{mongo_login}",tlsCAFile=certifi.where())
db = client["db2"]

server_data_col = db["server_data"]
muted_users_col = db["muted_users"]
privacy_settings_col = db["privacy_settings"]

ratios = {
    "years": 31556952,
    "months": 2629800,
    "days": 86400,
    "hours": 3600,
    "minutes": 60,
    "seconds": 1
}

## -- FUNCTIONS -- ##

def hours_minutes_seconds(td):
    return td.seconds//3600, (td.seconds//60)%60, td.seconds


## -- COG -- ##

class OnMemberJoin(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: disnake.Member):

        naive = datetime.datetime.replace(member.created_at, tzinfo=None)
        created_ago = (datetime.datetime.now() - naive)
        seconds_old = created_ago.total_seconds()

        query = {
            "guild_id": str(member.guild.id)
        }
        data = {
            "guild_id": str(member.guild.id),
            "member_join_logs_webhook": "None",
            "welcome_channel": "None",
            "welcome_toggle": "false",
        }
        server_data = server_data_col.find_one(query)
        if not server_data:
            server_data_col.insert_one(data)
            return
            
        webhook_url = server_data.get("member_join_logs_webhook")
        welcome_channel_id = server_data.get("welcome_channel")
        welcome_toggle = server_data.get("welcome_toggle")

        update = {
            "member_join_logs_webhook": webhook_url or "None",
            "welcome_channel": welcome_channel_id or "None",
            "welcome_toggle": welcome_toggle or "false"
        }
        
        if webhook_url == "None" or not webhook_url:
            if not webhook_url:
                server_data_col.update_one(query, update)
                return
            return
        if welcome_channel_id == "None" or not welcome_channel_id:
            if not welcome_channel_id:
                server_data_col.update_one(query, update)
                return
        if not welcome_toggle:
            server_data_col.update_one(query, update)
            return
        welcome_channel = self.bot.get_channel(int(welcome_channel_id))

        webhook = Webhook(url=webhook_url, username="OutDash Logging", avatar_url=str(self.bot.user.avatar or "https://cdn.discordapp.com/embed/avatars/1.png"))

        embed = disnake.Embed(description="**Member joined**", color=config.logs_add_embed_color, timestamp=datetime.datetime.utcnow())
        embed.set_author(name=f"{member.name}#{member.discriminator}", icon_url=member.avatar or "https://cdn.discordapp.com/embed/avatars/1.png")
        embed.add_field(name="Account Created", value=f"{modules.seconds_to_text(seconds_old, 3)} ago", inline=False)

        webhook.add_embed(embed)
        
        data = {
            "username": "OutDash Logging",
            "avatar_url": str(self.bot.user.avatar)
        }

        welcome_embed = disnake.Embed(description=f"**Welcome to __{member.guild.name}__!**", color=config.logs_embed_color)
        welcome_embed.set_author(name=f"{member.name}#{member.discriminator}", icon_url=member.avatar)
        welcome_embed.set_thumbnail(url=member.guild.icon)
        welcome_embed.timestamp = datetime.datetime.utcnow()

        webhook.post(remove_embeds=False)
        
        if welcome_channel_id != "None" and welcome_channel_id and welcome_toggle == "true":
            await welcome_channel.send(content=f"<@{member.id}>,", embed=welcome_embed)

    
    
def setup(bot):
    bot.add_cog(OnMemberJoin(bot))