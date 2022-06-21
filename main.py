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

from utils import config, functions, colors
from utils.checks import *
from utils.classes import *

from app import run_api

## -- VARIABLES -- ##

load_dotenv()

# LOGGERS
logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("OutDash")
logger.setLevel(logging.DEBUG if not config.IS_SERVER else logging.INFO)

disnake_logger = logging.getLogger("disnake")
disnake_logger.setLevel(logging.INFO)

# TOKENS
bot_token = str(os.environ.get("BOT_TOKEN"))
test_bot_token = str(os.environ.get("TEST_BOT_TOKEN"))
api_key = os.environ.get("API_KEY")

# EXTENSIONS
extensions = [
    "events.events",
    "events.logging",
    "events.errors",
    "events.automod",
    "utils.loops",
    "developer_commands",
    "settings",
    "leveling",
    "fun",
    "miscellaneous",
    "help",
    "moderation",
    "music",
]

test_extensions = ["buttons"]

## -- FUNCTIONS -- ##


def get_prefix(bot, message: disnake.Message):
    if not message.guild:
        return commands.when_mentioned_or(config.DEFAULT_PREFIX)(bot, message)

    data_obj = GuildData(message.guild)
    data = data_obj.get_data()

    return commands.when_mentioned_or(data["prefix"])(bot, message)


async def load_extensions(bot: commands.Bot):
    for extension in extensions:
        bot.load_extension(f"extensions.{extension}")
        logger.debug(f"Loaded extension {extension}.")

    if not config.IS_SERVER:
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
            owner_id=config.OWNERS[0],
            reconnect=True,
            reload=config.IS_SERVER,
            max_messages=10000,
            strip_after_prefix=True,
            test_guilds=[config.BOT_SERVER, 746363347829784646]
            if not config.IS_SERVER else None,
            intents=disnake.Intents(
                guilds=True,
                members=True,
                bans=True,
                emojis=True,
                integrations=False,
                webhooks=False,
                invites=False,
                voice_states=True,
                presences=True,
                guild_messages=True,
                guild_reactions=True,
                guild_typing=False,
                dm_typing=False,
                message_content=True,
            ),
        )

        self.launch_time = datetime.datetime.utcnow()
        self.presence_index = 0
        self.started = False

        # automod data
        self.automod_warnings = {}
        self.moderated_messages = []

        # user data
        self.snipes = {}
        self.afk = {}
        self.leveling_awards = {}

        # guild data
        self.mode247 = {}

    def start_bot(self):
        self.run(bot_token if config.IS_SERVER else test_bot_token)

    async def on_connect(self):
        if self.started == True:
            return

        self.avatar = await self.user.avatar.read()
        self.started = True

        if config.IS_SERVER:
            STATUS_CHANNEL = self.get_channel(config.STATUS_CHANNEL)
            embed = disnake.Embed(
                title=f"Singed In As: {self.user.name} ({self.user.id})",
                description=f"Bot started in `{str(len(self.guilds))}` servers, with total of `{len(self.users)}` users, on an average latency of `{round(self.latency * 1000)} ms`.",
                color=colors.success_embed_color,
            )

            await STATUS_CHANNEL.send(embed=embed)

        print(f"Singed in as {self.user}."
              f"\nStats: {len(self.guilds)} servers, {len(self.users)} users.")

        with open("data/stats.json", "w") as file:
            json.dump({"commands_run": 0}, file)

    async def is_booster(self, user: disnake.User):
        if user.id in config.OWNERS:
            return True

        bot_guild = self.get_guild(config.BOT_SERVER)
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
    extension_options[extension] = extension

extension_options = commands.option_enum(extension_options)


@bot.slash_command(
    name="extensions",
    description="Manages the bot's extensions.",
    default_permission=False,
    guild_ids=[config.BOT_SERVER],
)
@commands.has_guild_permissions(guild_id=int(config.BOT_SERVER),
                            roles={871899070283800636: True})
async def slash_extensions(inter):
    pass


@slash_extensions.sub_command(name="load",
                              description="Load a specific extension.")
async def load_extension(inter: disnake.ApplicationCommandInteraction,
                         extension: extension_options):
    await inter.send("Loading extension...", ephemeral=True)

    try:
        bot.load_extension(f"extensions.{extension}")
    except Exception as error:
        logger.warning(f"Failed to load extension {extension} | {error}")

    await inter.edit_original_message(
        content=f"`{extension}` has been loaded (?)")


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

    await inter.edit_original_message(
        content=f"All extensions have been reloaded (?)")


@reload.sub_command(name="extension",
                    description="Reload one specific extension.")
async def reload_extension(inter: disnake.ApplicationCommandInteraction,
                           extension: extension_options):
    await inter.send("Reloading extension...", ephemeral=True)

    try:
        bot.reload_extension(f"extensions.{extension}")
    except Exception as error:
        logger.warning(f"Failed to reload extension {extension} | {error}")

    await inter.edit_original_message(
        content=f"`{extension}` has been reloaded (?)")


## -- RUNNING BOT -- ##

if __name__ == "__main__":
    if not config.IS_SERVER:
        Thread(target=run_api).start()

    bot.loop.create_task(load_extensions(bot))
    bot.start_bot()
