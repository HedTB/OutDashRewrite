## -- IMPORTING -- ##

# MODULES
import disnake
import os
import random
import datetime
import praw

from disnake.ext import commands
from dotenv import load_dotenv

# FILES
import config

## -- REDDIT CLIENT -- ##

load_dotenv()
reddit = praw.Reddit(client_id=os.environ.get("REDDIT_CLIENT_ID"),
                     client_secret=os.environ.get("REDDIT_CLIENT_SECRET"),
                     user_agent="Python outdash discordbot v2.0 (by /u/HedTB )",
                     check_for_async=False)

class Meme(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    async def meme(self, ctx):
      """Generates a random meme from the r/memes subreddit!"""
      async with ctx.typing():

        memes_submissions = reddit.subreddit('memes').hot()
        post_to_pick = random.randint(1, 50)
        for i in range(0, post_to_pick):
          submission = next(x for x in memes_submissions if not x.stickied)
        
        embed = disnake.Embed(description=f"**{submission.title}**", color=config.embed_color)
        
        embed.set_footer(icon_url=ctx.author.avatar or "https://cdn.discordapp.com/embed/avatars/1.png", text=f"Requested by {ctx.author}")
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_image(url=submission.url)
        
      await ctx.send(embed=embed)
    
    @commands.slash_command(name="meme", description="Generates a random meme from the r/memes subreddit!", guild_ids=[config.bot_server])
    async def slash_meme(self, inter):
        await inter.response.defer()

        memes_submissions = reddit.subreddit('memes').hot()
        post_to_pick = random.randint(1, 100)
        for i in range(0, post_to_pick):
            submission = next(x for x in memes_submissions if not x.stickied)

        embed = disnake.Embed(description=f"**{submission.title}**", color=config.embed_color)

        embed.set_footer(icon_url=inter.author.avatar or "https://cdn.discordapp.com/embed/avatars/1.png", text=f"Requested by {inter.author}")
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_image(url=submission.url)
        
        await inter.send(embed=embed)
    
def setup(bot):
    bot.add_cog(Meme(bot))