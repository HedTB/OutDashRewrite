## -- IMPORTING -- ##

# MODULES
import discord
import os
import random
import asyncio
import datetime
import certifi
import praw

from discord.ext import commands
from discord.commands.commands import Option
from discord.errors import Forbidden, HTTPException
from discord.ext.commands import errors
from pymongo import MongoClient
from dotenv import load_dotenv

# FILES
import bot_info

## -- REDDIT CLIENT -- ##

load_dotenv()
reddit = praw.Reddit(client_id=os.environ.get("REDDIT_CLIENT_ID"),
                     client_secret=os.environ.get("REDDIT_CLIENT_SECRET"),
                     user_agent="Python outdash discordbot v2.0 (by /u/HedTB )",
                     check_for_async=False)

class Meme(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(rate=1, per=bot_info.cooldown_time, type=commands.BucketType.member)
    async def meme(self, ctx):
      async with ctx.typing():

        memes_submissions = reddit.subreddit('memes').hot()
        post_to_pick = random.randint(1, 50)
        for i in range(0, post_to_pick):
          submission = next(x for x in memes_submissions if not x.stickied)
        
        embed = discord.Embed(title="Meme", description=f"{submission.title}", color=0x505050)
        
        embed.set_footer(icon_url=ctx.author.avatar, text=f"Requested by {ctx.author}")
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_image(url=submission.url)
        
      await ctx.send(embed=embed)
    
    @commands.slash_command(name="meme", description="Generates a random meme from the r/memes subreddit!", guild_ids=[bot_info.bot_server])
    async def slash_meme(self, ctx):
      async with ctx.channel.typing():

        memes_submissions = reddit.subreddit('memes').hot()
        post_to_pick = random.randint(1, 100)
        for i in range(0, post_to_pick):
          submission = next(x for x in memes_submissions if not x.stickied)

        embed = discord.Embed(title="Meme", description=f"{submission.title}", color=0x505050)

        embed.set_footer(icon_url=ctx.author.avatar, text=f"Requested by {ctx.author}")
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_image(url=submission.url)
        
      await ctx.respond(embed=embed)
        
    
def setup(bot):
    bot.add_cog(Meme(bot))