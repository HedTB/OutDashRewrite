## -- IMPORTING -- ##

# MODULES
import disnake
import os
import certifi

from disnake.ext import commands
from pymongo import MongoClient
from dotenv import load_dotenv

# FILES
from utils import config, functions, colors

from utils.checks import *
from utils.classes import *
from utils.emojis import *

## -- VARIABLES -- ##

load_dotenv()

PERMISSIONS = os.environ.get("PERMISSIONS")

info_message = """
**Main Developer:** {hedtb}
**Web Developer:** {taiyangshan}

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
        

    ## -- TEXT COMMANDS -- ##

    """
    ! BOT COMMANDS

    Miscellaneous commands around the bot.
    """

    @commands.command()
    @commands.cooldown(1, config.COOLDOWN_TIME, commands.BucketType.member)
    async def info(self, ctx: commands.Context):
        """Get to know about OutDash!"""

        embed = disnake.Embed(title="Information",
                              description=info_message.format(
                                  hedtb=self.bot.get_user(config.OWNERS[0]),
                                  taiyangshan=self.bot.get_user(
                                      config.OWNERS[1]),
                                  permissions=PERMISSIONS
                              ),
                              color=colors.embed_color
                              )

        embed.set_footer(
            text=f"Requested by {ctx.author}",
            icon_url=ctx.author.avatar or config.DEFAULT_AVATAR_URL
        )
        embed.timestamp = datetime.datetime.utcnow()

        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, config.COOLDOWN_TIME, commands.BucketType.member)
    async def stats(self, ctx):
        """Get to know how OutDash is doing!"""
        start = time.time()

        embed_one = disnake.Embed(
            description="Getting all data...", color=colors.embed_color)
        msg = await ctx.send(embed=embed_one)

        end = time.time()
        time_result = end - start
        commands_run = get_commands_run()

        delta_uptime = datetime.datetime.utcnow() - self.bot.launch_time
        hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)

        embed = disnake.Embed(
            title="OutDash Stats",
            description="A list of statistics for OutDash.",
            color=colors.embed_color
        )

        embed.add_field(name=":signal_strength: Connection",
                        value=f"Bot Latency: `{round(self.bot.latency * 1000)} ms`\nAPI Latency: `{round(time_result * 1000)} ms`\nUptime: `{hours} hrs {minutes} mins`", inline=True)
        embed.add_field(name=":chart_with_upwards_trend: Bot Values",
                        value=f"Server Count: `{len(self.bot.guilds)}`\nCommands Run: `{commands_run}`\nUser Count: `{len(self.bot.users)}`", inline=True)
        embed.add_field(name=":bar_chart: Server Values",
                        value=f"Member Count: `{ctx.guild.member_count}`\nServer Prefix: `{self.bot.get_bot_prefix(ctx.guild)}`", inline=True)

        embed.set_footer(
            text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar or config.DEFAULT_AVATAR_URL)
        embed.timestamp = datetime.datetime.utcnow()

        await msg.edit(embed=embed)

    @commands.command()
    @commands.cooldown(1, config.COOLDOWN_TIME, commands.BucketType.member)
    async def ping(self, ctx: commands.Context):
        """Gets the latency of the bot."""

        start = time.time()
        embed = disnake.Embed(
            description="Pinging...",
            color=colors.embed_color
        )
        message = await ctx.send(embed=embed)

        end = time.time()
        time_result = end - start

        embed = disnake.Embed(
            description=f":hourglass: Bot Latency - **{round(self.bot.latency * 1000)}** ms\n\n:stopwatch: API Latency - **{round(time_result * 1000)}** ms",
            color=colors.embed_color
        )

        embed.set_footer(
            text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar or config.DEFAULT_AVATAR_URL)
        embed.timestamp = datetime.datetime.utcnow()

        await message.edit(content="_ _", embed=embed)

    """
    ! GUILD COMMANDS
    
    Miscellaneous commands around guilds.
    """

    @commands.command(name="membercount", aliases=["members"])
    @commands.cooldown(1, config.COOLDOWN_TIME, commands.BucketType.member)
    async def membercount(self, ctx: commands.Context):
        """Returns your current member count!"""

        bots = []
        humans = []

        online_members = sum(
            i.status == (disnake.Status.online or disnake.Status.dnd or disnake.Status.idle) for i in ctx.guild.members
        )
        offline_members = sum(
            i.status == disnake.Status.offline for i in ctx.guild.members
        )

        for i in ctx.guild.members:
            if i.bot:
                bots.append(i)
            if i.bot == False:
                humans.append(i)

        embed = disnake.Embed(
            title=f"Member Count",
            description=f"""
                :white_check_mark: Total - {ctx.guild.member_count}
                :bust_in_silhouette: Humans - {len(humans)}
                :robot: Bots - {len(bots)}
                
                **User Statuses**
                {online} Online - {online_members}
                {offline} Offline - {offline_members}
                """,
            color=colors.embed_color
        )

        embed.set_footer(
            text=f"Requested by {ctx.author}",
            icon_url=ctx.author.avatar or config.DEFAULT_AVATAR_URL
        )
        embed.timestamp = datetime.datetime.utcnow()

        await ctx.send(embed=embed)

    ## -- SLASH COMMANDS -- ##

    """
    ! BOT COMMANDS

    Miscellaneous commands around the bot.
    """

    @commands.slash_command(name="info", description="Get to know about OutDash!", guild_ids=[config.BOT_SERVER])
    async def slash_info(self, inter: disnake.ApplicationCommandInteraction):
        """Get to know about OutDash!"""

        embed = disnake.Embed(
            title="Information",
            description=info_message.format(
                hedtb=self.bot.get_user(config.OWNERS[0]),
                taiyangshan=self.bot.get_user(config.OWNERS[1]),
                permissions=PERMISSIONS
            ),
            color=colors.embed_color
        )

        embed.set_footer(
            text=f"Requested by {inter.author}",
            icon_url=inter.author.avatar or config.DEFAULT_AVATAR_URL
        )
        embed.timestamp = datetime.datetime.utcnow()

        await inter.send(embed=embed)

    @commands.slash_command(name="stats", description="Get to know how OutDash is doing!")
    async def slash_stats(self, inter: disnake.ApplicationCommandInteraction):
        """Get to know how OutDash is doing!"""
        
        start = time.time()

        embed = disnake.Embed(
            description="Getting all data...",
            color=colors.embed_color
        )
        await inter.send(embed=embed)

        end = time.time()
        time_result = end - start
        commands_run = get_commands_run()
        hours, minutes, seconds = self.get_uptime()

        embed = disnake.Embed(
            title="OutDash Stats",
            description="A list of statistics for OutDash.",
            color=colors.embed_color
        )

        embed.add_field(
            name=":signal_strength: Connection",
            value=f"Bot Latency: `{round(self.bot.latency * 1000)} ms`\nAPI Latency: `{round(time_result * 1000)} ms`\nUptime: `{hours} hrs {minutes} mins`",
            inline=True
        )
        embed.add_field(
            name=":chart_with_upwards_trend: Bot Values",
            value=f"Server Count: `{len(self.bot.guilds)}`\nCommands Run: `{commands_run}`\nUser Count: `{len(self.bot.users)}`",
            inline=True
        )
        embed.add_field(
            name=":bar_chart: Server Values",
            value=f"Member Count: `{inter.guild.member_count}`\nServer Prefix: `{self.bot.get_bot_prefix(inter.guild)}`",
            inline=True
        )

        embed.set_footer(
            text=f"Requested by {inter.author}",
            icon_url=inter.author.avatar or config.DEFAULT_AVATAR_URL
        )
        embed.timestamp = datetime.datetime.utcnow()

        await inter.edit_original_message(embed=embed)

    @commands.slash_command(name="ping", description="Gets the latency of the bot.")
    async def slash_ping(self, inter: disnake.ApplicationCommandInteraction):
        """Gets the latency of the bot."""

        start = time.time()
        
        embed = disnake.Embed(
            description="Pinging...",
            color=colors.embed_color
        )
        await inter.send(embed=embed)

        end = time.time()
        time_result = end - start

        embed = disnake.Embed(
            description=f":hourglass: Bot Latency - **{round(self.bot.latency * 1000)}** ms\n\n:stopwatch: API Latency - **{round(time_result * 1000)}** ms",
            color=colors.embed_color
        )

        embed.set_footer(
            text=f"Requested by {inter.author}",
            icon_url=inter.author.avatar or config.DEFAULT_AVATAR_URL
        )
        embed.timestamp = datetime.datetime.utcnow()

        await inter.edit_original_message(embed=embed)

    """
    ! GUILD COMMANDS
    
    Miscellaneous commands around guilds.
    """

    @commands.slash_command(name="membercount", description="Returns your current member count!")
    async def slash_membercount(self, inter: disnake.ApplicationCommandInteraction):
        """Returns your current member count!"""

        bots = []
        humans = []

        online_members = sum(
            i.status == (disnake.Status.online or disnake.Status.dnd or disnake.Status.idle) for i in inter.guild.members
        )
        offline_members = sum(
            i.status == disnake.Status.offline for i in inter.guild.members
        )

        for i in inter.guild.members:
            if i.bot:
                bots.append(i)
            if i.bot == False:
                humans.append(i)

        embed = disnake.Embed(
            title=f"Member Count",
            description=f"""
                :white_check_mark: Total - {inter.guild.member_count}
                :bust_in_silhouette: Humans - {len(humans)}
                :robot: Bots - {len(bots)}"
                
                **User Statuses**
                {online} Online - {online_members}
                {offline} Offline - {offline_members}
                """,
            color=colors.embed_color
        )

        embed.set_footer(
            text=f"Requested by {inter.author}",
            icon_url=inter.author.avatar or config.DEFAULT_AVATAR_URL
        )
        embed.timestamp = datetime.datetime.utcnow()

        await inter.send(embed=embed)


def setup(bot):
    bot.add_cog(Miscellaneous(bot))
