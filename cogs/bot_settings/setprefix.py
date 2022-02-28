## -- IMPORTING -- ##

# MODULE
import disnake
import os
import random
import asyncio
import datetime
import certifi

from disnake.ext import commands
from disnake.ext.commands import errors
from pymongo import MongoClient
from dotenv import load_dotenv

# FILES
import extra.config as config
import extra.functions as functions

load_dotenv()

## -- VARIABLES -- ##

mongo_token = os.environ.get("MONGO_LOGIN")
client = MongoClient(f"{mongo_token}",tlsCAFile=certifi.where())
db = client[config.database_collection]

prefixes_col = db["prefixes"]
confirmations_col = db["bot_farm_confirmations"]
server_data_col = db["server_data"]


class SetPrefix(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        

    @commands.command(aliases=["changeprefix", "prefix"])
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    @commands.has_permissions(manage_guild=True)
    async def setprefix(self, ctx, new_prefix: str):
        """Changes the server prefix."""

        data = functions.get_db_data(str(ctx.guild.id))
        query = {"guild_id": str(ctx.guild.id)}
        result = server_data_col.find_one(query)

        if not result:
            server_data_col.insert_one(data)
            self.setprefix(ctx, new_prefix)

        settings_locked = result.get("settings_locked")
        if settings_locked == "true":
            embed = disnake.Embed(description=f"{config.no} The server's settings are locked.", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
        elif not settings_locked:
            update = {"$set": {
                "settings_locked": "false"
            }}
            server_data_col.update_one(query, update)

        if self.bot.get_bot_prefix(ctx.guild.id) == new_prefix:
            embed = disnake.Embed(description=f"{config.no} The prefix is already set to `{new_prefix}`.", color=config.error_embed_color)
            await ctx.send(embed=embed)

        else:
            self.bot.change_prefix(ctx.guild.id, new_prefix)
            embed = disnake.Embed(description=f"{config.yes} Changed the prefix to `{new_prefix}` successfully.", color=config.success_embed_color)
            await ctx.send(embed=embed)
    
    @setprefix.error 
    async def prefix_error(self, ctx, error):
        if isinstance(error, errors.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `Manage Guild` permission.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, errors.MissingRequiredArgument):
            embed = disnake.Embed(description=f"{config.no} You need to specify the new prefix.", color=config.error_embed_color)
            await ctx.send(embed=embed)


    @commands.slash_command(name="setprefix", description="Change the prefix for text commands.")
    @commands.has_permissions(manage_guild=True)
    async def slash_setprefix(self, inter: disnake.ApplicationCommandInteraction, new_prefix: str):
        """Change the prefix for text commands.
        Parameters
        ----------
        new_prefix: What you want your new prefix to be.
        """

        data = functions.get_db_data(str(inter.guild_id))
        query = {"guild_id": str(inter.guild.id)}
        result = server_data_col.find_one(query)
        if not result:
            server_data_col.insert_one(data)
            self.slash_setprefix(inter, new_prefix)

        if result["settings_locked"] == "true":
            embed = disnake.Embed(description=f"{config.no} The server's settings are locked.", color=config.error_embed_color)
            await inter.send(embed=embed)
            return
        elif not result["settings_locked"]:
            update = {"$set": {
                "settings_locked": "false"
            }}
            server_data_col.update_one(query, update)

        if self.bot.get_bot_prefix(inter.guild.id) == new_prefix:
            embed = disnake.Embed(description=f"{config.no} The prefix is already set to `{new_prefix}`.", color=config.error_embed_color)
            await inter.send(embed=embed, ephemeral=True)
            
        else:
            self.bot.change_prefix(inter.guild.id, new_prefix)
            embed = disnake.Embed(description=f"{config.yes} Changed the prefix to `{new_prefix}` successfully.", color=config.success_embed_color)
            await inter.send(embed=embed)
    
        
    
def setup(bot):
    bot.add_cog(SetPrefix(bot))