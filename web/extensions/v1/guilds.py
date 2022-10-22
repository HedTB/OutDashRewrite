## -- IMPORTING -- ##

from flask import Blueprint

from utils.data import *

from web.utils.decorators import *
from web.utils.responses import *
from web.utils.exceptions import *

## -- VARIABLES -- ##

guilds = Blueprint(name="guilds", import_name=__name__, url_prefix="/guilds")

## -- FUNCTIONS -- ##

## -- ROUTES -- ##


@guilds.route("/bot", methods=["GET"])
@bot_endpoint
def get_bot_guilds(bot_obj: BotObject):
    return {"guilds": bot_obj.get_guilds()}, 200


@guilds.route("/bot/count", methods=["GET"])
@bot_endpoint
def get_guild_count(bot_obj: BotObject):
    return {"guild_count": bot_obj.get_guild_count()}, 200


@guilds.route("/user", methods=["GET"])
@user_endpoint
def get_user_guilds_(user_data_obj: ApiUser):
    try:
        guilds = user_data_obj.get_guilds()
    except InvalidAccessToken:
        return invalid_access_token()

    return {"guilds": guilds}, 200
