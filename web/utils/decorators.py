## -- IMPORTING -- ##

import json
import logging
import os
import typing
from functools import wraps

import disnake
import requests
from flask import current_app, make_response, request
from jwcrypto import jwe, jwk

from utils.data import ApiUser, ApiUserData, BotObject, GuildData
from web.utils.exceptions import InvalidAccessToken, InvalidOauthCode, InvalidUserToken
from web.utils.responses import invalid_user_token

## -- VARIABLES -- ##

# CONSTANTS
SECRET = os.environ.get("SECRET")

# OBJECTS
logger = logging.getLogger("App")

## -- FUNCTIONS -- ##


def preflight_response():
    response = make_response()
    headers = response.headers

    headers.add("Access-Control-Allow-Origin", "*")
    headers.add("Access-Control-Allow-Headers", "*")
    headers.add("Access-Control-Allow-Methods", "*")

    return response


def validate_user_token(token: str) -> typing.Tuple[int, dict | None, ApiUser | None]:
    try:
        key = jwk.JWK.from_password(current_app.config["SECRET"])
        decrypted = jwe.JWE()

        decrypted.deserialize(raw_jwe=token, key=key)

        data = json.loads(decrypted.payload)
        user_id = data["sub"]

        try:
            user_data_obj = ApiUserData(
                user_id=user_id, access_token=data["access_token"], refresh_token=data["refresh_token"]
            )
        except InvalidOauthCode or InvalidAccessToken:
            raise InvalidUserToken
        except requests.HTTPError:
            raise

        return 200, data, user_data_obj

    except InvalidUserToken or jwe.InvalidJWEData:
        return 401, None, None
    except Exception as error:
        logger.exception(error)
        return 400, None, None


## -- DECORATORS -- ##


def bot_endpoint(method: typing.Callable):
    @wraps(method)
    def decorated_function(*args, **kwargs):
        if request.method == "OPTIONS":
            return preflight_response()

        if not request.headers.get("api-key"):
            return {"message": "Missing API key", "error": "invalid_input"}, 400
        elif request.headers.get("api-key") != current_app.config["API_KEY"]:
            return {"message": "Invalid API key", "error": "invalid_token"}, 401

        return method(*args, BotObject(), **kwargs)

    return decorated_function


def user_endpoint(method: typing.Callable):
    @wraps(method)
    def decorated_function(*args, **kwargs):
        if method == "OPTIONS":
            return preflight_response()

        token = request.cookies.get("token", request.headers.get("x-access-tokens"))

        if token is None:
            return {"message": "User token is missing", "error": "invalid_input"}, 400

        status_code, _, user_data_obj = validate_user_token(token)

        if status_code == 200:
            return method(*args, user_data_obj, **kwargs)
        elif status_code == 400:
            return {"message": "Malformed user token", "error": "invalid_input"}, 400
        elif status_code == 401:
            return invalid_user_token()

    return decorated_function


def guild_endpoint(method: typing.Callable):
    @wraps(method)
    # @user_endpoint
    def decorated_function(*args, **kwargs):
        guild_id = kwargs.get("guild_id")

        token = request.cookies.get("token", request.headers.get("x-access-tokens"))
        status_code, _, user_data_obj = validate_user_token(token)

        if guild_id is None:
            return {"message": "Guild ID is missing", "error": "invalid_input"}, 400
        elif token is None:
            return {"message": "User token is missing", "error": "invalid_input"}, 400

        try:
            guild_id = int(guild_id)
        except Exception:
            return {"message": "Guild ID has to be a valid integer", "error": "invalid_input"}, 400

        guild_data_obj = GuildData(guild_id)

        if guild_data_obj.get_data(can_insert=False) is None:
            return {"message": "Invalid guild ID", "error": "invalid_guild_id"}, 400

        if status_code == 200:
            user_guild = user_data_obj.get_api_guild(guild_id)

            if user_guild is None:
                return {"message": "You don't have access to this guild", "error": "missing_access"}, 403

            permissions = disnake.Permissions(int(user_guild["permissions"]))

            if not user_guild["owner"] and not permissions.administrator and not permissions.manage_guild:
                return {"message": "You don't have access to this guild", "error": "missing_access"}, 403

            return method(*args, user_data_obj, guild_data_obj, **kwargs)
        elif status_code == 400:
            return {"message": "Malformed user token", "error": "invalid_input"}, 400
        elif status_code == 401:
            return invalid_user_token()

    return decorated_function
