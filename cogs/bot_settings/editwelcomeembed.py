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
db = client["db"]

server_data_col = db["server_data"]
muted_users_col = db["muted_users"]
privacy_settings_col = db["privacy_settings"]

embed_values = [
    "title",
    "description",
    "author_name",
    "author_icon",
    "footer_text",
    "footer_icon",
    "timestamp",
    "thumbnail",
    "color"
]

## -- FUNCTIONS -- ##

def list_to_str(list: list):
    return_str = ""

    for ele in list:
        return_str += str(ele)
    return return_str

def replace_variable(str: str, variable: str):
    variables = {
        "guild_name", "guild_icon", "member_username", "member_icon",
        "member_name", "member_discriminator", "member_mention"
    }


## -- COG -- ##

class EditWelcomeEmbed(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    @commands.has_permissions(manage_guild=True)
    async def editwelcomeembed(self, ctx: commands.Context, embed_part: str, *, value: str):
        """Toggles if welcome messages should be sent."""
        embed_part = embed_part.lower()
        
        query = {"guild_id": str(ctx.guild.id)}
        result = server_data_col.find_one(query)

        if not result:
            server_data_col.insert_one(await functions.get_db_data(ctx.guild.id))
            self.editwelcomeembed(ctx, embed_part, value)

        if result["settings_locked"] == "true":
            embed = disnake.Embed(description=f"{config.no} The server's settings are locked.", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
        elif not result["settings_locked"]:
            update = {"$set": {
                "settings_locked": "false"
            }}
            server_data_col.update_one(query, update)

        if not embed_part in embed_values:
            embed = disnake.Embed(description=f"{config.no} Please specify a valid part of the embed!\nEmbed parts:\n```{', '.join(e for e in embed_values)}```", color=config.error_embed_color)
            await ctx.send(embed=embed)
        else:
            embed = disnake.Embed(description=f"{config.no} Please give a valid toggle value!\nToggles:\n```on, yes, true, enabled - welcome messages enabled\noff, no, false, disabled - welcome messages disabled```", color=config.error_embed_color)
            await ctx.send(embed=embed)
    
    @editwelcomeembed.error 
    async def setwelcomechannel_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `Manage Guild` permission.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = disnake.Embed(description=f"{config.no} Please specify a toggle value!\nToggles:\n```on, yes, true, enabled - welcome messages enabled\noff, no, false, disabled - welcome messages disabled```", color=config.error_embed_color)
            await ctx.send(embed=embed)
            
    
def setup(bot):
    bot.add_cog(EditWelcomeEmbed(bot))