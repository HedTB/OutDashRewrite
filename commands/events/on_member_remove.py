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
from extra.webhooks import Webhook

# FILES
import extra.config as config
import extra.functions as functions

## -- VARIABLES -- ##

mongo_login = os.environ.get("MONGO_LOGIN")
client = MongoClient(f"{mongo_login}",tlsCAFile=certifi.where())
db = client[config.database_collection]

server_data_col = db["server_data"]
muted_users_col = db["muted_users"]
user_data_col = db["user_data"]

## -- FUNCTIONS -- ##

def list_to_string(list: list):
    str1 = ""
    for element in list:
        str1 + element
        
    return str1

def days_hours_minutes_seconds(td):
    return td.days, td.seconds//3600, (td.seconds//60)%60, td.seconds

## -- COG -- ##

class OnMemberRemove(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_remove(self, member: disnake.Member):

        naive = datetime.datetime.replace(member.joined_at, tzinfo=None)
        joined_at = (datetime.datetime.now() - naive)
        seconds_old = joined_at.total_seconds()

        query = {
            "guild_id": str(member.guild.id)
        }
        data = {
            "guild_id": str(member.guild.id),
            "member_leave_logs_webhook": "None"
        }
        update = { "$set": { "member_leave_logs_webhook": "None" } }
        server_data = server_data_col.find_one(query)
        if not server_data:
            print(1)
            server_data_col.insert_one(data)
            await self.on_member_remove(member)
            return
            
        webhook_url = server_data.get("member_remove_logs_webhook")
        if webhook_url == "None" or not webhook_url:
            if not webhook_url:
                server_data_col.update_one(query, update)
                return
            return
        
        roles = []
        for role in member.roles:
            if role.name == "@everyone":
                continue
            roles.append(role.mention + " ")
        role_str = "".join(roles)
        
        webhook = Webhook(url=webhook_url, username="OutDash Logging", avatar_url=str(self.bot.user.avatar))
        embed = disnake.Embed(description=f"**Member left**", color=config.logs_delete_embed_color)

        embed.add_field(name="Member Since", value=f"{functions.seconds_to_text(seconds_old, 3)} ago", inline=False)
        embed.add_field(name="Roles", value=str(role_str), inline=False)
        embed.set_author(name=f"{member.name}#{member.discriminator}", icon_url=member.avatar or "https://cdn.discordapp.com/embed/avatars/1.png")
        embed.timestamp = datetime.datetime.utcnow()
        
        webhook.add_embed(embed)
        webhook.post()
    
    
def setup(bot):
    bot.add_cog(OnMemberRemove(bot))
