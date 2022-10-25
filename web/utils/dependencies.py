## -- IMPORTS -- ##

import logging
import os
import disnake

from time import time
from fastapi import Cookie, HTTPException, Path

from utils.data import Guild, GuildData
from web.utils.functions import validate_user_token

## -- VARIABLES -- ##

secret = os.environ.get("SECRET")

logger = logging.getLogger("App")

## -- FUNCTIONS -- ##


def get_user_data(token: str = Cookie(default=None)):
    status_code, _, user_data_obj = validate_user_token(token)

    if status_code == 200:
        return user_data_obj
    elif status_code == 400:
        raise HTTPException(status_code=400, detail="Malformed user token")
    elif status_code == 401:
        raise HTTPException(status_code=401, detail="Invalid user token")


def get_guild_data(
    guild_id: int = Path(
        default=None,
        title="Guild ID",
        description="The ID of the guild.",
        gt=15,
    ),
    token: str = Cookie(default=None),
) -> Guild | None:
    start = time()

    status_code, _, user_data_obj = validate_user_token(token)

    print(f"Validated user token, took: {(time() - start) * 1000} ms")
    start = time()

    guild_data_obj = GuildData(guild_id)

    print(f"Created guild data object, took: {(time() - start) * 1000} ms")
    start = time()

    if status_code == 200:
        user_guild = user_data_obj.get_api_guild(guild_id)

        print(f"Grabbed API guild, took: {(time() - start) * 1000} ms")
        start = time()

        temp_guild_data = guild_data_obj.get_data(can_insert=False)

        print(f"Grabbed guild data, took: {(time() - start) * 1000} ms")
        start = time()

        if temp_guild_data is None and user_guild is None:
            raise HTTPException(status_code=404, detail="Invalid guild ID")
        elif temp_guild_data is None and user_guild is not None:
            guild_data_obj.insert_data()
        elif user_guild is None:
            raise HTTPException(status_code=403, detail="You don't have access to this guild")

        permissions = disnake.Permissions(int(user_guild["permissions"]))

        if not user_guild["owner"] and not permissions.administrator and not permissions.manage_guild:
            raise HTTPException(status_code=403, detail="You don't have access to this guild")

        return guild_data_obj
    elif status_code == 400:
        raise HTTPException(status_code=400, detail="Malformed user token")
    elif status_code == 401:
        raise HTTPException(status_code=401, detail="Invalid user token")
