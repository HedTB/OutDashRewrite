## -- IMPORTING -- ##

import typing
import os

from jwcrypto import jwe, jwk
from functools import wraps
from flask import request, make_response, current_app
from werkzeug.security import check_password_hash

from utils.data import *
from web.utils.responses import *

from .exceptions import *

## -- VARIABLES -- ##

secret = os.environ.get("SECRET")

## -- FUNCTIONS -- ##


def preflight_response():
    response = make_response()
    headers = response.headers

    headers.add("Access-Control-Allow-Origin", "*")
    headers.add("Access-Control-Allow-Headers", "*")
    headers.add("Access-Control-Allow-Methods", "*")

    return response


def validate_user_token(user_token: str) -> typing.Tuple[int, dict | None, ApiUser | None]:
    try:
        key = jwk.JWK.from_password(current_app.config["SECRET"])
        decrypted = jwe.JWE()

        decrypted.deserialize(raw_jwe=user_token, key=key)

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

        user_token = request.headers.get("x-access-tokens")

        if user_token is None:
            return {"message": "User token is missing", "error": "invalid_input"}, 400

        status_code, _, user_data_obj = validate_user_token(user_token)

        if status_code == 200:
            return method(*args, user_data_obj, **kwargs)
        elif status_code == 400:
            return {"message": "Malformed user token", "error": "invalid_input"}, 400
        elif status_code == 401:
            return invalid_user_token()

    return decorated_function


def guild_endpoint(method: typing.Callable):
    @wraps(method)
    def decorated_function(*args, **kwargs):
        if method == "OPTIONS":
            return preflight_response()

        guild_id = kwargs.get("guild_id")
        user_token = request.headers.get("x-access-tokens")
        status_code, _, user_data_obj = validate_user_token(user_token)

        if guild_id is None:
            return {"message": "Guild ID is missing", "error": "invalid_input"}, 400
        elif user_token is None:
            return {"message": "User token is missing", "error": "invalid_input"}, 400

        try:
            guild_id = int(guild_id)
        except:
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
