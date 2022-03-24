## -- IMPORTS -- ##

import json
import logging
import os
from uuid import uuid4
import certifi
import requests
import time
import random  
import string  

from pymongo import MongoClient
from dotenv import load_dotenv
from flask import Flask, make_response, redirect, render_template, request, jsonify, url_for
from functools import wraps
from flask_cors import CORS, cross_origin
from threading import Thread
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pprint import pprint

# FILES
from utils import config
from utils import functions

## -- SETUP -- ##

load_dotenv()

## -- VARIABLES -- ##

# SECRETS
mongo_token = os.environ.get("MONGO_LOGIN")
api_key = os.environ.get("API_KEY")
developer_password = os.environ.get("DEVELOPER_PASSWORD")

bot_token = os.environ.get("BOT_TOKEN" if config.is_server else "TEST_BOT_TOKEN")
bot_id = os.environ.get("BOT_ID" if config.is_server else "TEST_BOT_ID")
bot_secret = os.environ.get("BOT_SECRET" if config.is_server else "TEST_BOT_SECRET")

# APP VARIABLES
app = Flask(__name__, template_folder="web", static_folder="web/static")
cors = CORS(app, resources={r"/*": {"origins": "*"}}, send_wildcard=True, origins="*")

# APP CONFIG
app.config["CORS_HEADERS"] = "Content-Type"
app.config["TEMPLATES_AUTO_RELOAD"] = True

# OTHER VARIABLES
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["1/second"]
)

# CONSTANTS
BASE_DISCORD_URL = "https://discordapp.com/api/v9{}"
DATA_REFRESH_DELAY = 180

SERVER_URL = "http://127.0.0.1:8080" if not config.is_server else "https://outdash-beta2.herokuapp.com"
REDIRECT_URI = f"{SERVER_URL}/callback"

# DATABASE VARIABLES
client = MongoClient(mongo_token, tlsCAFile=certifi.where())
db = client[config.database_collection]

server_data_col = db["server_data"]

guild_setting_names = [
    "prefix", "message_delete_logs_webhook", "message_edit_logs_webhook",
    "message_bulk_delete_logs_webhook"
]
request_headers = {
    "Authorization": f"Bot {bot_token}",
    "User-Agent": "OutDash (https://outdash.ga, v0.1)",
    "Content-Type": "application/json",
}

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
        headers = request.headers
        method = request.method
        
        oauth_code = headers.get("oauth-code")
        
        file = open("data/oauth_tokens.json", "r")
        data = json.load(file)
        
        if method == "OPTIONS":
            return preflight_response()
        
        if not oauth_code:
            file.close()
            return {"message": "Missing access code"}, 403
        elif oauth_code and not data.get(oauth_code):
            file.close()
            return {"message": "Invalid access code"}, 403
            
        return f()
    return decorated_function

## -- FUNCTIONS -- ##

# MISC
def generate_random_string(letter_count: int, digit_count: int) -> str:
    generated_str = "".join((random.choice(string.ascii_letters) for i in range(letter_count)))  
    generated_str += "".join((random.choice(string.digits) for i in range(digit_count)))  
  
    letter_list = list(generated_str)
    random.shuffle(letter_list)
    final_string = "".join(letter_list)
    
    return final_string

# REQUESTS
def bot_request(endpoint, params=None) -> requests.Response:
    return requests.get(
        url = BASE_DISCORD_URL.format(endpoint),
        headers = request_headers,
        params = params
    )
    
def user_request(endpoint, bearer_token, params=None) -> requests.Response:
    return requests.get(
        url = BASE_DISCORD_URL.format(endpoint),
        headers = {
            "Authorization": "Bearer " + bearer_token,
            "Content-Type": "application/json"
        },
        params = params
    )
    
# USER DATA
def get_user_guilds(bearer_token=None, access_code=None) -> dict:
    file = open("data/oauth_tokens.json", "r+")
    
    try:
        data = json.load(file)
    except:
        file.seek(0)
        file.truncate(0)
        
        json.dump({}, file)
        file.close()
        
        return get_user_guilds(bearer_token, access_code)
    
    user_data = data.get(access_code)
    user_guilds_cache = user_data.get("guilds")
    user_guilds_refresh = user_data.get("guilds_refresh")
    
    if not user_guilds_cache or not user_guilds_refresh or len(user_guilds_cache) == 0 or time.time() - user_guilds_refresh > DATA_REFRESH_DELAY:
        user_result = user_request("/users/@me/guilds", bearer_token)
        user_guilds = user_result.json()
        
        for guild in user_guilds:
            guild.pop("features")
        
        user_data["guilds_refresh"] = time.time()
        user_data["guilds"] = user_guilds
        
        file.seek(0)
        json.dump(data, file)
        
        user_guilds_cache = user_guilds
        
    return user_guilds_cache


# BOT DATA
def get_guilds(bearer_token=None, access_code=None) -> dict:
    file = open("data/api.json", "r+")
    
    try:
        data = json.load(file)
    except:
        file.seek(0)
        file.truncate(0)
        
        json.dump({}, file)
        file.close()
        
        return get_guilds(bearer_token, access_code)
    
    bot_guilds_refresh = data.get("bot_guilds_refresh")
    bot_guilds_cache = data.get("bot_guilds")
    
    if bearer_token and access_code:
        user_guilds = get_user_guilds(bearer_token, access_code)
    
    if not (bot_guilds_cache or bot_guilds_refresh) or len(bot_guilds_cache) == 0 or time.time() - bot_guilds_refresh > DATA_REFRESH_DELAY:
        bot_guilds = bot_request("/users/@me/guilds")
        bot_guilds_dict = bot_guilds.json()
        
        if bot_guilds.status_code == 200:
            data["bot_guilds_refresh"] = time.time()
            data["bot_guilds"] = bot_guilds_dict
            
            for guild in bot_guilds_dict:
                guild.pop("features")
            
            file.seek(0)
            json.dump(data, file)
                
        if bearer_token and bot_guilds.status_code == 200:
            for index, guild in enumerate(bot_guilds_dict):
                if not guild in user_guilds:
                    bot_guilds_dict.pop(index)
                
        file.close()
        return bot_guilds_dict 
    else:
        if bearer_token:
            for index, guild in enumerate(bot_guilds_cache):
                if not guild in user_guilds:
                    bot_guilds_cache.pop(index)
                    
        file.close()
        return bot_guilds_cache

def get_guild(guild_id, bearer_token=None, access_code=None) -> dict | None:
    guilds = get_guilds(bearer_token, access_code)
    
    for guild in guilds:
        if guild.get("id") == str(guild_id):
            return guild

    return None

# API RESPONSES
def preflight_response():
    response = make_response()
    headers = response.headers
    
    headers.add("Access-Control-Allow-Origin", "*")
    headers.add('Access-Control-Allow-Headers', "*")
    headers.add('Access-Control-Allow-Methods', "*")
    
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

def identify_user(bearer_token: str) -> dict:
    response = requests.get(
        url = BASE_DISCORD_URL.format("/oauth2/@me"),
        headers = {
            "Authorization": "Bearer " + bearer_token,
            "Content-Type": "application/json"
        }
    )
    
    response.raise_for_status()
    return response.json()

def get_bearer(access_code: str) -> str | None:
    file = open("data/oauth_tokens.json", "r")
    data = json.load(file)
    
    user_data = data.get(access_code)
    if not user_data:
        return None
    else:
        return user_data["token"]["access_token"]

def get_bearer_from_code(oauth_code: str) -> str | None:
    file = open("data/oauth_tokens.json", "r")
    data = json.load(file)
    
    for access_code in data:
        authorization = data[access_code]
        auth_oauth_code = authorization["token"]["oauth_code"]
        
        if auth_oauth_code == oauth_code:
            return authorization["token"]["access_token"]
        
    return None

# DEV PANEL
def is_logged_in(cookies: dict) -> bool:
    file = open("data/panel_bearers.json")
    bearer_tokens = json.load(file)
    
    bearer_token = cookies.get("bearer_token")
    
    if not bearer_token:
        return False
    elif not bearer_token in bearer_tokens:
        return False
    else:
        return True

## -- ROUTES -- ##

@app.route("/api/save-settings", methods=["POST", "OPTIONS"])
@user_endpoint
def save_guild_settings():
    params = request.args
    form = request.form
    headers = request.headers
    
    guild_id = params.get("guild_id")
    access_code = headers.get("access-code")
    
    bearer_token = get_bearer(access_code)
    if not bearer_token:
        return {"message": "An error occurred, please try again later."}, 500
    if not guild_id:
        return {"message": "Missing guild ID"}, 400
    
    guild = get_guild(guild_id, bearer_token, access_code)
    guild_data = server_data_col.find_one({"guild_id": guild_id})
    
    if not guild:
        return {"message": "Invalid guild ID"}, 400
    elif guild and not guild_data:
        server_data_col.insert_one(functions.get_db_data(guild_id))
        return {"message": "An error occured, please try again."}, 500
    
    updated_settings = {}
    
    for argument in form:
        value = form.get(argument)
        
        if not (value or argument in guild_setting_names):
            continue
        elif guild_data[argument] == value:
            continue
        
        updated_settings[argument] = value
        
    server_data_col.update_one({"guild_id": str(guild_id)}, {"$set": updated_settings})
    
    if len(updated_settings) == 0:
        return {"message": "No settings were updated."}, 200
    else:
        return {"changed_settings": argument for argument in list(updated_settings.keys())}, 200


@app.route("/api/get-bot-guilds", methods=["GET", "OPTIONS"])
@api_endpoint
@limiter.exempt
def get_bot_guilds():
    bot_guilds = get_guilds()
    
    if type(bot_guilds) != list:
        try:
            bot_guilds = json.loads(bot_guilds)
        except Exception as error:
            logging.warning(bot_guilds)
            
            return {"message": "An error occurred, please try again later."}, 500
    
    return {"guilds": bot_guilds}, 200

@app.route("/api/get-user-guilds", methods=["GET", "OPTIONS"])
@user_endpoint
@limiter.exempt
def get_user_guilds_():
    headers = request.headers
    access_code = headers["oauth-code"]
    
    bearer_token = get_bearer(access_code)
    if not bearer_token:
        return {"message": "An error occurred, please try again later."}, 500
    
    user_guilds = get_user_guilds(bearer_token, access_code)
    
    if type(user_guilds) != list:
        try:
            user_guilds = json.loads(user_guilds)
        except Exception as error:
            logging.warning(user_guilds)
            
            return {"message": "An error occurred, please try again later."}, 500
    
    return {"guilds": user_guilds}, 200
    

@app.route("/api/get-guild-count", methods=["GET", "OPTIONS"])
@api_endpoint
@limiter.exempt
def get_guild_count():
    bot_guilds = get_guilds()
    
    if type(bot_guilds) != list:
        try:
            bot_guilds = json.loads(bot_guilds)
        except Exception as error:
            logging.warning(bot_guilds)
            
            return {"message": "An error occurred, please try again later."}, 500
    
    return {"guild_count": len(bot_guilds)}, 200

@app.route("/api/authorize", methods=["POST", "OPTIONS"])
def authorize():
    headers = request.headers
    oauth_code = headers.get("oauth-code")
    
    file = open("data/oauth_tokens.json", "r+")
    data = json.load(file)
    
    if not oauth_code:
        return {"message": "Missing OAuth code"}, 403
    elif oauth_code and get_bearer_from_code(oauth_code):
        return {"message": "You have already authorized"}, 200
    else:
        result, status = exchange_code(oauth_code)
        if status != 200:
            return result
        
        bearer_token = result.get("access_token")
        access_code = generate_random_string(random.randint(7, 10), random.randint(6, 9))
        
        to_pop = []
        for oauth_token in data:
            if data[oauth_token]["token"]["access_token"] == bearer_token:
                to_pop.append(oauth_token)
        
        for oauth_token in to_pop:
            data.pop(oauth_token)
        
        auth_info = identify_user(bearer_token)
        
        data[access_code] = {
            "token": result,
            "expires": auth_info["expires"],
            "user": auth_info["user"],
        }
        data[access_code]["token"]["oauth_code"] = oauth_code
        
        file.seek(0)
        json.dump(data, file)
        file.close()

        return {"message": "You have been authorized", "access_code": access_code}, 200
    
@app.route("/demo-login")
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


@app.route("/login")
@limiter.exempt
def panel_login():
    signed_in = is_logged_in(request.cookies)
    
    if signed_in:
        return redirect(url_for("dev_dashboard"))
    
    return render_template("login.html")

@app.route("/dev/login", methods=["POST", "OPTIONS"])
@limiter.exempt
def dev_login():
    headers = request.headers
    bearer_token = str(uuid4())
    signed_in = is_logged_in(request.cookies)
    
    if signed_in:
        return redirect(url_for("dev_dashboard"))
    
    if not headers.get("password"):
        return {"message": "Missing password"}, 400
    elif headers.get("password") != developer_password:
        return {"message": "Invalid password"}, 403
    
    file = open("data/panel_bearers.json", "r+")
    data = json.load(file)
    
    data.append(bearer_token)
    
    file.seek(0)
    json.dump(data, file)
    file.close()
    
    return {"bearer_token": bearer_token, "message": "You have been logged in."}, 200
    

@app.route("/dev/dashboard")
@limiter.exempt
def dev_dashboard():
    logged_in = is_logged_in(request.cookies)
    
    if not logged_in:
        return redirect(url_for("panel_login"))
    
    return render_template("dashboard.html")

@app.route("/dev/get-bot-data")
@limiter.exempt
def dev_bot_data():
    logged_in = is_logged_in(request.cookies)
    bot_guilds = get_guilds()
    
    if not logged_in:
        return {"message": "Please log in before accessing this endpoint."}, 403
    
    return {"guilds": bot_guilds, "guild_count": len(bot_guilds)}, 200
    
        

@app.route("/webhooks/bot-upvotes", methods=["POST", "OPTIONS"])
def bot_upvotes_webhook():
    data = request.json
    headers = request.headers
           
    if not headers.get("authorization") == "OutDashIsCool":
        return
    elif json["type"] == "test":
        print(data)
        return
           
    user_voted = data["user"]
    voted_bot = data["bot"]
           
    print(user_voted, voted_bot)
    
           

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
    return {"message": "Something went wrong (internally) while trying to process your request."}, 500

## -- START -- ##

def run_api():
    server = Thread(target=app.run, args=("127.0.0.1", 8080, ))
    server.run()

if __name__ == "__main__" and not config.is_server:
    run_api()
