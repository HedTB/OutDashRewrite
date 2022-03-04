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
from app import run_api


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
db = client[config.database_collection]

prefixes_col = db["prefixes"]
confirmations_col = db["bot_farm_confirmations"]
server_data_col = db["server_data"]


# IMPORTANT FUNCTIONS
def get_prefix(bot, message: disnake.Message):
    query = {"guild_id": str(message.guild.id)}
    data = functions.get_db_data(message.guild.id)
    
    result = server_data_col.find_one(query)
    
    if not result:
        server_data_col.insert_one(data)
        return commands.when_mentioned_or(config.default_prefix)(bot, message)
    elif not result.get("prefix"):
        server_data_col.update_one(query, {"$set": {"prefix": "?"}})
        return commands.when_mentioned_or(config.default_prefix)(bot, message)
    
    return commands.when_mentioned_or(result["prefix"])(bot, message)

async def load_cogs(bot: commands.Bot):
    for folder in os.listdir("./commands"):
        for file in os.listdir(f"./commands/{folder}"):
            if not file.endswith(".py"): continue

            file = file[:-3]
            try:
                bot.load_extension(f"commands.{folder}.{file}")
            except Exception as e:
                print(e)

    print("Loaded all commands.")


# BOT
class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.launch_time = datetime.datetime.utcnow()
        
    async def on_ready(self):
        self.avatar = await self.user.avatar.read()
        status_channel = self.get_channel(config.messages_channel)
        embed = disnake.Embed(title=f"Singed In As: {bot.user.name} ({bot.user.id})", 
                            description=f"Bot started in `{str(len(bot.guilds))}` servers, with total of `{len(bot.users)}` users, on an average latency of `{round(bot.latency * 1000)} ms`.", 
                            color=config.success_embed_color)
        
        await status_channel.send(embed=embed)

        print(f"Bot started on {'the server' if config.is_server else 'a local computer'}. Stats: {len(bot.guilds)} servers, {len(bot.users)} users.")
        
        stats_data = {
            "commands_run": 0
        }
        with open("stats.json", 'w') as jsonfile:
            json.dump(stats_data, jsonfile, indent=4)
            
    async def load_cogs(self, specific_cog: str = None):
        if not specific_cog:
            for folder in os.listdir("./commands"):
                for file in os.listdir(f"./commands/{folder}"):
                    if not file.endswith(".py"): return

                    file = file[:-3]
                    try:
                        self.load_extension(f"commands.{folder}.{file}")
                    except Exception as e:
                        print(e)
                        
            print("Loaded all commands.")
                    
        else:
            for folder in os.listdir("./commands"):
                for file in os.listdir(f"./commands/{folder}"):
                    if not file.endswith(".py") or file[:-3] != specific_cog: return

                    file = file[:-3]
                    try:
                        self.load_extension(f"commands.{folder}.{file}")
                    except Exception as e:
                        print(e)
                    
    async def unload_cogs(self, specific_cog: str = None):
        if not specific_cog:
            for folder in os.listdir("./commands"):
                for file in os.listdir(f"./commands/{folder}"):
                    if not file.endswith(".py"): return

                    file = file[:-3]
                    try:
                        self.unload_extension(f"commands.{folder}.{file}")
                    except Exception as e:
                        print(e)
                    
        else:
            for folder in os.listdir("./commands"):
                for file in os.listdir(f"./commands/{folder}"):
                    if not file.endswith(".py") or file[:-3] != specific_cog: return

                    file = file[:-3]
                    try:
                        self.unload_extension(f"commands.{folder}.{file}")
                    except Exception as e:
                        print(e)
                    
    def get_bot_prefix(self, guild_id: int) -> str:
        query = {"guild_id" : str(guild_id)}
        data = functions.get_db_data(guild_id)
        update = { "$set": { "guild_id" : str(guild_id), "prefix" : "?" } }
        
        result = server_data_col.find_one(filter=query, limit=1)

        if not result or not result["prefix"]:
            if not result:
                server_data_col.insert_one(data)
            elif result and not result["prefix"]:
                server_data_col.update_one(query, update)

        return server_data_col.find_one(query)["prefix"]

    def change_prefix(self, guild_id: int, new_prefix: str) -> str:
        query = {"guild_id" : str(guild_id)}
        data = functions.get_db_data(guild_id)
        update = { "$set": { "guild_id" : str(guild_id), "prefix" : "?" } }
        
        result = server_data_col.find_one(filter=query, limit=1)

        if not result:
            server_data_col.insert_one(data)
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
    #test_guilds=[int(config.bot_server)], 
    sync_permissions=True
)

## -- COGS -- ##

@bot.slash_command(name="cogs", default_permission=False, guild_ids=[config.bot_server])
@commands.guild_permissions(guild_id=int(config.bot_server), roles={871899070283800636: True})
async def cogs(inter):
    pass

@cogs.sub_command(name="load", description="Load a specific cog.")
async def loadcog(inter, cog: str):
    try:
        await inter.response.defer()
    except Exception:
        pass
        
    await bot.load_cogs(cog)
    embed = disnake.Embed(description=f"{config.yes} Loaded `{cog}` successfully.", color=config.success_embed_color)
    
    try:
        await inter.send(embed=embed, ephemeral=True)
    except Exception:
        pass

@cogs.sub_command_group(name="reload")
async def reload(inter):
    pass

@reload.sub_command(name="all", description="Reload all commands.")
async def reloadcogs(inter):
    try:
        await inter.response.defer()
    except Exception:
        pass
    
    await bot.unload_cogs()
    await bot.load_cogs()
    embed = disnake.Embed(description=f"{config.yes} Reloaded all cogs successfully.", color=config.success_embed_color)
    
    try:
        await inter.send(embed=embed, ephemeral=True)
    except Exception:
        pass

@reload.sub_command(name="cog", description="Reload one specific cog.")
async def reloadcog(inter, cog: str):
    try:
        await inter.response.defer()
    except Exception:
        pass
    
    await bot.unload_cogs(cog)
    await bot.load_cogs(cog)
    embed = disnake.Embed(description=f"{config.yes} Reloaded `{cog}` successfully.", color=config.success_embed_color)
    
    try:
        await inter.send(embed=embed, ephemeral=True)
    except Exception:
        pass
    
@bot.command()
async def reloadcogs(ctx: commands.Context):
    if ctx.author.id not in config.owners:
        return
    
    await bot.unload_cogs()
    await bot.load_cogs()
    
    embed = disnake.Embed(description=f"{config.yes} Reloaded all cogs successfully.", color=config.success_embed_color)
    await ctx.send(embed=embed)

## -- RUNNING BOT -- ##

if __name__ == "__main__":
    if not config.is_server:
        Thread(target=run_api).start()
    
    bot.loop.create_task(load_cogs(bot))
    bot.run(bot_token if config.is_server else test_bot_token)