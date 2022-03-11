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


class UnMute(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @commands.command(aliases=["untimeout"])
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    @is_moderator(moderate_members=True)
    async def unmute(self, ctx: commands.Context, member: disnake.Member, *, reason: str = "No reason provided."):
        """Unmute a member and allow them to talk again."""
        if not member.current_timeout:
            embed = disnake.Embed(description=f"{config.no} This member isn't muted!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return

        embed = disnake.Embed(description=f"{config.yes} **{member.name}#{member.discriminator}** has been unmuted.", color=config.success_embed_color)
        await member.timeout(duration=None, reason=reason)
        await ctx.send(embed=embed)
        
    
    @unmute.error
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
        
    
    @commands.slash_command(name="unmute", description="Unmute a member and allow them to talk again.")
    @is_moderator(moderate_members=True)
    async def slash_unmute(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, reason: str = "No reason provided."):
        """Unmute a member and allow them to talk again.
        Parameters
        ----------
        member: The member you want to mute.
        reason: The reason for the unmute.
        """
        if not member.current_timeout:
            embed = disnake.Embed(description=f"{config.no} This member isn't muted!", color=config.error_embed_color)
            await inter.send(embed=embed)
            return

        embed = disnake.Embed(description=f"{config.yes} **{member.name}#{member.discriminator}** has been unmuted.", color=config.success_embed_color)
        await member.timeout(duration=None, reason=reason)
        await inter.send(embed=embed)


    @slash_unmute.error 
    async def slash_unmute_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions[0].capitalize()}` permission.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == "member":
                embed = disnake.Embed(description=f"{config.no} Please specify the member you want to unmute.", color=config.error_embed_color)
                await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error.original, Forbidden):
            is_role_above_role = functions.is_role_above_role(inter.guild.get_member(self.bot.user.id).top_role, inter.author.top_role)
            if is_role_above_role:
                embed = disnake.Embed(description=f"{config.no} You don't have permission to unmute this member.", color=config.error_embed_color)
                await inter.response.send_message(embed=embed)
            elif is_role_above_role == False:
                embed = disnake.Embed(description=f"{config.no} I don't have permission to unmute this member.", color=config.error_embed_color)
                await inter.response.send_message(embed=embed)
            
    
        
    
def setup(bot):
    bot.add_cog(UnMute(bot))