## -- IMPORTS -- ##

import json
import logging
import os

from fastapi import APIRouter, Cookie, FastAPI
from fastapi.responses import RedirectResponse

from jwcrypto import jwe, jwk

from utils import config
from utils.data import ApiUserData, BotObject
from web.utils.exceptions import InvalidOauthCode
from web.utils.functions import validate_user_token

from web.extensions.v2.guild import router as guild
from web.extensions.v2.webhooks import router as webhooks
from web.extensions.v2.data import router as data

## -- VARIABLES -- ##

# CONSTANTS
BASE_DISCORD_URL = "https://discord.com/api{}"
SERVER_URL = "http://127.0.0.1:8080" if not config.IS_SERVER else "https://outdash-beta2.herokuapp.com"
REDIRECT_URI = SERVER_URL + "/callback"

BOT_ID = os.environ.get("BOT_ID" if config.IS_SERVER else "TEST_BOT_ID")
SECRET = os.environ.get("SECRET")

# OBJECTS
app = FastAPI()
version2 = APIRouter(prefix="/api/v2")

logger = logging.getLogger("App")
bot = BotObject()

logging.getLogger("Database").level = logging.DEBUG

## -- DECORATORS -- ##


## -- ROUTES -- ##


@app.api_route("/", methods=["GET", "HEAD"])
async def index():
    return {
        "message": "Seems like you have found the API for OutDash. "
        "Well, there's nothing you can really do here, so you may aswell just exit this page and move on :)"
    }


@app.get("/login")
async def login(redirect: str = SERVER_URL, token: str = Cookie(default=None)):
    status_code, _, _ = validate_user_token(token)

    if status_code == 200:
        return RedirectResponse("/")
    else:
        return RedirectResponse(
            "{}?response_type=code&client_id={}&scope=identify&prompt=none&redirect_uri={}&state={}".format(
                BASE_DISCORD_URL.format("/oauth2/authorize"),
                BOT_ID,
                REDIRECT_URI,
                redirect,
            )
        )


@app.get("/callback")
def callback(code: str, state: str):
    try:
        user_data_obj = ApiUserData(oauth_code=code)
    except InvalidOauthCode:
        return RedirectResponse("/login")

    key = jwk.JWK.from_password(SECRET)
    jwe_token = jwe.JWE(
        plaintext=json.dumps(
            {
                "sub": user_data_obj.user_id,
                "exp": user_data_obj._expires_at,
                "access_token": user_data_obj._access_token,
                "refresh_token": user_data_obj._refresh_token,
            }
        ),
        protected={
            "alg": "A256KW",
            "enc": "A256CBC-HS512",
        },
        recipient=key,
    )

    token = jwe_token.serialize(compact=True)
    user_data_obj._oauth_code = code

    return {"message": "You have been authorized", "token": token, "redirect": state}


## -- SETUP -- ##

version2.include_router(guild)
version2.include_router(webhooks)
version2.include_router(data)

app.include_router(version2)
