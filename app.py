## -- IMPORTS -- ##

import os
import certifi
import requests
import logging

from pymongo import MongoClient
from dotenv import load_dotenv
from flask import Flask, request
from functools import wraps
from flask_cors import CORS, cross_origin
from threading import Thread

# FILES
from extra import config
from extra import functions

## -- SETUP -- ##

load_dotenv()

## -- VARIABLES -- ##

mongo_token = os.environ.get("MONGO_LOGIN")
bot_token = os.environ.get("BOT_TOKEN" if config.is_server else "TEST_BOT_TOKEN")
api_key = os.environ.get("API_KEY")

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}}, send_wildcard=True, origins="*")

logging.getLogger("flask_cors").level = logging.DEBUG

app.config["CORS_HEADERS"] = "Content-Type"

client = MongoClient(mongo_token, tlsCAFile=certifi.where())
db = client[config.database_collection]

server_data_col = db["server_data_col"]

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

def requires_api_authorization(f):
    @wraps(f)
    
    def decorated_function(*args, **kwargs):
        headers = request.headers
        
        if not headers.get("api-key"):
            return {"message": "Missing API key"}, 403
        elif headers.get("api-key") != api_key:
            return {"message": "Invalid API key"}, 403
        
        return f()
    return decorated_function

## -- FUNCTIONS -- ##

def bot_request(endpoint, params=None):
    return requests.get(
        url = f"https://discordapp.com/api/v9/{endpoint}",
        headers = request_headers,
        params = params
    )
    
def get_guilds():
    return bot_request("users/@me/guilds")

def get_guild(guild_id):
    return bot_request(f"guilds/{guild_id}")

## -- ROUTES -- ##

@app.route("/api/save-settings", methods=["POST", "OPTIONS"])
@requires_api_authorization
@cross_origin()
def save_guild_settings():
    guild_id = request.args.get("guild_id")
    form = request.form
    
    guild = get_guild(guild_id).json()
    guild_data = server_data_col.find_one({"guild_id": str(guild_id)})
    
    if not guild_data:
        server_data_col.insert_one(functions.get_db_data(guild_id))
        return {"message": "An error occured, please try again."}, 500
    
    updated_settings = {}

    if not guild_id:
        return {"message": "Missing guild ID"}, 400
    elif not guild:
        return {"message": "Invalid guild ID"}, 400
    
    for argument in form:
        value = form.get(argument)
        
        if not (value or argument in guild_setting_names):
            continue
        elif guild_data[argument] == value:
            continue
        
        updated_settings[argument] = value
        
    server_data_col.update_one({"guild_id": str(guild_id)}, {"$set": updated_settings})
    return {"changed_settings": argument_name for argument_name in list(updated_settings.keys())}


@app.route("/api/get-bot-guilds", methods=["GET", "OPTIONS"])
@requires_api_authorization
@cross_origin()
def get_bot_guilds():
    bot_guilds = get_guilds()
    
    return {"guilds": bot_guilds.text}, 200


@app.route("/api/get-guild-count", methods=["GET", "OPTIONS"])
@requires_api_authorization
#@cross_origin()
def get_guild_count():
    bot_guilds = get_guilds().json()
    
    return {"guild_count": len(bot_guilds)}, 200

@app.route("/")
@cross_origin()
def index():
    return {"message": "Seems like you have found the API page for OutDash. Well, there's nothing you can do here, so you may aswell just exit this page and move on :)"}
    

## -- EXTRA METHODS -- ##

"""
@app.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    #response.headers.add("Access-Control-Allow-Origin", "Access-Control-Allow-Headers,Origin,Accept,X-Requested-With,Content-Type,Access-Control-Request-Method,Access-Control-Request-Headers")
    
    return response
"""

## -- START -- ##

def run_api():
    server = Thread(target=app.run, args=("127.0.0.1", 8080, ))
    server.run()

if __name__ == "__main__" and not config.is_server:
    run_api()
