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

# FILES
from utils import config, functions, colors

from utils.checks import *
from utils.emojis import *

## -- VARIABLES -- ##

load_dotenv()

## -- FUNCTIONS -- ##

async def aexec(code, global_variables, **kwargs):
    locs = {}
    
    globs = globals().copy()
    args = ", ".join(list(kwargs.keys()))
    
    exec(f"async def func({args}):\n    " + code.replace("\n", "\n    "), global_variables, locs)
    
    result = await locs["func"](**kwargs)
    
    try:
        globals().clear()
    finally:
        globals().update(**globs)
        
    return result

## -- COG -- ##

class DeveloperCommands(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot


    ## -- COMMANDS -- ##
    
    @commands.command(hidden=True)
    async def exec(self, ctx: commands.Context, *, code: str):
        if ctx.author.id not in config.OWNERS:
            return

        code_to_run = code[code.find("```py") + len("```py"): code.rfind("```")]
        
        if not code_to_run:
            embed = disnake.Embed(description=f"{no} There's no code I can run!", color=colors.error_embed_color)
            
            await ctx.send(embed=embed)
            return
        
        await aexec(code_to_run, {
            "ctx": ctx,
            "bot": self.bot,
        })
        
    @commands.command(hidden=True)
    async def generatecaptcha(self, ctx: commands.Context):
        if ctx.author.id not in config.OWNERS:
            return

        captcha = functions.generate_captcha()

        await ctx.send(file=disnake.File(f"{captcha}.png"))
        os.remove(f"{captcha}.png")

        def check(message2):
            return message2.author == ctx.message.author and message2.content.upper() == captcha

        try:
            await self.bot.wait_for("message", timeout=15.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(f"{no} the captcha was: `" + captcha + "`")
        else:
            await ctx.send(yes)
            
    @commands.command(hidden=True)
    async def getguilddata(self, ctx: commands.Context, guild_id: int = 836495137651294258):
        if ctx.author.id not in config.OWNERS:
            return

        guild = self.bot.get_guild(guild_id)
        embed = disnake.Embed(title=guild.name, description="")

        embed.set_thumbnail(guild.icon or config.DEFAULT_AVATAR_URL)
        embed.add_field("Member Count", len(guild.members))

        await ctx.send(embed=embed)
        
    @commands.command(hidden=True)
    async def getbotguilds(self, ctx: commands.Context):
        if ctx.author.id not in config.OWNERS:
            return

        guilds = self.bot.guilds
        message = ""
        
        for guild in guilds:
            message += f"**{guild.name}**\n`{guild.id}`\n\n"

        await ctx.send(message)
    
    ## -- COMMAND HANDLERS -- ##

    @exec.error
    async def exec_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingRequiredArgument):
            return
        
    
def setup(bot):
    bot.add_cog(DeveloperCommands(bot))