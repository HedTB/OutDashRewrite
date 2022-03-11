## -- IMPORTING -- ##

# MODULES
import disnake
import os
import random
import asyncio
import datetime
import certifi
import time
import json

from disnake.ext import commands
from disnake.errors import Forbidden, HTTPException
from disnake.ext.commands import errors
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# FILES
from extra import config
from extra import functions
from extra.checks import is_moderator

## -- VARIABLES -- ##

mongo_login = os.environ.get("MONGO_LOGIN")
client = MongoClient(f"{mongo_login}",tlsCAFile=certifi.where())
db = client[config.database_collection]

server_data_col = db["server_data"]
warns_col = db["warns"]


class Warn(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        
    
    @commands.slash_command(name="warn", description="Warn a member for their bad actions!")
    @is_moderator(moderate_members=True)
    async def slash_warn(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, reason: str):
        """Warn a member for their bad actions!
        Parameters
        ----------
        member: The member you want to warn.
        reason: The reason for the warn.
        """

        result = warns_col.find_one({
            "guild_id": str(inter.guild.id)
        })

        if member == inter.author:
            embed = disnake.Embed(description=f"{config.no} You can't warn yourself!", color=config.error_embed_color)
            await inter.send(embed=embed, ephemeral=True)
            return
        elif member.bot:
            embed = disnake.Embed(description=f"{config.no} You can't warn a bot!", color=config.error_embed_color)
            await inter.send(embed=embed, ephemeral=True)
            return
        elif functions.is_role_above_role(member.top_role, inter.author.top_role) or member.top_role == inter.author.top_role:
            embed = disnake.Embed(description=f"{config.no} You don't have permission to warn this member!", color=config.error_embed_color)
            await inter.send(embed=embed, ephemeral=True)
            return

        try:
            warnings = result[str(member.id)]
        except Exception as error:
            warnings = [{
                "moderator": inter.author.id, 
                "reason": reason, 
                "time": str(datetime.datetime.utcnow())
            }]

        if not result:
            warns_col.insert_one({
                "guild_id": str(inter.guild.id),
                str(member.id): json.dumps(warnings)
            })
            await self.slash_warn(inter, member, reason)
            
            return
        elif not warnings or type(warnings) == dict:
            warns_col.update_one({"guild_id": str(inter.guild.id)}, {"$set": {
                str(member.id): json.dumps(warnings)
            }})
        else:
            warnings = json.loads(warnings)
            
            warnings.append({
                "moderator": inter.author.id, 
                "reason": reason, 
                "time": str(datetime.datetime.utcnow())
            })
            warnings = json.dumps(warnings)

            warns_col.update_one(
                filter = {"guild_id": str(inter.guild.id)},
                update = {"$set": {
                    str(member.id): warnings
                }}
            )

        embed = disnake.Embed(description=f"{config.yes} **{member.name}#{member.discriminator}** has been warned.", color=config.success_embed_color)
        dm_embed = disnake.Embed(description=f"{config.moderator} You have been warned in **{inter.guild.name}**.\n**Reason**: {reason}", color=config.logs_embed_color)
        
        await member.send(dm_embed)
        await inter.send(embed=embed)
        
    @slash_warn.sub_command(name="remove", description="Remove a warning from a member.")
    @is_moderator(moderate_members=True)
    async def slash_warnremove(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, warning: int):
        """Remove a warning from a member.
        Parameters
        ----------
        member: The member you want to remove a warning from.
        warning: The warning you want to remove.
        """

        result = warns_col.find_one({
            "guild_id": str(inter.guild.id)
        })

        if not result:
            embed = disnake.Embed(description=f"{config.no} This member doesn't have any warnings!", color=config.error_embed_color)
            await inter.send(embed=embed, ephemeral=True)
            return

        if member == inter.author:
            embed = disnake.Embed(description=f"{config.no} You can't remove warnings from yourself!", color=config.error_embed_color)
            await inter.send(embed=embed, ephemeral=True)
            return
        elif member.bot:
            embed = disnake.Embed(description=f"{config.no} You can't remove warnings from a bot!", color=config.error_embed_color)
            await inter.send(embed=embed, ephemeral=True)
            return
        elif functions.is_role_above_role(member.top_role, inter.author.top_role) or member.top_role == inter.author.top_role:
            embed = disnake.Embed(description=f"{config.no} You don't have permission to remove a warning from this member!", color=config.error_embed_color)
            await inter.send(embed=embed, ephemeral=True)
            return

        try:
            warnings = result[str(member.id)]
            warnings = json.loads(warnings)
        except Exception as error:
            embed = disnake.Embed(description=f"{config.no} This member doesn't have any warnings!", color=config.error_embed_color)
            await inter.send(embed=embed, ephemeral=True)
            return
        
        if not warnings:
            embed = disnake.Embed(description=f"{config.no} This member doesn't have any warnings!", color=config.error_embed_color)
            await inter.send(embed=embed, ephemeral=True)
            return
        elif not warnings.get(str(warning)):
            embed = disnake.Embed(description=f"{config.no} Please provide a valid warning!", color=config.error_embed_color)
            await inter.send(embed=embed, ephemeral=True)
            return
        else:
            temp_warnings = warnings.copy()
            
            warnings.clear()
            for warn_num in temp_warnings:
                if int(warn_num) != int(warning):
                    warnings[warn_num] = temp_warnings[warn_num]
            
            warnings = json.dumps(warnings)
            warns_col.update_one(
                filter = {"guild_id": str(inter.guild.id)},
                update = {"$set": {
                    str(member.id): warnings
                }}
            )

        embed = disnake.Embed(description=f"{config.yes} Warning `{warning}` has been removed from **{member}**.", color=config.success_embed_color)
        
        await inter.send(embed=embed)


    @slash_warnremove.error
    async def slash_warnremove_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions[0].capitalize()}` permission.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == "member":
                embed = disnake.Embed(description=f"{config.no} Please specify the member you want to remove a warn from.", color=config.error_embed_color)
                await inter.response.send_message(embed=embed, ephemeral=True)
            elif error.param.name == "warning":
                embed = disnake.Embed(description=f"{config.no} Please specify the warning you want to remove.", color=config.error_embed_color)
                await inter.response.send_message(embed=embed, ephemeral=True)

    @slash_warn.error 
    async def slash_warn_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions[0].capitalize()}` permission.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == "member":
                embed = disnake.Embed(description=f"{config.no} Please specify the member you want to warn.", color=config.error_embed_color)
                await inter.response.send_message(embed=embed, ephemeral=True)
            elif error.param.name == "reason":
                embed = disnake.Embed(description=f"{config.no} Please specify the reason for the warn.", color=config.error_embed_color)
                await inter.response.send_message(embed=embed, ephemeral=True)
        
    
def setup(bot):
    bot.add_cog(Warn(bot))