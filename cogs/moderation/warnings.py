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

## -- VARIABLES -- ##

mongo_login = os.environ.get("MONGO_LOGIN")
client = MongoClient(f"{mongo_login}",tlsCAFile=certifi.where())
db = client["db2"]

server_data_col = db["server_data"]
warns_col = db["warns"]


class Warnings(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @commands.command()
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    async def warnings(self, ctx: commands.Context, member: disnake.Member = None):
        """View how many warnings you or another member has."""
        result = warns_col.find_one({
            "guild_id": str(ctx.guild.id)
        })

        if not member:
            member = ctx.author

        try:
            warnings = result[str(member.id)]
        except Exception:
            warnings = None

        if not result:
            warns_col.insert_one({
                "guild_id": str(ctx.guild.id)
            })
        elif not warnings:
            embed = disnake.Embed(title=f"0 warnings for {member}", description=f"{config.info} This user doesn't have any warnings.", color=config.embed_color)
        else:
            warnings = json.loads(warnings)
            recent_warning = int(list(warnings.keys())[-1]) or 1
            description = ""
            
            for warning in warnings:
                warning_num = warning
                warning = warnings[warning]
                reason = warning["reason"]
                moderator = warning["moderator"]
                warn_time = warning["time"]

                description +=  f"**#{warning_num} | Moderator: {self.bot.get_user(moderator)}**\n" + f"{reason} | {warn_time[:16]} UTC\n"

            embed = disnake.Embed(title=f"{recent_warning} warnings for {member}", 
            description=description, color=config.embed_color)

        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar or "https://cdn.discordapp.com/embed/avatars/1.png")
        await ctx.send(embed=embed)
        
    
    @commands.slash_command(name="warnings", description="View how many warnings you or another member has.")
    @commands.has_permissions(moderate_members=True)
    async def slash_warnings(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member = None):
        """View how many warnings you or another member has.
        Parameters
        ----------
        member: The member you want to view warnings for.
        """

        result = warns_col.find_one({
            "guild_id": str(inter.guild.id)
        })

        if not member:
            member = inter.author

        try:
            warnings = result[str(member.id)]
        except Exception:
            warnings = None

        if not result:
            warns_col.insert_one({
                "guild_id": str(inter.guild.id)
            })
        elif not warnings:
            embed = disnake.Embed(title=f"0 warnings for {member}", description=f"{config.info} This user doesn't have any warnings.", color=config.embed_color)
        else:
            warnings = json.loads(warnings)
            recent_warning = int(list(warnings.keys())[-1]) or 1
            description = ""

            for warning in warnings:
                warning_num = warning
                warning = warnings[warning]
                reason = warning["reason"]
                moderator = warning["moderator"]
                warn_time = warning["time"]

                description +=  f"**#{warning_num} | Moderator: {self.bot.get_user(moderator)}**\n" + f"{reason} | {warn_time[:16]} UTC\n"

            embed = disnake.Embed(title=f"{recent_warning} warnings for {member}", 
            description=description, color=config.embed_color)

        embed.set_footer(text=f"Requested by {inter.author}", icon_url=inter.author.avatar or "https://cdn.discordapp.com/embed/avatars/1.png")
        await inter.send(embed=embed)
            
    
        
    
def setup(bot):
    bot.add_cog(Warnings(bot))