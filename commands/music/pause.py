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
from disnake import utils
from pymongo import MongoClient
from dotenv import load_dotenv
from extra import DiscordUtils

# FILES
from extra import config
from extra import functions

## -- VARIABLES -- ##

load_dotenv()

## -- COG -- ##

class Pause(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.music: DiscordUtils.Music = DiscordUtils.Music()
        
    
    @commands.slash_command(name="pause", description="Makes me leave your voice channel.")
    async def slash_pause(self, inter: disnake.ApplicationCommandInteraction):
        """Makes me leave your voice channel."""
        voice_client = utils.get(inter.bot.voice_clients, guild=inter.guild)
        user_voice = inter.author.voice
        
        if not user_voice:
            embed = disnake.Embed(description=f"{config.no} You're not connected to a voice channel!", color=config.error_embed_color)
            await inter.send(embed=embed)
            return
        
        user_vc = user_voice.channel
        embed = disnake.Embed(description=f"{config.yes} Left {user_vc.mention} successfully.", color=config.success_embed_color)
        
        if voice_client and voice_client.is_connected():
            await voice_client.disconnect()
        else:
            embed = disnake.Embed(description=f"{config.no} I'm not connected to a voice channel!", color=config.error_embed_color)
            await inter.send(embed=embed)
            return
            
        await user_vc.connect()
        await inter.send(embed=embed)
        
    
def setup(bot):
    bot.add_cog(Pause(bot))