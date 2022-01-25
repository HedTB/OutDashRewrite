## -- IMPORTING -- ##

# MODULES
import disnake
import os
import random
import asyncio
import datetime
import certifi
import time
import json

from disnake.ext import commands
from disnake.errors import Forbidden, HTTPException
from disnake.ext.commands import errors
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# FILES
import extra.config as config
import extra.functions as functions
from extra.checks import is_moderator

## -- VARIABLES -- ##

mongo_login = os.environ.get("MONGO_LOGIN")
client = MongoClient(f"{mongo_login}",tlsCAFile=certifi.where())
db = client["db2"]

server_data_col = db["server_data"]
warns_col = db["warns"]


class Warn(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @commands.command()
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    @is_moderator()
    async def warn(self, ctx: commands.Context, member: disnake.Member, *, reason: str):
        """Warn a member for their bad actions!"""
        result = warns_col.find_one({
            "guild_id": str(ctx.guild.id)
        })

        if member == ctx.author:
            embed = disnake.Embed(description=f"{config.no} You can't warn yourself!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
        elif member.bot:
            embed = disnake.Embed(description=f"{config.no} You can't warn a bot!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
        elif functions.is_role_above_role(member.top_role, ctx.author.top_role) or member.top_role == ctx.author.top_role:
            embed = disnake.Embed(description=f"{config.no} You don't have permission to warn this member!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return

        try:
            warnings = result[str(member.id)]
        except Exception as error:
            warnings = {1: {
                "moderator": ctx.author.id, 
                "reason": reason, 
                "time": str(datetime.datetime.utcnow())
            }}

        if not result:
            warns_col.insert_one({
                "guild_id": str(ctx.guild.id),
                str(member.id): json.dumps(warnings)
            })
        elif not warnings or type(warnings) == dict:
            warns_col.update_one({"guild_id": str(ctx.guild.id)}, {"$set": {
                str(member.id): json.dumps(warnings)
            }})
        else:
            warnings = json.loads(warnings)
            recent_warning = int(list(warnings.keys())[-1]) or 1
            warnings[recent_warning + 1] = {
                "moderator": ctx.author.id, 
                "reason": reason, 
                "time": str(datetime.datetime.utcnow())
            }
            warnings = json.dumps(warnings)

            warns_col.update_one(
                filter = {"guild_id": str(ctx.guild.id)},
                update = {"$set": {
                    str(member.id): warnings
                }}
            )

        embed = disnake.Embed(description=f"{config.yes} **{member.name}#{member.discriminator}** has been warned.", color=config.success_embed_color)
        await ctx.send(embed=embed)
        
    
    @warn.error
    async def warn_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `Moderate Members` permission.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == "member":
                embed = disnake.Embed(description=f"{config.no} Please specify the member you want to warn.", color=config.error_embed_color)
                await ctx.send(embed=embed)
            elif error.param.name == "reason":
                embed = disnake.Embed(description=f"{config.no} Please specify the the reason for the warn.", color=config.error_embed_color)
                await ctx.send(embed=embed)
        
    
    @commands.slash_command(name="warn", description="Warn a member for their bad actions!")
    @is_moderator()
    async def slash_warn(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, reason: str):
        """Warn a member for their bad actions!
        Parameters
        ----------
        member: The member you want to warn.
        reason: The reason for the warn.
        """

        result = warns_col.find_one({
            "guild_id": str(inter.guild.id)
        })

        if member == inter.author:
            embed = disnake.Embed(description=f"{config.no} You can't warn yourself!", color=config.error_embed_color)
            await inter.send(embed=embed, ephemeral=True)
            return
        elif member.bot:
            embed = disnake.Embed(description=f"{config.no} You can't warn a bot!", color=config.error_embed_color)
            await inter.send(embed=embed, ephemeral=True)
            return
        elif functions.is_role_above_role(member.top_role, inter.author.top_role) or member.top_role == inter.author.top_role:
            embed = disnake.Embed(description=f"{config.no} You don't have permission to warn this member!", color=config.error_embed_color)
            await inter.send(embed=embed, ephemeral=True)
            return

        try:
            warnings = result[str(member.id)]
        except Exception as error:
            warnings = {1: {
                "moderator": inter.author.id, 
                "reason": reason, 
                "time": str(datetime.datetime.utcnow())
            }}

        if not result:
            warns_col.insert_one({
                "guild_id": str(inter.guild.id),
                str(member.id): json.dumps(warnings)
            })
        elif not warnings or type(warnings) == dict:
            warns_col.update_one({"guild_id": str(inter.guild.id)}, {"$set": {
                str(member.id): json.dumps(warnings)
            }})
        else:
            warnings = json.loads(warnings)
            recent_warning = int(list(warnings.keys())[-1]) or 1
            warnings[recent_warning + 1] = {
                "moderator": inter.author.id, 
                "reason": reason, 
                "time": str(datetime.datetime.utcnow())
            }
            warnings = json.dumps(warnings)

            warns_col.update_one(
                filter = {"guild_id": str(inter.guild.id)},
                update = {"$set": {
                    str(member.id): warnings
                }}
            )

        embed = disnake.Embed(description=f"{config.yes} **{member.name}#{member.discriminator}** has been warned.", color=config.success_embed_color)
        await inter.send(embed=embed)


    @slash_warn.error 
    async def slash_warn_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `Moderate Members` permission.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == "member":
                embed = disnake.Embed(description=f"{config.no} Please specify the member you want to warn.", color=config.error_embed_color)
                await inter.response.send_message(embed=embed, ephemeral=True)
            elif error.param.name == "reason":
                embed = disnake.Embed(description=f"{config.no} Please specify the the reason for the warn.", color=config.error_embed_color)
                await inter.response.send_message(embed=embed, ephemeral=True)
            
    
        
    
def setup(bot):
    bot.add_cog(Warn(bot))