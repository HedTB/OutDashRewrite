## -- IMPORTING -- ##

# MODULES
import disnake
import os
import random
import asyncio
import datetime
import certifi

from disnake.ext import commands
from disnake.errors import Forbidden, HTTPException
from disnake.ext.commands import errors
from pymongo import MongoClient
from dotenv import load_dotenv

# FILES
from extra import config
from extra import functions
from extra.checks import *
from extra.webhooks import *

## -- VARIABLES -- ##

load_dotenv()

mongo_login = os.environ.get("MONGO_LOGIN")

client = MongoClient(f"{mongo_login}",tlsCAFile=certifi.where())
db = client["db2"]

server_data_col = db["server_data"]
muted_users_col = db["muted_users"]
privacy_settings_col = db["privacy_settings"]

ignored = (commands.CommandNotFound, commands.MissingPermissions, Forbidden, HTTPException, commands.MissingRequiredArgument, )

## -- COG -- ##

class CommandEvents(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command(self, ctx):
        with open("data/stats.json", "r") as file_object:
            data = json.load(file_object)
        
        number = data.get("commands_run") or 0
        new_data = {"commands_run" : number + 1}

        with open("data/stats.json", 'w') as jsonfile:
            json.dump(new_data, jsonfile, indent=4)

    @commands.Cog.listener()
    async def on_slash_command(self, inter):
        with open("data/stats.json", "r") as file_object:
            data = json.load(file_object)
        
        number = data.get("commands_run") or 0
        new_data = {"commands_run" : number + 1}

        with open("data/stats.json", 'w') as jsonfile:
            json.dump(new_data, jsonfile, indent=4)
            
            
    @commands.Cog.listener()
    async def on_slash_command_error(self, inter: disnake.ApplicationCommandInteraction, error):
        channel = self.bot.get_channel(config.error_channel)
        
        if isinstance(error, ignored):
            return
            
        elif isinstance(error, errors.CommandInvokeError):
            embed = disnake.Embed(title="Slash Command Error", description=f"```py\n{error}\n```\n_ _", color=config.error_embed_color)
            error_embed = disnake.Embed(description=f"{config.no} Oh no! Something went wrong while running the command! Please join our [support server](https://discord.com/invite/4pfUqEufUm) and report the bug.", color=config.error_embed_color)
            
            embed.add_field(name="Occured in:", value=f"{inter.guild.name} ({inter.guild.id})", inline=False)
            embed.add_field(name="Occured by:", value=f"{inter.author.name} ({inter.author.id})", inline=False)
            embed.add_field(name="Command run:", value=f"/{inter.data.name}", inline=False)
            
            logging.error(error)
            await channel.send(embed=embed)
            
            try:
                await inter.response.send_message(embed=error_embed, ephemeral=True)
            except AttributeError:
                await inter.send(embed=error_embed)

    
    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        channel = self.bot.get_channel(config.error_channel)
        
        if isinstance(error, ignored) or str(error).find("Missing Permissions"):
            return
            
        elif isinstance(error, commands.CommandOnCooldown):
            embed = disnake.Embed(description=f"{config.no} You're on a cooldown. Please try again after **{str(round(error.retry_after, 1))} seconds.**", color=config.error_embed_color)
            await ctx.send(embed=embed)
            
        elif isinstance(error, errors.CommandInvokeError):
            embed = disnake.Embed(title="Command Error", description=f"```py\n{error}\n```\n_ _", color=config.error_embed_color)
            error_embed = disnake.Embed(description=f"{config.no} Oh no! Something went wrong while running the command! Please join our [support server](https://discord.com/invite/4pfUqEufUm) and report the bug.", color=config.error_embed_color)
            
            embed.add_field(name="Occured in:", value=f"{ctx.guild.name} ({ctx.guild.id})", inline=False)
            embed.add_field(name="Occured by:", value=f"{ctx.author.name} ({ctx.author.id})", inline=False)
            embed.add_field(name="Command run:", value=f"{ctx.message.content}", inline=False)
            
            logging.error(error)

            await channel.send(embed=embed)
            await ctx.send(embed=error_embed)
    
    
def setup(bot):
    bot.add_cog(CommandEvents(bot))