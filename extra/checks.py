import disnake
import os
import certifi
import json

from disnake.ext import commands
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# FILES
import extra.config as config
import extra.functions as functions

## -- VARIABLES -- ##

mongo_login = os.environ.get("MONGO_LOGIN")
client = MongoClient(f"{mongo_login}",tlsCAFile=certifi.where())
db = client[config.database_collection]

server_data_col = db["server_data"]
warns_col = db["warns"]

## -- EXCEPTIONS -- ##

class SettingsLocked(Exception):
    pass

## -- FUNCTIONS -- ##

def is_moderator(**perms):
    async def predicate(ctx: commands.Context):
        result = server_data_col.find_one({"guild_id": str(ctx.guild.id)})

        if result and result.get("moderators"):
            moderators = json.loads(result.get("moderators"))
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

def server_setting():
    async def predicate(ctx: commands.Context):
        query = {"guild_id": str(ctx.guild.id)}
        result = server_data_col.find_one(query)
        
        if not result:
            server_data_col.insert_one(functions.get_db_data(ctx.guild.id))
            await predicate(ctx)
            return
        
        settings_locked = result.get("settings_locked")
        
        if not settings_locked:
            server_data_col.update_one(query, {"settings_locked": "false"})
            return True
        elif settings_locked == "true":
            raise SettingsLocked
    return commands.check(predicate)