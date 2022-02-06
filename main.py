## -- IMPORTING -- ##

# MODULE
import multiprocessing
import os
import datetime
import certifi
import disnake
import json
import time
import logging

from disnake.ext import commands
from pymongo import MongoClient
from dotenv import load_dotenv
from threading import Thread


# FILES
from extra import functions
from extra import config
#from app import run_website


## -- VARIABLES / FUNCTIONS -- ##
load_dotenv()

# LOGGERS
logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("disnake")
logger.setLevel(logging.INFO)

handler = logging.FileHandler(filename='disnake.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))

logger.addHandler(handler)

# TOKENS
bot_token = str(os.environ.get("BOT_TOKEN"))
test_bot_token = str(os.environ.get("TEST_BOT_TOKEN"))
mongo_token = os.environ.get("MONGO_LOGIN")
api_key = os.environ.get("API_KEY")


# DATABASE VARIABLES
client = MongoClient(f"{mongo_token}", tlsCAFile=certifi.where())
db = client["db"]

prefixes_col = db["prefixes"]
confirmations_col = db["bot_farm_confirmations"]
server_data_col = db["server_data"]


# IMPORTANT FUNCTIONS
def get_prefix(bot, message: disnake.Message):
    query = {"guild_id": str(message.guild.id)}
    data = functions.get_db_data(message.guild.id)
    
    result = server_data_col.find_one(query)
    result2 = prefixes_col.find_one(query)
    
    if not result:
        server_data_col.insert_one(data)
        return commands.when_mentioned_or("?")(bot, message)
    
    if not result["prefix"]:
        if not result2["prefix"]:
            if result:
                server_data_col.replace_one(query, data)
                return commands.when_mentioned_or("?")(bot, message)
            elif not result:
                server_data_col.insert_one(data)
                return commands.when_mentioned_or("?")(bot, message)
        else:
            if result:
                server_data_col.replace_one(query, data)
                return commands.when_mentioned_or("?")(bot, message)
            elif not result:
                server_data_col.insert_one(data)
                return commands.when_mentioned_or("?")(bot, message)
    
    return commands.when_mentioned_or(result["prefix"])(bot, message)
    
    
async def load_cogs(bot, cog = None):
    if not cog:
        await bot.wait_until_ready()
        start = time.time()
        amount = 0

        for foldername in os.listdir("./cogs"):
            for filename in os.listdir(f"./cogs/{foldername}"):
                if filename.endswith(".py"):
                    try:
                        bot.load_extension(f"cogs.{foldername}.{filename[:-3]}")
                        amount += 1
                    except Exception as e:
                        print(e)
                        continue

        end = time.time()

        print(f"Loaded {amount} cogs, took {round(end - start)} seconds.")
    
    else:
        for foldername in os.listdir("./cogs"):
            for filename in os.listdir(f"./cogs/{foldername}"):
                if filename.endswith(".py") and filename[:3] == cog:
                    try:
                        bot.load_extension(f"cogs.{foldername}.{filename[:-3]}")
                    except Exception as e:
                        print(e)
                        continue
        
        print(f"Loaded {cog} successfully.")
                
async def unload_cogs(bot):
    start = time.time()
    amount = 0

    for foldername in os.listdir("./cogs"):
        for filename in os.listdir(f"./cogs/{foldername}"):
            if filename.endswith(".py"):
                try:
                    bot.unload_extension(f"cogs.{foldername}.{filename[:-3]}")
                    amount += 1
                except Exception as e:
                    print(e)
                    continue

    end = time.time()
    print(f"Unloaded {amount} cogs, took {round(end - start)} seconds.")

async def reload_cogs(bot, cog: str):
    if not cog:
        start = time.time()
        amount = 0
        for foldername in os.listdir("./cogs"):
            for filename in os.listdir(f"./cogs/{foldername}"):
                if filename.endswith(".py"):
                    try:
                        bot.reload_extension(f"cogs.{foldername}.{filename[:-3]}")
                        amount += 1
                    except Exception as e:
                        print(e)
                        continue

        end = time.time()
        print(f"Reloaded {amount} cogs, took {round(end - start)} seconds.")

    else:
        for foldername in os.listdir("./cogs"):
            for filename in os.listdir(f"./cogs/{foldername}"):
                if filename.endswith(".py") and filename[:-3] == cog:
                    try:
                        bot.reload_extension(f"cogs.{foldername}.{filename[:-3]}")
                    except Exception as e:
                        print(e)
                        continue
        
        print(f"Reloaded {cog} successfully.")


# BOT
class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.launch_time = datetime.datetime.utcnow()
        
    async def on_ready(self):
        self.avatar = await self.user.avatar.read()
        status_channel = self.get_channel(config.messages_channel)
        embed = disnake.Embed(title=f"Singed In As: {bot.user.name} ({bot.user.id})", 
                            description=f"Bot started in `{str(len(bot.guilds))}` server(s), with total of `{len(bot.users)}` member(s), on an average latency of `{round(bot.latency * 1000)} ms`.", 
                            color=config.success_embed_color)
        
        await status_channel.send(embed=embed)

        print(f"Signed In As: {bot.user.name} ({bot.user.id})")
        print(f"Bot started in {len(bot.guilds)} server(s), with {len(bot.users)} total members.")
        
        stats_data = {
            "commands_run": 0
        }
        with open("stats.json", 'w') as jsonfile:
            json.dump(stats_data, jsonfile, indent=4)

    def get_bot_prefix(self, guild_id: int) -> str:
        query = {"guild_id" : str(guild_id)}
        data = {
            "guild_id": str(guild_id),
            "prefix": "?"
        }
        update = { "$set": { "guild_id" : str(guild_id), "prefix" : "?" } }
        
        result = server_data_col.find_one(filter=query, limit=1)
        result2 = prefixes_col.find_one(filter=query, limit=1)

        if not result or not result["prefix"]:
            if not result2 or not result2["prefix"]:
                if result:
                    server_data_col.update_one(filter=query, update=update)
                elif not result:
                    server_data_col.insert_one(data)
            else:
                if result:
                    server_data_col.update_one(filter=query, update=update)
                elif not result and result2["prefix"]:
                    new_data = {
                        "guild_id": str(guild_id),
                        "prefix": str(result2["prefix"])
                    }
                    server_data_col.insert_one(new_data)

        return server_data_col.find_one(query)["prefix"]

    def change_prefix(self, guild_id: int, new_prefix: str) -> str:
        query = {"guild_id": str(guild_id)}
        data = {
            "guild_id": str(guild_id),
            "prefix": "?"
        }
        update = { "$set": { "guild_id" : str(guild_id), "prefix" : str(new_prefix) } }

        result = server_data_col.find_one(query)
        result2 = prefixes_col.find_one(query)

        if not result or not result["prefix"]:
            if not result2 or not result2["prefix"]:
                if result:
                    server_data_col.update_one(filter=query, update=update)
                elif not result:
                    server_data_col.insert_one(data)
            else:
                if result:
                    server_data_col.update_one(filter=query, update=update)
                elif not result and result2["prefix"]:
                    new_data = {
                        "guild_id": str(guild_id),
                        "prefix": str(result2["prefix"])
                    }
                    server_data_col.insert_one(new_data)
        else:
            server_data_col.update_one(filter=query, update=update)

        result = self.get_bot_prefix(guild_id)
        if result == new_prefix:
            return result
        else:
            return False
        
       
bot = Bot(
    command_prefix=get_prefix, 
    intents=disnake.Intents.all(),
    status=disnake.Status.idle, 
    activity=disnake.Game(name="booting up.."), 
    case_insensitive=True, 
    test_guilds=[int(config.bot_server)], 
    sync_permissions=True
)

## -- COGS -- ##

@bot.slash_command(name="cogs", default_permission=False)
@commands.guild_permissions(guild_id=int(config.bot_server), roles={871899070283800636: True})
async def cogs(inter):
    pass

@cogs.sub_command(name="load", description="Load a specific cog.")
async def loadcog(inter, cog: str):
    try:
        await inter.response.defer()
    except Exception:
        pass
        
    await load_cogs(bot, cog)
    embed = disnake.Embed(description=f"{config.yes} Loaded `{cog}` successfully.", color=config.success_embed_color)
    
    try:
        await inter.send(embed=embed)
    except Exception:
        pass

@cogs.sub_command_group(name="reload")
async def reload(inter):
    pass

@reload.sub_command(name="all", description="Reload all cogs.")
async def reloadcogs(inter):
    try:
        await inter.response.defer()
    except Exception:
        pass
    
    await reload_cogs(bot, None)
    embed = disnake.Embed(description=f"{config.yes} Reloaded all cogs successfully.", color=config.success_embed_color)
    
    try:
        await inter.send(embed=embed)
    except Exception:
        pass

@reload.sub_command(name="cog", description="Reload one specific cog.")
async def reloadcog(inter, cog: str):
    try:
        await inter.response.defer()
    except Exception:
        pass
    
    await reload_cogs(bot, cog)
    embed = disnake.Embed(description=f"{config.yes} Reloaded `{cog}` successfully.", color=config.success_embed_color)
    
    try:
        await inter.send(embed=embed)
    except Exception:
        pass
    
@bot.command()
async def reloadcogs(ctx: commands.Context):
    if ctx.author.id not in config.owners:
        return
    await reload_cogs(bot, None)
    embed = disnake.Embed(description=f"{config.yes} Reloaded all cogs successfully.", color=config.success_embed_color)
    await ctx.send(embed=embed)

## -- RUNNING BOT -- ##

if __name__ == "__main__":
    #Thread(target=run_website, args=(bot, )).start()
    
    bot.loop.create_task(load_cogs(bot, None))
    bot.run(bot_token)