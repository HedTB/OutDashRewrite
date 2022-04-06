## -- IMPORTING -- ##

# MODULES
import disnake
import os
import certifi

from disnake.ext import commands
from pymongo import MongoClient
from dotenv import load_dotenv
from typing import (
    List,
)

# FILES
from utils import config, functions, colors
from utils.checks import *
from utils.classes import *
from utils.emojis import *

## -- VARIABLES -- ##

load_dotenv()

## -- COG -- ##


class Automod(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    ## -- FUNCTIONS -- ##

    async def exact_match(self, ctx: commands.Context, filters: List[str]) -> bool:
        message = ctx.message

        for word in message.content.split():
            if word in filters:
                embed = disnake.Embed(
                    description=f"{moderator} Watch your language, {ctx.author.mention}!",
                    color=colors.embed_color,
                )

                await message.delete()
                await ctx.send(embed=embed, delete_after=7)

                await self.bot.log_automod(ctx.author, {
                    "type": "exact",
                    "word": word,
                    "message": message,
                    "time": time.time(),
                })
                
                return True

    async def wildcard_match(self, ctx: commands.Context, filters: List[str]) -> bool:
        message = ctx.message
        search = re.match(
            pattern=r"^.*(?:{}).*$".format("|".join(filters)),
            string=message.content,
            flags=re.IGNORECASE
        )

        if bool(search) == True:
            embed = disnake.Embed(
                description=f"{moderator} Watch your language, {ctx.author.mention}!",
                color=colors.embed_color,
            )

            await message.delete()
            await ctx.send(embed=embed, delete_after=7)

            await self.bot.log_automod(ctx.author, {
                "type": "wildcard",
                "word": search.group(0),
                "message": message,
                "time": time.time(),
            })
            
    ## -- KEYWORD FILTERS -- ##

    @commands.Cog.listener("on_message")
    async def automod_message(self, message: disnake.Message):
        ctx = commands.Context(
            message=message,
            bot=self.bot,
            view=None
        )

        data_obj = GuildData(ctx.guild)
        data = data_obj.get_data()

        if not data["automod_toggle"]:
            return

        automod_filters = data["automod_filters"]
        exact_result = await self.exact_match(ctx, automod_filters["exact"])

        if exact_result == True:
            return

        await self.wildcard_match(ctx, automod_filters["wildcard"])

    @commands.Cog.listener("on_message_edit")
    async def automod_edit_trigger(self, before: disnake.Message, after: disnake.Message):
        await self.automod_message(after)


def setup(bot):
    bot.add_cog(Automod(bot))
