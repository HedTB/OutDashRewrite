## -- IMPORTING -- ##

# MODULE
import multiprocessing
import os
import datetime
import time
import disnake
import logging
import typing

from disnake.ext import commands
from dotenv import load_dotenv

# FILES

from utils import config, colors, enums
from utils.data import Guild, GuildData, MemberData


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
extension_files = [
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
    # "music",
    "forms",
]

test_extensions = ["buttons"]

## -- FUNCTIONS -- ##


async def load_extensions(bot: commands.Bot):
    for extension in extension_files:
        bot.load_extension(f"extensions.{extension}")
        logger.debug(f"Loaded extension {extension}.")

    if not config.IS_SERVER:
        for extension in test_extensions:
            bot.load_extension(f"extensions.tests.{extension}")
            logger.debug(f"Loaded test extension {extension}.")

    logger.info("Loaded all extensions.")


# BOT
class Bot(commands.InteractionBot):
    def __init__(self, *args, **kwargs):
        super().__init__(
            sync_commands=True,
            status=disnake.Status.idle,
            activity=disnake.Game(name="booting up.."),
            owner_id=config.OWNERS[0],
            reload=config.IS_SERVER,
            max_messages=10000,
            test_guilds=[config.BOT_SERVER, 746363347829784646] if not config.IS_SERVER else None,
            intents=disnake.Intents(
                message_content=True,
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
            ),
        )

        self.launch_time = datetime.datetime.utcnow()
        self.presence_index = 0
        self.started = False
        self.commands_run = 0

        # automod data
        self.automod_warnings = {}
        self.moderated_messages = []

        # user data
        self.snipes = {}
        self.afk = {}
        self.leveling_awards = {}

        # guild data
        self.mode247 = {}

        # temporary data
        self.chatbot_status = True

    def start_bot(self):
        self.pool = multiprocessing.Pool()
        self.run(bot_token if config.IS_SERVER else test_bot_token)

    async def on_ready(self):
        if self.started is True:
            return

        self.avatar = await self.user.avatar.read()
        self.started = True

        if config.IS_SERVER:
            STATUS_CHANNEL = self.get_channel(config.STATUS_CHANNEL)
            embed = disnake.Embed(
                title=f"Singed In As: {self.user.name} ({self.user.id})",
                description=f"Bot started in `{str(len(self.guilds))}` servers, "
                f"with total of `{len(self.users)}` users, "
                f"on an average latency of `{round(self.latency * 1000)} ms`.",
                color=colors.success_embed_color,
            )

            await STATUS_CHANNEL.send(embed=embed)

        logger.info("Inserting missing data for bot's guilds")

        for guild in self.guilds:
            logger.debug(f"Fetching data for {guild.name} ({guild.id})")
            Guild.create(guild.id, cache=False).run_asynchronously(self.pool, Guild.fetch_data)

        logger.info(
            f"""
            Singed in as {self.user}

            \tServers: {len(self.guilds)}
            \tUsers: {len(self.users)}
            \tPing: {round(self.latency * 1000)} ms
        """
        )

    def get_staff_members(self, guild: disnake.Guild) -> typing.Dict[str, typing.Dict[str, disnake.Member]]:
        guild_data_obj = GuildData(guild.id)
        guild_data = guild_data_obj.get_data()

        return guild_data["staff_members"]

    def get_staff_rank(self, member: disnake.Member):
        if member.id in config.OWNERS:
            return "Owner"

        staff_members = self.get_staff_members(member.guild)

        for staff_rank, members in staff_members.items():
            if member.id in members:
                return staff_rank

    def is_booster(self, user: disnake.User):
        if user.id in config.OWNERS:
            return True

        bot_guild = self.get_guild(config.BOT_SERVER)
        member = bot_guild.get_member(user.id)

        if disnake.utils.get(member.roles, id=955179507055222834):
            return True

        return False

    async def get_audit_log(
        self, action: disnake.AuditLogAction, guild: disnake.Guild, user: disnake.User
    ) -> disnake.AuditLogEntry | None:
        try:
            entries = await guild.audit_logs(
                limit=50,
                after=datetime.datetime.fromtimestamp(time.time() - 10),
                action=action,
            ).flatten()
        except Exception:
            entries = []

        for entry in entries:
            if entry._target_id and entry._target_id == user.id:
                return entry

        return None

    def log_moderation(
        self,
        *,
        moderator: disnake.Member,
        offender: disnake.User | disnake.Member,
        action: enums.Moderation,
        reason: str = "No reason provided.",
        **extras,
    ):
        assert moderator.guild, "The moderator has to be in a guild"

        guild_data_obj = GuildData(moderator.guild.id)
        moderator_data_obj = MemberData(moderator.id, moderator.guild.id)
        offender_data_obj = MemberData(offender.id, moderator.guild.id)

        guild_data = guild_data_obj.get_data()
        moderator_data = moderator_data_obj.get_guild_data()
        offender_data = offender_data_obj.get_guild_data()

        cases = guild_data.get("cases", [])
        moderation_action_logs = moderator_data.get("moderation_action_logs", [])
        moderation_logs = offender_data.get("moderation_logs", [])

        case_id = len(cases) + 1

        cases.append(
            {
                "id": case_id,
                "moderator": moderator.id,
                "offender": offender.id,
                "action": action.value,
                "reason": reason,
                "timestamp": datetime.datetime.utcnow(),
                **extras,
            }
        )

        moderation_action_logs.append(case_id)
        moderation_logs.append(case_id)

        guild_data_obj.update_data(guild_data)
        moderator_data_obj.update_guild_data(moderator_data)
        offender_data_obj.update_guild_data(offender_data)

    def get_cases(self, guild: disnake.Guild) -> list[dict]:
        guild_data_obj = GuildData(guild.id)
        guild_data = guild_data_obj.get_data()

        return guild_data["cases"]

    def get_member_cases(self, member: disnake.Member):
        member_data_obj = MemberData(member.id, member.guild.id)
        member_data = member_data_obj.get_guild_data()

        cases = self.get_cases(member.guild)
        member_cases = []

        for case_num in member_data.get("moderation_logs"):
            try:
                case = cases[case_num - 1]
            except Exception:
                continue

            member_cases.append(case)

        return member_cases


bot = Bot()

## -- EXTENSIONS -- ##


@bot.slash_command(
    name="extensions",
    description="Manages the bot's extensions.",
    default_member_permissions=disnake.Permissions.advanced(),
    guild_ids=[config.BOT_SERVER],
)
async def extension(inter):
    pass


@extension.sub_command(name="load", description="Load a specific extension.")
async def load_extension(
    inter: disnake.ApplicationCommandInteraction,
    extension: commands.option_enum({extension: extension for extension in extension_files}),
):
    await inter.send("Loading extension...", ephemeral=True)

    try:
        bot.load_extension(f"extensions.{extension}")
        await inter.edit_original_message(content=f"`{extension}` has been loaded")
    except Exception as error:
        logger.warning(f"Failed to load extension {extension} | {error}")
        await inter.edit_original_message(content=f"Failed to load extension `{extension}`")


@extension.sub_command_group(name="reload")
async def reload(inter):
    pass


@reload.sub_command(name="all", description="Reload all extensions.")
async def reload_extensions(inter: disnake.ApplicationCommandInteraction):
    await inter.send("Reloading all extensions...", ephemeral=True)

    for extension in extension_files:
        try:
            bot.reload_extension(f"extensions.{extension}")
        except Exception as error:
            logger.warning(f"Failed to reload extension {extension} | {error}")

    await inter.edit_original_message(content="All extensions have been reloaded (?)")


@reload.sub_command(name="extension", description="Reload one specific extension.")
async def reload_extension(
    inter: disnake.ApplicationCommandInteraction,
    extension: commands.option_enum({extension: extension for extension in extension_files}),
):
    await inter.send("Reloading extension...", ephemeral=True)

    try:
        bot.reload_extension(f"extensions.{extension}")
        await inter.edit_original_message(content=f"`{extension}` has been reloaded")
    except Exception as error:
        logger.warning(f"Failed to load extension {extension} | {error}")
        await inter.edit_original_message(content=f"Failed to lreoad extension `{extension}`")


## -- RUNNING BOT -- ##

if __name__ == "__main__":
    # if not config.IS_SERVER:
    #     Thread(target=run_api).start()

    bot.loop.create_task(load_extensions(bot))
    bot.start_bot()
else:
    bot = None
