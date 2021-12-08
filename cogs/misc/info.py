## -- IMPORTING -- ##

# MODULES
import discord
import os
import random
import asyncio
import datetime
import certifi

from discord.ext import commands
from discord.commands.commands import Option
from discord.errors import Forbidden, HTTPException
from discord.ext.commands import errors
from pymongo import MongoClient

# FILES
import bot_info

class Info(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(rate=1, per=bot_info.cooldown_time, type=commands.BucketType.member)
    async def info(self, ctx):
        
        embed = discord.Embed(title="Information",
                        description=f"**Main Developer:** {self.bot.get_user(bot_info.owners[0])}\n**Web Developer:** {self.bot.get_user(bot_info.owners[1])}\n\n"
                        f"\n**Upvote OutDash Here:** https://bit.ly/UpvoteOD1\n**If you wanna support us, go here:** https://bit.ly/SupportOutDash\n**Join the support server to report bugs or if you have any questions:** https://bit.ly/OutDashSupport\n\n**Invite OutDash Here:** https://bit.ly/OutDash\n**Invite The Beta Bot Here:** https://bit.ly/OutDashBeta\n\n " 
                        "Thanks for using our bot, it means a lot :heart:",
                        color=bot_info.embed_color)
        embed.set_footer(text=f"Requested by {ctx.author}")
        embed.timestamp = datetime.datetime.utcnow()
        
        await ctx.send(embed=embed)
        
    
    @commands.slash_command(name="info", description="Get to know about OutDash!", guild_ids=[bot_info.bot_server])
    async def slash_info(self, ctx):
        
        embed = discord.Embed(title="Information",
                        description=f"**Main Developer:** {self.bot.get_user()}\n**Web Developer:** hachamer#5321\n\n"
                        f"\n**Upvote OutDash Here:** https://bit.ly/UpvoteOD1\n**If you wanna support us, go here:** https://bit.ly/SupportOutDash\n**Join the support server to report bugs or if you have any questions:** https://bit.ly/OutDashSupport\n\n**Invite OutDash Here:** https://bit.ly/OutDash\n**Invite The Beta Bot Here:** https://bit.ly/OutDashBeta\n\n " 
                        "Thanks for using our bot, it means a lot :heart:",
                        color=bot_info.embed_color)
        embed.set_footer(text=f"Requested by {ctx.author}")
        embed.timestamp = datetime.datetime.utcnow()
        
        await ctx.respond(embed=embed)
        
    
def setup(bot):
    bot.add_cog(Info(bot))