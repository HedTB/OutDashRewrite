## -- IMPORTANT -- ##

import os
import requests

from flask import Flask, request, redirect, render_template, url_for
from flask_discord import DiscordOAuth2Session, Unauthorized, requires_authorization
from dotenv import load_dotenv

## -- VARIABLES -- ##

app = Flask(__name__)
load_dotenv()

app.secret_key = b"%\xe0'\x01\xdeH\x8e\x85m|\xb3\xffCN\xc9g"
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "true"

app.config['SERVER_NAME'] = 'outdash-test-bot.herokuapp.com'
app.config["DISCORD_CLIENT_ID"] = 844937957185159198
app.config["DISCORD_CLIENT_SECRET"] = str(os.environ.get("CLIENT_SECRET"))
app.config["DISCORD_REDIRECT_URI"] = "https://outdash-test-bot.herokuapp.com/callback"
app.config["DISCORD_BOT_TOKEN"] = str(os.environ.get("TEST_BOT_TOKEN"))

discord = DiscordOAuth2Session(app)
HYPERLINK = '<a href="{}">{}</a>'

## -- FUNCTIONS -- ##

def welcome_user(user):
    dm_channel = discord.bot_request("/users/@me/channels", "POST", json={"recipient_id": user.id})
    return discord.bot_request(
        f"/channels/{dm_channel['id']}/messages", "POST", json={"content": "Thanks for authorizing the app!"}
    )
def get_guilds_with_permission():
    guilds = discord.fetch_guilds()
    for g in guilds:
        if not g.permissions.manage_guild:
            guilds.pop(g)
    
    return guilds

## -- METHODS -- ##

@app.route('/test_button')
def background_process_test():
    print("YO")
    return("nothing")

@app.route("/")
def index():
    user = discord.fetch_user()

    id, avatar, username, usertag = user.id, user.avatar_url, user.username, user.discriminator
    
    if not discord.authorized:
        return f"""
        {HYPERLINK.format(url_for(".login"), "Login")} <br />
        {HYPERLINK.format(url_for(".login_with_data"), "Login with custom data")} <br />
        {HYPERLINK.format(url_for(".invite_bot"), "Invite Bot with permissions 8")} <br />
        {HYPERLINK.format(url_for(".invite_oauth"), "Authorize with oauth and bot invite")}
        """
    
    access_token = discord.get_authorization_token().get("access_token")
    guilds = get_guilds_with_permission()

    return render_template('servers.html', render_avatar=avatar, render_username=f'{username}#{usertag}', render_guilds=guilds)

    
@app.route('/servers', methods=['GET'])
def dashboard():
    if not discord.authorized:
        return discord.create_session()

    user = discord.fetch_user()
    guilds = discord.fetch_guilds()

    id, avatar, username, usertag = user.id, user.avatar_url, user.username, user.discriminator

    return render_template('servers.html', render_avatar=avatar, render_username=f'{username}#{usertag}', render_guilds=guilds) 


@app.route("/login/")
def login():
    return discord.create_session()


@app.route("/login-data/")
def login_with_data():
    return discord.create_session(data=dict(redirect="/me/", coupon="15off", number=15, zero=0, status=False))


@app.route("/invite-bot/")
def invite_bot():
    return discord.create_session(scope=["bot"], permissions=8, guild_id=859482895009579039, disable_guild_select=True)


@app.route("/invite-oauth/")
def invite_oauth():
    return discord.create_session(scope=["bot", "identify"], permissions=8)


@app.route("/callback/")
def callback():
    data = discord.callback()
    redirect_to = data.get("redirect", "/")

    user = discord.fetch_user()
    welcome_user(user)

    return redirect(redirect_to)


@app.route("/me/")
def me():
    user = discord.fetch_user()
    return f"""
<html>
<head>
<title>{user.name}</title>
</head>
<body><img src='{user.avatar_url or user.default_avatar_url}' />
<p>Is avatar animated: {str(user.is_avatar_animated)}</p>
<a href={url_for("my_connections")}>Connections</a>
<br />
</body>
</html>
"""


@app.route("/me/guilds/")
def get_permission_guilds():
    guilds = discord.fetch_guilds()
    for g in guilds:
        has_permission = g.permissions.manage_guild
        print(has_permission)
        
    # return str.join([f"[SERVER MANAGER] {g.name}" if g.permissions.manage_guild else None for g in guilds])


@app.route("/add_to/<int:guild_id>/")
def add_to_guild(guild_id):
    user = discord.fetch_user()
    return user.add_to_guild(guild_id)


@app.route("/me/connections/")
def my_connections():
    user = discord.fetch_user()
    connections = discord.fetch_connections()
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
def logout():
    discord.revoke()
    return redirect(url_for(".index"))


@app.route("/secret/")
@requires_authorization
def secret():
    return os.urandom(16)


@app.errorhandler(Unauthorized)
def redirect_unauthorized(e):
    return redirect(url_for("login"))



if __name__ == '__main__':
    # from waitress import serve
    # serve(app, host="0.0.0.0", port=5000)
    app.run(debug=False)