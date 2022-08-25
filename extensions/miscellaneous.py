## -- IMPORTING -- ##

# MODULES
import disnake
import os

from disnake.ext import commands
from dotenv import load_dotenv

# FILES
from utils import config, functions, colors

from utils.checks import *
from utils.data import *
from utils.emojis import *

## -- VARIABLES -- ##

load_dotenv()

PERMISSIONS = os.environ.get("PERMISSIONS")

info_message = """
    **Main Developer:** {hedtb}
    **Web Developer:** {nox}

    Upvote OutDash **[here](https://bit.ly/UpvoteOD1)** to help us grow!
    To support us, go **[here.](https://bit.ly/SupportOutDash)**
    Join the **[support server](https://discord.com/invite/4pfUqEufUm)** to report bugs.

    **[Invite OutDash!](https://discord.com/api/oauth2/authorize?client_id=836494578135072778&permissions={permissions}&scope=bot%20applications.commands)**

    Thanks for using our bot, it means a lot to us :heart:
"""

## -- FUNCTIONS -- ##


def get_commands_run():
    with open("data/stats.json") as file:
        return json.load(file).get("commands_run")


## -- COG -- ##


class Miscellaneous(commands.Cog):
    name = f"{work} Miscellaneous"
    description = "Miscellaneous commands to for example view bot information."
    emoji = work

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def get_uptime(self) -> tuple[int, int, int]:
        delta_uptime = datetime.datetime.utcnow() - self.bot.launch_time
        hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)

        return hours, minutes, seconds

    ## -- SLASH COMMANDS -- ##

    """
    ! BOT COMMANDS

    Miscellaneous commands around the bot.
    """

    @commands.slash_command(
        name="info",
        description="Get to know about OutDash!",
        guild_ids=[config.BOT_SERVER],
    )
    async def info(self, inter: disnake.ApplicationCommandInteraction):
        """Get to know about OutDash!"""

        await inter.send(embed=disnake.Embed(
            title="Information",
            description=info_message.format(
                hedtb=self.bot.get_user(config.OWNERS[0]),
                nox=self.bot.get_user(config.OWNERS[1]),
                permissions=PERMISSIONS,
            ),
            timestamp=datetime.datetime.utcnow(),
            color=colors.embed_color,
        ).set_footer(
            text=f"Requested by {inter.author}",
            icon_url=inter.author.avatar or config.DEFAULT_AVATAR_URL,
        ))

    @commands.slash_command(
        name="stats", description="Get to know how OutDash is doing!"
    )
    async def stats(self, inter: disnake.ApplicationCommandInteraction):
        """Get to know how OutDash is doing!"""

        start = time.time()
        hours, minutes, _ = self.get_uptime()

        await inter.send(embed=disnake.Embed(
            description="Getting all data...", color=colors.embed_color
        ))

        await inter.edit_original_message(embed=disnake.Embed(
            title="OutDash Stats",
            description="A list of statistics for OutDash.",
            timestamp=datetime.datetime.utcnow(),
            color=colors.embed_color,
        ).add_field(
            name=":signal_strength: Connection",
            value=f"Bot Latency: `{round(self.bot.latency * 1000)} ms`\nAPI Latency: `{round((time.time() - start) * 1000)} ms`\nUptime: `{hours} hrs {minutes} mins`",
            inline=True,
        ).add_field(
            name=":chart_with_upwards_trend: Bot Values",
            value=f"Server Count: `{len(self.bot.guilds)}`\nCommands Run: `{get_commands_run()}`\nUser Count: `{len(self.bot.users)}`",
            inline=True,
        ).add_field(
            name=":bar_chart: Server Values",
            value=f"Member Count: `{inter.guild.member_count}`",
            inline=True,
        ).set_footer(
            text=f"Requested by {inter.author}",
            icon_url=inter.author.avatar or config.DEFAULT_AVATAR_URL,
        ))

    @commands.slash_command(name="ping", description="Gets the latency of the bot.")
    async def ping(self, inter: disnake.ApplicationCommandInteraction):
        """Gets the latency of the bot."""

        start = time.time()

        await inter.send(embed=disnake.Embed(
            description="Pinging...",
            color=colors.embed_color
        ))

        await inter.edit_original_message(embed=disnake.Embed(
            description=f":hourglass: Bot Latency - **{round(self.bot.latency * 1000)}** ms\n\n:stopwatch: API Latency - **{round((time.time() - start) * 1000)}** ms",
            timestamp=datetime.datetime.utcnow(),
            color=colors.embed_color,
        ).set_footer(
            text=f"Requested by {inter.author}",
            icon_url=inter.author.avatar or config.DEFAULT_AVATAR_URL,
        ))

    """
    ! GUILD COMMANDS
    
    Miscellaneous commands around guilds.
    """

    @commands.slash_command(
        name="membercount", description="Returns your current member count!"
    )
    async def membercount(self, inter: disnake.ApplicationCommandInteraction):
        """Returns your current member count!"""

        bots = [member.bot and member for member in inter.guild.members]
        humans = [not member.bot and member for member in inter.guild.members]

        online_members = sum(
            member.status
            == (disnake.Status.online or disnake.Status.dnd or disnake.Status.idle)
            for member in inter.guild.members
        )
        offline_members = sum(
            member.status == disnake.Status.offline for member in inter.guild.members
        )

        await inter.send(embed=disnake.Embed(
            title=f"Member Count",
            description=f"""
                :white_check_mark: Total - {inter.guild.member_count}
                :bust_in_silhouette: Humans - {len(humans)}
                :robot: Bots - {len(bots)}"
                
                **User Statuses**
                {online} Online - {online_members}
                {offline} Offline - {offline_members}
                """,
            timestamp=datetime.datetime.utcnow(),
            color=colors.embed_color,
        ).set_footer(
            text=f"Requested by {inter.author}",
            icon_url=inter.author.avatar or config.DEFAULT_AVATAR_URL,
        ))


def setup(bot):
    bot.add_cog(Miscellaneous(bot))
