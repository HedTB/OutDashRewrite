## -- IMPORTS -- ##

import asyncio
import datetime
import json
import typing
import disnake
import os
import certifi
import requests

from dotenv import load_dotenv
from pymongo import MongoClient, collection
from uuid import uuid4
from threading import Thread

from utils.webhooks import *
from utils.database_types import *

from utils import config, functions, colors

## -- VARIABLES -- ##

load_dotenv()

# TYPES
DataType = typing.Union[str, int, dict, list, bool, None]
Data = typing.Dict[str, DataType]

# CONSTANTS
BASE_DISCORD_URL = "https://discordapp.com/api/v9{}"
DATA_REFRESH_DELAY = 180

LIFETIME = 10

OBJECTS = {
    "guild": {},
    "warns": {},
    "user": {},
    "member": {},
    "youtube": {},
}

# VARIABLES
client = MongoClient(os.environ.get("MONGO_LOGIN"), tlsCAFile=certifi.where())
db = client[config.DATABASE_COLLECTION]

logger = logging.getLogger("Database")
logger.level = logging.DEBUG

guild_data_col = db["guild_data"]
warns_col = db["warns"]
user_data_col = db["user_data"]
youtube_data_col = db["youtube_data"]

access_codes_col = db["access_codes"]
api_data_col = db["api_data"]


request_headers = {
    "Authorization": "Bot {}".format(os.environ.get("BOT_TOKEN" if config.IS_SERVER else "TEST_BOT_TOKEN")),
    "User-Agent": "OutDash (https://outdash.ga, v0.1)",
    "Content-Type": "application/json",
}

## -- FUNCTIONS -- ##


def reconcicle_dict(base: Data, current: Data) -> Data:
    if type(base) != dict or type(current) != dict:
        print(type(base), type(current))
        raise TypeError("Both base and current must be dicts")

    data = {**base, **current}

    for key in data:
        value = data[key]
        base_value = base.get(key)

        try:
            int(key)
            continue
        except:
            pass

        if isinstance(key, str) and key.startswith("_"):
            continue

        if key in base and type(value) != type(base_value):
            data[key] = base_value
        elif base_value is not None and isinstance(value, dict):
            data[key] = reconcicle_dict(base_value, value)

    return data


def clean_dict(base: Data, current: Data) -> typing.Dict[str, str]:
    assert type(current) == dict, "Current must be a dict"

    data = {}

    for key in current:
        value = current[key]
        base_value = base.get(key)

        if not key in base:
            continue
        elif type(value) != type(base_value):
            data[key] = base_value
        elif isinstance(value, dict):
            data[key] = clean_dict(base_value, value)
        elif value == None or value == "None":
            data[key] = None
        else:
            data[key] = value

    return data


def get_dict_difference(dict1: dict, dict2: dict):
    return {key: dict2[key] for key in set(dict2) - set(dict1)}


def get_all_documents(collection_name: str) -> list:
    return db[collection_name].find()


## -- CLASSES -- ##

# EXCEPTIONS


class InvalidLogType(Exception):
    """Raised if the passed log type is an invalid log type."""

    pass


class InvalidAccessCode(Exception):
    """Raised if the passed access code is invalid"""

    pass


class RequestFailed(Exception):
    """Raised if a HTTP request failed"""

    pass


# DATABASE CLASSES


class DatabaseObjectBase:
    query: str | int
    data: Data

    _query: typing.Dict[str, typing.Union[str, int]]
    _insert_data: Data
    _collection: collection.Collection

    _last_use: float

    def fetch_data(self, *, can_insert=True, reconcicle=True) -> None:
        data = self._collection.find_one(self._query)

        if not data and can_insert:
            self.insert_data()
            return self.fetch_data(can_insert=False)
        elif data and reconcicle:
            self.data = clean_dict(self._insert_data, reconcicle_dict(self._insert_data, data))

            if len(get_dict_difference(data, self.data)) > 0:
                self.data = self.update_data(self.data)
        elif data:
            self.data = data

        self._last_use = time.time()
        return self.data

    def get_data(self, *, can_insert=True, reconcicle=True) -> Data:
        if not self.data:
            self.fetch_data(can_insert=can_insert, reconcicle=reconcicle)

        self._last_use = time.time()
        return self.data

    def insert_data(self) -> Data:
        self._collection.insert_one(self._insert_data)
        self._last_use = time.time()

        self.fetch_data(can_insert=False, reconcicle=False)
        return self._insert_data

    def update_data(self, data: dict, key: str | None = None) -> Data:
        if not isinstance(data, dict):
            raise TypeError("Data must be a dict")

        data = data or self.data
        self.data.update({[key]: data} if key else data)

        result = self._collection.replace_one(self._query, self.data, True)
        self._last_use = time.time()

        if result.modified_count == 0:
            logger.critical("No documents were updated, result: {}".format(result.raw_result))
        else:
            logger.debug(
                "Updated {} documents for data object of type {}".format(result.modified_count, self.__class__.__name__)
            )

        self.fetch_data(can_insert=False, reconcicle=False)
        return self.data

    def unset_data(self, data: dict):
        if data.get("_id"):
            data.pop("_id")

        self._collection.update_one(self._query, {"$unset": data})
        self._last_use = time.time()

    def can_destroy(self) -> bool:
        return self._last_use + LIFETIME < time.time()

    def destroy(self) -> None:
        if not self.can_destroy():
            return None

        OBJECTS[self.__class__.__name__].pop(self.query)


class Guild(DatabaseObjectBase):
    def __init__(self, guild: disnake.Guild):
        self.guild = guild
        self.query = guild.id
        self.data = None

        self._query = {"guild_id": guild.id}
        self._insert_data = guild_data(guild.id)
        self._collection = guild_data_col

        self._last_use = time.time()

        self.__class__.__name__ = "guild"
        OBJECTS["guild"][guild.id] = self

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

            webhook = data[log_type]
            webhooks[log_type] = webhook

        self.update_data(webhooks, "webhooks")

    def update_log_webhook(self, log_type: str, data: dict):
        if not log_type in log_types:
            print(log_type + " is not a valid log type")
            raise InvalidLogType

        self.update_log_webhooks({log_type: data})


class Warns(DatabaseObjectBase):
    def __init__(self, guild: disnake.Guild):
        self.guild = guild
        self.query = guild.id
        self.data = None

        self._query = {"guild_id": guild.id}
        self._insert_data = warns_data(guild.id)
        self._collection = warns_col

        self._last_use = time.time()

        self.__class__.__name__ = "warns"
        OBJECTS["warns"][guild.id] = self

    def update_warnings(self, member: disnake.Member, data: dict):
        self.update_data({str(member.id): data})

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

        member_warnings.update(
            {
                warning_id: {
                    "reason": reason,
                    "moderator": moderator.id,
                    "time": str(datetime.datetime.utcnow()),
                    "id": warning_id,
                }
            }
        )
        self.update_warnings(member, member_warnings)

    def remove_warning(self, member: disnake.Member, warning_id: str):
        member_warnings = self.get_member_warnings(member)

        if not member_warnings.get(warning_id):
            return False
        else:
            member_warnings.pop(warning_id)

        self.update_warnings(member, member_warnings)


class User(DatabaseObjectBase):
    def __init__(self, user: disnake.User):
        self.user = user
        self.query = user.id
        self.data = None

        self._query = {"user_id": user.id}
        self._insert_data = user_data(user.id)
        self._collection = user_data_col

        self._last_use = time.time()

        self.__class__.__name__ = "user"
        OBJECTS["user"][user.id] = self


class Member(DatabaseObjectBase):
    def __init__(self, member: disnake.Member):
        self.user = member
        self.guild = member.guild
        self.query = member.id
        self.data = None

        self._query = {"user_id": member.id}
        self._insert_data = member_data(self.user.id, self.guild.id)
        self._collection = user_data_col

        self._last_use = time.time()

        self.__class__.__name__ = "member"
        OBJECTS["member"][member.id] = self

    def get_guild_data(self, can_insert: bool = True, reconcicle: bool = True) -> dict:
        data = self.get_data(can_insert=can_insert, reconcicle=reconcicle)

        guild_id = str(self.guild.id)
        guild_data = data.get(guild_id)

        if not guild_data and can_insert:
            insert_data = member_data(self.user.id, guild_id)

            self.update_data({guild_id: insert_data.get(guild_id)})
            return self.get_guild_data(can_insert, reconcicle)

        if type(guild_data) == dict:
            return guild_data
        else:
            return json.loads(guild_data)

    def update_guild_data(self, data: dict):
        guild_data = self.get_guild_data()

        guild_data.update(data)
        self.update_data({str(str(self.guild.id)): json.dumps(guild_data)})


class YouTube(DatabaseObjectBase):
    def __init__(self, guild_id: int):
        self.query = guild_id
        self.data = None

        self._query = {"guild_id": guild_id}
        self._insert_data = youtube_channels_data(guild_id)
        self._collection = youtube_data_col

        self._last_use = time.time()

        self.__class__.__name__ = "youtube"
        OBJECTS["youtube"][guild_id] = self

    def get_youtube_channels(self, can_insert: bool = True, reconcicle: bool = True) -> list:
        data = self.get_data(can_insert=can_insert, reconcicle=reconcicle)

        return data.get("channels")

    def get_youtube_channel(self, channel_id: str, can_insert: bool = True, reconcicle: bool = True) -> dict:
        channels = self.get_youtube_channels(can_insert, reconcicle)
        channel = next(filter(lambda x: x["channel_id"] == channel_id, channels), None)

        return channel

    def add_youtube_channel(self, channel_id: str):
        channels = self.get_youtube_channels()

        if len(channels) >= config.MAX_CHANNELS:
            print("Maximum amount of channels reached")
            return
        elif self.get_youtube_channel(channel_id):
            print("Channel already exists")
            return

        channel_data = youtube_channel_data(channel_id)
        channels.append(channel_data)

        self.update_data({"channels": channels})

    def remove_youtube_channel(self, channel_id: str):
        channels = self.get_youtube_channels()
        channel = self.get_youtube_channel(channel_id)

        if not channel:
            return

        index = channels.index(channel)
        channels.pop(index)

        self.update_data({"channels": channels})

    def update_youtube_channel(self, channel_id: str, data: dict):
        channels = self.get_youtube_channels()
        channel = self.get_youtube_channel(channel_id)

        if not channel:
            return

        index = channels.index(channel)
        channels[index].update(data)

        self.update_data({"channels": channels})


# API
class BotObject(DatabaseObjectBase):
    def __init__(self) -> None:
        self._query = {"bot_document": True}
        self._collection = api_data_col
        self._insert_data = bot_api_data()

    def get_guilds(self) -> dict:
        data = self.get_data()

        last_refresh = data.get("last_refresh")
        guilds_cache = data.get("guilds")

        if (
            not (guilds_cache or last_refresh)
            or len(guilds_cache) == 0
            or time.time() - last_refresh > DATA_REFRESH_DELAY
        ):
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
            url=BASE_DISCORD_URL.format(endpoint),
            headers=request_headers,
            params=params,
        )

    def get_token_from_code(self, access_code: str):
        access_codes = list(access_codes_col.find({}))

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
        self._bot_object = BotObject()

        self._query = {"access_code": self._access_code}
        self._collection = access_codes_col

        result = access_codes_col.find_one(self._query)
        if not result:
            raise InvalidAccessCode

        access_token, refresh_token = result["access_token"], result["refresh_token"]
        user = json.loads(result["user"])

        self._insert_data = user_api_data(access_token, refresh_token, self._access_code, user)

    def request(self, endpoint, params=None) -> requests.Response:
        access_token = self._bot_object.get_token_from_code(self._access_code)

        return requests.get(
            url=BASE_DISCORD_URL.format(endpoint),
            headers={
                "Authorization": "Bearer " + access_token,
                "Content-Type": "application/json",
            },
            params=params,
        )

    def get_guilds(self) -> dict:
        data = self.get_data()

        guilds_cache = data.get("guilds")
        last_refresh = data.get("last_refresh")

        if (
            not guilds_cache
            or not last_refresh
            or len(guilds_cache) == 0
            or time.time() - last_refresh > DATA_REFRESH_DELAY
        ):
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


# -- COLLECTIONS -- #


def GuildData(guild: disnake.Guild) -> Guild:
    return OBJECTS["guild"].get(guild.id) or Guild(guild)


def WarnsData(guild: disnake.Guild) -> Warns:
    return OBJECTS["warns"].get(guild.id) or Warns(guild)


def UserData(user: disnake.User) -> User:
    return OBJECTS["user"].get(user.id) or User(user)


def MemberData(member: disnake.Member) -> Member:
    return OBJECTS["member"].get(member.id) or Member(member)


def YouTubeData(guild_id: int) -> YouTube:
    return OBJECTS["youtube"].get(guild_id) or YouTube(guild_id)


async def update_loop():
    while True:
        await asyncio.sleep(1)

        if len(OBJECTS) == 0:
            continue

        for objects in OBJECTS.values():
            if len(objects) == 0:
                continue

            destroyed = []

            for id, object in objects.items():
                if object.can_destroy():
                    destroyed.append(id)

            for id in destroyed:
                objects[id].destroy()


def threaded_function():
    loop = asyncio.new_event_loop()

    asyncio.set_event_loop(loop)
    loop.run_until_complete(update_loop())
    loop.close()


Thread(target=threaded_function).start()
