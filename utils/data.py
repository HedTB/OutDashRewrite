## -- IMPORTS -- ##

import asyncio
import datetime
import json
import logging
import multiprocessing
from multiprocessing.pool import Pool
import os
import time
import typing
import certifi
import dictdiffer
import disnake
import requests

from functools import wraps
from threading import Thread
from uuid import uuid4
from dotenv import load_dotenv
from pymongo import MongoClient, collection

from utils import config, functions
from utils.database_types import (
    guild_data,
    log_types,
    member_data,
    user_data,
    warns_data,
    youtube_channel_data,
    youtube_channels_data,
)
from web.utils.exceptions import InvalidAccessToken, InvalidOauthCode

## -- VARIABLES -- ##

load_dotenv()

# TYPES
DataType = typing.Union[str, int, float, dict, list, bool, None]
Data = typing.Dict[str, DataType]

# CONSTANTS
BASE_DISCORD_URL = "https://discord.com/api/{}{}"
DATA_REFRESH_DELAY = 300

LIFETIME = 300
FETCH_INTERVAL = 15

OBJECTS = {
    "guild": {},
    "warns": {},
    "user": {},
    "api_user": {},
    "member": {},
    "youtube": {},
}

# ENV VARIABLES
bot_token = os.environ.get("BOT_TOKEN" if config.IS_SERVER else "TEST_BOT_TOKEN")
bot_secret = os.environ.get("BOT_SECRET" if config.IS_SERVER else "TEST_BOT_SECRET")

# OBJECTS
client = MongoClient(os.environ.get("MONGO_LOGIN"), tlsCAFile=certifi.where())
db = client[config.DATABASE_COLLECTION]

logger = logging.getLogger("Database")
logger.level = logging.DEBUG if not config.IS_SERVER else logging.INFO

# COLLECTIONS
guild_data_col = db["guild_data"]
warns_col = db["warns"]
user_data_col = db["user_data"]
youtube_data_col = db["youtube_data"]

api_data_col = db["api_data"]

# OTHER
request_headers = {
    "Authorization": "Bot {}".format(os.environ.get("BOT_TOKEN" if config.IS_SERVER else "TEST_BOT_TOKEN")),
    "User-Agent": "OutDash (https://outdash.ga, v0.1)",
    "Content-Type": "application/json",
}

## -- FUNCTIONS -- ##


def reconcicle_dict(base: Data, current: Data) -> Data:
    if type(base) != dict or type(current) != dict:
        raise TypeError("Both base and current must be dicts")

    data = {**base, **current}

    for key in data:
        value = data[key]
        base_value = base.get(key)

        if isinstance(key, str) and key.startswith("_"):
            continue

        if key in base and type(value) != type(base_value) and base_value is not None:
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

        if key not in base:
            continue
        elif type(value) != type(base_value):
            data[key] = base_value
        elif isinstance(value, dict):
            data[key] = clean_dict(base_value, value)
        elif value is None or value == "None":
            data[key] = None
        else:
            data[key] = value

    return data


def get_dict_difference(dict1: dict, dict2: dict):
    return {key: dict2[key] for key in set(dict2) - set(dict1)}


def are_dicts_identical(dict1: dict, dict2: dict):
    if type(dict1) != dict or type(dict2) != dict:
        return False

    return list(dictdiffer.diff(dict1, dict2)) == []


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
    data: Data = None

    _query: typing.Dict[str, typing.Union[str, int]]
    _insert_data: Data
    _collection: collection.Collection

    _last_use: float = 0
    _last_fetch: float = 0

    def __del__(self):
        print(f"destroying {self.__class__.__name__} object")

    def __init__(self, life_time: int = LIFETIME) -> None:
        self.life_time = life_time
        self._last_use = time.time()

    def run_asynchronously(self, pool: multiprocessing.Pool, f: typing.Callable, args: dict = {}):
        return pool.apply_async(f, {"self": self, **args})

    def fetch_data(self, *, can_insert=True, pool: Pool = None) -> Data:
        start = time.time()

        self.data = self._collection.find_one(self._query)  # .limit(1).explain()

        print(f"[data fetch] Fetched, took: {(time.time() - start) * 1000} ms")
        start = time.time()

        if not self.data and can_insert is True:
            return self.insert_data()
        elif self.data and self._insert_data:
            cleaned_data = reconcicle_dict(self._insert_data, self.data)

            if not are_dicts_identical(cleaned_data, self.data):
                logger.debug("Updated database for object of type {} with cleaned data".format(self.__class__.__name__))

                self.data.update(cleaned_data)
                self.update_data(cleaned_data)
            else:
                self.data.pop("_id")

        self._last_use = time.time()
        self._last_fetch = time.time()

        return self.data

    def get_data(self, *, can_insert=True) -> Data:
        self._last_use = time.time()

        if self.data is None or time.time() - self._last_fetch > FETCH_INTERVAL:
            return self.fetch_data(can_insert=can_insert)
        else:
            return self.data

    def insert_data(self, *, force: bool = False, pool: Pool = None) -> Data | None:
        if self.fetch_data(can_insert=False) is not None and force:
            return self.get_data()

        if pool:
            self.run_asynchronously(pool, self.insert_data)
        else:
            self._collection.insert_one(self._insert_data)
            self._last_use = time.time()
            self.data = self._insert_data

            logger.debug(f"Inserted data for data object of type {self.__class__.__name__}")
            return self.data

    def update_data(self, data: Data, *, pool: Pool = None) -> Data | None:
        if not self.data:
            self.insert_data()

        if pool:
            self.run_asynchronously(pool, self.update_data, (data))
        else:
            self.data.update(data)
            self._last_use = time.time()

            result = self._collection.replace_one(self._query, self.data)

            if result.modified_count == 0:
                logger.critical(
                    "No documents were updated for data object of type {}, result: {}".format(
                        self.__class__.__name__, result.raw_result
                    )
                )
            else:
                logger.debug(
                    "Updated {} documents for data object of type {}".format(
                        result.modified_count, self.__class__.__name__
                    )
                )

            return self.data

    def delete_data(self):
        self._collection.delete_one(self._query)
        self._last_use = time.time()

        self.data = None

    def can_destroy(self) -> bool:
        return self._last_use + self.life_time < time.time() and self.query in OBJECTS[self.__class__.__name__]

    def destroy(self) -> None:
        if not self.can_destroy():
            return None

        OBJECTS[self.__class__.__name__].pop(self.query, None)


class Guild(DatabaseObjectBase):
    def __init__(self, guild_id: int, *, cache: bool = True):
        self.guild_id = guild_id
        self.query = guild_id

        self._query = {"guild_id": guild_id}
        self._insert_data = guild_data(guild_id)
        self._collection = guild_data_col

        self._last_use = time.time()

        self.__class__.__name__ = "guild"

        if cache is True:
            OBJECTS["guild"][guild_id] = self

        super().__init__()

    @staticmethod
    def create(guild_id: int, *, cache: bool = True):
        if guild_id in OBJECTS["guild"]:
            return OBJECTS["guild"][guild_id]
        else:
            return Guild(guild_id, cache=cache)

    def get_log_webhooks(self) -> typing.Dict[str, DataType]:
        data = self.get_data()

        return data["webhooks"]

    def get_log_webhook(self, log_type: str):
        if log_type not in log_types:
            raise InvalidLogType

        return self.get_log_webhooks()[log_type]

    def update_log_webhooks(self, data: Data):
        webhooks = self.get_log_webhooks()

        for log_type in data:
            if log_type not in log_types:
                continue

            webhook = data[log_type]
            webhooks[log_type] = webhook

        self.update_data({"webhooks": webhooks})

    def update_log_webhook(self, log_type: str, data: dict):
        if log_type not in log_types:
            raise InvalidLogType(f"{log_type} is not a valid logging type")

        self.update_log_webhooks({log_type: data})


class Warns(DatabaseObjectBase):
    def __init__(self, guild_id: int):
        super().__init__()

        self.guild_id = guild_id
        self.query = guild_id

        self._query = {"guild_id": guild_id}
        self._insert_data = warns_data(guild_id)
        self._collection = warns_col

        self._last_use = time.time()

        self.__class__.__name__ = "warns"
        OBJECTS["warns"][guild_id] = self

    @staticmethod
    def create(guild_id: int):
        if guild_id in OBJECTS["warns"]:
            return OBJECTS["warns"][guild_id]
        else:
            return Warns(guild_id)

    def update_warnings(self, member: disnake.Member, data: dict):
        self.update_data({str(member.id): data})

    def get_member_warnings(self, member: disnake.Member):
        data = self.get_data()
        member_warnings = data.get(str(member.id))

        if member_warnings is None:
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
    def __init__(self, user_id: int, *, life_time: int):
        self.user_id = user_id
        self.query = user_id

        self._query = {"user_id": user_id}
        self._insert_data = user_data(user_id)
        self._collection = user_data_col

        self.__class__.__name__ = "user"
        OBJECTS["user"][user_id] = self

        super().__init__(life_time=life_time)

    @staticmethod
    def create(user_id: int):
        if user_id in OBJECTS["user"]:
            return OBJECTS["user"][user_id]
        else:
            return User(user_id)


class Member(DatabaseObjectBase):
    def __init__(self, member_id: int, guild_id: int):
        self.user_id = member_id
        self.guild_id = guild_id
        self.query = member_id

        self._query = {"user_id": member_id}
        self._insert_data = member_data(self.user_id, self.guild_id)
        self._collection = user_data_col

        self._last_use = time.time()

        self.__class__.__name__ = "member"
        OBJECTS["member"][member_id] = self

        super().__init__()

    @staticmethod
    def create(member_id: int, guild_id: int):
        if member_id in OBJECTS["member"]:
            return OBJECTS["member"][member_id]
        else:
            return Member(member_id, guild_id)

    def get_guild_data(self, can_insert: bool = True) -> Data:
        data = self.get_data(can_insert=can_insert)

        guild_id = str(self.guild_id)
        guild_data = data.get(guild_id)

        if not guild_data and can_insert:
            self.update_data({guild_id: self._insert_data.get(guild_id)})
            return self.get_guild_data(can_insert=False)

        return guild_data

    def update_guild_data(self, data: dict, *, pool: Pool = None):
        guild_data = self.get_guild_data()

        guild_data.update(data)
        self.update_data({str(self.guild_id): guild_data}, pool=pool)


class YouTube(DatabaseObjectBase):
    def __init__(self, guild_id: int):
        self.query = guild_id

        self._query = {"guild_id": guild_id}
        self._insert_data = youtube_channels_data(guild_id)
        self._collection = youtube_data_col

        self._last_use = time.time()

        self.__class__.__name__ = "youtube"
        OBJECTS["youtube"][guild_id] = self

        super().__init__()

    @staticmethod
    def create(guild_id: int):
        if guild_id in OBJECTS["youtube"]:
            return OBJECTS["youtube"][guild_id]
        else:
            return YouTube(guild_id)

    def get_youtube_channels(self, can_insert: bool = True) -> list:
        data = self.get_data(can_insert=can_insert)

        return data.get("channels")

    def get_youtube_channel(self, channel_id: str, can_insert: bool = True) -> dict:
        channels = self.get_youtube_channels(can_insert)
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
class BotObject:
    def get_guild_count(self) -> int:
        return len(list(guild_data_col.find({})))

    def get_guilds(self) -> DataType:
        guilds = []

        for document in guild_data_col.find({}):
            guilds.append({"id": document["guild_id"]})

        return guilds

    def get(self, endpoint, params=None, *, api_version: str = "v10") -> requests.Response:
        return requests.get(
            url=BASE_DISCORD_URL.format(api_version, endpoint),
            headers=request_headers,
            params=params,
        )

    def get_guild(self, guild_id: int) -> dict | None:
        guilds = self.get_guilds()

        for guild in guilds:
            if guild["id"] == guild_id:
                return guild

        return None


bot_object = BotObject()


class ApiUser(DatabaseObjectBase):
    def __init__(
        self,
        user_id: int,
        *,
        oauth_code: str,
        access_token: str | None = None,
        refresh_token: str | None = None,
        expires_at: float,
    ):
        start = time.time()
        super().__init__(life_time=600)

        print(f"[api user] Initialized superclass, took: {(time.time() - start) * 1000} ms")
        start = time.time()

        self.user_id = user_id
        self.query = user_id

        self._query = {"user_id": user_id}
        self._insert_data = user_data(user_id)
        self._collection = user_data_col

        self._oauth_code = oauth_code
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._expires_at = expires_at

        self.__class__.__name__ = "api_user"

        OBJECTS["user"].pop(user_id, None)
        OBJECTS["api_user"][user_id] = self

    @staticmethod
    def create(
        user_id: int | None = None,
        oauth_code: str | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None,
        expires_at: float | None = None,
    ):
        if not user_id and not oauth_code and not access_token:
            raise AttributeError("Either the user ID or at least one token needs to be specified")

        if not user_id and oauth_code and not access_token:
            response = requests.post(
                url=BASE_DISCORD_URL.format("v10", "/oauth2/token"),
                data={
                    "client_id": config.CLIENT_ID,
                    "client_secret": bot_secret,
                    "grant_type": "authorization_code",
                    "code": oauth_code,
                    "redirect_uri": config.REDIRECT_URI,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code == 400:
                print(response.json())
                raise InvalidOauthCode
            elif response.status_code != 200:
                response.raise_for_status()

            data = functions.convert_strings(response.json())
            access_token = data["access_token"]
            refresh_token = data["refresh_token"]
            expires_at = time.time() + data["expires_in"]

        if not user_id and access_token:
            response = requests.get(
                url=BASE_DISCORD_URL.format("v10", "/oauth2/@me"),
                headers={
                    "Authorization": "Bearer " + access_token,
                    "Content-Type": "application/json",
                },
            )

            if response.status_code == 400:
                raise InvalidAccessToken
            elif response.status_code != 200:
                response.raise_for_status()

            data = functions.convert_strings(response.json())
            user_id = data["user"]["id"]

        if user_id in OBJECTS["api_user"]:
            return OBJECTS["api_user"][user_id]
        else:
            return ApiUser(
                user_id,
                oauth_code=oauth_code,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
            )

    @staticmethod
    def requires_access_token(method: typing.Callable):
        @wraps(method)
        def decorator(self, *args, **kwargs):
            if time.time() > self._expires_at:
                return {"message": "Your token has expired, please re-login.", "error": "token_expired"}, 401

            return method(self, *args, **kwargs)

        return decorator

    def request(
        self, method: str, endpoint: str, *, api_version: str = "v10", headers: typing.Dict[str, any] = {}, **kwargs
    ) -> requests.Response:
        return requests.request(
            method=method,
            url=BASE_DISCORD_URL.format(api_version, endpoint),
            headers={"Content-Type": "application/json", **headers},
            **kwargs,
        )

    @requires_access_token
    def token_request(
        self,
        method: str,
        endpoint: str,
        *,
        api_version: str = "v10",
        headers: typing.Dict[str, any] = {},
        **kwargs,
    ) -> requests.Response:
        return requests.request(
            method=method,
            url=BASE_DISCORD_URL.format(api_version, endpoint),
            headers={"Authorization": "Bearer " + self._access_token, "Content-Type": "application/json", **headers},
            **kwargs,
        )

    def exchange_code(self, code: str | None = None):
        if not self._oauth_code and not code:
            raise AttributeError("Missing oauth code")

        logger.debug("Exchanging oauth code")

        response = self.request(
            "post",
            "/oauth2/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "client_id": config.CLIENT_ID,
                "client_secret": bot_secret,
                "grant_type": "authorization_code",
                "code": self._oauth_code,
                "redirect_uri": config.REDIRECT_URI,
            },
        )

        if response.status_code == 400:
            raise InvalidOauthCode
        elif response.status_code != 200:
            response.raise_for_status()

        data = functions.convert_strings(response.json())

        self._access_token = data["access_token"]
        self._refresh_token = data["refresh_token"]
        self._expires_at = time.time() + float(data["expires_in"])

    def refresh_token(self):
        logger.debug("Refreshing token for user")

        response = self.request(
            "post",
            "/oauth2/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "client_id": config.CLIENT_ID,
                "client_secret": bot_secret,
                "grant_type": "refresh_token",
                "refresh_token": self._refresh_token,
            },
        )

        if response.status_code == 400:
            raise InvalidAccessToken
        elif response.status_code != 200:
            return response.raise_for_status()

        data = functions.convert_strings(response.json())

        self._expires_at = time.time() + data["expires_in"]
        self._access_token = data["access_token"]
        self._refresh_token = data["refresh_token"]

        self.update_oauth_data()

    def identify(self):
        logger.debug("Identifying user")
        response = self.token_request("get", "/oauth2/@me")

        if response.status_code == 400:
            raise InvalidAccessToken
        elif response.status_code != 200:
            return response.raise_for_status()

        data = functions.convert_strings(response.json())
        user = data["user"]

        self.user_id = user["id"]
        self.user = user

        return data

    def get_guilds(self, *, fetch: bool = False) -> dict:
        guilds = None

        with open("data/users.json", "r") as file:
            data = json.load(file)
            user = data.get(str(self.user_id), {})

        if user:
            guilds = user.get("guilds", None)
            last_refresh = user.get("last_refresh", 0)

        if guilds is None or len(guilds) == 0 or time.time() - last_refresh > DATA_REFRESH_DELAY or fetch:
            logger.debug("Fetching user guilds")

            response = self.token_request("get", "/users/@me/guilds")
            guilds = response.json()

            if response.status_code == 401:
                raise InvalidAccessToken
            elif response.status_code != 200:
                raise RequestFailed

            for guild in guilds:
                guild.pop("features")

                guild["id"] = int(guild["id"])
                guild["permissions"] = int(guild["permissions"])

            user["last_refresh"] = time.time()
            user["guilds"] = guilds

            data[self.user_id] = user

            with open("data/users.json", "w") as file:
                json.dump(data, file)

        return guilds

    def get_api_guild(self, guild_id: int) -> dict | None:
        guilds = self.get_guilds()

        for guild in guilds:
            if guild["id"] == guild_id:
                return guild

        return None


# -- COLLECTIONS -- #


def GuildData(guild_id: int) -> Guild:
    return Guild.create(guild_id)


def WarnsData(guild_id: int) -> Warns:
    return Warns.create(guild_id)


def UserData(user_id: int) -> User:
    return User.create(user_id)


def BotObject():
    return bot_object


def ApiUserData(
    *,
    user_id: int | None = None,
    oauth_code: str | None = None,
    access_token: str | None = None,
    refresh_token: str | None = None,
    expires_at: float | None = None,
) -> ApiUser:
    return ApiUser.create(
        user_id=int(user_id) if user_id else None,
        oauth_code=oauth_code,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at,
    )


def MemberData(member_id: int, guild_id: int) -> Member:
    return Member.create(member_id, guild_id)


def YouTubeData(guild_id: int) -> YouTube:
    return YouTube.create(guild_id)


async def update_loop():
    last_cache_clear = 0

    while True:
        await asyncio.sleep(5)

        for objects in OBJECTS.values():
            if len(objects) == 0:
                continue

            destroyed = []

            for id, object in objects.items():
                if object.can_destroy():
                    destroyed.append(id)

            for id in destroyed:
                objects[id].destroy()

        if time.time() - last_cache_clear >= 10:
            last_cache_clear = time.time()

            with open("data/users.json", "r") as file:
                try:
                    data = json.load(file)
                except json.JSONDecodeError:
                    data = {}

                to_pop = []

                for user_id, user in data.items():
                    if time.time() - user["last_refresh"] > 300:
                        to_pop.append(user_id)

                for user_id in to_pop:
                    data.pop(user_id)

            with open("data/users.json", "w") as file:
                json.dump(data, file)


def thread_function(method: typing.Callable):
    loop = asyncio.new_event_loop()

    asyncio.set_event_loop(loop)
    loop.run_until_complete(method())
    loop.close()


Thread(target=thread_function, args=[update_loop]).start()
