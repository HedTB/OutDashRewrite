## -- IMPORTING -- ##

# MODULES
import disnake
import datetime
import time
import os
import certifi

from disnake.ext import commands
from pymongo import MongoClient

# FILES
import extra.config as config

## -- VARIABLES -- ##

mongo_login = os.environ.get("MONGO_LOGIN")
client = MongoClient(f"{mongo_login}",tlsCAFile=certifi.where())
db = client["db"]
server_data_col = db["server_data_col"]

## -- COG -- ##

class Ping(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    async def ping(self, ctx):
        """Gets the latency of the bot."""
        start = time.time()
        message = await ctx.send("Pinging...")
        end = time.time()
        time_result = end - start

        start2 = time.time()
        server_data_col.find_one({"guild_id": str(ctx.guild.id)})
        end2 = time.time()
        time_result2 = end2 - start2
        
        embed = disnake.Embed(description=f':hourglass: Bot Latency - **{round(self.bot.latency * 1000)}** ms\n\n:stopwatch: API Latency - **{round(time_result * 1000)}** ms\n\n:timer: Database Latency - **{round(time_result2 * 1000)}** ms', color=config.embed_color)
            
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar or "https://cdn.discordapp.com/embed/avatars/1.png")
        embed.timestamp = datetime.datetime.utcnow()
        
        await message.edit(content="_ _", embed=embed)
        
    
    @commands.slash_command(name="ping", description="Gets the latency of the bot.")
    async def slash_ping(self, inter):
        """Gets the latency of the bot."""
        start = time.time()
        message = await inter.send("Pinging...")
        end = time.time()
        time_result = end - start

        start2 = time.time()
        server_data_col.find_one({"guild_id": str(inter.guild.id)})
        end2 = time.time()
        time_result2 = end2 - start2
        
        embed = disnake.Embed(description=f':hourglass: Bot Latency - **{round(self.bot.latency * 1000)}** ms\n\n:stopwatch: API Latency - **{round(time_result * 1000)}** ms\n\n:timer: Database Latency - **{round(time_result2 * 1000)}** ms', color=config.embed_color)
            
        embed.set_footer(text=f"Requested by {inter.author}", icon_url=inter.author.avatar or "https://cdn.discordapp.com/embed/avatars/1.png")
        embed.timestamp = datetime.datetime.utcnow()
        
        await inter.edit_original_message(content="_ _", embed=embed)
        
    
def setup(bot):
    bot.add_cog(Ping(bot))