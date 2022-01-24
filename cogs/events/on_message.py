## -- IMPORTING -- ##

# MODULES
import disnake
import requests
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
from randomstuff import AsyncClient
from dotenv import load_dotenv
from googleapiclient import discovery

# FILES
import config
import modules

## -- VARIABLES -- ##

load_dotenv()
mongo_token = os.environ.get("MONGO_LOGIN")
google_api_key = os.environ.get("GOOGLE_API_KEY")

ai_client = AsyncClient(api_key="b61wK9syZ9gZ")
perspective_client = discovery.build(
    "commentanalyzer",
    "v1alpha1",
    developerKey=google_api_key,
    discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
    static_discovery=False,
)
client = MongoClient(f"{mongo_token}", tlsCAFile=certifi.where())

db = client["db2"]
server_data_col = db["server_data"]

## -- FUNCTIONS -- ##

def get_response_score(response, attribute: str):
    attribute = attribute.upper()
    attribute_scores = response["attributeScores"]

    if attribute_scores[attribute]:
        return round(attribute_scores[attribute]["summaryScore"]["value"], 3)
    else:
        return None


## -- COG -- ##

class OnMessage(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.author == self.bot.user or message.author.bot:
            return
            
        analyze_request = {
            "comment": { "text": message.content if len(message.content) >= 1 else "e"},
            "requestedAttributes": {"TOXICITY": {}, "INSULT": {}, "PROFANITY": {}},
            "languages": ["en"]
        }
        """
        response = perspective_client.comments().analyze(body=analyze_request).execute()

        toxicity = get_response_score(response, "toxicity")
        insult = get_response_score(response, "insult")
        profanity = get_response_score(response, "profanity")

        if (toxicity or insult or profanity) > float(0.95):
            return
            #await message.delete()
        """

        query = {"guild_id": str(message.guild.id)}
        data = await modules.get_db_data(str(message.guild.id))
        result = server_data_col.find_one(query)

        if not result:
            server_data_col.insert_one(data)
            self.on_message(message)

        if (
            message.content.endswith(f"<@{self.bot.user.id}>") and 
            message.content.startswith(f"<@{self.bot.user.id}>") or 
            message.content.endswith(f"<@!{self.bot.user.id}>") and 
            message.content.startswith(f"<@!{self.bot.user.id}>")
        ):
            prefix = result["prefix"]
            embed = disnake.Embed(
                description=
                f"{config.info} The prefix for this server is `{prefix}`.",
                color=config.embed_color)
            await message.channel.send(embed=embed)

        chat_bot_channel = result.get("chat_bot_channel")
        if chat_bot_channel and chat_bot_channel != "None" and message.content and not message.content.startswith(result["prefix"]):
            channel = self.bot.get_channel(int(chat_bot_channel))
            if not channel:
                return
            if message.channel != channel:
                return

            headers = {
                "authorization": "b61wK9syZ9gZ",
                "x-rapidapi-host": "random-stuff-api.p.rapidapi.com",
                "x-rapidapi-key": "6eaccb2fa7mshb708280fd913d54p145fffjsne7f88976a2ac"
            }

            params = {"msg":message.content,"bot_name":"OutDash","bot_gender":"male","bot_master":"HedTB","bot_age":"9","bot_company":"OutDash","bot_location":"Sweden","bot_build":"Beta","bot_birth_year":"2021","bot_birth_place":"Sweden","bot_favorite_color":"Blue","bot_favorite_band":"Imagine Dragons","bot_favorite_artist":"Eminem","id":str(message.author.id)}

            response = requests.get(headers=headers, url = "https://random-stuff-api.p.rapidapi.com/ai"
, params=params)

            try:
                await message.reply(response.json().get("AIResponse"))
            except HTTPException:
                pass



def setup(bot):
    bot.add_cog(OnMessage(bot))