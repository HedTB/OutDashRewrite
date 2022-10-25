## -- IMPORTING -- ##

from flask import Blueprint, request

from utils import config, enums
from utils.data import ApiUserData, GuildData, UserData, WarnsData, MemberData

from web.utils.decorators import *
from web.utils.exceptions import *

## -- VARIABLES -- ##

blueprint = Blueprint(name="guild", import_name=__name__, url_prefix="/guild")

## -- FUNCTIONS -- ##


def try_int(string: str) -> int | None:
    try:
        return int(string)
    except:
        return None


## -- ROUTES -- ##


@blueprint.route("/<int:guild_id>/cases", methods=["GET", "POST", "PATCH", "DELETE"])
@guild_endpoint
def guild_cases(user_data_obj: ApiUser, guild_data_obj: Guild, guild_id: int):
    if request.method == "GET":
        return "hi", 200
    elif request.method == "POST":
        moderator = try_int(request.args.get("moderator"))
        offender = try_int(request.args.get("offender"))
        action = request.args.get("action")
        reason = request.args.get("reason", "No reason provided.")

        if moderator is None:
            return {
                "message": "Argument moderator should be a valid snowflake",
                "error": "invalid_input",
            }, 400
        elif offender is None:
            return {
                "message": "Argument offender should be a valid snowflake",
                "error": "invalid_input",
            }, 400
        elif not action or action.upper() not in enums.Moderation._member_names_:
            return {
                "message": f"Argument action has to be one of the following values: { enums.Moderation._member_names_ }",
                "error": "invalid_input",
            }, 400

        moderator_data_obj = MemberData(moderator, guild_id)
        offender_data_obj = MemberData(offender, guild_id)

        guild_data = guild_data_obj.get_data()
        moderator_data = moderator_data_obj.get_guild_data()
        offender_data = offender_data_obj.get_guild_data()

        cases = guild_data.get("cases", [])
        moderation_action_logs = moderator_data.get("moderation_action_logs", [])
        moderation_logs = offender_data.get("moderation_logs", [])

        case_id = len(cases) + 1

        cases.append(
            {
                "id": len(cases) + 1,
                "moderator": moderator,
                "offender": offender,
                "action": enums.Moderation[action].value,
                "reason": reason,
                "timestamp": datetime.datetime.utcnow(),
            }
        )

        moderation_action_logs.append(case_id)
        moderation_logs.append(case_id)

        guild_data_obj.update_data(guild_data)
        moderator_data_obj.update_guild_data(moderator_data)
        offender_data_obj.update_guild_data(offender_data)

        return {"message": "The case has been counted in the guild's data."}, 200
