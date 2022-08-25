## -- IMPORTING -- ##

# MODULES
import disnake
import os
import random
import asyncio
import datetime
import certifi

from disnake.ext import commands
from disnake.errors import Forbidden, HTTPException
from disnake.ext.commands import errors
from disnake.utils import get
from pymongo import MongoClient
from dotenv import load_dotenv

# FILES
from utils import config, functions, colors

from utils.checks import *
from utils.emojis import *

load_dotenv()

## -- VARIABLES -- ##

MONGO_LOGIN = os.environ.get("MONGO_LOGIN")
client = MongoClient(MONGO_LOGIN, tlsCAFile=certifi.where())
db = client[config.DATABASE_COLLECTION]

guild_data_col = db["guild_data"]
muted_users_col = db["muted_users"]
user_data_col = db["user_data"]

type_list = commands.option_enum({"wildcard": "wildcard", "normal": "normal"})

## -- COG -- ##


class AutomodSlash(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(name="automod")
    @is_staff(manage_guild=True)
    async def automod(self, inter):
        pass

    @automod.sub_command_group(name="filter")
    @is_staff(manage_guild=True)
    async def filter(self, inter):
        pass

    @filter.sub_command(name="add")
    async def filteradd(
        self, inter: disnake.ApplicationCommandInteraction, type: type_list, word: str
    ):
        await inter.send("wip")

    @automod.error
    async def automod_error(
        self, inter: disnake.ApplicationCommandInteraction, error
    ):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(
                description="{emoji} You're missing the `{permission}` permission.".format(
                    emoji=no,
                    permission=error.missing_permissions[0].title().replace("_", " "),
                ),
                color=colors.error_embed_color,
            )
            await inter.response.send_message(embed=embed)


def setup(bot):
    bot.add_cog(AutomodSlash(bot))
