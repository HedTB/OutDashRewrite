## -- IMPORTING -- ##

# MODULES
import disnake
import os
import random
import asyncio
import datetime
import certifi
import string

from disnake.ext import commands
from disnake.errors import Forbidden, HTTPException
from disnake.ext.commands import errors
from pymongo import MongoClient
from dotenv import load_dotenv
from captcha.image import ImageCaptcha

# FILES
import extra.config as config
import extra.functions as functions

## -- VARIABLES -- ##

load_dotenv()

## -- COG -- ##

class GenerateCaptcha(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def generatecaptcha(self, ctx: commands.Context):
        if ctx.author.id not in config.owners:
            return

        captcha = functions.generate_captcha()

        await ctx.send(file=disnake.File(f"{captcha}.png"))
        os.remove(f"{captcha}.png")

        def check(message2):
            return message2.author == ctx.message.author and message2.content.upper() == captcha

        try:
            await self.bot.wait_for("message", timeout=15.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(f"{config.no} the captcha was: `" + captcha + "`")
        else:
            await ctx.send(config.yes)


        
    
def setup(bot):
    bot.add_cog(GenerateCaptcha(bot))