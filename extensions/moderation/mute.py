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
from dotenv import load_dotenv

load_dotenv()

# FILES
from extra import config
from extra import functions
from extra.checks import is_moderator

## -- VARIABLES -- ##

mongo_login = os.environ.get("MONGO_LOGIN")
client = MongoClient(f"{mongo_login}",tlsCAFile=certifi.where())
db = client[config.database_collection]

server_data_col = db["server_data"]
muted_users_col = db["muted_users"]


class Mute(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @commands.command(aliases=["timeout"])
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    @is_moderator(moderate_members=True)
    async def mute(self, ctx: commands.Context, member: disnake.Member, length: str, *, reason: str = "No reason provided."):
        """Mute a member who's breaking the rules!"""
        if member == ctx.author:
            embed = disnake.Embed(description=f"{config.no} You can't mute yourself!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
        elif member == self.bot.user:
            embed = disnake.Embed(description=f"{config.no} I can't mute myself!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
        
        seconds = functions.manipulate_time(length, return_type="seconds")
        
        if seconds == "InvalidInput":
            embed = disnake.Embed(description=f"{config.no} Please provide a valid time format. \nExample:\n```10s = 10 seconds\n1m = 1 minute\n3h = 3 hours\n2d = 2 days```",
                                    color=config.error_embed_color)
            await ctx.send(embed=embed)

        embed = disnake.Embed(description=f"{config.yes} **{member.name}#{member.discriminator}** has been muted.\n**Reason:** {reason}", color=config.success_embed_color)
        
        await member.timeout(duration=int(seconds), reason=reason)
        await ctx.send(embed=embed)
        
    
    @mute.error
    async def mute_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions[0].capitalize()}` permission.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == "member":
                embed = disnake.Embed(description=f"{config.no} Please specify the member you want to mute.", color=config.error_embed_color)
                await ctx.send(embed=embed)
            elif error.param.name == "length":
                embed = disnake.Embed(description=f"{config.no} Please specify how long they should be muted.", color=config.error_embed_color)
                await ctx.send(embed=embed)
        elif isinstance(error.original, Forbidden):
            is_role_above_role = functions.is_role_above_role(ctx.guild.get_member(self.bot.user.id).top_role, ctx.author.top_role)
            if is_role_above_role:
                embed = disnake.Embed(description=f"{config.no} You don't have permission to mute this member.", color=config.error_embed_color)
                await ctx.send(embed=embed)
            elif is_role_above_role == False:
                embed = disnake.Embed(description=f"{config.no} I don't have permission to mute this member.", color=config.error_embed_color)
                await ctx.send(embed=embed)
        
    
    @commands.slash_command(name="mute", description="Mute a member who's breaking the rules!")
    @is_moderator(moderate_members=True)
    async def slash_mute(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, length: str = "5m", reason: str = "No reason provided."):
        """Mute a member who's breaking the rules!
        Parameters
        ----------
        member: The member you want to mute.
        length: How long the mute should last.
        reason: The reason for the mute.
        """
        if member == inter.author:
            embed = disnake.Embed(description=f"{config.no} You can't mute yourself!", color=config.error_embed_color)
            await inter.send(embed=embed)
            return
        elif member == self.bot.user:
            embed = disnake.Embed(description=f"{config.no} I can't mute myself!", color=config.error_embed_color)
            await inter.send(embed=embed)
            return
        
        seconds = functions.manipulate_time(length, return_type="seconds")
        
        if seconds == "InvalidInput":
            embed = disnake.Embed(description=f"{config.no} Please provide a valid time format. \nExample:\n```10s = 10 seconds\n1m = 1 minute\n3h = 3 hours\n2d = 2 days```",
                                    color=config.error_embed_color)
            await inter.send(embed=embed)

        embed = disnake.Embed(description=f"{config.yes} **{member.name}#{member.discriminator}** has been muted.\n**Reason:** {reason}", color=config.success_embed_color)
        
        await member.timeout(duration=int(seconds), reason=reason)
        await inter.send(embed=embed)


    @slash_mute.error 
    async def slash_mute_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions[0].capitalize()}` permission.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == "member":
                embed = disnake.Embed(description=f"{config.no} Please specify the member you want to mute.", color=config.error_embed_color)
                await inter.response.send_message(embed=embed, ephemeral=True)
            elif error.param.name == "length":
                embed = disnake.Embed(description=f"{config.no} Please specify how long they should be muted.", color=config.error_embed_color)
                await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error.original, Forbidden):
            is_role_above_role = functions.is_role_above_role(inter.guild.get_member(self.bot.user.id).top_role, inter.author.top_role)
            if is_role_above_role:
                embed = disnake.Embed(description=f"{config.no} You don't have permission to mute this member.", color=config.error_embed_color)
                await inter.response.send_message(embed=embed)
            elif is_role_above_role == False:
                embed = disnake.Embed(description=f"{config.no} I don't have permission to mute this member.", color=config.error_embed_color)
                await inter.response.send_message(embed=embed)
            
    
        
    
def setup(bot):
    bot.add_cog(Mute(bot))