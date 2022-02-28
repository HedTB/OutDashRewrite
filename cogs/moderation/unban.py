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

## -- FUNCTIONS -- ##

async def is_banned(bot: commands.Bot, guild: disnake.Guild, user: int):
    user = bot.get_user(user)
    print(user)
    
    try:
        return True if await guild.fetch_ban(user) else False
    except:
        return False

class Unban(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @commands.command()
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.user)
    @is_moderator(ban_members=True)
    async def unban(self, ctx: commands.Context, user: disnake.User, *, reason: str = "No reason provided."):
        """Unban someone from the server."""
                
        if not await is_banned(self.bot, ctx.guild, user.id):
            embed = disnake.Embed(description=f"{config.no} This user isn't banned!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
        
        embed = disnake.Embed(description=f"{config.yes} **{user}** was unbanned.", color=config.success_embed_color)
        embed2 = disnake.Embed(description=f"{config.yes} **{user}** was unbanned. I couldn't DM them though.", color=config.success_embed_color)
        dmEmbed = disnake.Embed(description=f"{config.moderator} You was unbanned in **{ctx.guild.name}**. \nReason: {reason}", color=config.embed_color)
        
        try:
            await user.send(embed=dmEmbed)
            await ctx.guild.unban(user, reason=reason)
            await ctx.send(embed=embed)
        except HTTPException as e:
            if e.status == 400:
                await ctx.guild.unban(user, reason=reason)
                await ctx.send(embed=embed2)
    
    @unban.error
    async def unban_error(self, ctx: commands.Context, error):
        if isinstance(error, errors.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `Ban Members` permission.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, errors.MissingRequiredArgument):
            embed = disnake.Embed(description=f"{config.no} You need to specify who you want to unban.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error.original, Forbidden):
            is_role_above_role = functions.is_role_above_role(ctx.guild.get_member(self.bot.user.id).top_role, ctx.author.top_role)
            if is_role_above_role:
                embed = disnake.Embed(description=f"{config.no} You don't have permission to unban this user.", color=config.error_embed_color)
                await ctx.send(embed=embed)
            elif not is_role_above_role:
                embed = disnake.Embed(description=f"{config.no} I don't have permission to unban this user.", color=config.error_embed_color)
                await ctx.send(embed=embed)
                
    
    @commands.slash_command(name="unban", description="Unban someone from the server.")
    @is_moderator(ban_members=True)
    async def slash_unban(self, inter: disnake.ApplicationCommandInteraction, user: disnake.Member, reason: str = "No reason provided."):
        """Unban someone from the server.
        Parameters
        ----------
        user: The user you want to unban.
        reason: The reason for the unban.
        ----------
        """
        
        if not await is_banned(self.bot, inter.guild, user.id):
            embed = disnake.Embed(description=f"{config.no} This user isn't banned!", color=config.error_embed_color)
            await inter.send(embed=embed)
            return
        
        embed = disnake.Embed(description=f"{config.yes} **{user}** was unbanned.", color=config.success_embed_color)
        embed2 = disnake.Embed(description=f"{config.yes} **{user}** was unbanned. I couldn't DM them though.", color=config.success_embed_color)
        dmEmbed = disnake.Embed(description=f"{config.moderator} You was unbanned in **{inter.guild.name}**. \nReason: {reason}", color=config.embed_color)
        
        try:
            await user.send(embed=dmEmbed)
            await inter.guild.unban(user, reason=reason)
            await inter.send(embed=embed)
        except HTTPException as e:
            if e.status == 400:
                await inter.guild.unban(user, reason=reason)
                await inter.send(embed=embed2)


    @slash_unban.error 
    async def slash_unban_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, errors.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `Ban Members` permission.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error, errors.MissingRequiredArgument):
            embed = disnake.Embed(description=f"{config.no} You need to specify who you want to unban.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error.original, Forbidden):
            is_role_above_role = functions.is_role_above_role(inter.guild.get_member(self.bot.user.id).top_role, inter.author.top_role)
            if is_role_above_role:
                embed = disnake.Embed(description=f"{config.no} You don't have permission to unban this user.", color=config.error_embed_color)
                await inter.response.send_message(embed=embed)
            elif is_role_above_role == False:
                embed = disnake.Embed(description=f"{config.no} I don't have permission to unban this user.", color=config.error_embed_color)
                await inter.response.send_message(embed=embed)
                
                
def setup(bot):
    bot.add_cog(Unban(bot))