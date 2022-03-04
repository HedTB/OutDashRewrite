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
import extra.config as config
import extra.functions as functions

## -- VARIABLES -- ##

load_dotenv()

## -- FUNCTIONS -- ##

async def aexec(code, globals2, **kwargs):
    locs = {}
    
    globs = globals().copy()
    args = ", ".join(list(kwargs.keys()))
    exec(f"async def func({args}):\n    " + code.replace("\n", "\n    "), globals2, locs)
    
    result = await locs["func"](**kwargs)
    try:
        globals().clear()
    finally:
        globals().update(**globs)
    return result

## -- COG -- ##

class Exec(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(hidden=True)
    async def exec(self, ctx: commands.Context, *, code: str):
        if ctx.author.id not in config.owners:
            return

        code_to_run = code[code.find("```py") + len("```py"): code.rfind("```")]
        
        if not code_to_run:
            embed = disnake.Embed(description=f"{config.no} There's no code I can run!", color=config.error_embed_color)
            
            await ctx.send(embed=embed)
            return
        
        await aexec(code_to_run, {
            "ctx": ctx,
            "bot": self.bot,
        })


    @exec.error
    async def exec_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            return
        
    
def setup(bot):
    bot.add_cog(Exec(bot))
