## -- IMPORTING -- ##

# MODULES
import disnake
import os
import random
import asyncio
import datetime

from disnake.ext import commands
from disnake.errors import Forbidden, HTTPException
from disnake.ext.commands import errors

# FILES
import config
import modules
from checks import is_moderator

class Kick(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    @is_moderator(kick_members=True)
    async def kick(self, ctx, member:disnake.Member, *, reason="No reason provided."):
        """Kicks a member from the server."""
        
        if member == ctx.author:
            embed = disnake.Embed(description=f"{config.no} You can't kick yourself!", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif member == self.bot.user:
            embed = disnake.Embed(description=f"{config.no} I can't kick myself!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return

        embed = disnake.Embed(description=f"{config.yes} **{member}** was kicked.", color=config.success_embed_color)
        embed2 = disnake.Embed(description=f"{config.yes} **{member}** was kicked. I couldn't DM them though.", color=config.success_embed_color)
        dmEmbed = disnake.Embed(description=f"{config.moderator} You got kicked from **{ctx.guild.name}**. \nReason: {reason}", color=config.embed_color)
        
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
            embed = disnake.Embed(description=f"{config.no} You're missing the `Kick Members` permission.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, errors.MissingRequiredArgument):
            embed = disnake.Embed(description=f"{config.no} You need to specify who you want to kick.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error.original, Forbidden):
            is_role_above_role = modules.is_role_above_role(ctx.guild.get_member(self.bot.user.id).top_role, ctx.author.top_role)
            if is_role_above_role:
                embed = disnake.Embed(description=f"{config.no} You don't have permission to kick this member.", color=config.error_embed_color)
                await ctx.send(embed=embed)
            elif is_role_above_role == False:
                embed = disnake.Embed(description=f"{config.no} I don't have permission to kick this member.", color=config.error_embed_color)
                await ctx.send(embed=embed)
            
        
    
    @commands.slash_command(name="kick", description="Kick a member from the guild.")
    @is_moderator(kick_members=True)
    async def slash_kick(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, reason: str = "No reason provided."):
        """Kick a member from the guild.
        Parameters
        ----------
        member: The member you want to kick.
        reason: The reason for the kick.
        """
        
        if member == inter.author:
            embed = disnake.Embed(description=f"{config.no} You can't kick yourself!", color=config.error_embed_color)
            await inter.send(embed=embed)
            return
        elif member == self.bot.user:
            embed = disnake.Embed(description=f"{config.no} I can't kick myself!", color=config.error_embed_color)
            await inter.send(embed=embed)
            return
        
        embed = disnake.Embed(description=f"{config.yes} **{member}** was kicked.", color=config.success_embed_color)
        embed2 = disnake.Embed(description=f"{config.yes} **{member}** was kicked. I couldn't DM them though.", color=config.success_embed_color)
        dmEmbed = disnake.Embed(description=f"{config.moderator} You got kicked from **{inter.guild.name}**. \nReason: {reason}", color=config.embed_color)
        
        try:
            await member.send(embed=dmEmbed)
            await member.kick(reason=reason)
            await inter.send(embed=embed)
        except HTTPException as e:
            if e.status == 400:
                await member.kick(reason=reason)
                await inter.send(embed=embed2)
                
    
    @slash_kick.error 
    async def slash_kick_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, errors.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `Kick Members` permission.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        if isinstance(error, errors.MissingRequiredArgument):
            embed = disnake.Embed(description=f"{config.no} You need to specify who you want to kick.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error.original, Forbidden):
            is_role_above_role = modules.is_role_above_role(inter.guild.get_member(self.bot.user.id).top_role, inter.author.top_role)
            if is_role_above_role:
                embed = disnake.Embed(description=f"{config.no} You don't have permission to kick this member.", color=config.error_embed_color)
                await inter.response.send_message(embed=embed)
            elif is_role_above_role == False:
                embed = disnake.Embed(description=f"{config.no} I don't have permission to kick this member.", color=config.error_embed_color)
                await inter.response.send_message(embed=embed)
    
    
        
    
def setup(bot):
    bot.add_cog(Kick(bot))