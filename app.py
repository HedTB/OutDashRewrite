## -- IMPORTS -- ##

from http import cookies
import json
import logging
import os
import re
import typing
import certifi
import requests
import time

from pymongo import MongoClient
from dotenv import load_dotenv
from flask import Flask, make_response, redirect, request
from functools import wraps
from flask_cors import CORS, cross_origin
from threading import Thread
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from uuid import uuid4

# FILES
from utils import config
from utils import functions
from utils.database_types import *
from utils.classes import *

## -- SETUP -- ##

load_dotenv()

## -- VARIABLES -- ##

# SECRETS
mongo_token = os.environ.get("MONGO_LOGIN")
api_key = os.environ.get("API_KEY")

bot_token = os.environ.get("BOT_TOKEN" if config.is_server else "TEST_BOT_TOKEN")
bot_id = os.environ.get("BOT_ID" if config.is_server else "TEST_BOT_ID")
bot_secret = os.environ.get("BOT_SECRET" if config.is_server else "TEST_BOT_SECRET")

# APP VARIABLES
app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}}, send_wildcard=True, origins="*")

# APP CONFIG
app.config["CORS_HEADERS"] = "Content-Type"

# OTHER VARIABLES
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["1/second"]
)

logger = logging.getLogger("OutDash")
bot = BotObject()

# CONSTANTS
SERVER_URL = "http://127.0.0.1:8080" if not config.is_server else "https://outdash-beta2.herokuapp.com"
REDIRECT_URI = "http://127.0.0.1:8080/callback" if not config.is_server else "https://outdash-beta2.herokuapp.com/callback"

# DATABASE VARIABLES
client = MongoClient(mongo_token, tlsCAFile=certifi.where())
db = client[config.database_collection]

guild_data_col = db["guild_data"]
api_data_col = db["api_data"]
access_codes_col = db["access_codes"]

guild_setting_names = [
    "prefix", "message_delete_logs_webhook", "message_edit_logs_webhook",
    "message_bulk_delete_logs_webhook"
]

# DATA
oauth_tokens = {}
api_data = {}

## -- CLASSES -- ##

# EXCEPTIONS
    
## -- CHECKS -- ##

def api_endpoint(f):
    @wraps(f)
    
    def decorated_function(*args, **kwargs):
        headers = request.headers
        method = request.method
        
        if method == "OPTIONS":
            return preflight_response()
        
        if not headers.get("api-key"):
            return {"message": "Missing API key"}, 403
        elif headers.get("api-key") != api_key:
            return {"message": "Invalid API key"}, 403
        
        return f()
    return decorated_function

def user_endpoint(f):
    @wraps(f)
    
    def decorated_function(*args, **kwargs):
        cookies = request.cookies
        method = request.method
        
        access_code = cookies.get("access-code")
        
        if method == "OPTIONS":
            return preflight_response()
        
        if not access_code:
            return {"message": "Missing access code"}, 403
        
        try:
            UserObject(access_code)
        except InvalidAccessCode:
            return {"message": "Invalid access code"}, 403
            
        return f()
    return decorated_function

## -- FUNCTIONS -- ##

# API RESPONSES
def preflight_response():
    response = make_response()
    headers = response.headers
    
    headers.add("Access-Control-Allow-Origin", "*")
    headers.add("Access-Control-Allow-Headers", "*")
    headers.add("Access-Control-Allow-Methods", "*")
    
    return response

def corsify_response(response):
    headers = response.headers
    
    headers.add("Access-Control-Allow-Origin", "*")
    return response

# OAUTH
def exchange_code(code: str) -> dict:
    response = requests.post(
        url = BASE_DISCORD_URL.format("/oauth2/token"),
        data = {
            "client_id": bot_id,
            "client_secret": bot_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI
        },
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )
    
    if response.status_code != 200:
        return {"message": "Invalid OAuth code"}, response.status_code
    else:
        return response.json(), 200

def refresh_token(refresh_token: str) -> dict:
    response = requests.post(
        url = BASE_DISCORD_URL.format("/oauth2/token"),
        data = {
            "client_id": bot_id,
            "client_secret": bot_secret,
            "grant_type": "authorization_code",
            "refresh_token": refresh_token
        },
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )
    
    response.raise_for_status()
    return response.json()

def identify_user(access_token: str) -> dict:
    response = requests.get(
        url = BASE_DISCORD_URL.format("/oauth2/@me"),
        headers = {
            "Authorization": "Bearer " + access_token,
            "Content-Type": "application/json"
        }
    )
    
    response.raise_for_status()
    return response.json()

def get_token(access_code: str) -> str | None:
    try:
        user = UserObject(access_code)
    except InvalidAccessCode:
        return None
    
    return user.get_data()["access_token"]

## -- ROUTES -- ##

@app.route("/api/save-settings", methods=["POST", "OPTIONS"])
@user_endpoint
def save_guild_settings():
    params = request.args
    form = request.form
    cookies = request.cookies
    
    guild_id = params.get("guild_id")
    access_code = cookies.get("access-code")
    
    user = UserObject(access_code)
    
    if not guild_id:
        return {"message": "Missing guild ID"}, 400
    
    guild = user.get_guild(guild_id)
    guild_data = guild_data_col.find_one({ "guild_id": guild_id })
    
    if not guild:
        return { "message": "Invalid guild ID" }, 400
    elif guild and not guild_data:
        guild_data_col.insert_one(functions.get_db_data(guild_id))
        return { "message": "An error occured, please try again." }, 500
    
    updated_settings = {}
    for argument in form:
        value = form.get(argument)
        
        if not (value or argument in guild_setting_names):
            continue
        elif guild_data[argument] == value:
            continue
        
        updated_settings[argument] = value
        
    guild_data_col.update_one({ "guild_id": guild_id }, { "$set": updated_settings })
    
    if len(updated_settings) == 0:
        return {"message": "No settings were updated."}, 200
    else:
        return {"changed_settings": argument for argument in list(updated_settings.keys())}, 200


@app.route("/api/get-bot-guilds", methods=["GET", "OPTIONS"])
@api_endpoint
@limiter.exempt
def get_bot_guilds():
    bot_guilds = bot.get_guilds()
    
    if type(bot_guilds) != list:
        return {"message": "An error occurred, please try again later."}, 500
    
    return {"guilds": bot_guilds}, 200

@app.route("/api/get-user-guilds", methods=["GET", "OPTIONS"])
@user_endpoint
@limiter.exempt
def get_user_guilds_():
    cookies = request.cookies
    access_code = cookies["access-code"]
    
    user = UserObject(access_code)
    user_guilds = user.get_guilds()
    
    if not isinstance(user_guilds, list):
        print(type(user_guilds))
        try:
            user_guilds = json.loads(user_guilds)
        except Exception as error:
            logger.warning("Failed retrieving user guilds | " + error)
            
            return {"message": "An error occurred, please try again later."}, 500
    
    return {"guilds": user_guilds}, 200
    

@app.route("/api/get-guild-count", methods=["GET", "OPTIONS"])
@api_endpoint
@limiter.exempt
def get_guild_count():
    bot_guilds = bot.get_guilds()
    
    if type(bot_guilds) != list:
        return {"message": "An error occurred, please try again later."}, 500
    
    return {"guild_count": len(bot_guilds)}, 200

@app.route("/api/authorize", methods=["POST", "OPTIONS"])
def authorize():
    headers = request.headers
    oauth_code = headers.get("oauth-code")
    
    if not oauth_code:
        return {"message": "Missing OAuth code"}, 403
    elif oauth_code and bot.get_token_from_code(oauth_code):
        return {"message": "You have already authorized"}, 200
    
    else:
        result, status = exchange_code(oauth_code)
        if status == 400:
            return {"message": "Invalid OAuth code"}, 403
        elif status != 200:
            return {"message": "An error occured, please try again later."}, 500
        
        refresh_token = result["refresh_token"]
        access_token = result["access_token"]
        access_code = str(uuid4())
        
        # to_pop = []
        # access_tokens = access_codes_col.find()
        
        # for access_code in access_tokens:
        #     if access_tokens[access_code]["token"]["access_token"] == access_token:
        #         to_pop.append(access_code)
        access_codes_col.delete_many({ "access_token": access_token })
        
        auth_info = identify_user(access_token)
        access_codes_col.insert_one(user_api_data(access_token, refresh_token, access_code, auth_info["user"]))

        return {"message": "You have been authorized", "access_code": access_code}, 200
    
@app.route("/login")
@limiter.exempt
def login():
    return redirect(f"https://discord.com/api/oauth2/authorize?response_type=code&client_id={bot_id}&scope=identify&prompt=none&redirect_uri={REDIRECT_URI}")

@app.route("/callback")
def callback():
    params = request.args

    code = params.get("code")
    response = requests.post(
        url = f"{SERVER_URL}/api/authorize",
        headers = {
            "oauth-code": code
        }
    )
    
    return response.json(), response.status_code


@app.route("/webhooks/bot-upvotes", methods=["POST", "OPTIONS"])
def bot_upvotes_webhook():
    data = request.json
    headers = request.headers
           
    if not headers.get("authorization") == api_key:
        return {"message": "Invalid authorization header"}, 403
    
    elif data["type"] == "test":
        print(data)
    else:
        user_voted = data["user"]
        is_weekend = data["isWeekend"]
        
        logger.debug(f"User with ID {user_voted} has voted on top.gg.")
            
        with open("data/votes.json", "r+") as file:
            file_data = json.load(file)
            
            file_data.update({ str(user_voted): {
                "is_weekend": is_weekend,
                "expires_at": time.time() + (24 * 3600),
            } })
            json.dump(file_data, file)
            
    return {"message": "The vote has been logged"}, 200
        

@app.route("/")
@cross_origin()
def index():
    return {"message": "Seems like you have found the API for OutDash. Well, there's nothing you can really do here, so you may aswell just exit this page and move on :)"}
    

## -- EXTRA METHODS -- ##

@app.errorhandler(404)
def page_not_found(error):
    return {"message": "The page you requested does not exist."}, 404

@app.errorhandler(500)
def internal_server_error(error):
    return {"message": "Something went wrong while trying to process your request."}, 500

## -- START -- ##

def run_api():
    server = Thread(target=app.run, args=("127.0.0.1", 8080, ))
    server.run()

if __name__ == "__main__" and not config.is_server:
    run_api()