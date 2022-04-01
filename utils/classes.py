## -- IMPORTS -- ##

import datetime
import json
import re
import disnake
import os
import certifi
import requests

from dotenv import load_dotenv
from pymongo import MongoClient
from uuid import uuid4

from utils.webhooks import *
from utils.database_types import *
from utils import functions
from utils import config

## -- VARIABLES -- ##

load_dotenv()

_client = MongoClient(os.environ.get("MONGO_LOGIN"), tlsCAFile=certifi.where())
_db = _client["db2"]

_guild_data_col = _db["guild_data"]
_user_data_col = _db["user_data"]
_access_codes_col = _db["access_codes"]
_api_data_col = _db["api_data"]
_warns_col = _db["warns"]

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

# API VARIABLES
BASE_DISCORD_URL = "https://discordapp.com/api/v9{}"
DATA_REFRESH_DELAY = 180

request_headers = {
    "Authorization": "Bot {}".format(os.environ.get("BOT_TOKEN" if config.is_server else "TEST_BOT_TOKEN")),
    "User-Agent": "OutDash (https://outdash.ga, v0.1)",
    "Content-Type": "application/json",
}

## -- FUNCTIONS -- ##

## -- CLASSES -- ##

# EXCEPTIONS
class InvalidLogType(Exception):
    """Raised if the passed log type is an invalid log type."""
    pass

# UTIL CLASSES
class LoggingWebhook():
    def __init__(self, avatar: disnake.Asset, guild: disnake.Guild, log_type: str):
        data_obj = GuildData(guild)
        guild_data = data_obj.get_data()
        
        if not log_type in _log_types:
            raise InvalidLogType
            
        webhook = guild_data["webhooks"][log_type]
        url = webhook["url"]
        toggle = webhook["toggle"]
        
        if not toggle or not url:
            if toggle and not url:
                data_obj.update_log_webhook(log_type, { "toggle": False, "url": None })
                
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
            _guild_data_col.update_one(query, update)
            
# DATABASE CLASSES
class DatabaseObjectBase:
    def get_data(self, can_insert=True, reconcicle=True):
        data = self._database_collection.find_one(self._query)
        
        if not data and can_insert:
            self.insert_data()
            return self.get_data(can_insert, reconcicle)
        
        if reconcicle:
            unavailable_keys = []
            invalid_keys = []
            
            reconcicle_data = {}
            invalid_data = {}
            
            for key in data.keys():
                try:
                    int(key)
                    continue
                except ValueError:
                    pass
                
                if not key in self._insert_data.keys() and not key.startswith("_"):
                    invalid_keys.append(key)
            
            for key in self._insert_data.keys():
                try:
                    data[key]
                except:
                    unavailable_keys.append(key)
                    
            for key in unavailable_keys:
                reconcicle_data[key] = self._insert_data[key]
            for key in invalid_keys:
                invalid_data[key] = ""
            
            if len(reconcicle_data) > 0:
                print(1, reconcicle_data)
                self.update_data(reconcicle_data)
            if len(invalid_data) > 0:
                print(2, invalid_data)
                self.unset_data(invalid_data)
                
            if len(reconcicle_data) > 0 or len(invalid_data) > 0:
                return self.get_data(can_insert, reconcicle)
        
        for key in data:
            value = data[key]

            if not type(value) == str:
                continue
                
            elif value.startswith("{") and value.endswith("}") or value.startswith("[") and value.endswith("]"):
                try:
                    data[key] = json.loads(value)
                except:
                    continue
                
        return data
    
    def insert_data(self):
        insert_data = self._insert_data
        
        for key in insert_data:
            value = insert_data[key]
                
            if isinstance(value, (dict, list)):
                try:
                    insert_data[key] = json.dumps(value)
                except:
                    continue
        
        self._database_collection.insert_one(insert_data)
        
    def update_data(self, data: dict):
        for key in data:
            value = data[key]
                
            if isinstance(value, (dict, list)):
                try:
                    data[key] = json.dumps(value)
                except:
                    continue
                
        self._database_collection.update_one(self._query, { "$set": data })
        
    def unset_data(self, data: dict):
        self._database_collection.update_one(self._query, { "$unset": data })
        
class GuildData(DatabaseObjectBase):
    def __init__(self, guild: disnake.Guild):
        self.guild = guild
        
        self._query = { "guild_id": guild.id }
        self._insert_data = guild_data(guild.id)
        self._database_collection = _guild_data_col
        
        self.get_data()
        
    def get_log_webhooks(self):
        data = self.get_data()
        return data["webhooks"]
        
    def get_log_webhook(self, log_type: str):
        if not log_type in log_types:
            raise InvalidLogType
        
        webhooks = self.get_log_webhooks()
        return webhooks[log_type]
    
    def update_log_webhooks(self, data: dict):
        webhooks = self.get_log_webhooks()
        
        for log_type in data:
            if not log_type in log_types:
                continue
            
            value = data[log_type]
            webhooks[log_type] = value
            
        self.update_data({ "webhooks": webhooks})
    
    def update_log_webhook(self, log_type: str, data: dict):
        if not log_type in log_types:
            raise InvalidLogType
        
        self.update_log_webhooks({ log_type: data })
        

class WarnsData(DatabaseObjectBase):
    def __init__(self, guild: disnake.Guild):
        self.guild = guild
        
        self._insert_data = warns_data(guild.id)
        self._query = { "guild_id": guild.id }
        self._database_collection = _warns_col
        
    def update_warnings(self, member: disnake.Member, data: dict):
        self.update_data({ str(member.id): data })
        
    def get_member_warnings(self, member: disnake.Member):
        data = self.get_data()
        member_warnings = data.get(str(member.id))
        
        if member_warnings == None:
            self.update_warnings(member, {})
            return self.get_member_warnings(member)
            
        return member_warnings
        
    def add_warning(self, member: disnake.Member, moderator: disnake.Member, reason: str):
        warning_id = str(uuid4())
        member_warnings = self.get_member_warnings(member)
        
        member_warnings.update({ warning_id: {
            "reason": reason,
            "moderator": moderator.id,
            "time": str(datetime.datetime.utcnow()),
            "id": warning_id
        }})
        self.update_warnings(member, member_warnings)
        
    def remove_warning(self, member: disnake.Member, warning_id: str):
        member_warnings = self.get_member_warnings(member)
        
        if not member_warnings.get(warning_id):
            return False
        else:
            member_warnings.pop(warning_id)
            
        self.update_warnings(member, member_warnings)
        

class UserData(DatabaseObjectBase):
    def __init__(self, user: disnake.User):
        self.user = user
        
        self._query = { "user_id": user.id }
        self._insert_data = user_data(user.id)
        self._database_collection = _user_data_col
        
        self.get_data()
        
class MemberData(DatabaseObjectBase):
    def __init__(self, member: disnake.Member):
        self.user = member
        self.guild = member.guild
        
        self._query = { "user_id": member.id }
        self._insert_data = user_data(member.id)
        self._database_collection = _user_data_col
        
    def get_guild_data(self, can_update: bool = True, reconcicle: bool = True) -> dict:
        data = self.get_data(can_update, reconcicle)
        
        if not data.get(str(self.guild.id)) and can_update:
            insert_data = member_data(self.user.id, self.guild.id)
            
            self.update_data({ str(self.guild.id): insert_data.get(str(self.guild.id)) })
            return self.get_guild_data(can_update, reconcicle)

        return data.get(str(self.guild.id))
    
    def update_guild_data(self, data: dict):
        guild_data = self.get_guild_data()
        
        guild_data.update(data)
        self.update_data({ str(self.guild.id): json.dumps(guild_data) })
     


# API   
class BotObject(DatabaseObjectBase):
    def __init__(self) -> None:
        self._query = { "bot_document": True }
        self._database_collection = _api_data_col
        self._insert_data = bot_api_data()
        
    def get_guilds(self) -> dict:
        data = self.get_data()
        
        last_refresh = data.get("last_refresh")
        guilds_cache = data.get("guilds")
        
        if not (guilds_cache or last_refresh) or len(guilds_cache) == 0 or time.time() - last_refresh > DATA_REFRESH_DELAY:
            guilds = self.request("/users/@me/guilds")
            guilds_dict = guilds.json()
            
            if guilds.status_code == 200:
                data["last_refresh"] = time.time()
                data["guilds"] = guilds_dict
                
                for guild in guilds_dict:
                    guild.pop("features")
                    
            return guilds_dict
        else:
            return guilds_cache
        
    def request(self, endpoint, params=None) -> requests.Response:
        return requests.get(
            url = BASE_DISCORD_URL.format(endpoint),
            headers = request_headers,
            params = params
        )
        
    def get_token_from_code(self, access_code: str):
        access_codes = list(_access_codes_col.find({}))
        
        for authorization in access_codes:
            for key in authorization:
                value = authorization[key]

                if value.startswith("{") and value.endswith("}") or value.startswith("[") and value.endswith("]"):
                    try:
                        authorization[key] = json.loads(value)
                    except:
                        continue
                    
            auth_access_code = authorization["access_code"]
            if auth_access_code == access_code:
                return authorization["access_token"]
            
        return None
        
    def get_guild(self, guild_id) -> dict | None:
        guilds = self.get_guilds()
        
        for guild in guilds:
            if guild.get("id") == guild_id:
                return guild

        return None
        
        
class UserObject(DatabaseObjectBase):
    def __init__(self, access_code: str) -> None:
        self._access_code = access_code
        
        self._query = { "access_code": self._access_code }
        self._database_collection = _access_codes_col
        
        result = _access_codes_col.find_one(self._query)
        if not result:
            raise InvalidAccessCode
        
        access_token, refresh_token = result["access_token"], result["refresh_token"]
        user = json.loads(result["user"])
        
        self._insert_data = user_api_data(access_token, refresh_token, self._access_code, user)
        
    def request(self, endpoint, params=None) -> requests.Response:
        access_token = BotObject().get_token_from_code(self._access_code)
        
        return requests.get(
            url = BASE_DISCORD_URL.format(endpoint),
            headers = {
                "Authorization": "Bearer " + access_token,
                "Content-Type": "application/json"
            },
            params = params
        )
        
    def get_guilds(self) -> dict:
        data = self.get_data()
        
        guilds_cache = data.get("guilds")
        last_refresh = data.get("last_refresh")
        
        if not guilds_cache or not last_refresh or len(guilds_cache) == 0 or time.time() - last_refresh > DATA_REFRESH_DELAY:
            user_result = self.request("/users/@me/guilds")
            user_guilds = user_result.json()
            
            if user_result.status_code == 401:
                raise RequestFailed
            
            for guild in user_guilds:
                guild.pop("features")
            
            data["last_refresh"] = time.time()
            data["guilds"] = user_guilds
            guilds_cache = user_guilds
            
            self.update_data(data)
            
        return guilds_cache
    
    def get_guild(self, guild_id) -> dict | None:
        guilds = self.get_guilds()
        
        for guild in guilds:
            if guild.get("id") == guild_id:
                return guild

        return None
    
    
# EXCEPTIONS
class InvalidAccessCode(Exception):
    """Raised if the passed access code is invalid"""
    pass

class RequestFailed(Exception):
    """Raised if a HTTP request failed"""
    pass