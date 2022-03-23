## -- IMPORTING -- ##

# MODULES
from re import M
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
from utils import config
from utils import functions
from utils.checks import *

## -- VARIABLES -- ##

mongo_login = os.environ.get("MONGO_LOGIN")
client = MongoClient(mongo_login, tlsCAFile=certifi.where())
db = client[config.database_collection]

server_data_col = db["server_data"]
warns_col = db["warns"]


class Warnings(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        
    ## -- TEXT COMMANDS -- ##
    
    @commands.group(name="warn")
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    async def warn(self, ctx: commands.Context, member: disnake.Member, *, reason: str):
        """Warn a member for their bad actions!"""
        
        if ctx.invoked_subcommand != None:
            pass
        
        result = functions.get_warn_data(ctx.guild.ctx, member.id)

        if member == ctx.author:
            embed = disnake.Embed(description=f"{config.no} You can't warn yourself!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
        elif member.bot:
            embed = disnake.Embed(description=f"{config.no} You can't warn a bot!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
        elif functions.is_role_above_role(member.top_role, ctx.author.top_role) or member.top_role == ctx.author.top_role:
            embed = disnake.Embed(description=f"{config.no} You don't have permission to warn this member!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return

        try:
            warnings = result[str(member.id)]
        except Exception as error:
            warnings = [{
                "moderator": ctx.author.id, 
                "reason": reason, 
                "time": str(datetime.datetime.utcnow())
            }]
            
        if not warnings or type(warnings) == list or dict:
            warns_col.update_one({"guild_id": str(ctx.guild.id)}, {"$set": {
                str(member.id): json.dumps(warnings)
            }})
        else:
            warnings = json.loads(warnings)
            
            warnings.append({
                "moderator": ctx.author.id, 
                "reason": reason, 
                "time": str(datetime.datetime.utcnow())
            })
            warnings = json.dumps(warnings)

            warns_col.update_one(
                filter = {"guild_id": str(ctx.guild.id)},
                update = {"$set": {
                    str(member.id): warnings
                }}
            )

        embed = disnake.Embed(description=f"{config.yes} **{member.name}#{member.discriminator}** has been warned.", color=config.success_embed_color)
        dm_embed = disnake.Embed(description=f"{config.moderator} You have been warned in **{ctx.guild.name}**.\n**Reason**: {reason}", color=config.logs_embed_color)
        
        await member.send(dm_embed)
        await ctx.send(embed=embed)

    @warn.command(name="remove")
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    async def warn_remove(self, ctx: commands.Context, member: disnake.Member, warn_number: int, reason: str = "No reason provided."):
        """Remove a warning from a member."""
        
        print(member)
        
        query = {"guild_id": str(ctx.guild.id)}
        
        result = functions.get_warn_data(ctx.guild.id, member.id)
        warnings = result.get(str(member.id))
        
        if member == ctx.author:
            embed = disnake.Embed(description=f"{config.no} You can't remove warnings from yourself!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
        elif member.bot:
            embed = disnake.Embed(description=f"{config.no} Bots cannot have warnings!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
        elif functions.is_role_above_role(member.top_role, ctx.author.top_role) or member.top_role == ctx.author.top_role:
            embed = disnake.Embed(description=f"{config.no} You don't have permission to remove a warning from this member!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
        
        print(warnings)
        if not warnings or type(warnings) == list or dict:
            warns_col.update_one(query, {"$set": {
                str(member.id): "[]"
            }})
            await self.warn_remove(ctx, member, warn_number, reason)
            
        else:
            warnings = json.loads(warnings)
            
            try:
                warning = warnings[warn_number + 1]
                
                print(warning)
            except IndexError:
                embed = disnake.Embed(description=f"{config.no} Invalid warning!", color=config.error_embed_color)
                
            await ctx.send(embed=embed)
    
    

    @commands.group(name="warnings")
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    async def warnings(self, ctx: commands.Context, member: disnake.Member = None):
        """View how many warnings you or another member has."""
        
        if ctx.invoked_subcommand != None:
            return
        
        result = warns_col.find_one({
            "guild_id": str(ctx.guild.id)
        })

        if not member:
            member = ctx.author

        try:
            warnings = result[str(member.id)]
            warnings = json.loads(warnings)
        except Exception:
            warnings = None

        if not result:
            warns_col.insert_one({
                "guild_id": str(ctx.guild.id)
            })
            await self.warnings(ctx, member)
            
            return
        elif not warnings or len(warnings) == 0:
            embed = disnake.Embed(title=f"0 warnings for {member}", description=f"{config.info} This user doesn't have any warnings.", color=config.embed_color)
        else:
            warnings = json.loads(warnings)
            recent_warning = int(list(warnings.keys())[-1]) or 1
            description = ""
            
            for warning in warnings:
                warning_num = warning
                warning = warnings[warning]
                reason = warning["reason"]
                moderator = warning["moderator"]
                warn_time = warning["time"]

                description +=  f"**#{warning_num} | Moderator: {self.bot.get_user(moderator)}**\n" + f"{reason} | {warn_time[:16]} UTC\n"

            embed = disnake.Embed(title=f"{recent_warning} warnings for {member}", 
            description=description, color=config.embed_color)

        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar or config.default_avatar_url)
        await ctx.send(embed=embed)
        
    @warnings.command(name="clear")
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    @is_moderator()
    async def warningsclear(self, ctx: commands.Context, member: disnake.Member, reason: str = "No reason provided."):
        """Clear all warnings of a member."""

        query = {
            "guild_id": str(ctx.guild.id)
        }
        result = warns_col.find_one(query)

        try:
            warnings = result[str(member.id)]
            warnings = json.loads(warnings)
        except Exception:
            warnings = None

        if not result:
            warns_col.insert_one({
                "guild_id": str(ctx.guild.id)
            })
            await self.slash_warnings_clear(ctx, member, reason)
            
            return
        elif not warnings or len(warnings) == 0:
            embed = disnake.Embed(description=f"{config.info} This user doesn't have any warnings!", color=config.embed_color)
            await ctx.send(embed=embed)
        else:
            warns_col.update_one(query, {"$set": {
                str(member.id): "[]"
            }})
            functions.log_moderation(ctx.guild.id, ctx.author.id, f"Cleared warnings for <@{member.id}>", reason=reason)
    
        
    ## -- SLASH COMMANDS -- ##
    
    @commands.slash_command(name="warnings", description="Manage/view all warnings of a member.")
    async def slash_warnings(self, inter: disnake.ApplicationCommandInteraction):
        pass
    
    @slash_warnings.sub_command(name="view", description="View how many warnings you or another member has.")
    async def slash_warnings_view(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member = None):
        """View how many warnings you or another member has.
        Parameters
        ----------
        member: The member you want to view warnings for.
        """

        result = warns_col.find_one({
            "guild_id": str(inter.guild.id)
        })

        if not member:
            member = inter.author

        try:
            warnings = result[str(member.id)]
            warnings = json.loads(warnings)
        except Exception:
            warnings = None

        if not result:
            warns_col.insert_one({
                "guild_id": str(inter.guild.id)
            })
            await self.slash_warnings_view(inter, member)
            
            return
        elif not warnings or len(warnings) == 0:
            embed = disnake.Embed(title=f"0 warnings for {member}", description=f"{config.info} This user doesn't have any warnings.", color=config.embed_color)
        else:
            warnings = json.loads(warnings)
            description = ""

            for warning in warnings:
                warning_num = warning
                warning = warnings[warning]
                
                reason = warning["reason"]
                moderator = warning["moderator"]
                warn_time = warning["time"]

                description +=  f"**#{warning_num} | Moderator: {self.bot.get_user(moderator)}**\n" + f"{reason} | {warn_time[:16]} UTC\n"

            embed = disnake.Embed(title=f"{len(warnings)} warnings for {member}", 
            description=description, color=config.embed_color)

        embed.set_footer(text=f"Requested by {inter.author}", icon_url=inter.author.avatar or config.default_avatar_url)
        await inter.send(embed=embed)
        
    @slash_warnings.sub_command(name="clear", description="Clear all warnings of a member.")
    @is_moderator()
    async def slash_warnings_clear(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, reason: str = "No reason provided."):
        """Clear all warnings of a member
        Parameters
        ----------
        member: The member to clear warnings from.
        reason: The reason to clear the warnings.
        """

        query = {
            "guild_id": str(inter.guild.id)
        }
        result = warns_col.find_one(query)

        try:
            warnings = result[str(member.id)]
            warnings = json.loads(warnings)
        except Exception:
            warnings = None

        if not result:
            warns_col.insert_one({
                "guild_id": str(inter.guild.id)
            })
            await self.slash_warnings_clear(inter, member, reason)
            
            return
        elif not warnings or len(warnings) == 0:
            embed = disnake.Embed(description=f"{config.info} This user doesn't have any warnings!", color=config.embed_color)
            await inter.send(embed=embed, ephemeral=True)
        else:
            warns_col.update_one(query, {"$set": {
                str(member.id): "[]"
            }})
            functions.log_moderation(inter.guild.id, inter.author.id, f"Cleared warnings for <@{member.id}>", reason=reason)

    ## -- TEXT COMMAND ERRORS -- ##
    
    @warn.error
    async def warn_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions[0].capitalize()}` permission.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            missing_argument = error.param.name
            embed = disnake.Embed(description=f"{config.no} ", color=config.error_embed_color)
            
            if missing_argument == "member":
                embed.description += "Please specify the member you want to warn!"
            elif missing_argument == "reason":
                embed.description += "Please specify the reason for the warn!"
            
            await ctx.send(embed=embed)
            
    @warn_remove.error
    async def warn_remove_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions[0].capitalize()}` permission.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            missing_argument = error.param.name
            embed = disnake.Embed(description=f"{config.no} ", color=config.error_embed_color)
    
            if missing_argument == "member":
                embed.description = "Please specify the member to remove a warning from!"
            elif missing_argument == "warn_number":
                embed.description += "Please specify what warning to remove!"
    
            await ctx.send(embed=embed)
        elif isinstance(error, SettingsLocked):
            embed = disnake.Embed(description=f"{config.no} The server's settings are locked.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        
    
def setup(bot):
    bot.add_cog(Warnings(bot))