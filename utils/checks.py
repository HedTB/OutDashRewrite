import time
import disnake
import os
import certifi
import json

from disnake.ext import commands
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# FILES
from utils import config, functions, colors

from utils.classes import *

## -- VARIABLES -- ##

mongo_login = os.environ.get("MONGO_LOGIN")
client = MongoClient(mongo_login, tlsCAFile=certifi.where())
db = client[config.DATABASE_COLLECTION]

guild_data_col = db["guild_data"]
warns_col = db["warns"]

## -- EXCEPTIONS -- ##

class BoosterOnly(commands.CheckFailure):
    """Raised if the user isn't a booster of the bot server"""
    pass

class UserNotVoted(commands.CheckFailure):
    """Raised when the user haven't voted within the last 24 hours"""
    pass

class SettingsLocked(commands.CheckFailure):
    """Raised if the guild settings are locked"""
    pass

## -- FUNCTIONS -- ##

def is_moderator(**perms):
    async def predicate(ctx: commands.Context):
        data_obj = GuildData(ctx.guild)
        data = data_obj.get_data()
        
        moderators = data.get("moderators")

        if data and moderators:
            moderators = moderators
            
            for moderator in moderators:
                if int(moderators[moderator]["id"]) == ctx.author.id:
                    return True

        if perms:
            original = commands.has_permissions(**perms).predicate
            result = await original(ctx)
            
            if result:
                return True
                
        raise commands.MissingPermissions(perms)
    return commands.check(predicate)

def is_booster():
    async def predicate(ctx: commands.Context):
        if await ctx.bot.is_booster(ctx.author):
            return True
        
        raise BoosterOnly()
    return commands.check(predicate)

def is_voter():
    async def predicate(ctx: commands.Context):
        with open("data/votes.json", "r") as file:
            data = json.load(file)
            user_vote = data.get(ctx.author.id)
            
            if user_vote and user_vote["expires_at"] - time.time() > 0:
                return True
            
        raise UserNotVoted()
    return commands.check(predicate)

def server_setting():
    async def predicate(ctx: commands.Context):
        data_obj = GuildData(ctx.guild)
        data = data_obj.get_data()
        
        if data.get("settings_locked") == True:
            raise SettingsLocked
        else:
            return True
        
    return commands.check(predicate)