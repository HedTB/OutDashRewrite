## -- IMPORTING -- ##

# MODULES
import os
import random
import asyncio
import datetime
import disnake

from disnake.ext import commands
from disnake.errors import Forbidden, HTTPException
from disnake.ext.commands import errors

# FILES
from extra import config
from extra import functions
from extra.checks import is_moderator

class Ban(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    @is_moderator(ban_members=True)
    async def ban(self, ctx: commands.Context,member:disnake.Member, *, reason="No reason provided."):
        """Bans a member from the server."""
        
        if member == ctx.author:
            embed = disnake.Embed(description=f"{config.no} You can't ban yourself!", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif member == self.bot.user:
            embed = disnake.Embed(description=f"{config.no} I can't ban myself!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return

        embed = disnake.Embed(description=f"{config.yes} **{member}** was banned.", color=config.success_emdisnakeor)
        embed2 = disnake.Embed(description=f"{config.yes} **{member}** was banned. I couldn't DM them though.", color=config.success_emdisnakeor)
        dmEmbed = disnake.Embed(description=f"{config.moderator} You got banned from **{ctx.guild.name}**. \nReason: {reason}", color=config.embed_color)
        
        try:
            await member.send(embed=dmEmbed)
            await member.ban(reason=reason)
            await ctx.send(embed=embed)
        except HTTPException as e:
            if e.status == 400:
                await member.ban(reason=reason)
                await ctx.send(embed=embed2)
                
    
    @ban.error 
    async def ban_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, errors.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions[0].capitalize()}` permission.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, errors.MissingRequiredArgument):
            embed = disnake.Embed(description=f"{config.no} You need to specify who you want to ban.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error.original, Forbidden):
            is_role_above_role = functions.is_role_above_role(ctx.guild.get_member(self.bot.user.id).top_role, ctx.author.top_role)
            if is_role_above_role:
                embed = disnake.Embed(description=f"{config.no} You don't have permission to ban this member.", color=config.error_embed_color)
                await ctx.send(embed=embed)
            elif is_role_above_role == False:
                embed = disnake.Embed(description=f"{config.no} I don't have permission to ban this member.", color=config.error_embed_color)
                await ctx.send(embed=embed)
            
        
    
    @commands.slash_command(name="ban", description="Ban a member from the guild.")
    @is_moderator(ban_members=True)
    @is_moderator(ban_members=True)
    async def slash_ban(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, reason: str = "No reason provided."):
        """Ban a member from the guild.
        Parameters
        ----------
        member: The member you want to ban.
        reason: The reason for the ban.
        """
        if member == inter.author:
            embed = disnake.Embed(description=f"{config.no} You can't ban yourself!", color=config.error_embed_color)
            await inter.send(embed=embed)
        elif member == self.bot.user:
            embed = disnake.Embed(description=f"{config.no} I can't ban myself!", color=config.error_embed_color)
            await inter.send(embed=embed)
            return
        
        embed = disnake.Embed(description=f"{config.yes} **{member}** was banned.", color=config.success_embed_color)
        embed2 = disnake.Embed(description=f"{config.yes} **{member}** was banned. I couldn't DM them though.", color=config.success_embed_color)
        dmEmbed = disnake.Embed(description=f"{config.moderator} You was banned in **{inter.guild.name}**. \nReason: {reason}", color=config.embed_color)
        
        try:
            await member.send(embed=dmEmbed)
            await member.ban(reason=reason)
            await inter.send(embed=embed)
        except HTTPException as e:
            if e.status == 400:
                await member.ban(reason=reason)
                await inter.send(embed=embed2)
    
    @slash_ban.error 
    async def slash_ban_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, errors.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions[0].capitalize()}` permission.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error, errors.MissingRequiredArgument):
            embed = disnake.Embed(description=f"{config.no} You need to specify who you want to ban.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error.original, Forbidden):
            is_role_above_role = functions.is_role_above_role(inter.guild.get_member(self.bot.user.id).top_role, inter.author.top_role)
            if is_role_above_role:
                embed = disnake.Embed(description=f"{config.no} You don't have permission to ban this member.", color=config.error_embed_color)
                await inter.response.send_message(embed=embed)
            elif is_role_above_role == False:
                embed = disnake.Embed(description=f"{config.no} I don't have permission to ban this member.", color=config.error_embed_color)
                await inter.response.send_message(embed=embed)
    
        
    
def setup(bot):
    bot.add_cog(Ban(bot))