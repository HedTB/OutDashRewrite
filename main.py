## -- IMPORTING -- ##

# MODULE
import asyncio
import atexit
import os
import datetime
import certifi
import disnake
import json
import logging

from disnake.ext import commands
from pymongo import MongoClient
from dotenv import load_dotenv
from threading import Thread


# FILES
from utils import functions
from utils import config
from utils.checks import *
from utils.classes import *

from app import run_api


## -- VARIABLES -- ##

load_dotenv()

# LOGGERS
logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("OutDash")
logger.setLevel(logging.DEBUG if not config.is_server else logging.INFO)

disnake_logger = logging.getLogger("disnake")
disnake_logger.setLevel(logging.INFO)

# TOKENS
bot_token = str(os.environ.get("BOT_TOKEN"))
test_bot_token = str(os.environ.get("TEST_BOT_TOKEN"))
api_key = os.environ.get("API_KEY")

# OTHER
extensions = [
    "events.events", "events.logging", "events.errors", "utils.loops",
    "developer_commands", "bot_settings",
    "leveling", "fun", "miscellaneous", "help",
    
    "moderation", "music",
]

test_extensions = [
    "buttons"
]

## -- FUNCTIONS -- ##

def get_prefix(bot, message: disnake.Message):
    if not message.guild:
        return commands.when_mentioned_or(config.default_prefix)(bot, message)
    
    data_obj = GuildData(message.guild)
    data = data_obj.get_data()
    
    return commands.when_mentioned_or(data["prefix"])(bot, message)

async def load_extensions(bot: commands.Bot):
    for extension in extensions:
        bot.load_extension(f"extensions.{extension}")
        logger.debug(f"Loaded extension {extension}.")
        
    if not config.is_server:
        for extension in test_extensions:
            bot.load_extension(f"extensions.tests.{extension}")
            logger.debug(f"Loaded test extension {extension}.")

    logger.info("Loaded all extensions.")


# BOT
class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(
            command_prefix=get_prefix,
            case_insensitive=True,
            status=disnake.Status.idle,
            
            activity=disnake.Game(name="booting up.."),
            owner_id=config.owners[0],
            reconnect=True,
            
            reload=config.is_server,
            max_messages=10000,
            strip_after_prefix=True,
            
            test_guilds=[config.bot_server, 746363347829784646] if not config.is_server else None,
            sync_permissions=True,
            
            intents=disnake.Intents(
                guilds=True, members=True, bans=True, emojis=True,
                integrations=False, webhooks=False, invites=False,
                voice_states=True, presences=True, guild_messages=True,
                guild_reactions=True, guild_typing=False, dm_typing=False
            )
        )

        self.launch_time = datetime.datetime.utcnow()
        self.presence_index = 0
        self.started = False
        
        # automod data
        self.automod_warnings = {}
        
        # user data
        self.snipes = {}
        self.afk = {}
        self.leveling_awards = {}
        
        # guild data
        self.mode247 = {}
        
    def start_bot(self):
        self.run(bot_token if config.is_server else test_bot_token)
        
    async def on_ready(self):
        if self.started == True:
            return
        
        self.avatar = await self.user.avatar.read()
        self.started = True
        
        if config.is_server:
            status_channel = self.get_channel(config.messages_channel)
            embed = disnake.Embed(title=f"Singed In As: {self.user.name} ({self.user.id})", 
                                description=f"Bot started in `{str(len(self.guilds))}` servers, with total of `{len(self.users)}` users, on an average latency of `{round(bot.latency * 1000)} ms`.", 
                                color=config.success_embed_color)
            
            await status_channel.send(embed=embed)

        print(f"Bot started on {'the server' if config.is_server else 'a local computer'}.\nStats: {len(self.guilds)} servers, {len(self.users)} users.")
        
        with open("data/stats.json", "w") as file:
            json.dump({ "commands_run": 0}, file)
            
    async def is_booster(self, user: disnake.User):
        if user.id in config.owners:
            return True
        
        bot_guild = self.get_guild(config.bot_server)
        member = bot_guild.get_member(user.id)
        
        if disnake.utils.get(member.roles, id=955179507055222834):
            return True
            
        return False
                    
    def get_bot_prefix(self, guild: disnake.Guild) -> str:
        data_obj = GuildData(guild)
        data = data_obj.get_data()

        return data["prefix"]
    
        
bot = Bot()

## -- EXTENSIONS -- ##

extension_options = {}
for extension in extensions:
    extension_options[extension]= extension
    
extension_options = commands.option_enum(extension_options)
 
@bot.slash_command(name="extensions",
                   description="Manages the bot's extensions.",
                   default_permission=False,
                   guild_ids=[config.bot_server])
@commands.guild_permissions(guild_id=int(config.bot_server), roles={871899070283800636: True})
async def slash_extensions(inter):
    pass

@slash_extensions.sub_command(name="load", description="Load a specific extension.")
async def load_extension(inter: disnake.ApplicationCommandInteraction, extension: extension_options):
    await inter.send("Loading extension...", ephemeral=True)
        
    try:
        bot.load_extension(f"extensions.{extension}")
    except Exception as error:
        logger.warning(f"Failed to load extension {extension} | {error}")
        
    await inter.edit_original_message(content=f"`{extension}` has been loaded (?)")

@slash_extensions.sub_command_group(name="reload")
async def reload(inter):
    pass

@reload.sub_command(name="all", description="Reload all extensions.")
async def reload_extensions(inter: disnake.ApplicationCommandInteraction):
    await inter.send("Reloading all extensions...", ephemeral=True)
    
    for extension in extensions:
        try:
            bot.reload_extension(f"extensions.{extension}")
        except Exception as error:
            logger.warning(f"Failed to reload extension {extension} | {error}")
        
    await inter.edit_original_message(content=f"All extensions have been reloaded (?)")

@reload.sub_command(name="extension", description="Reload one specific extension.")
async def reload_extension(inter: disnake.ApplicationCommandInteraction, extension: extension_options):
    await inter.send("Reloading extension...", ephemeral=True)
    
    try:
        bot.reload_extension(f"extensions.{extension}")
    except Exception as error:
        logger.warning(f"Failed to reload extension {extension} | {error}")
        
    await inter.edit_original_message(content=f"`{extension}` has been reloaded (?)")
        

## -- RUNNING BOT -- ##

if __name__ == "__main__":
    if not config.is_server:
        Thread(target=run_api).start()
    
    bot.loop.create_task(load_extensions(bot))
    bot.start_bot()