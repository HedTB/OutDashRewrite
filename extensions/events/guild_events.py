## -- IMPORTING -- ##

# MODULES
import datetime
import disnake
import os
import certifi

from disnake.ext import commands
from pymongo import MongoClient
from dotenv import load_dotenv

# FILES
from extra import config
from extra import functions

## -- VARIABLES -- ##

load_dotenv()
mongo_token = os.environ.get("MONGO_LOGIN")

client = MongoClient(f"{mongo_token}", tlsCAFile=certifi.where())

db = client[config.database_collection]
server_data_col = db["server_data"]

## -- COG -- ##

class GuildEvents(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: disnake.Guild):
        data = functions.get_db_data(str(guild.id))
        query = {"guild_id": str(guild.id)}
        result = server_data_col.find_one(query)

        if not result:
            server_data_col.insert_one(data)

        embed = disnake.Embed(title="New Server", description=f"OutDash was added to a new server!\n\nWe're now in `{len(self.bot.guilds)}` guilds.", color=config.logs_add_embed_color)
        
        embed.add_field(name="Server Name", value=f"`{guild.name}`")
        embed.add_field(name="Server ID", value=f"`{guild.id}`")
        embed.add_field(name="Server Members", value=f"`{len(guild.members)}` total members", inline=False)
        
        embed.set_thumbnail(url=guild.icon.url)
        embed.timestamp = datetime.datetime.utcnow()

        await self.bot.get_channel(config.messages_channel).send(embed=embed)
        
    @commands.Cog.listener()
    async def on_guild_remove(self, guild: disnake.Guild):
        embed = disnake.Embed(title="Server Left", description=f"OutDash was removed from a server..\n\nWe're now in `{len(self.bot.guilds)}` guilds.", color=config.logs_delete_embed_color)
        
        embed.add_field(name="Server Name", value=f"`{guild.name}`")
        embed.add_field(name="Server ID", value=f"`{guild.id}`")
        
        embed.set_thumbnail(url=guild.icon.url)
        embed.timestamp = datetime.datetime.utcnow()

        await self.bot.get_channel(config.messages_channel).send(embed=embed)


def setup(bot):
    bot.add_cog(GuildEvents(bot))