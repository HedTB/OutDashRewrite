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
from pymongo import MongoClient
from randomstuff import AsyncClient
from dotenv import load_dotenv

# FILES
from extra import config
from extra import functions

## -- VARIABLES -- ##

load_dotenv()
mongo_token = os.environ.get("MONGO_LOGIN")

ai_client = AsyncClient(api_key="b61wK9syZ9gZ")
client = MongoClient(f"{mongo_token}", tlsCAFile=certifi.where())

db = client[config.database_collection]
server_data_col = db["server_data"]

## -- COG -- ##

class OnVoiceStateUpdate(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: disnake.Member, before: disnake.VoiceState, after: disnake.VoiceState):
        
        voice_client = member.guild.voice_client
        humans = []

        if voice_client and voice_client.is_connected():
            for member in voice_client.channel.members:
                if not member.bot:
                    humans.append(member)

            if after.channel != None:
                return
            elif len(humans) >= 1:
                return
            elif before.channel != voice_client.channel:
                return

            for i in range(20):
                humans.clear()
                for member in voice_client.channel.members:
                    if not member.bot:
                        humans.append(member)
                if len(humans) >= 1:
                    break
                
                await asyncio.sleep(1)

            if len(humans) == 0:
                await voice_client.disconnect()


def setup(bot):
    bot.add_cog(OnVoiceStateUpdate(bot))