## -- IMPORTS -- ##

import json
import disnake
import os
import certifi
import requests

from dotenv import load_dotenv
from pymongo import MongoClient

from utils.webhooks import *
from utils import functions
from utils import config

## -- VARIABLES -- ##

load_dotenv()

_client = MongoClient(os.environ.get("MONGO_LOGIN"), tlsCAFile=certifi.where())
_db = _client["db2"]

_server_data_col = _db["server_data"]
_user_data_col = _db["user_data"]

_log_types = [
    # messages
    "message_delete", "message_edit", "message_bulk_delete",
    # members
    "member_join", "member_remove", "member_update", "member_ban", "member_unban", "user_update",
    # channels
    "guild_channel_create", "guild_channel_delete", "guild_channel_update",
    # roles
    "guild_role_create", "guild_role_delete", "guild_role_update",
    # voice channels
    "voice_channel_join", "voice_channel_leave",
    # guild
    "guild_update", "guild_emojis_update", "guild_stickers_update",
]

## -- FUNCTIONS -- ##

def _get_server_data(guild_id: int):
    return {
        "guild_id": str(guild_id),
        "prefix": "?",
        "settings_locked": "false",

        "chat_bot_channel": "None",
        "chat_bot_toggle": "false",

        "message_delete_logs_webhook": "None",
        "message_bulk_delete_logs_webhook": "None",
        "message_edit_logs_webhook": "None",
        "member_join_logs_webhook": "None",
        "member_remove_logs_webhook": "None",
        "user_update_logs_webhook": "None",
        "guild_channel_create_logs_webhook": "None",
        "guild_channel_delete_logs_webhook": "None",
        "guild_channel_update_logs_webhook": "None",

        "captcha_verification": "false",
        "captcha_verification_length": 8,

        "welcome_channel": "None",
        "welcome_toggle": "False",
        "welcome_embed_title": "None",
        "welcome_embed_description": "**Welcome to __{guild_name}__!**",
        "welcome_embed_author_name": "{member_username}",
        "welcome_embed_author_icon": "{member_icon}",
        "welcome_embed_footer_text": "None",
        "welcome_embed_footer_icon": "None",
        "welcome_embed_timestamp": "true",
        "welcome_embed_thumbnail": "{guild_icon}",
        "welcome_embed_color": config.logs_embed_color,
        "welcome_message_content": "{member_mention},",
    }

def _get_user_data(user_id: int):
    return {
        "user_id": str(user_id),
        "timezone": "Europe/Belfast",
        "message_content_privacy": "false",
    }

def _get_member_data(member_id: int, guild_id: int):
    return {
        "user_id": str(member_id),
        "timezone": "Europe/Belfast",
        "message_content_privacy": "false",
        
        str(guild_id): json.dumps({
            "level": 0,
            "xp": 0,
            "total_xp": 0
        })
    }

## -- CLASSES -- ##

# EXCEPTIONS
class InvalidLogType(Exception):
    """Raised if the passed log type is an invalid log type."""
    pass

# UTIL CLASSES
class LoggingWebhook():
    def __init__(self, avatar: disnake.Asset, guild: disnake.Guild, log_type: str):
        guild_data_obj = GuildData(guild)
        guild_data = guild_data_obj.get_data()
        
        if not log_type in _log_types:
            raise InvalidLogType
            
        url = guild_data.get(f"{log_type}_logs_webhook")
        
        if url == "None":
            raise InvalidWebhook
        
        self._guild_id = guild.id
        self._log_type = log_type
        self._webhook = Webhook(url, avatar_url=str(avatar))
        
    def add_embed(self, embed: disnake.Embed):
        self._webhook.add_embed(embed)
        
    def post(self) -> requests.Response | None:
        query = {"guild_id": str(self._guild_id)}
        update = {"$set": {f"{self._log_type}_logs_webhook": "None"}}

        try:
            return self._webhook.post()
        except InvalidWebhook:
            _server_data_col.update_one(query, update)
            
# DATABASE CLASSES
class GuildData():
    def __init__(self, guild: disnake.Guild):
        self.guild = guild
        
        self._query = { "guild_id": str(guild.id) }
        
    def get_data(self, can_insert: bool = True, reconcicle: bool = True) -> dict:
        result = _server_data_col.find_one(self._query)
        
        if not result and can_insert:
            _server_data_col.insert_one(_get_server_data(self.guild.id))
            return self.get_data(can_insert, reconcicle)
        
        if reconcicle:
            unavailable_keys = []
            insert_data = _get_server_data(self.guild.id)
            update_data = {}
            
            for key in insert_data.keys():
                if not result.get(key):
                    unavailable_keys.append(key)
                    
            for key in unavailable_keys:
                update_data[key] = insert_data[key]
                
            if len(update_data) > 0:
                self.update_data(update_data)
                return self.get_data(can_insert, reconcicle)
            
        return result
                
    def update_data(self, data: dict):
        _server_data_col.update_one(self._query, { "$set": data })

class UserData():
    def __init__(self, user: disnake.User):
        self.user = user
        
        self._query = { "user_id": str(user.id) }
        
    def get_data(self, can_insert: bool = True, reconcicle: bool = True) -> dict:
        result = _user_data_col.find_one(self._query)
        
        if not result and can_insert:
            _user_data_col.insert_one(_get_user_data(self.user.id))
            return self.get_data(can_insert, reconcicle)
        
        if reconcicle:
            unavailable_keys = []
            insert_data = _get_user_data(self.user.id)
            update_data = {}
            
            for key in insert_data.keys():
                if not result[key]:
                    unavailable_keys.append(key)
                    
            for key in unavailable_keys:
                update_data[key] = insert_data[key]
                
            if len(update_data) > 0:
                self.update_data(update_data)
                return self.get_data(can_insert, reconcicle)
            
        return result
                
    def update_data(self, data: dict):
        _user_data_col.update_one(self._query, { "$set": data })
        
class MemberData(UserData):
    def __init__(self, member: disnake.Member):
        self.user = member
        self.guild = member.guild
        
        self._query = { "user_id": str(member.id) }
        
    def get_guild_data(self, can_update: bool = True, reconcicle: bool = True) -> dict:
        result = self.get_data(can_update, reconcicle)
        
        if not result.get(str(self.guild.id)) and can_update:
            insert_data = _get_member_data(self.user.id, self.guild.id)
            
            self.update_data({ str(self.guild.id): insert_data.get(str(self.guild.id)) })
            return self.get_guild_data(can_update, reconcicle)
        
        return json.loads(result.get(str(self.guild.id)))
    
    def update_guild_data(self, data: dict):
        guild_data = self.get_guild_data()
        
        guild_data.update(data)
        self.update_data({ str(self.guild.id): json.dumps(guild_data) })