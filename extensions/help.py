## -- IMPORTING -- ##

# MODULES
import disnake
import os
import certifi

from disnake.ext import commands
from pymongo import MongoClient
from dotenv import load_dotenv

# FILES
from utils import config
from utils import functions
from utils.checks import *
from utils.classes import *

## -- VARIABLES -- ##

load_dotenv()

## -- COG -- ##

class Help(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    ## -- TEXT COMMANDS -- ##
    
    
    
    ## -- SLASH COMMANDS -- ##
    
    @commands.slash_command(name="help", description="Lost? Use this command!")
    async def slash_help(self, inter: disnake.ApplicationCommandInteraction):
        permissions = os.environ.get("PERMISSIONS")
        
        embed = disnake.Embed(title="Help",
        description=f"The prefix for this bot is `{self.bot.get_bot_prefix(inter.guild.id)}`.\n**[Invite OutDash!](https://discord.com/api/oauth2/authorize?client_id=836494578135072778&permissions={permissions}&scope=bot%20applications.commands)**",
        color=config.embed_color)

        embed.add_field(name="<:modpower:868630492629565500> Moderation", 
                        value="All moderation commands, such as kick or ban.",
                        inline=True)
        embed.add_field(name=":balloon: Fun",
                        value="Fun commands to play around with, such as 8ball.",
                        inline=True)
        embed.add_field(name="<:work:868630493309071381> Miscellaneous",
                        value="Miscellaneous commands such as bot information.",
                        inline=True)
        embed.add_field(name=":notes: Music",
                        value="Commands for listening to music in a voice channel.\n\n_ _",
                        inline=True)

        embed.set_footer(text=f"Requested by {inter.author}", icon_url=inter.author.avatar or config.default_avatar_url)
        embed.timestamp = datetime.datetime.utcnow()

        await inter.send(embed=embed)


def setup(bot):
    bot.add_cog(Help(bot))