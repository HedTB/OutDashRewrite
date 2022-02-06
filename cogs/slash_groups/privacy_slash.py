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
user_data_col = db["user_data"]

message_settings_types = commands.option_enum({"message content": "message_content"})
message_settings_description = {
    "message_content": "message content"
}

## -- FUNCTIONS -- ##



## -- COG -- ##

class PrivacySlash(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.slash_command(name="privacy")
    async def slash_privacy(self, inter):
        pass

    @slash_privacy.sub_command(name="messages", description="Edit you message privacy settings.")
    async def slash_privacymessages(self, inter: disnake.ApplicationCommandInteraction, type: message_settings_types, toggle: bool):
        """Edit your message privacy settings.
        Parameters
        ----------
        type: The message privacy setting you want to edit.
        toggle: Whether the privacy setting should be on or not.
        """
        
        result = user_data_col.find_one({"user_id": str(inter.user.id)})
        data = functions.get_user_data(inter.user.id)
        
        if not result:
            user_data_col.insert_one(data)
            await self.slash_privacymessages(inter, type, toggle)
            return
        
        embed = disnake.Embed(description=f"{config.yes} The {message_settings_description[type]} privacy setting has been {'enabled' if toggle else 'disabled'}.", color=config.success_embed_color)
        update = {"$set": {
            "message_content_privacy": str(toggle).lower()
        }}
        
        user_data_col.update_one({"user_id": str(inter.user.id)}, update)
        await inter.send(embed=embed)
        
    
def setup(bot):
    bot.add_cog(PrivacySlash(bot))