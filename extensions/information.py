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

## -- VARIABLES -- ##

load_dotenv()

mongo_login = os.environ.get("MONGO_LOGIN")

## -- COG -- ##

class Information(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot




def setup(bot):
    bot.add_cog(Information(bot))