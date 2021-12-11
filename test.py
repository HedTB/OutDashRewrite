## -- IMPORTING -- ##

# MODULES
import discord
import os
import random
import asyncio
import datetime
import certifi
import flask
import requests

from discord.ext import commands
from pymongo import MongoClient
from dotenv import load_dotenv
from quart import Quart, request, redirect, render_template, url_for
from quart_discord import DiscordOAuth2Session, Unauthorized, requires_authorization, exceptions


# FILES
import bot_info


## -- VARIABLES / FUNCTIONS -- ##
load_dotenv()

API_ENDPOINT = 'https://discord.com/api/v9'
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")

# TOKENS
bot_token = str(os.environ.get("TEST_BOT_TOKEN"))
mongo_token = os.environ.get("MONGO_LOGIN")


# APP
class App(Quart):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = None
        
app = App(__name__)

app.secret_key = b"%\xe0'\x01\xdeH\x8e\x85m|\xb3\xffCN\xc9g"
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "false"

app.config['SERVER_NAME'] = 'outdash-test-bot.herokuapp.com'
app.config["DISCORD_CLIENT_ID"] = os.environ.get("CLIENT_ID")
app.config["DISCORD_CLIENT_SECRET"] = str(os.environ.get("CLIENT_SECRET"))
app.config["DISCORD_REDIRECT_URI"] = "https://%s/callback" % app.config["SERVER_NAME"]
app.config["DISCORD_BOT_TOKEN"] = bot_token

discord2 = DiscordOAuth2Session(app)
HYPERLINK = '<a href="{}">{}</a>'


# DATABASE VARIABLES
client = MongoClient(f"{mongo_token}", tlsCAFile=certifi.where())
db = client["db2"]

prefixes_col = db["prefixes"]
confirmations_col = db["bot_farm_confirmations"]


# IMPORTANT FUNCTIONS
def get_prefix(bot, message):
    
    query = {"guild_id": str(message.guild.id)}
    data = {"guild_id": str(message.guild.id), f"prefix": "?"}
    result = prefixes_col.find_one(query)
    
    try:
        if result["prefix"] == None:
            prefixes_col.insert_one(data)
        
        return commands.when_mentioned_or(*result["prefix"])(bot, message)
    
    except TypeError:
        prefixes_col.insert_one(data)
        result = prefixes_col.find_one(query)
    
        return commands.when_mentioned_or(*result["prefix"])(bot, message)
    
def load_cogs():
    for foldername in os.listdir("./cogs"):
        for filename in os.listdir(f"./cogs/{foldername}"):
            if filename.endswith(".py"):
                # try:
                bot.load_extension(f"cogs.{foldername}.{filename[:-3]}")
                """
                except Exception as e:
                    print(e)
                    return
                """
                
def unload_cogs():
    for foldername in os.listdir("./cogs"):
        for filename in os.listdir(f"./cogs/{foldername}"):
            if filename.endswith(".py"):
                # try:
                bot.unload_extension(f"cogs.{foldername}.{filename[:-3]}")
                """
                except Exception as e:
                    print(e)
                    return
                """

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

# BOT
class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ready = False
        # self.ipc = ipc.Server(self, secret_key=b"%\xe0'\x01\xdeH\x8e\x85m|\xb3\xffCN\xc9g")
        # self.loop.create_task(self.start_app())
        
    async def on_ready(self):
        self.ready = True
        
        status_channel = bot.get_channel(bot_info.messages_channel)
        embed = discord.Embed(title=f"Singed In As: {bot.user.name} ({bot.user.id})", 
                            description=f"Bot started in `{str(len(bot.guilds))}` server(s), with total of `{len(bot.users)}` member(s), on an average latency of `{round(bot.latency * 1000)} ms`.", 
                            color=bot_info.success_embed_color)
        
        await status_channel.send(embed=embed)

        print(f"Signed In As: {bot.user.name} ({bot.user.id})")
        print(f"Bot started in {len(bot.guilds)} server(s), with {len(bot.users)} total members.")
        
    async def start_app(self):
        await self.wait_until_ready()
        app.run("localhost", port=5000)
          
      
bot = Bot(command_prefix=get_prefix, intents=discord.Intents.all(), status=discord.Status.idle, activity=discord.Game(name="booting up.."), case_insensitive=True)
#bot.remove_command("help")


# OTHER
activities = ['Minecraft | ?help', f'in {len(bot.guilds)} servers | ?help', 'Roblox | ?help', f'with {len(bot.users)} users | ?help']


# IPC
# @bot.ipc.route(name="check_for_bot_in_server")
# async def check_for_bot_in_server(data):
#     print(data)
#     guild = bot.get_guild(data.guild_id)
    
#     if guild:
#         return guild
#     else:
#         return None


## -- LOOPS -- ##

async def bot_loop():
    
    await bot.wait_until_ready()
    load_cogs()
    await asyncio.sleep(5)
    
    while not bot.is_closed():
        activity = random.choice(activities)
        
        await bot.change_presence(activity=discord.Game(name=activity), status=discord.Status.online)
        await asyncio.sleep(15)
        
        
## -- COGS -- ##

@bot.command()
async def reloadcogs(ctx):
    
    id = int(ctx.author.id)
    if id in bot_info.owners:
        unload_cogs()
        load_cogs()
        embed = discord.Embed(description="Reloaded all cogs successfully.", color=bot_info.success_embed_color)
        await ctx.send(embed=embed)
        
@bot.command()
async def loadcogs(ctx):
    
    id = int(ctx.author.id)
    if id in bot_info.owners:
        load_cogs()
        embed = discord.Embed(description="Loaded all cogs successfully.", color=bot_info.success_embed_color)
        await ctx.send(embed=embed)
        
@bot.command()
async def unloadcogs(ctx):
    
    id = int(ctx.author.id)
    if id in bot_info.owners:
        unload_cogs()
        embed = discord.Embed(description="Unloaded all cogs successfully.", color=bot_info.success_embed_color)
        await ctx.send(embed=embed)
        

## -- APP -- ##

@app.route('/test_button')
async def background_process_test():
    print("YO")
    return("nothing")

@app.route("/")
async def index():
    user = await discord2.fetch_user()
    id, avatar, username, usertag = user.id, user.avatar_url, user.username, user.discriminator
    
    if not await discord2.authorized:
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

    user = await discord2.fetch_user()
    guilds = await get_guilds_with_permission()

    id, avatar, username, usertag = user.id, user.avatar_url, user.username, user.discriminator

    return await render_template('servers.html', render_avatar=avatar, render_username=f'{username}#{usertag}', render_guilds=guilds)


@app.route("/login/")
async def login():
    return await discord2.create_session(scope=["identify", "guilds", "email"])


@app.route("/dashboard/<int:guild_id>/")
@requires_authorization
async def server_dashboard(guild_id: int):
    
    guild = bot.get_guild(guild_id)
    print(guild)
    
    return str(guild.get("name"))


@app.route("/invite-bot/")
async def invite_bot():
    return await discord2.create_session(scope=["bot"], permissions=8, guild_id=859482895009579039, disable_guild_select=True)


@app.route("/invite-oauth/")
async def invite_oauth():
    return await discord2.create_session(scope=["bot", "identify"], permissions=8)


@app.route("/callback/")
async def callback():
    data = await discord2.callback()
    redirect_to = data.get("redirect", "/")

    return redirect(redirect_to)


@app.route("/me/")
async def me():
    user = await discord2.fetch_user()
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
    guilds = await discord2.fetch_guilds()
        
    return "<br />".join([f"[SERVER MANAGER] {g.name}" if g.permissions.manage_guild else g.name for g in guilds])


@app.route("/add_to/<int:guild_id>/")
async def add_to_guild(guild_id):
    user = await discord2.fetch_user()
    return await user.add_to_guild(guild_id)


@app.route("/me/connections/")
async def my_connections():
    user = await discord2.fetch_user()
    connections = await discord2.fetch_connections()
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
    discord2.revoke()
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


## -- RUNNING BOT -- ##

if __name__ == "__main__":
    bot.loop.create_task(bot_loop())
    bot.run(bot_token)