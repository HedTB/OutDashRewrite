## -- IMPORTING -- ##

# MODULES
import asyncio
import functools
import disnake
import os
import certifi
import random
import logging

from disnake.ext import commands
from pymongo import MongoClient
from dotenv import load_dotenv
from disrank.generator import Generator

# FILES
from utils import config
from utils import functions
from utils.checks import *
from utils.classes import *

## -- VARIABLES -- ##

load_dotenv()

mongo_login = os.environ.get("MONGO_LOGIN")

logger = logging.getLogger("OutDash")

client = MongoClient(mongo_login, tlsCAFile=certifi.where())
db = client[config.database_collection]

user_data_col = db["user_data"]

## -- FUNCTIONS -- ##

def xp_to_levelup(lvl, xp=0):
    return 5 * (lvl ** 2) + (50 * lvl) + 100 - xp

def total_xp_for_level(lvl, current_total_xp):
    total_xp = 0
    
    for level in range(0, lvl):
        total_xp += xp_to_levelup(level, 0)
        
    return total_xp - current_total_xp
            
def add_xp(member: disnake.Member, amount: int):
    member_data_obj = MemberData(member)
    member_data = member_data_obj.get_guild_data()
    
    level = member_data["level"]
    total_xp = member_data["total_xp"]
    xp = member_data["xp"]
    
    update = {}
    xp_for_levelup = xp_to_levelup(level, xp)
    
    update["total_xp"] = total_xp + amount
    
    if xp_for_levelup <= 0:
        update["level"] = level + 1
        update["xp"] = 0
        
        logger.debug(f"{member} is now level {level + 1}!")
    else:
        update["xp"] = xp + amount
        logger.debug(f"{member} has been given {amount} XP, they now have a total of {total_xp + amount} XP!")
        
    member_data_obj.update_guild_data(update)
    
    if xp_for_levelup <= 0:
        return "level_up", level + 1
    else:
        return "xp_add", None

    
def generate_card(args):
    return Generator().generate_profile(**args)

## -- COG -- ##

class Leveling(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot


    """
    ! TEXT COMMANDS
    
    The text/prefix commands.
    """
    
    @commands.command()
    @commands.cooldown(1, config.cooldown_time, commands.BucketType.member)
    async def rank(self, ctx: commands.Context, member: disnake.Member = None):
        if not member:
            member = ctx.author
            
        member_data_obj = MemberData(member)
        member_data = member_data_obj.get_guild_data()
        
        level = member_data.get("level")
        xp = member_data.get("xp")
            
        func = functools.partial(generate_card, {
            "bg_image": "https://dummyimage.com/900x200/121212/121212.jpg",
            "profile_image": member.avatar.url,
            "level": level,
            
            "current_xp": 0,
            "user_xp": xp,
            "next_xp": xp_to_levelup(level + 1),
            
            "user_position": 1,
            "user_name": str(member),
            "user_status": member.status.name
        })
        image = await asyncio.get_event_loop().run_in_executor(None, func)
        
        file = disnake.File(fp=image, filename="card.png")
        await ctx.send(file=file)
        
    """
    ! SLASH commands
    
    The slash commands.
    """
    
    @commands.slash_command()
    @commands.cooldown(1, config.cooldown_time, commands.BucketType.member)
    async def rank(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member = None):
        if not member:
            member = inter.author
            
        member_data_obj = MemberData(member)
        member_data = member_data_obj.get_guild_data()
        
        level = member_data.get("level")
        xp = member_data.get("xp")
            
        func = functools.partial(generate_card, {
            "bg_image": "https://dummyimage.com/900x200/121212/121212.jpg",
            "profile_image": member.avatar.url,
            "level": level,
            
            "current_xp": 0,
            "user_xp": xp,
            "next_xp": xp_to_levelup(level + 1),
            
            "user_position": 1,
            "user_name": str(member),
            "user_status": member.status.name
        })
        image = await asyncio.get_event_loop().run_in_executor(None, func)
        
        file = disnake.File(fp=image, filename="card.png")
        await inter.send(file=file)
        

def setup(bot):
    bot.add_cog(Leveling(bot))