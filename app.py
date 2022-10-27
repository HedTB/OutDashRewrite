## -- IMPORTS -- ##

import json
import logging
import os
import uvicorn

from fastapi import APIRouter, Cookie, FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from jwcrypto import jwe, jwk
from threading import Thread

from utils import config
from utils.data import ApiUserData, BotObject
from web.utils.exceptions import InvalidOauthCode
from web.utils.functions import validate_user_token

from web.extensions.v2.guild import router as guild
from web.extensions.v2.webhooks import router as webhooks
from web.extensions.v2.data import router as data

## -- VARIABLES -- ##

# OBJECTS
app = FastAPI()
templating = Jinja2Templates("./web/templates")
version2 = APIRouter(prefix="/api/v2")

logger = logging.getLogger("App")
bot = BotObject()

# CONSTANTS
BASE_DISCORD_URL = "https://discord.com/api{}"

SECRET = os.environ.get("SECRET")

logging.getLogger("Database").level = logging.DEBUG

## -- DECORATORS -- ##


## -- ROUTES -- ##


@app.api_route("/", methods=["GET", "HEAD"])
async def index(request: Request):
    return templating.TemplateResponse("dashboard.html", context={"request": request})
    return {
        "message": "Seems like you have found the API for OutDash. "
        "Well, there's nothing you can really do here, so you may aswell just exit this page and move on :)"
    }


@app.get("/login")
async def login(redirect: str = config.SERVER_URL, token: str = Cookie(default=None)):
    status_code, _, _ = validate_user_token(token)

    if status_code == 200:
        return RedirectResponse("/")
    else:
        return RedirectResponse(
            "{}?response_type=code&client_id={}&scope=identify&prompt=none&redirect_uri={}&state={}".format(
                BASE_DISCORD_URL.format("/oauth2/authorize"),
                config.CLIENT_ID,
                config.REDIRECT_URI,
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
app.mount("/static", StaticFiles(directory="./web/static"), name="static")
app.mount("/", StaticFiles(directory="./web/data"), name="data")

## -- START -- ##


def _start_app():
    uvicorn.run(app="app:app", host="0.0.0.0", port=80, reload=True, reload_excludes=["./extensions"])


# TODO fix multiprocessing pool issue
def run_api():
    Thread(target=_start_app).run()


if __name__ == "__main__":
    _start_app()
