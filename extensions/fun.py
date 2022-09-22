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
from utils.data import *
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

    ## -- SLASH COMMANDS -- ##

    @commands.slash_command(
        name="meme",
        description="Generates a random meme from the r/memes subreddit!",
        guild_ids=[config.BOT_SERVER],
    )
    async def meme(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()

        memes_submissions = reddit.subreddit("memes").hot()
        post_to_pick = random.randint(1, 100)

        for _ in range(0, post_to_pick):
            submission = next(x for x in memes_submissions if not x.stickied)

        await inter.send(
            embed=disnake.Embed(
                description=f"**{submission.title}**", color=colors.embed_color, timestamp=datetime.datetime.utcnow()
            )
            .set_footer(
                icon_url=inter.author.avatar or config.DEFAULT_AVATAR_URL,
                text=f"Requested by {inter.author}",
            )
            .set_image(url=submission.url)
        )


def setup(bot):
    bot.add_cog(Fun(bot))
