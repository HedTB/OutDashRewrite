import os
from flask import Flask, request, redirect, render_template, url_for
# from routes.discord_oauth import DiscordOauth
from flask_discord import DiscordOAuth2Session, requires_authorization, Unauthorized

app = Flask(__name__)

app.secret_key = b"%\xe0'\x01\xdeH\x8e\x85m|\xb3\xffCN\xc9g"
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "true"

app.config['SERVER_NAME'] = 'domain.com'
app.config["DISCORD_CLIENT_ID"] = 844937957185159198
app.config["DISCORD_CLIENT_SECRET"] = str(os.getenv("CLIENT_SECRET"))
app.config["DISCORD_REDIRECT_URI"] = "http://127.0.0.1:5000/callback"
app.config["DISCORD_BOT_TOKEN"] = str(os.getenv("TEST_BOT_TOKEN"))

discord = DiscordOAuth2Session(app)
HYPERLINK = '<a href="{}">{}</a>'

"""
@app.route("/login/")
def login():
    return discord.create_session()
	

@app.route("/callback/")
def callback():
    discord.callback()
    return redirect(url_for(".me"))

@app.route("/me/")
@requires_authorization
def me():
    user = discord.fetch_user()
    return f
    <html>
        <head>
            <title>{user.name}</title>
        </head>
        <body>
            <img src='{user.avatar_url}' />
        </body>
    </html>
    
    # return render_template('dashboard.html', render_user_avatar=user.avatar_url,
    #                        render_username=f'{user.username}#{user.discriminator}', render_guild=discord.fetch_guilds())


@app.errorhandler(Unauthorized)
def redirect_unauthorized(e):
    return redirect(url_for("login"))


# Route for dashboard
@app.route('/', methods=['GET'])
def dashboard():

    code = request.args.get('code')
    access_token = DiscordOauth.get_access_token(code)
    if not access_token:
        return redirect(DiscordOauth.login_url)

    user_object = DiscordOauth.get_user(access_token)
    user_guild_object = DiscordOauth.get_user_current_guild(access_token)

    id, avatar, username, usertag = user_object.get('id'), user_object.get('avatar'), user_object.get('username'), \
                                    user_object.get('discriminator')

    return render_template('dashboard.html', render_user_avatar=f'https://cdn.discordapp.com/avatars/{id}/{avatar}.png',
                           render_username=f'{username}#{usertag}', render_guild=user_guild_object)
    
    
@app.route('/test_button')
def background_process_test():
    print("YO")
    return("nothing")
"""


def welcome_user(user):
    dm_channel = discord.bot_request("/users/@me/channels", "POST", json={"recipient_id": user.id})
    return discord.bot_request(
        f"/channels/{dm_channel['id']}/messages", "POST", json={"content": "Thanks for authorizing the app!"}
    )


@app.route("/")
def index():
    if not discord.authorized:
        return f"""
        {HYPERLINK.format(url_for(".login"), "Login")} <br />
        {HYPERLINK.format(url_for(".login_with_data"), "Login with custom data")} <br />
        {HYPERLINK.format(url_for(".invite_bot"), "Invite Bot with permissions 8")} <br />
        {HYPERLINK.format(url_for(".invite_oauth"), "Authorize with oauth and bot invite")}
        """

    return f"""
    {HYPERLINK.format(url_for(".me"), "@ME")}<br />
    {HYPERLINK.format(url_for(".logout"), "Logout")}<br />
    {HYPERLINK.format(url_for(".user_guilds"), "My Servers")}<br />
    {HYPERLINK.format(url_for(".add_to_guild", guild_id=475549041741135881), "Add me to 475549041741135881.")}    
    """


@app.route("/login/")
def login():
    return discord.create_session()


@app.route("/login-data/")
def login_with_data():
    return discord.create_session(data=dict(redirect="/me/", coupon="15off", number=15, zero=0, status=False))


@app.route("/invite-bot/")
def invite_bot():
    return discord.create_session(scope=["bot"], permissions=8, guild_id=464488012328468480, disable_guild_select=True)


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
def user_guilds():
    guilds = discord.fetch_guilds()
    return "<br />".join([f"[ADMIN] {g.name}" if g.permissions.administrator else g.name for g in guilds])


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