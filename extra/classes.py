## -- IMPORTS -- ##

import disnake
import os
import certifi
import requests

from dotenv import load_dotenv
from pymongo import MongoClient

from extra.webhooks import *
from extra import functions

## -- VARIABLES -- ##

load_dotenv()

mongo_login = os.environ.get("MONGO_LOGIN")

client = MongoClient(f"{mongo_login}",tlsCAFile=certifi.where())
db = client["db2"]
server_data_col = db["server_data"]

## -- CLASSES -- ##

class LoggingWebhook():
    def __init__(self, avatar: disnake.Asset, guild_id: int, log_type: str):
        query = {"guild_id": str(guild_id)}
        update = {"$set": {f"{log_type}_logs_webhook": "None"}}
        server_data = server_data_col.find_one(query)
        
        if not server_data:
            server_data_col.insert_one(functions.get_db_data(guild_id))
            server_data = server_data_col.find_one(query)
            
        url = server_data.get(f"{log_type}_logs_webhook")
        if url == "None" or not url:
            if not url:
                server_data_col.update_one(query, update)
                self.__init__(avatar, guild_id, log_type)
                
                return
            else:  
                raise Exception("There's no webhook for this log type.")
        
        self.guild_id = guild_id
        self.log_type = log_type
        self.webhook = Webhook(url, avatar_url=str(avatar))
        
    def add_embed(self, embed: disnake.Embed):
        self.webhook.add_embed(embed)
        
    def post(self) -> requests.Response | None:
        query = {"guild_id": str(self.guild_id)}
        update = {"$set": {f"{self.log_type}_logs_webhook": "None"}}

        try:
            return self.webhook.post()
        except InvalidWebhook:
            server_data_col.update_one(query, update)