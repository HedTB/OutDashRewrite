## -- IMPORTING -- ##

from flask import Blueprint

from utils.data import ApiUserData, GuildData, UserData, WarnsData, MemberData

from web.utils.decorators import *
from web.utils.exceptions import *

## -- VARIABLES -- ##

blueprint = Blueprint(name="guild/settings", import_name=__name__, url_prefix="/guild/<int:guild_id>/settings")

## -- FUNCTIONS -- ##

## -- ROUTES -- ##


@blueprint.route("/lock", methods=["GET", "PUT"])
@guild_endpoint
def set_settings_lock(user_data_obj: ApiUser, guild_data_obj: Guild, *, guild_id: int):
    settings_lock = request.args.get("toggle")

    if request.method == "GET":
        guild_data = guild_data_obj.get_data()

        return {"settings-lock": guild_data["settings_locked"]}, 200
    elif request.method == "PUT":
        if settings_lock is None:
            return {"message": 'Missing parameter "toggle"', "error": "invalid_input"}, 400
        elif settings_lock.lower() not in ["true", "false"]:
            return {"message": 'Parameter "toggle" needs to be a boolean', "error": "invalid_input"}, 400

        settings_lock = settings_lock.lower() == "true"
        guild_data_obj.update_data({"settings_locked": settings_lock})

        return {"message": f"The settings have been {'locked' if settings_lock is True else 'unlocked'}"}, 200
