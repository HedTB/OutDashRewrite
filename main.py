## -- IMPORTING -- ##

# MODULES
import discord
import os
import random
import asyncio
import datetime
import certifi
import flask

from discord.ext import commands
from pymongo import MongoClient
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, request
from ipc.discord.ext import ipc


# FILES
import bot_info


## -- VARIABLES / FUNCTIONS -- ##
load_dotenv()

# TOKENS
bot_token = str(os.environ.get("TEST_BOT_TOKEN"))
mongo_token = os.environ.get("MONGO_LOGIN")


# DATABASE VARIABLES
client = MongoClient(f"{mongo_token}", tlsCAFile=certifi.where())
db = client["db2"]

prefixes_col = db["prefixes"]
confirmations_col = db["bot_farm_confirmations"]


# IMPORTANT FUNCTIONS
def get_prefix(bot, message):
    
    query = {"guild_id": str(message.guild.id)}
    data = {"guild_id": str(message.guild.id), f"prefix": "?"}
    result = prefixes_col.find_one(query)
    
    try:
        if result["prefix"] == None:
            prefixes_col.insert_one(data)
        
        return commands.when_mentioned_or(*result["prefix"])(bot, message)
    
    except TypeError:
        prefixes_col.insert_one(data)
        result = prefixes_col.find_one(query)
    
        return commands.when_mentioned_or(*result["prefix"])(bot, message)
    
    
def load_cogs():
    for foldername in os.listdir("./cogs"):
        for filename in os.listdir(f"./cogs/{foldername}"):
            if filename.endswith(".py"):
                # try:
                bot.load_extension(f"cogs.{foldername}.{filename[:-3]}")
                """
                except Exception as e:
                    print(e)
                    return
                """
                
def unload_cogs():
    for foldername in os.listdir("./cogs"):
        for filename in os.listdir(f"./cogs/{foldername}"):
            if filename.endswith(".py"):
                # try:
                bot.unload_extension(f"cogs.{foldername}.{filename[:-3]}")
                """
                except Exception as e:
                    print(e)
                    return
                """


# BOT
app = Flask(__name__)

class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ready = False
        self.ipc = ipc.Server(self, host="localhost", port=5000, secret_key="Yes", do_multicast=False)
        self.loop.create_task(self.start_ipc())
        
    async def on_ready(self):
        self.ready = True
        
        status_channel = bot.get_channel(bot_info.messages_channel)
        embed = discord.Embed(title=f"Singed In As: {bot.user.name} ({bot.user.id})", 
                            description=f"Bot started in `{str(len(bot.guilds))}` server(s), with total of `{len(bot.users)}` member(s), on an average latency of `{round(bot.latency * 1000)} ms`.", 
                            color=bot_info.success_embed_color)
        
        await status_channel.send(embed=embed)

        print(f"Signed In As: {bot.user.name} ({bot.user.id})")
        print(f"Bot started in {len(bot.guilds)} server(s), with {len(bot.users)} total members.")
        

    async def on_ipc_ready(self):
        print("Ipc is ready.")

    async def on_ipc_error(self, endpoint, error):
        print(endpoint, "raised", error)
        
    async def start_ipc(self):
        await self.wait_until_ready()
        await self.ipc.start()
          
      
bot = Bot(command_prefix=get_prefix, intents=discord.Intents.all(), status=discord.Status.idle, activity=discord.Game(name="booting up.."), case_insensitive=True)
#bot.remove_command("help")


# OTHER
activities = ['Minecraft | ?help', f'in {len(bot.guilds)} servers | ?help', 'Roblox | ?help', f'with {len(bot.users)} users | ?help']


# IPC
@bot.ipc.route(name="get_guild_data")
async def get_guild_data(data):
    guild = bot.get_guild(data.guild_id)
    
    if data.type == "check_for_bot_in_server":
        for member in guild.members:
            if member.id == bot.user.id:
                return True
        return False
    elif data.type == "name":
        return guild.name
    elif data.type == "id":
        return guild.id


## -- LOOPS -- ##

async def bot_loop():
    
    await bot.wait_until_ready()
    load_cogs()
    await asyncio.sleep(5)
    
    while not bot.is_closed():
        activity = random.choice(activities)
        
        await bot.change_presence(activity=discord.Game(name=activity), status=discord.Status.online)
        await asyncio.sleep(15)
        
        
## -- COGS -- ##

@bot.command()
async def reloadcogs(ctx):
    
    id = int(ctx.author.id)
    if id in bot_info.owners:
        unload_cogs()
        load_cogs()
        embed = discord.Embed(description="Reloaded all cogs successfully.", color=bot_info.success_embed_color)
        await ctx.send(embed=embed)
        
@bot.command()
async def loadcogs(ctx):
    
    id = int(ctx.author.id)
    if id in bot_info.owners:
        load_cogs()
        embed = discord.Embed(description="Loaded all cogs successfully.", color=bot_info.success_embed_color)
        await ctx.send(embed=embed)
        
@bot.command()
async def unloadcogs(ctx):
    
    id = int(ctx.author.id)
    if id in bot_info.owners:
        unload_cogs()
        embed = discord.Embed(description="Unloaded all cogs successfully.", color=bot_info.success_embed_color)
        await ctx.send(embed=embed)
        

## -- RUNNING BOT -- ##

if __name__ == "__main__":
    bot.loop.create_task(bot_loop())
    bot.run(bot_token)