## -- IMPORTING -- ##

# MODULES
import disnake
import os
import random
import asyncio
import datetime
import certifi
import json

from disnake.ext import commands
from disnake.errors import Forbidden, HTTPException
from disnake.ext.commands import errors
from pymongo import MongoClient
from dotenv import load_dotenv

# FILES
import extra.config as config
import extra.functions as functions
from extra.checks import is_moderator

load_dotenv()

## -- VARIABLES -- ##

mongo_login = os.environ.get("MONGO_LOGIN")
client = MongoClient(f"{mongo_login}",tlsCAFile=certifi.where())
db = client["db"]

server_data_col = db["server_data"]
muted_users_col = db["muted_users"]
privacy_settings_col = db["privacy_settings"]

## -- FUNCTIONS -- ##



## -- COG -- ##

class ThreadSlash(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.slash_command(name="thread")
    async def slash_thread(self, inter):
        pass

    @slash_thread.sub_command(name="create", description="Create a new thread in your server.")
    @is_moderator(create_public_threads=True)
    async def slash_threadcreate(self, inter: disnake.ApplicationCommandInteraction, name: str, message: str = "New thread."):
        """Create a new thread in your server.
        Parameters
        ----------
        name: What your new thread should be named.
        message: The starting message of your thread.
        """

        message = await inter.channel.send(message)
        thread = await inter.channel.create_thread(name=name, message=message)
        embed = disnake.Embed(description=f"{config.yes} {thread.mention} has been created.", color=config.success_embed_color)

        await inter.send(embed=embed)


    @slash_thread.sub_command(name="delete", description="Delete a thread.")
    @is_moderator(manage_threads=True)
    async def slash_threaddelete(self, inter: disnake.ApplicationCommandInteraction):
        if type(inter.channel) == disnake.Thread:
            await inter.channel.delete()
            await inter.send("deleted thread")
        else:
            embed = disnake.Embed(description=f"{config.no} This command can only be run in a thread!", color=config.error_embed_color)
            await inter.send(embed=embed)


        
    @slash_threadcreate.error
    async def slash_thread_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `Create Public Threads` permission.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        
    
def setup(bot):
    bot.add_cog(ThreadSlash(bot))