## -- IMPORTS -- ##

import json
import logging
import os
import certifi
import requests
import time

from pymongo import MongoClient
from dotenv import load_dotenv
from flask import Flask, make_response, request, jsonify
from functools import wraps
from flask_cors import CORS, cross_origin
from threading import Thread
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# FILES
from extra import config
from extra import functions

## -- SETUP -- ##

load_dotenv()

## -- VARIABLES -- ##

# SECRETS
mongo_token = os.environ.get("MONGO_LOGIN")
bot_token = os.environ.get("BOT_TOKEN" if config.is_server else "TEST_BOT_TOKEN")
api_key = os.environ.get("API_KEY")

# APP VARIABLES
app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}}, send_wildcard=True, origins="*")

# APP CONFIG
app.config["CORS_HEADERS"] = "Content-Type"

# OTHER VARIABLES
# limiter = Limiter(
#     app=app,
#     key_func=get_remote_address,
#     default_limits=["2/second"]
# )

# DATABASE VARIABLES
client = MongoClient(mongo_token, tlsCAFile=certifi.where())
db = client[config.database_collection]

server_data_col = db["server_data"]

guild_setting_names = [
    "prefix", "message_delete_logs_webhook", "message_edit_logs_webhook",
    "message_bulk_delete_logs_webhook"
]
request_headers = {
    "Authorization": "Bot " + bot_token,
    "User-Agent": "myBotThing (http://some.url, v0.1)",
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

## -- FUNCTIONS -- ##

def bot_request(endpoint, params=None) -> requests.Response:
    return requests.get(
        url = f"https://discordapp.com/api/v9/{endpoint}",
        headers = request_headers,
        params = params
    )
    
def get_guilds():
    file = open("data/api.json", "r")
    data = json.load(file)
    
    bot_guilds_refresh = data.get("bot_guilds_refresh")
    bot_guilds = data.get("bot_guilds")
    
    if len(bot_guilds) == 0 or time.time() - bot_guilds_refresh > 180:
        result = bot_request("users/@me/guilds")
        
        if result.status_code == 200:
            with open("data/api.json", "w") as file:
                json.dump({
                    "bot_guilds_refresh": time.time(),
                    "bot_guilds": result.json()
                }, file, indent=4)
            
        file.close()
        return result.json()
    else:
        file.close()
        return bot_guilds

def get_guild(guild_id):
    guilds = get_guilds()
    
    for guild in guilds:
        if guild.get("id") == str(guild_id):
            return guild

    return None

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

## -- ROUTES -- ##

@app.route("/api/save-settings", methods=["POST", "OPTIONS"])
@api_endpoint
def save_guild_settings():
    guild_id = request.args.get("guild_id")
    form = request.form

    if not guild_id:
        return jsonify({"message": "Missing guild ID"}), 400
    
    guild = get_guild(guild_id)
    guild_data = server_data_col.find_one({"guild_id": str(guild_id)})
    
    if not guild:
        return jsonify({"message": "Invalid guild ID"}), 400
    elif guild and not guild_data:
        server_data_col.insert_one(functions.get_db_data(guild_id))
        return jsonify({"message": "An error occured, please try again."}), 500
    
    updated_settings = {}
    
    for argument in form:
        value = form.get(argument)
        
        if not (value or argument in guild_setting_names):
            continue
        elif guild_data[argument] == value:
            continue
        
        updated_settings[argument] = value
        
    server_data_col.update_one({"guild_id": str(guild_id)}, {"$set": updated_settings})
    return jsonify({"changed_settings": argument_name for argument_name in list(updated_settings.keys())}), 200


@app.route("/api/get-bot-guilds", methods=["GET", "OPTIONS"])
@api_endpoint
def get_bot_guilds():
    bot_guilds = get_guilds()
    
    if type(bot_guilds) != list:
        try:
            bot_guilds = json.loads(bot_guilds)
        except Exception as error:
            logging.warning(bot_guilds)
            
            return {"message": "An error occurred, please try again later."}
    
    return {"guilds": bot_guilds}, 200


@app.route("/api/get-guild-count", methods=["GET", "OPTIONS"])
@api_endpoint
def get_guild_count():
    bot_guilds = get_guilds()
    
    if type(bot_guilds) != list:
        try:
            bot_guilds = json.loads(bot_guilds)
        except Exception as error:
            logging.warning(bot_guilds)
            
            return {"message": "An error occurred, please try again later."}
    
    return {"guild_count": len(bot_guilds)}, 200

@app.route("/")
@cross_origin()
def index():
    return {"message": "Seems like you have found the API for OutDash. Well, there's nothing you can really do here, so you may aswell just exit this page and move on :)"}
    

## -- EXTRA METHODS -- ##



## -- START -- ##

def run_api():
    server = Thread(target=app.run, args=("127.0.0.1", 8080, ))
    server.run()

if __name__ == "__main__" and not config.is_server:
    run_api()
