## -- IMPORTING -- ##

import datetime

from fastapi import APIRouter, Depends, HTTPException, Path, Body
from fastapi.responses import JSONResponse


from utils.data import Guild, MemberData

from web.utils.dependencies import get_guild_data
from web.utils.models import CaseData, Message, SettingsLock

## -- VARIABLES -- ##

router = APIRouter(
    prefix="/guild/{guild_id}",
    responses={
        400: {"model": Message, "description": "Passed user token was malformed"},
        401: {"model": Message, "description": "Passed user token was invalid"},
        403: {"model": Message, "description": "Access to the passed guild was missing"},
        404: {"model": Message, "description": "Passed guild ID was invalid"},
    },
)

## -- FUNCTIONS -- ##


def try_int(string: str) -> int | None:
    try:
        return int(string)
    except ValueError:
        return None


## -- MODELS -- ##


## -- ROUTES -- ##


@router.get(
    path="/cases",
    summary="Get all open cases in a guild.",
    response_description="A list of the guild's open cases.",
    response_model=list[CaseData],
)
async def get_cases(guild_data_obj: Guild = Depends(get_guild_data)) -> list[CaseData]:
    guild_data = guild_data_obj.get_data()

    return guild_data["cases"]


@router.get(
    path="/cases/{case_id}",
    summary="Get information on a specified case in a guild.",
    response_model=CaseData,
    responses={
        200: {"description": "Case data requested by ID"},
        400: {"model": Message, "description": "The given case ID is invalid"},
    },
)
async def get_case(
    case_id: int = Path(
        default=None,
        title="Case ID",
        description="The ID of the case.",
        gt=0,
    ),
    guild_data_obj: Guild = Depends(get_guild_data),
) -> CaseData:
    guild_data = guild_data_obj.get_data()
    cases = guild_data["cases"]

    if case_id > len(cases):
        return JSONResponse(status_code=400, content={"message": "Invalid case ID"})

    return cases[case_id - 1]


@router.post(
    path="/cases",
    summary="Open a new case in a guild.",
    response_description="A JSON response describing whether the operation succeded or not.",
    response_model=Message,
)
async def create_case(
    case_data: CaseData = Body(default=None, alias="case-data", title="Case data"),
    guild_id: int = Path(
        default=None,
        title="Guild ID",
        description="The ID of the guild.",
        gt=15,
    ),
    guild_data_obj: Guild = Depends(get_guild_data),
) -> Message:
    """
    Body
    ----
    - **moderator - snowflake**: The ID of the moderator who opened the case.
    - **offender - snowflake**: The ID of the member the case was opened against.
    - **action - int**: The value of the action the case was opened for. Available values:
        - 1: warning
        - 2: kick
        - 3: ban
        - 4: mute
        - 5: unmute
        - 6: softban
    - **reason - str?**: The reason as to why the case was opened. Defaults to "No reason provided."
    - **timestamp - date?**: The time that the case was opened. Defaults to the time the endpoint was called.
    """

    moderator_data_obj = MemberData(case_data.moderator, guild_id)
    offender_data_obj = MemberData(case_data.offender, guild_id)

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
            "moderator": case_data.moderator,
            "offender": case_data.offender,
            "action": case_data.action,
            "reason": case_data.reason,
            "timestamp": datetime.datetime.utcnow(),
        }
    )

    moderation_action_logs.append(case_id)
    moderation_logs.append(case_id)

    guild_data_obj.update_data(guild_data)
    moderator_data_obj.update_guild_data(moderator_data)
    offender_data_obj.update_guild_data(offender_data)

    return {"message": "The case has been counted in the guild's data."}


@router.patch(
    path="/cases/{case_id}",
    summary="Edit an open case in a guild.",
    response_description="A JSON response describing whether the operation succeded or not.",
    response_model=Message,
    responses={400: {"model": Message}},
)
async def edit_case(
    case_data: CaseData = Body(default=None, alias="case-data", title="Case data"),
    case_id: int = Path(
        default=None,
        title="Case ID",
        description="The ID of the case.",
        gt=0,
    ),
    guild_data_obj: Guild = Depends(get_guild_data),
):
    """
    Body
    ----
    - **moderator - snowflake**: The ID of the moderator who opened the case.
    - **offender - snowflake**: The ID of the member the case was opened against.
    - **action - int**: The value of the action the case was opened for. Available values:
        - 1: warning
        - 2: kick
        - 3: ban
        - 4: mute
        - 5: unmute
        - 6: softban
    - **reason - str?**: The reason as to why the case was opened. Defaults to "No reason provided."
    - **timestamp - date?**: The time that the case was opened. Defaults to the time the endpoint was called.
    """
    guild_data = guild_data_obj.get_data()
    cases = guild_data["cases"]

    if case_id > len(cases):
        return JSONResponse(status_code=400, content={"message": "Invalid case ID"})

    case = cases[case_id - 1]

    for key, value in case_data:
        if value is None or key == "id":
            continue

        case[key] = value

    guild_data_obj.update_data(guild_data)
    return {"message": "The case has been updated."}


@router.delete(
    path="/cases/{case_id}",
    summary="Delete an open case in a guild",
    response_description="A JSON response describing whether the operation succeded or not.",
    response_model=Message,
)
async def delete_case(
    case_id: int = Path(
        default=None,
        title="Case ID",
        description="The ID of the case.",
        gt=0,
    ),
    guild_id: int = Path(
        default=None,
        title="Guild ID",
        description="The ID of the guild.",
        gt=15,
    ),
    guild_data_obj: Guild = Depends(get_guild_data),
):
    """Delete an open case from a guild.

    Returns
    -------
    A success JSON message, if the deletion succeeded.
    """

    guild_data = guild_data_obj.get_data()
    cases = guild_data["cases"]

    if case_id > len(cases):
        raise HTTPException(status_code=400, detail="Invalid case ID")

    case = cases[case_id - 1]

    moderator_data_obj = MemberData(case["moderator"], guild_id)
    offender_data_obj = MemberData(case["offender"], guild_id)

    moderator_data = moderator_data_obj.get_guild_data()
    offender_data = offender_data_obj.get_guild_data()

    moderator_logs: list = moderator_data["moderation_action_logs"]
    offender_logs: list = offender_data["moderation_logs"]

    if case_id in moderator_logs:
        moderator_logs.pop(moderator_logs.index(case_id))
    if case_id in offender_logs:
        offender_logs.pop(offender_logs.index(case_id))

    cases.pop(case_id - 1)
    guild_data_obj.update_data(guild_data)

    moderator_data_obj.update_guild_data(moderator_data)
    offender_data_obj.update_guild_data(offender_data)

    return {"message": "The case has been deleted."}


@router.get(
    path="/settings/lock",
    summary="Get a boolean describing whether the guild's settings are locked or not.",
    response_description="A boolean describing whether the guild's settings are locked or not.",
    response_model=SettingsLock,
)
async def get_settings_lock(guild_data_obj=Depends(get_guild_data)) -> SettingsLock:
    guild_data = guild_data_obj.get_data()

    return {"settings_locked": guild_data["settings_locked"]}


@router.put(
    path="/settings/lock",
    summary="Toggle a guild's setting lock.",
    response_description="A JSON response describing whether the operation succeded or not.",
    response_model=Message,
)
async def set_settings_lock(toggle: bool, guild_data_obj: Guild = Depends(get_guild_data)) -> Message:
    guild_data_obj.run_asynchronously(guild_data_obj.update_data, {"data": {"settings_locked": toggle}})

    return JSONResponse(
        status_code=202, content={"message": f"The settings are being {'locked' if toggle is True else 'unlocked'}."}
    )
