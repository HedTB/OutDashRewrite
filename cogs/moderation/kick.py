## -- IMPORTING -- ##

# MODULES
import discord
import os
import random
import asyncio
import datetime

from discord.ext import commands
from discord.commands.commands import Option
from discord.errors import Forbidden, HTTPException
from discord.ext.commands import errors
from pymongo import MongoClient

# FILES
import bot_info

class Kick(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.member)
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member:discord.Member, *, reason="No reason provided."):
        
        embed = discord.Embed(description=f"{bot_info.yes} **{member}** was kicked.", color=bot_info.success_embed_color)
        embed2 = discord.Embed(description=f"{bot_info.yes} **{member}** was kicked. I couldn't DM them though.", color=bot_info.success_embed_color)
        dmEmbed = discord.Embed(description=f"You got kicked from **{ctx.guild.name}**. Reason: {reason}", color=bot_info.embed_color)
        
        try:
            await member.send(embed=dmEmbed)
            await member.kick(reason=reason)
            await ctx.send(embed=embed)
        except HTTPException as e:
            if e.status == 400:
                await member.kick(reason=reason)
                await ctx.send(embed=embed2)
                
    
    @kick.error 
    async def kick_error(self, ctx, error):
        if isinstance(error, errors.MissingPermissions):
            embed = discord.Embed(description=f"{bot_info.no} You're missing the `Kick Members` permission.", color=bot_info.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, errors.MissingRequiredArgument):
            embed = discord.Embed(description=f"{bot_info.no} You need to specify who you want to kick.", color=bot_info.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, errors.CommandInvokeError) or isinstance(error, Forbidden):
            embed = discord.Embed(description=f"{bot_info.no} You don't have permission to kick this member.", color=bot_info.error_embed_color)
            await ctx.send(embed=embed)
            
        
    
    @commands.slash_command(name="kick", description="Kick a member from the guild.", guild_ids=[bot_info.bot_server])
    @commands.has_permissions(kick_members=True)
    async def slash_kick(self, ctx,
                  member:Option(discord.Member, "The user you want to kick.", required=True),
                  reason:Option(str, "The reason for the kick.", required=False, default="No reason provided.")):
        
        embed = discord.Embed(description=f"{bot_info.yes} **{member}** was kicked.", color=bot_info.success_embed_color)
        embed2 = discord.Embed(description=f"{bot_info.yes} **{member}** was kicked. I couldn't DM them though.", color=bot_info.success_embed_color)
        dmEmbed = discord.Embed(description=f"You got kicked from **{ctx.guild.name}**. Reason: {reason}", color=bot_info.embed_color)
        
        try:
            await member.send(embed=dmEmbed)
            await member.kick(reason=reason)
            await ctx.respond(embed=embed)
        except HTTPException as e:
            if e.status == 400:
                await member.kick(reason=reason)
                await ctx.send(embed=embed2)
                
    
    @slash_kick.error 
    async def slash_kick_error(self, ctx, error):
        if isinstance(error, errors.MissingPermissions):
            embed = discord.Embed(description=f"{bot_info.no} You're missing the `Kick Members` permission.", color=bot_info.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, errors.MissingRequiredArgument):
            embed = discord.Embed(description=f"{bot_info.no} You need to specify who you want to kick.", color=bot_info.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, errors.CommandInvokeError) or isinstance(error, Forbidden):
            embed = discord.Embed(description=f"{bot_info.no} You don't have permission to kick this member.", color=bot_info.error_embed_color)
            await ctx.send(embed=embed)
    
        
    
def setup(bot):
    bot.add_cog(Kick(bot))