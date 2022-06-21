## -- IMPORTING -- ##

# MODULES
import random
import disnake
import os
import certifi
import praw

from disnake.ext import commands
from pymongo import MongoClient
from dotenv import load_dotenv

# FILES
from utils import config, functions, colors, functions, colors
from utils.checks import *
from utils.classes import *
from utils.emojis import *

## -- VARIABLES -- ##

load_dotenv()

reddit = praw.Reddit(
    client_id=os.environ.get("REDDIT_CLIENT_ID"),
    client_secret=os.environ.get("REDDIT_CLIENT_SECRET"),
    user_agent="Python outdash discordbot v2.0 (by /u/HedTB )",
    check_for_async=False,
)

## -- COG -- ##


class Fun(commands.Cog):
    name = ":balloon: Fun"
    description = "Fun commands to play around with, such as meme."
    emoji = "🎈"

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    ## -- TEXT COMMANDS -- ##

    @commands.command()
    @commands.cooldown(1, config.COOLDOWN_TIME, commands.BucketType.member)
    async def meme(self, ctx):
        """Generates a random meme from the r/memes subreddit!"""
        async with ctx.typing():
            memes_submissions = reddit.subreddit("memes").hot()
            post_to_pick = random.randint(1, 50)

            for i in range(0, post_to_pick):
                submission = next(x for x in memes_submissions if not x.stickied)

            embed = disnake.Embed(
                description=f"**{submission.title}**", color=colors.embed_color
            )

            embed.set_footer(
                icon_url=ctx.author.avatar or config.DEFAULT_AVATAR_URL,
                text=f"Requested by {ctx.author}",
            )
            embed.timestamp = datetime.datetime.utcnow()
            embed.set_image(url=submission.url)

            await ctx.send(embed=embed)

    ## -- SLASH COMMANDS -- ##

    @commands.slash_command(
        name="meme",
        description="Generates a random meme from the r/memes subreddit!",
        guild_ids=[config.BOT_SERVER],
    )
    async def slash_meme(self, inter):
        await inter.response.defer()

        memes_submissions = reddit.subreddit("memes").hot()
        post_to_pick = random.randint(1, 100)
        for i in range(0, post_to_pick):
            submission = next(x for x in memes_submissions if not x.stickied)

        embed = disnake.Embed(
            description=f"**{submission.title}**", color=colors.embed_color
        )

        embed.set_footer(
            icon_url=inter.author.avatar or config.DEFAULT_AVATAR_URL,
            text=f"Requested by {inter.author}",
        )
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_image(url=submission.url)

        await inter.send(embed=embed)


def setup(bot):
    bot.add_cog(Fun(bot))
