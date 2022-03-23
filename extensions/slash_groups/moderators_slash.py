## -- IMPORTING -- ##

# MODULES
import disnake
import os
import random
import asyncio
import datetime
import certifi
import json

from disnake.ext import commands
from disnake.errors import Forbidden, HTTPException
from disnake.ext.commands import errors
from pymongo import MongoClient
from dotenv import load_dotenv

# FILES
from utils import config
from utils import functions
from utils.checks import *

load_dotenv()

## -- VARIABLES -- ##

mongo_login = os.environ.get("MONGO_LOGIN")
client = MongoClient(mongo_login, tlsCAFile=certifi.where())
db = client[config.database_collection]

server_data_col = db["server_data"]
muted_users_col = db["muted_users"]
user_data_col = db["user_data"]

## -- FUNCTIONS -- ##



## -- COG -- ##

class ModeratorsSlash(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.slash_command(name="moderators")
    @is_moderator(manage_guild=True)
    async def slash_moderators(self, inter):
        pass

    @slash_moderators.sub_command(name="add", description="Add a moderator to your server.")
    @is_moderator(manage_guild=True)
    async def slash_moderatorsadd(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member):
        """Add a moderator to your server.
        Parameters
        ----------
        member: The member you want to make a moderator.
        """

        if member == inter.author:
            embed = disnake.Embed(description=f"{config.no} You can't make yourself a moderator!", color=config.error_embed_color)
            await inter.send(embed=embed, ephemeral=True)
            return
        elif member.bot:
            embed = disnake.Embed(description=f"{config.no} You can't make a bot a moderator!", color=config.error_embed_color)
            await inter.send(embed=embed, ephemeral=True)
            return
        elif functions.is_role_above_role(member.top_role, inter.author.top_role):
            embed = disnake.Embed(description=f"{config.no} You don't have permission to make this member a moderator!", color=config.error_embed_color)
            await inter.send(embed=embed, ephemeral=True)
            return
        
        data = functions.get_db_data(inter.guild.id)
        query = {"guild_id": str(inter.guild.id)}
        result = server_data_col.find_one(query)
        
        if not result:
            server_data_col.insert_one(data)
            self.slash_moderatorsadd(inter, member)
            
        moderators = result.get("moderators")

        if not moderators:
            moderators = {1: {
                "id": member.id,
                "time": str(datetime.datetime.utcnow()),
                "moderator": inter.author.id,
            }}
            update = {
                "moderators": json.dumps(moderators)
            }
        else:
            moderators = json.loads(moderators)
            last_moderator = int(list(moderators.keys())[-1]) or 1

            for moderator in moderators:
                moderator = moderators[moderator]
                if int(moderator["id"]) == member.id:
                    embed = disnake.Embed(description=f"{config.no} This member is already a moderator!", color=config.error_embed_color)
                    await inter.send(embed=embed, ephemeral=True)
                    return

            moderators[last_moderator + 1] = {
                "id": member.id,
                "time": str(datetime.datetime.utcnow()),
                "moderator": inter.author.id,
            }
            update = {
                "moderators": json.dumps(moderators)
            }
        server_data_col.update_one(query, {"$set": update})

        embed = disnake.Embed(description=f"{config.yes} **{member}** has been added as a moderator.", color=config.success_embed_color)
        await inter.send(embed=embed)


    @slash_moderators.sub_command(name="remove", description="Remove a moderator from the server.")
    @is_moderator(manage_guild=True)
    async def slash_moderatorsremove(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member):
        pass

    @slash_moderators.sub_command(name="view", description="View all current moderators.")
    @is_moderator(manage_guild=True)
    async def slash_moderatorsview(self, inter: disnake.ApplicationCommandInteraction):
        """"View all current moderators."""
        
        data = functions.get_db_data(inter.guild.id)
        query = {"guild_id": str(inter.guild.id)}
        result = server_data_col.find_one(query)
        
        if not result:
            server_data_col.insert_one(data)
            self.slash_moderatorsview(inter)
            
        moderators = result.get("moderators")
        description = ""

        if not moderators:
            description = f"{config.info} There's no moderators."
        else:
            moderators = json.loads(moderators)
            for moderator in moderators:
                moderator = moderators[moderator]

                moderator_user = self.bot.get_user(int(moderator["id"]))
                added_user = self.bot.get_user(int(moderator["moderator"]))
                description += f"**{moderator_user}** ({moderator_user.mention})" + "\n" + f"Added by {added_user} | {moderator['time'][:16]} UTC\n\n"

        embed = disnake.Embed(title=f"Moderators for {inter.guild.name}", description=description, color=config.embed_color)

        embed.set_footer(text=f"Requested by {inter.author}", icon_url=inter.author.avatar or config.default_avatar_url)
        await inter.send(embed=embed)


        
    @slash_moderators.error
    async def slash_moderators_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions[0].capitalize()}` permission.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        
    
def setup(bot):
    bot.add_cog(ModeratorsSlash(bot))