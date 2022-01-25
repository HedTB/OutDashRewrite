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
from dotenv import load_dotenv

# FILES
import extra.config as config
import extra.functions as functions

load_dotenv()

## -- VARIABLES -- ##

mongo_login = os.environ.get("MONGO_LOGIN")
client = MongoClient(f"{mongo_login}",tlsCAFile=certifi.where())
db = client["db2"]

server_data_col = db["server_data"]
muted_users_col = db["muted_users"]
privacy_settings_col = db["privacy_settings"]

toggle_list = commands.option_enum({"enabled": "enabled", "disabled": "disabled"})

## -- COG -- ##

class SetWelcomeChannel(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    @commands.has_permissions(manage_guild=True)
    async def setwelcomechannel(self, ctx, channel: disnake.TextChannel = None):
        """Set the channel where welcome messages should be sent."""
        
        data = functions.get_db_data(str(ctx.guild_id))
        query = {"guild_id": str(ctx.guild.id)}
        result = server_data_col.find_one(query)
        if not result:
            server_data_col.insert_one(data)
            self.setwelcomechannel(ctx, channel)

        if result["settings_locked"] == "true":
            embed = disnake.Embed(description=f"{config.no} The server's settings are locked.", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
        elif not result["settings_locked"]:
            update = {"$set": {
                "settings_locked": "false"
            }}
            server_data_col.update_one(query, update)
        
        update = { "$set": {
                "welcome_channel": str(channel.id)
            }}
        server_data_col.update_one(query, update)
        embed = disnake.Embed(description=f"{config.yes} Welcome messages will now be sent in <#{channel.id}>.", color=config.success_embed_color)
        await ctx.send(embed=embed)
    
    @setwelcomechannel.error 
    async def setwelcomechannel_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `Manage Guild` permission.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = disnake.Embed(description=f"{config.no} Please specify a channel!\n If you're looking to disable the welcome message, run `{self.bot.get_prefix}togglewelcome off`.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        
    
def setup(bot):
    bot.add_cog(SetWelcomeChannel(bot))