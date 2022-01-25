## -- IMPORTING -- ##

# MODULES
import disnake
import requests
import os
import random
import asyncio
import datetime
import certifi

from disnake.ext import commands
from disnake.errors import Forbidden, HTTPException
from disnake.ext.commands import errors
from pymongo import MongoClient
from randomstuff import AsyncClient
from dotenv import load_dotenv

# FILES
import extra.config as config
import extra.functions as functions

## -- VARIABLES -- ##

load_dotenv()
mongo_token = os.environ.get("MONGO_LOGIN")

client = MongoClient(f"{mongo_token}", tlsCAFile=certifi.where())

db = client["db"]
server_data_col = db["server_data"]

## -- COG -- ##

class OnGuildJoin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: disnake.Guild):
        
        data = await functions.get_db_data(str(guild.id))
        query = {"guild_id": str(guild.id)}
        result = server_data_col.find_one(query)

        if not result:
            server_data_col.insert_one(data)

        embed = disnake.Embed(title="New Server", description=f"OutDash was added to a new server!\n\nWe're now in `{len(self.bot.guilds)}` guilds.", color=config.logs_embed_color)
        embed.add_field(name="Server Name", value=f"`{guild.name}`")
        embed.add_field(name="Server ID", value=f"`{guild.id}`")
        embed.add_field(name="Server Members", value=f"`{len(guild.members)}` total members", inline=False)

        channel = self.bot.get_channel(config.messages_channel)
        await channel.send(embed=embed)


    @commands.command()
    async def test_join(self, ctx):
        await self.on_guild_join(ctx.guild)


def setup(bot):
    bot.add_cog(OnGuildJoin(bot))