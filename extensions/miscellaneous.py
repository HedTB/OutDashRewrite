## -- IMPORTING -- ##

# MODULES
import disnake
import os
import certifi

from disnake.ext import commands
from pymongo import MongoClient
from dotenv import load_dotenv

# FILES
from utils import config
from utils import functions
from utils.checks import *
from utils.classes import *

## -- VARIABLES -- ##

load_dotenv()

PERMISSIONS = os.environ.get("PERMISSIONS")

## -- FUNCTIONS -- ##

def get_commands_run():
    with open("data/stats.json") as file:
        return json.load(file).get("commands_run")

## -- COG -- ##

class Miscellanous(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    ## -- TEXT COMMANDS -- ##
    
    """
    ! BOT COMMANDS

    Miscellaneous commands around the bot.
    """
    
    @commands.command()
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    async def info(self, ctx: commands.Context):
        """Get to know about OutDash!"""
        
        embed = disnake.Embed(title="Information",
                        description=f"**Main Developer:** {self.bot.get_user(config.owners[0])}\n**Web Developer:** {self.bot.get_user(config.owners[1])}\n\n"
                        f"Upvote OutDash **[here.](https://bit.ly/UpvoteOD1)**\nTo support us, go **[here.](https://bit.ly/SupportOutDash)**\nJoin the **[support server](https://discord.com/invite/4pfUqEufUm)** to report bugs and ask questions.\n\n**[Invite OutDash!](https://discord.com/api/oauth2/authorize?client_id=836494578135072778&permissions={PERMISSIONS}&scope=bot%20applications.commands)**\n\n"
                        "Thanks for using our bot, it means a lot :heart:",
                        color=config.embed_color)
        
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar or config.default_avatar_url)
        embed.timestamp = datetime.datetime.utcnow()
        
        await ctx.send(embed=embed)
        
    @commands.command()
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    async def stats(self, ctx):
        """Get to know how OutDash is doing!"""
        start = time.time()
        
        embed_one = disnake.Embed(description="Getting all data...", color=config.embed_color)
        msg = await ctx.send(embed=embed_one)
        
        end = time.time()
        time_result = end - start
        commands_run = get_commands_run()
        
        delta_uptime = datetime.datetime.utcnow() - self.bot.launch_time
        hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        embed = disnake.Embed(title="OutDash Stats", description="A list of statistics for OutDash.", color=config.embed_color)
        
        embed.add_field(name=":signal_strength: Connection", value=f"Bot Latency: `{round(self.bot.latency * 1000)} ms`\nAPI Latency: `{round(time_result * 1000)} ms`\nUptime: `{hours} hrs {minutes} mins`", inline=True)
        embed.add_field(name=":chart_with_upwards_trend: Bot Values", value=f"Server Count: `{len(self.bot.guilds)}`\nCommands Run: `{commands_run}`\nUser Count: `{len(self.bot.users)}`", inline=True)
        embed.add_field(name=":bar_chart: Server Values", value=f"Member Count: `{ctx.guild.member_count}`\nServer Prefix: `{self.bot.get_bot_prefix(ctx.guild.id)}`", inline=True)
            
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar or config.default_avatar_url)
        embed.timestamp = datetime.datetime.utcnow()
        
        await msg.edit(embed=embed)
        
    @commands.command()
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    async def ping(self, ctx: commands.Context):
        """Gets the latency of the bot."""
        start = time.time()
        message = await ctx.send("Pinging...")
        
        end = time.time()
        time_result = end - start
        
        embed = disnake.Embed(description=f":hourglass: Bot Latency - **{round(self.bot.latency * 1000)}** ms\n\n:stopwatch: API Latency - **{round(time_result * 1000)}** ms", color=config.embed_color)

        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar or config.default_avatar_url)
        embed.timestamp = datetime.datetime.utcnow()
        
        await message.edit(content="_ _", embed=embed)
        
    """
    ! GUILD COMMANDS
    
    Miscellaneous commands around guilds.
    """
    
    @commands.command(name="membercount", aliases=["members"])
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    async def membercount(self, ctx: commands.Context):
        """Returns your current member count!"""
            
        guild = ctx.guild
        bots = []
        humans = []
        
        online = sum(member.status==disnake.Status.online or member.status==disnake.Status.do_not_disturb or member.status==disnake.Status.idle for member in guild.members)
        offline = sum(member.status==disnake.Status.offline for member in guild.members)
        
        for i in guild.members:
            if i.bot:
                bots.append(i)
            if i.bot == False:
                humans.append(i)
                
        embed = disnake.Embed(title=f"Member Count",
        description=f":white_check_mark: Total - {guild.member_count}\n:bust_in_silhouette: Humans - {len(humans)}\n:robot: Bots - {len(bots)}"
        f"\n\n**User Statuses**\n{config.online} Online - {online}\n{config.offline} Offline - {offline}", color=config.embed_color)
        
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar or config.default_avatar_url)
        embed.timestamp = datetime.datetime.utcnow()
        
        await ctx.send(embed=embed)
    
    ## -- SLASH COMMANDS -- ##
    
    """
    ! BOT COMMANDS

    Miscellaneous commands around the bot.
    """

    @commands.slash_command(name="info", description="Get to know about OutDash!", guild_ids=[config.bot_server])
    async def slash_info(self, inter: disnake.ApplicationCommandInteraction):
        """Get to know about OutDash!"""
        
        embed = disnake.Embed(title="Information",
                        description=f"**Main Developer:** {self.bot.get_user(config.owners[0])}\n**Web Developer:** {self.bot.get_user(config.owners[1])}\n\n"
                        f"Upvote OutDash **[here.](https://bit.ly/UpvoteOD1)**\nTo support us, go **[here.](https://bit.ly/SupportOutDash)**\nJoin the **[support server](https://discord.com/invite/4pfUqEufUm)** to report bugs and ask questions.\n\n**[Invite OutDash!](https://discord.com/api/oauth2/authorize?client_id=836494578135072778&permissions={PERMISSIONS}&scope=bot%20applications.commands)**\n\n"
                        "Thanks for using our bot, it means a lot :heart:",
                        color=config.embed_color)
        
        embed.set_footer(text=f"Requested by {inter.author}", icon_url=inter.author.avatar or config.default_avatar_url)
        embed.timestamp = datetime.datetime.utcnow()
        
        await inter.send(embed=embed)
        
    @commands.slash_command(name="stats", description="Get to know how OutDash is doing!")
    async def slash_stats(self, inter: disnake.ApplicationCommandInteraction):
        """Get to know how OutDash is doing!"""
        start = time.time()
        
        embed_one = disnake.Embed(description="Getting all data...", color=config.embed_color)
        await inter.send(embed=embed_one)
        
        end = time.time()
        time_result = end - start
        commands_run = get_commands_run()
        
        delta_uptime = datetime.datetime.utcnow() - self.bot.launch_time
        hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
                    
        embed = disnake.Embed(title="OutDash Stats", description="A list of statistics for OutDash.", color=config.embed_color)
        
        embed.add_field(name=":signal_strength: Connection", value=f"Bot Latency: `{round(self.bot.latency * 1000)} ms`\nAPI Latency: `{round(time_result * 1000)} ms`\nUptime: `{hours} hrs {minutes} mins`", inline=True)

        embed.add_field(name=":chart_with_upwards_trend: Bot Values", value=f"Server Count: `{len(self.bot.guilds)}`\nCommands Run: `{commands_run}`\nUser Count: `{len(self.bot.users)}`", inline=True)

        embed.add_field(name=":bar_chart: Server Values", value=f"Member Count: `{inter.guild.member_count}`\nServer Prefix: `{self.bot.get_bot_prefix(inter.guild.id)}`", inline=True)

        embed.set_footer(text=f"Requested by {inter.author}", icon_url=inter.author.avatar or config.default_avatar_url)
        embed.timestamp = datetime.datetime.utcnow()
        
        await inter.edit_original_message(embed=embed)
        
    @commands.slash_command(name="ping", description="Gets the latency of the bot.")
    async def slash_ping(self, inter: disnake.ApplicationCommandInteraction):
        """Gets the latency of the bot."""
        
        start = time.time()
        await inter.send("Pinging...")
        
        end = time.time()
        time_result = end - start
        
        embed = disnake.Embed(description=f":hourglass: Bot Latency - **{round(self.bot.latency * 1000)}** ms\n\n:stopwatch: API Latency - **{round(time_result * 1000)}** ms", color=config.embed_color)

        embed.set_footer(text=f"Requested by {inter.author}", icon_url=inter.author.avatar or config.default_avatar_url)
        embed.timestamp = datetime.datetime.utcnow()
        
        await inter.edit_original_message(content="_ _", embed=embed)
        
    """
    ! GUILD COMMANDS
    
    Miscellaneous commands around guilds.
    """    
    
    @commands.slash_command(name="membercount", description="Returns your current member count!")
    async def slash_membercount(self, inter: disnake.ApplicationCommandInteraction):
        """Returns your current member count!"""
            
        guild = inter.guild
        bots = []
        humans = []
        
        online = sum(member.status==disnake.Status.online or member.status==disnake.Status.do_not_disturb or member.status==disnake.Status.idle for member in guild.members)
        offline = sum(member.status==disnake.Status.offline for member in guild.members)
        
        for i in guild.members:
            if i.bot:
                bots.append(i)
            if i.bot == False:
                humans.append(i)
                
        embed = disnake.Embed(title=f"Member Count",
        description=f":white_check_mark: Total - {guild.member_count}\n:bust_in_silhouette: Humans - {len(humans)}\n:robot: Bots - {len(bots)}"
        f"\n\n**User Statuses**\n{config.online} Online - {online}\n{config.offline} Offline - {offline}", color=config.embed_color)
        
        embed.set_footer(text=f"Requested by {inter.author}", icon_url=inter.author.avatar or config.default_avatar_url)
        embed.timestamp = datetime.datetime.utcnow()
        
        await inter.send(embed=embed)


def setup(bot):
    bot.add_cog(Miscellanous(bot))