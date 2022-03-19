## -- IMPORTING -- ##

# MODULES
import disnake
import datetime
import time
import json

from disnake.ext import commands

# FILES
from extra import config

def get_commands_run():
    with open("data/stats.json") as file_object:
        data = json.load(file_object)
    return data.get("commands_run")

class Stats(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

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
        
    
    @commands.slash_command(name="stats", description="Get to know how OutDash is doing!")
    async def slash_stats(self, inter):
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
    
        
    
def setup(bot):
    bot.add_cog(Stats(bot))
