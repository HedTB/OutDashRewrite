## -- IMPORTING -- ##

# MODULES
import disnake
import os
import certifi

from disnake.ext import commands
from pymongo import MongoClient
from dotenv import load_dotenv

# FILES
from utils import config, functions, colors
from utils.checks import *
from utils.classes import *
from utils.emojis import *

## -- VARIABLES -- ##

load_dotenv()

## -- COG -- ##

class Automod(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener("on_message")
    async def automod_exact(self, message: disnake.Message):
        ctx = commands.Context(
            message=message,
            bot=self.bot,
            view=None
        )
        
        data_obj = GuildData(ctx.guild)
        data = data_obj.get_data()
        
        if not data["automod_toggle"]:
            print("[AUTOMOD] Disabled")
            return
        
        automod_filters = data["automod_filters"]["exact"]
        
        for word in message.content.split():
            if word in automod_filters:
                embed = disnake.Embed(
                    description=f"{moderator} Watch your language, {ctx.author.mention}!",
                    color=colors.embed_color,
                )
                
                await message.delete()
                await ctx.send(embed=embed, delete_after=7)
                
                await self.bot.log_automod(ctx.author, {
                    "type": "exact",
                    "word": word,
                    "message": message,
                    "time": time.time(),
                })
                
    @commands.Cog.listener("on_message_edit")
    async def automod_edit_trigger(self, before: disnake.Message, after: disnake.Message):
        await self.automod_exact(after)


def setup(bot):
    bot.add_cog(Automod(bot))