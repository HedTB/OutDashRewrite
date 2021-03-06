## -- IMPORTANT -- ##

import json
import os
import requests
import extra.config as config
import certifi
import disnake
import time
import flask_discord
import flask
#import uvicorn

from flask import Flask, request, redirect, render_template, url_for
from flask_cors import CORS, cross_origin
from flask_discord import DiscordOAuth2Session, Unauthorized, requires_authorization
from dotenv import load_dotenv
from threading import Thread
from waitress import serve
from pymongo import MongoClient
from functools import wraps
from disnake.ext import commands
#from fastapi import FastAPI, Header, Response, status, Query
#from typing import Optional, List

import extra.functions as functions

## -- FUNCTIONS -- ##

load_dotenv()

## -- VARIABLES -- ##

mongo_login = os.environ.get("MONGO_LOGIN")
api_key = os.environ.get("API_KEY")
bot_token = os.environ.get("BOT_TOKEN")
        
app = Flask(__name__, template_folder="templates")
#api_app = FastAPI()
CORS(app, support_credentials=True)

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

app.jinja_env.auto_reload = True
app.config["SECRET_KEY"] = api_key
app.config["CORS_HEADERS"] = "Content-Type"
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SERVER_NAME"] = "outdash-beta-alt.herokuapp.com"
app.config["DISCORD_CLIENT_ID"] = os.environ.get("CLIENT_ID")
app.config["DISCORD_CLIENT_SECRET"] = str(os.environ.get("CLIENT_SECRET"))
app.config["DISCORD_REDIRECT_URI"] = "https://%s/callback" % app.config["SERVER_NAME"]
app.config["DISCORD_BOT_TOKEN"] = str(os.environ.get("TEST_BOT_TOKEN"))

discord = DiscordOAuth2Session(app)

client = MongoClient(f"{mongo_login}",tlsCAFile=certifi.where())
db = client[config.database_collection]

server_data_col = db["server_data"]

argument_names = {
    "prefix": "prefix",
    "member_remove_logs_webhook": "member_remove_logs_webhook"
}
headers={"Authorization": f"Bot {bot_token}",
        "User-Agent": "myBotThing (http://some.url, v0.1)",
        "Content-Type": "application/json", }

## -- CHECKS -- ##

def requires_api_authorization(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        headers = request.headers

        if not headers.get("api-key"):
            return {"message": "Missing API Key"}, 403
        elif headers.get("api-key") != api_key:
            return {"message": "Invalid API Key"}, 403
            
        return f()
    return decorated_function
        

## -- FUNCTIONS -- ##

def guild_to_dict(guild: disnake.Guild):
    guild_dict = dict()

    guild_dict["id"] = guild.id
    guild_dict["name"] = guild.name
    guild_dict["icon"] = str(guild.icon)

    return json.dumps(guild_dict)

def api_request(endpoint, params=None):
    return requests.get(
        url=f"https://outdash.ga/api/{endpoint}",
        headers={"api-key": api_key},
        params=params
    )

def message_user(user, message: str):
    dm_channel = discord.bot_request("/users/@me/channels", "POST", json={"recipient_id": user.id})
    return discord.bot_request(
        f"/channels/{dm_channel['id']}/messages", "POST", json={"content": message}
    )
def get_guilds():
    return requests.get(
        url="https://discordapp.com/api/v9/users/@me/guilds",
        headers=headers,
    )
def get_guild(guild_id):
    return requests.get(
        url=f"https://discordapp.com/api/v9/guilds/{guild_id}",
        headers=headers,
    )
    
def get_guilds_with_permission():
    guilds = discord.fetch_guilds()
    for g in guilds[:]:
        if not g.permissions.administrator:
            guilds.remove(g)
    
    return guilds

def get_guild_with_permission(guild_id: int):
    guilds = get_guilds_with_permission()

    for g in guilds[:]:
        if g.id == guild_id:
            return g
    
    return None

def check_permissions(guild_id: int):
    user = discord.fetch_user()

    if user.id in config.owners:
        return True
    if get_guild_with_permission(guild_id):
        return True

    return False

## -- METHODS -- ##

server = Thread(target=app.run, args=("0.0.0.0", 8080,))

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Access-Control-Allow-Headers,Origin,Accept,X-Requested-With,Content-Type,Access-Control-Request-Method,Access-Control-Request-Headers')
    return response

@app.route("/api/save-settings", methods=["POST"])
@requires_api_authorization
@cross_origin(supports_credentials=True)
def save_guild_settings():
    arguments = request.args

    guild_id = arguments.get("guild_id")
    guild = get_guild(guild_id).json()
    update_values = {}
    query = {"guild_id": str(guild_id)}

    if not guild_id:
        return {"message": "Missing guild ID"}, 400
    elif not guild:
        return {"message": "Invalid guild ID"}, 400

    for argument in arguments:
        value = arguments.get(argument)
        if argument == "guild_id" or not argument in argument_names:
            continue
            
        argument_name = argument_names[argument]
        update_values[argument_name] = value

    server_data_col.update_one(query, {"$set": update_values})
    return {"changed_settings": argument_name for argument_name in list(update_values.keys())}

@app.route("/api/get-bot-guilds", methods=["GET", "OPTIONS"])
@requires_api_authorization
@cross_origin(supports_credentials=True)
def get_bot_guilds():
    bot_guilds = get_guilds()

    return bot_guilds.text, 200

@app.route("/api/get-guild-count")
@requires_api_authorization
@cross_origin(supports_credentials=True)
def get_guild_count():
    bot_guilds = get_guilds().json()

    return {"guild_count": len(bot_guilds)}, 200


@app.route("/")
def index():
    return {"message": "hey"}, 200
    #return render_template("index.html", authorized = discord.authorized)

"""
@app.route("/dashboard")
@requires_authorization
def dashboard():
    bot_guilds = get_guilds().json()

    guild_count = len(bot_guilds)
    guild_ids = []

    for guild in bot_guilds:
        guild_ids.append(guild.get("id"))

    user_guilds = discord.fetch_guilds()
    user = discord.fetch_user()

    guilds = []

    for guild in user_guilds:
        if guild.permissions.administrator:
            guild.class_color = "green-border" if guild.id in guild_ids else "red-border"
            guilds.append(guild)

    guilds.sort(key = lambda x: x.class_color == "red-border")
    name = user.name
    
    return render_template("dashboard_list.html", guild_count=guild_count, guilds=guilds, username=name)


@app.route("/login")
def login():
    return discord.create_session(scope=["identify", "guilds"])


@app.route("/dashboard/<int:guild_id>/")
@requires_authorization
def server_dashboard(guild_id: int):
    user = discord.fetch_user()
    guild = get_guild(guild_id).json()
    can_enter_dashboard = check_permissions(guild_id)

    result = server_data_col.find_one({"guild_id": str(guild_id)})

    if not can_enter_dashboard:
        return "You don't have permission to access this dashboard."
    if not guild:
        return discord.create_session(scope=["bot"], permissions=int(os.environ.get("PERMISSIONS")), guild_id=guild_id)

    prefix = result.get("prefix")
    return render_template("dashboard.html", guild=guild, prefix=prefix)

@app.route("/invite-bot/<int:guild_id>")
def invite_bot(guild_id):
    return discord.create_session(scope=["bot"], permissions=int(os.environ.get("PERMISSIONS")), guild_id=guild_id, disable_guild_select=True)


@app.route("/invite-oauth")
def invite_oauth():
    return discord.create_session(scope=["bot", "identify"], permissions=8)


@app.route("/callback")
def callback():
    try:
        data = discord.callback()
        print(data.get("redirect"))
        return redirect(data.get("redirect", "/dashboard"))
    except Exception as e:
        return redirect("/login")


@app.route("/me/")
def me():
    user = discord.fetch_user()
    return f""
    <html>
        <head>
            <title>{user.name}</title>
        </head>
        <body>
            <img src="{user.avatar_url or user.default_avatar_url}" />
            <p>Is avatar animated: {str(user.is_avatar_animated)}</p>
            <a href={url_for("my_connections")}>Connections</a>
            <a href={url_for("get_permission_guilds")}>Guilds</a>
            <br />
        </body>
    </html>
""


@app.route("/me/guilds/")
def get_permission_guilds():
    guilds = discord.fetch_guilds()
        
    return "<br />".join([f"[SERVER MANAGER] {g.name}" if g.permissions.manage_guild else g.name for g in guilds])


@app.route("/add_to/<int:guild_id>/")
def add_to_guild(guild_id):
    user = discord.fetch_user()
    return user.add_to_guild(guild_id)


@app.route("/me/connections/")
def my_connections():
    user = discord.fetch_user()
    connections = discord.fetch_connections()

    return f""
    <html>
        <head>
            <title>{user.name}</title>
        </head>
        <body>
            {str([f"{connection.name} - {connection.type}" for connection in connections])}
        </body>
    </html>
    ""


@app.route("/logout/")
def logout():
    discord.revoke()
    return redirect(url_for("index"))


@app.route("/secret/")
@requires_authorization
def secret():
    return os.urandom(16)
"""

@app.errorhandler(Unauthorized)
def redirect_unauthorized(e):
    return redirect(url_for("login"))

@app.errorhandler(flask_discord.exceptions.AccessDenied)
def access_denied(e):
    return redirect(url_for("login"))

#server.run()
#uvicorn.run("app:api_app", host="0.0.0.0", port=8080, log_level="info", reload=False)
#serve(app=app, host="0.0.0.0", port=8080)

"""
def run_website(bot):
    if not bot:
        raise Exception("You have to assign the bot to run the website.")

    server = Thread(target=run, args=(bot, ))
    server.start()

if __name__ == "__main__":
    run_website(None)
"""
