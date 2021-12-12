## -- IMPORTANT -- ##

import asyncio
import os
import requests
import bot_info
import socket

from quart import Quart, request, redirect, render_template, url_for
from quart_discord import DiscordOAuth2Session, Unauthorized, requires_authorization, exceptions
from dotenv import load_dotenv
from discord.ext import ipc
# from ipc import ipc

## -- FUNCTIONS -- ##

API_ENDPOINT = 'https://discord.com/api/v9'
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")

## -- VARIABLES -- ##
load_dotenv()

class App(Quart):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = None
        # self.ipc = ipc.Client(host="localhost", port=int(os.environ.get("IPC_PORT")), secret_key=os.environ.get("IPC_KEY"))
        
app = App(__name__)
ipc_client = ipc.Client(secret_key = "Swas")

# ipc_client = ipc.Client(secret_key=b"%\xe0'\x01\xdeH\x8e\x85m|\xb3\xffCN\xc9g")

app.secret_key = "yay"
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "true"

app.config['SERVER_NAME'] = 'localhost:8080'
app.config["DISCORD_CLIENT_ID"] = os.environ.get("CLIENT_ID")
app.config["DISCORD_CLIENT_SECRET"] = str(os.environ.get("CLIENT_SECRET"))
app.config["DISCORD_REDIRECT_URI"] = "http://%s/callback" % app.config["SERVER_NAME"]
app.config["DISCORD_BOT_TOKEN"] = str(os.environ.get("TEST_BOT_TOKEN"))

discord = DiscordOAuth2Session(app)
HYPERLINK = '<a href="{}">{}</a>'

## -- FUNCTIONS -- ##

async def welcome_user(user):
    dm_channel = await discord.bot_request("/users/@me/channels", "POST", json={"recipient_id": user.id})
    return await discord.bot_request(
        f"/channels/{dm_channel['id']}/messages", "POST", json={"content": "Thanks for authorizing the app!"}
    )
    
async def get_guild(guild_id: int):
    return await discord.bot_request(
        route=f"/guilds{guild_id}",
        method="GET"
    )
    
async def get_guilds_with_permission():
    guilds = await discord.fetch_guilds()
    for g in guilds[:]:
        if not g.permissions.manage_guild:
            guilds.remove(g)
    
    return guilds

async def get_guild_with_permission(guild_id: int):
    guilds = await get_guilds_with_permission()
    
    for g in guilds[:]:
        if g.id == guild_id:
            return g
        
    return None

async def check_for_bot_in_server(guild_id: int):
    response = await discord.bot_request(
        route=f"/guilds/{guild_id}/members",
        method="GET"
    )
    print(response)
    for member in response:
        print(member.get("user").get("id"))
        if member.get("user").get("id") == os.environ.get("CLIENT_ID"): 
            return True
        else:
            print("no")
            
    # return False

## -- METHODS -- ##

@app.route('/test_button')
async def background_process_test():
    print("YO")
    return("nothing")

@app.route("/")
async def index():
	return await render_template("index.html", authorized = await discord.authorized)

    
@app.route('/servers', methods=['GET'])
@requires_authorization
async def servers():
    user = await discord.fetch_user()
    guilds = await get_guilds_with_permission()

    id, avatar, username, usertag = user.id, user.avatar_url, user.username, user.discriminator

    return await render_template('servers.html', render_avatar=avatar, render_username=f'{username}#{usertag}', render_guilds=guilds)

@app.route("/dashboard")
@requires_authorization
async def dashboard(): 

    guild_count = await app.ipc.request("get_guild_count")
    guild_ids = await app.ipc.request("get_guild_ids")

    user_guilds = await discord.fetch_guilds()

    guilds = []

    for guild in user_guilds:
        if guild.permissions.administrator:
            guild.class_color = "green-border" if guild.id in guild_ids else "red-border"
            guilds.append(guild)

    guilds.sort(key = lambda x: x.class_color == "red-border")
    name = (await discord.fetch_user()).name
    return await render_template("dashboard.html", guild_count = guild_count, guilds = guilds, username=name)


@app.route("/login")
async def login():
	return await discord.create_session(scope=["identify", "guilds", "email"])


@app.route("/dashboard/<int:guild_id>/")
@requires_authorization
async def server_dashboard(guild_id: int):
	guild = await ipc_client.request("get_guild", guild_id = guild_id)
	if guild is None:
		return redirect(f'https://discord.com/oauth2/authorize?&client_id={app.config["DISCORD_CLIENT_ID"]}&scope=bot&permissions=8&guild_id={guild_id}&response_type=code&redirect_uri={app.config["DISCORD_REDIRECT_URI"]}')
	return guild["name"]


@app.route("/invite-bot")
async def invite_bot():
    return await discord.create_session(scope=["bot"], permissions=os.environ.get("PERMISSIONS"), guild_id=859482895009579039, disable_guild_select=True)


@app.route("/invite-oauth")
async def invite_oauth():
    return await discord.create_session(scope=["bot", "identify"], permissions=8)


@app.route("/callback")
async def callback():
    try:
        data = await discord.callback()
        return redirect(data.get("redirect", "/"))
    except Exception as e:
        raise e


@app.route("/me/")
async def me():
    user = await discord.fetch_user()
    return f"""
    <html>
        <head>
            <title>{user.name}</title>
        </head>
        <body>
            <img src='{user.avatar_url or user.default_avatar_url}' />
            <p>Is avatar animated: {str(user.is_avatar_animated)}</p>
            <a href={url_for("my_connections")}>Connections</a>
            <br />
        </body>
    </html>
"""


@app.route("/me/guilds/")
async def get_permission_guilds():
    guilds = await discord.fetch_guilds()
        
    return "<br />".join([f"[SERVER MANAGER] {g.name}" if g.permissions.manage_guild else g.name for g in guilds])


@app.route("/add_to/<int:guild_id>/")
async def add_to_guild(guild_id):
    user = await discord.fetch_user()
    return await user.add_to_guild(guild_id)


@app.route("/me/connections/")
async def my_connections():
    user = await discord.fetch_user()
    connections = await discord.fetch_connections()
    return f"""
    <html>
        <head>
            <title>{user.name}</title>
        </head>
        <body>
            {str([f"{connection.name} - {connection.type}" for connection in connections])}
        </body>
    </html>
    """


@app.route("/logout/")
async def logout():
    discord.revoke()
    return redirect(url_for(".index"))


@app.route("/secret/")
@requires_authorization
async def secret():
    return os.urandom(16)


@app.errorhandler(Unauthorized)
async def redirect_unauthorized(e):
    return redirect(url_for("login"))

@app.errorhandler(exceptions.AccessDenied)
async def access_denied(e):
    return redirect(url_for("login"))


def import_bot(bot):
    app.bot = bot
    print("Bot received in app successfully.")

def setBotAttribute(bot):
    app.config["bot"] = bot

if __name__ == "__main__":
    app.run(debug=True, host="localhost", port=8080)