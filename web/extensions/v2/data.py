## -- IMPORTING -- ##

import logging
import os

from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse

from utils.data import BotObject
from web.utils.dependencies import get_user_data
from web.utils.exceptions import InvalidAccessToken
from web.utils.models import GuildData, BotGuildData, BotGuildCount


## -- VARIABLES -- ##

# CONSTANTS
API_KEY = os.environ.get("API_KEY")

# OBJECTS
bot_object = BotObject()

router = APIRouter(prefix="/guilds")
logger = logging.getLogger("App")

## -- FUNCTIONS -- ##

## -- MODELS -- ##


## -- ROUTES -- ##


@router.get(
    path="/user",
    summary="Get the signed in user's joined guilds.",
    response_description="A list of the user's joined guilds",
    response_model=list[GuildData],
)
async def get_user_guilds(user_data_obj=Depends(get_user_data)):
    try:
        guilds = user_data_obj.get_guilds()
    except InvalidAccessToken:
        return JSONResponse(status_code=401, content={"message": "Invalid user token"})

    return guilds


@router.get(
    path="/bot",
    summary="Get the bot's joined guilds.",
    response_description="A list of the bot's joined guilds",
    response_model=list[BotGuildData],
)
def get_bot_guilds(
    api_key: str = Header(
        default=None,
        alias="api-key",
    )
):
    if api_key != API_KEY:
        return JSONResponse(status_code=403, content={"message": "Invalid API key"})

    return bot_object.get_guilds()


@router.get(
    path="/bot/count",
    summary="Get the amount of guilds the bot is in.",
    response_description="The amount of guilds the bot is in",
    response_model=BotGuildCount,
)
def get_guild_count():
    return {"guild_count": bot_object.get_guild_count()}
