## -- IMPORTANT -- ##

import asyncio
import os
import requests

from quart import Quart, request, redirect, render_template, url_for
from quart_discord import DiscordOAuth2Session, Unauthorized, requires_authorization, exceptions
from dotenv import load_dotenv
from discord.ext import ipc

from main import export_bot

## -- VARIABLES -- ##

app = Quart(__name__)
# ipc_client = ipc.Client(secret_key=b"%\xe0'\x01\xdeH\x8e\x85m|\xb3\xffCN\xc9g")

load_dotenv()

app.secret_key = b"%\xe0'\x01\xdeH\x8e\x85m|\xb3\xffCN\xc9g"
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "false"

app.config['SERVER_NAME'] = 'outdash-test-bot.herokuapp.com'
app.config["DISCORD_CLIENT_ID"] = os.environ.get("CLIENT_ID")
app.config["DISCORD_CLIENT_SECRET"] = str(os.environ.get("CLIENT_SECRET"))
app.config["DISCORD_REDIRECT_URI"] = "https://%s/callback" % app.config["SERVER_NAME"]
app.config["DISCORD_BOT_TOKEN"] = str(os.environ.get("TEST_BOT_TOKEN"))

discord = DiscordOAuth2Session(app)
HYPERLINK = '<a href="{}">{}</a>'

## -- FUNCTIONS -- ##

async def welcome_user(user):
    dm_channel = await discord.bot_request("/users/@me/channels", "POST", json={"recipient_id": user.id})
    return await discord.bot_request(
        f"/channels/{dm_channel['id']}/messages", "POST", json={"content": "Thanks for authorizing the app!"}
    )
    
async def get_guilds_with_permission():
    guilds = await discord.fetch_guilds()
    for g in guilds[:]:
        if not g.permissions.manage_guild:
            guilds.remove(g)
    
    return guilds

async def get_guild(guild_id: int):
    guilds = await get_guilds_with_permission()
    
    for g in guilds[:]:
        if g.id == guild_id:
            return g
        
    return None

## -- METHODS -- ##

@app.route('/test_button')
async def background_process_test():
    print("YO")
    return("nothing")

@app.route("/")
async def index():
    user = await discord.fetch_user()
    id, avatar, username, usertag = user.id, user.avatar_url, user.username, user.discriminator
    
    if not await discord.authorized:
        return f"""
        {HYPERLINK.format(url_for(".login"), "Login")} <br />
        {HYPERLINK.format(url_for(".login_with_data"), "Login with custom data")} <br />
        {HYPERLINK.format(url_for(".invite_bot"), "Invite Bot with permissions 8")} <br />
        {HYPERLINK.format(url_for(".invite_oauth"), "Authorize with oauth and bot invite")}
        """
    
    guilds = await get_guilds_with_permission()
    
    # print(hasattr(app, "bot"))
    # print(app.bot.get_guild(836495137651294258))
    # print(app.bot.users)

    return await render_template('servers.html', render_avatar=avatar, render_username=f'{username}#{usertag}', render_guilds=guilds)

    
@app.route('/servers', methods=['GET'])
async def dashboard():

    user = await discord.fetch_user()
    guilds = await get_guilds_with_permission()

    id, avatar, username, usertag = user.id, user.avatar_url, user.username, user.discriminator

    return await render_template('servers.html', render_avatar=avatar, render_username=f'{username}#{usertag}', render_guilds=guilds)


@app.route("/login/")
async def login():
    return await discord.create_session(scope=["identify", "guilds", "email"])


@app.route("/dashboard/<int:guild_id>/")
async def server_dashboard(guild_id: int):
    
    # member_count = await ipc_client.request(
    #     "get_member_count", guild_id=guild_id
    # )
    bot = export_bot()
    print(bot)
    guild = bot.get_guild(guild_id)
    
    return str(guild.name)


@app.route("/invite-bot/")
async def invite_bot():
    return await discord.create_session(scope=["bot"], permissions=8, guild_id=859482895009579039, disable_guild_select=True)


@app.route("/invite-oauth/")
async def invite_oauth():
    return await discord.create_session(scope=["bot", "identify"], permissions=8)


@app.route("/callback/")
async def callback():
    data = await discord.callback()
    redirect_to = data.get("redirect", "/")

    return redirect(redirect_to)


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
    
async def start_app():
    return
    # await ipc_client.init_sock()

if __name__ == "__main__":
    app.run(debug=True, host="localhost", port=8080)