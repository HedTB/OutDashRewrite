## -- IMPORTS -- ##

import json
import logging
import os
import time

from threading import Thread
from dotenv import load_dotenv
from flask import Blueprint, Flask, redirect, request, url_for
from flask_cors import CORS, cross_origin
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from jwcrypto import jwe, jwk

# FILES
from utils import config
from utils.data import ApiUserData, BotObject

from web.utils.decorators import validate_user_token
from web.utils.exceptions import InvalidOauthCode

from web.extensions.v1.guild import blueprint as guild
from web.extensions.v1.guild_settings import blueprint as settings
from web.extensions.v1.guilds import guilds as guilds

## -- SETUP -- ##

load_dotenv()

## -- VARIABLES -- ##

# SECRETS
bot_token = os.environ.get("BOT_TOKEN" if config.IS_SERVER else "TEST_BOT_TOKEN")
bot_id = os.environ.get("BOT_ID" if config.IS_SERVER else "TEST_BOT_ID")
bot_secret = os.environ.get("BOT_SECRET" if config.IS_SERVER else "TEST_BOT_SECRET")

# APP VARIABLES
app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}}, send_wildcard=True, origins="*")

# APP CONFIG
app.config["CORS_HEADERS"] = "Content-Type"
app.config["SECRET"] = os.environ.get("SECRET")
app.config["API_KEY"] = os.environ.get("API_KEY")

# OTHER VARIABLES
limiter = Limiter(app=app, key_func=get_remote_address, default_limits=["1/second"])

api_blueprint = Blueprint(name="api", import_name=__name__, url_prefix="/api")

version1_blueprint = Blueprint(name="v1", import_name=__name__, url_prefix="/v1")

logger = logging.getLogger("App")
bot = BotObject()

# CONSTANTS
BASE_DISCORD_URL = "https://discord.com/api{}"
SERVER_URL = "http://127.0.0.1:8080" if not config.IS_SERVER else "https://outdash-beta2.herokuapp.com"
REDIRECT_URI = SERVER_URL + "/callback"

# DATA
oauth_tokens = {}
api_data = {}

## -- FUNCTIONS -- ##

## -- ROUTES -- ##


@app.route("/login", methods=["GET"])
@limiter.exempt
def login():
    token = request.cookies.get("token")
    status_code, _, _ = validate_user_token(token)

    if status_code == 200:
        return redirect(url_for("index"))

    return redirect(
        "{}?response_type=code&client_id={}&scope=identify&prompt=none&redirect_uri={}&state={}".format(
            BASE_DISCORD_URL.format("/oauth2/authorize"), bot_id, REDIRECT_URI, request.args.get("redirect", SERVER_URL)
        )
    )


@app.route("/callback", methods=["GET"])
@limiter.exempt
def callback():
    code = request.args.get("code")
    state = request.args.get("state")

    if not code:
        return {"message": "Missing OAuth code"}, 400
    elif code and bot.get_token_from_code(code):
        return {"message": "You have already authorized"}, 200

    try:
        user_data_obj = ApiUserData(oauth_code=code)
    except InvalidOauthCode:
        return redirect(url_for("login"))

    oauth_data = user_data_obj.get_oauth_data()

    if oauth_data["code"] and time.time() > oauth_data["expires_at"]:
        print("token expired")
        return redirect(url_for("login"))

    key = jwk.JWK.from_password(app.config["SECRET"])
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

    return {"message": "You have been authorized", "token": token, "redirect": state}, 200


@app.route("/api/authorize", methods=["POST"])
def authorize():
    pass


@app.route("/")
@cross_origin()
def index():
    return {
        "message": "Seems like you have found the API for OutDash."
        "Well, there's nothing you can really do here, so you may aswell just exit this page and move on :)"
    }


## -- ERROR HANDLERS -- ##


@app.errorhandler(404)
def page_not_found(error):
    return {"message": "The page you requested does not exist."}, 404


@app.errorhandler(405)
def method_not_allowed(error):
    return {"message": "The target endpoint doesn't support this method."}, 405


@app.errorhandler(500)
def internal_server_error(error):
    return {"message": "Something went wrong while trying to process your request."}, 500


## -- SETUP -- ##

version1_blueprint.register_blueprint(settings)
version1_blueprint.register_blueprint(guild)
version1_blueprint.register_blueprint(guilds)

api_blueprint.register_blueprint(version1_blueprint)
app.register_blueprint(api_blueprint)

limiter.init_app(app)

## -- START -- ##


def run_api():
    server = Thread(
        target=app.run,
        args=(
            "127.0.0.1",
            8080,
        ),
    )
    server.run()


if __name__ == "__main__" and not config.IS_SERVER:
    run_api()
