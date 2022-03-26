## -- IMPORTING -- ##

# MODULES
import disnake

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

## -- COG -- ##

class Moderation(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    ## -- TEXT COMMANDS -- ##
    
    """
    ! WARNINGS
    
    The warning system, such as viewing warnings, and obviously adding warnings.
    """
    
    @commands.group(name="warn")
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    @is_moderator(manage_guild=True)
    async def warn(self, ctx: commands.Context, member: disnake.Member, *, reason: str):
        """Warn a member for their bad actions!"""
        
        if ctx.invoked_subcommand != None:
            pass
        
        warns_data_obj = WarnsData(ctx.guild)

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
            
        warns_data_obj.add_warning(member, ctx.author, reason)

        embed = disnake.Embed(description=f"{config.yes} **{member.name}#{member.discriminator}** has been warned. | {reason}", color=config.success_embed_color)
        dm_embed = disnake.Embed(description=f"{config.moderator} You have been warned in **{ctx.guild.name}**.\n**Reason**: {reason}", color=config.logs_embed_color)
        
        await member.send(dm_embed)
        await ctx.send(embed=embed)
        
    @warn.command(name="remove")
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    @is_moderator(manage_guild=True)
    async def warn_remove(self, ctx: commands.Context, member: disnake.Member, warning_id: str, reason: str = "No reason provided."):
        """Remove a warning from a member."""
        
        warns_data_obj = WarnsData(ctx.guild)
        
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
            
        result = warns_data_obj.remove_warning(member, warning_id)
        
        if not result:
            embed = disnake.Embed(description=f"{config.no} Please provice a valid warning ID.", color=config.error_embed_color)
        else:
            embed = disnake.Embed(description=f"{config.yes} The warning with ID {warning_id} has been removed.", color=config.success_embed_color)
            
        await ctx.send(embed=embed)
        
        
    @commands.group(name="warnings")
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    async def warnings(self, ctx: commands.Context, member: disnake.Member = None):
        """View how many warnings you or another member has."""
        
        if ctx.invoked_subcommand != None:
            return
        if not member:
            member = ctx.author
        
        warns_data_obj = WarnsData(ctx.guild)

        if len(warnings) == 0:
            embed = disnake.Embed(title=f"0 warnings for {member}", description=f"{config.info} This user doesn't have any warnings.", color=config.embed_color)
        else:
            warnings = warns_data_obj.get_member_warnings(member)
            description = ""
            
            for warning in warnings:
                warning_num = warning
                warning = warnings[warning]
                reason, moderator, warn_time = warning["reason"], warning["moderator"], warning["time"]

                description +=  f"**#{warning_num} | Moderator: {self.bot.get_user(moderator)}**\n" + f"{reason} | {warn_time[:16]} UTC\n"

            embed = disnake.Embed(title=f"{len(warnings)} warnings for {member}", 
            description=description, color=config.embed_color)

        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar or config.default_avatar_url)
        await ctx.send(embed=embed)
        
    @warnings.command(name="clear")
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    @is_moderator(manage_guild=True)
    async def warnings_clear(self, ctx: commands.Context, member: disnake.Member, reason: str = "No reason provided."):
        """Clear all warnings of a member."""

        warns_data_obj = WarnsData(ctx.guild)
        warnings = warns_data_obj.get_member_warnings(member)
            
        if len(warnings) == 0:
            embed = disnake.Embed(description=f"{config.info} This user doesn't have any warnings!", color=config.embed_color)
            await ctx.send(embed=embed)
        else:
            warns_data_obj.update_warnings(member, {})
            functions.log_moderation(ctx.guild.id, ctx.author.id, f"Cleared warnings for <@{member.id}>", reason=reason)
    
    """
    ! PUNISH COMMANDS
    
    Commands for punishment, such as banning and kicking.
    """
    
    @commands.command()
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    @is_moderator(ban_members=True)
    async def ban(self, ctx: commands.Context,member:disnake.Member, *, reason="No reason provided."):
        """Bans a member from the server."""
        
        GuildData(ctx.guild)
        
        if member == ctx.author:
            embed = disnake.Embed(description=f"{config.no} You can't ban yourself!", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif member == self.bot.user:
            embed = disnake.Embed(description=f"{config.no} I can't ban myself!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return

        embed = disnake.Embed(description=f"{config.yes} **{member}** was banned.", color=config.success_emdisnakeor)
        dm_fail_embed = disnake.Embed(description=f"{config.yes} **{member}** was banned. I couldn't DM them though.", color=config.success_emdisnakeor)
        dm_embed = disnake.Embed(description=f"{config.moderator} You got banned from **{ctx.guild.name}**. \nReason: {reason}", color=config.embed_color)
        
        try:
            await member.send(embed=dm_embed)
            await member.ban(reason=reason)
            await ctx.send(embed=embed)
        except disnake.errors.HTTPException as e:
            if e.status == 400:
                await member.ban(reason=reason)
                await ctx.send(embed=dm_fail_embed)
    
    ## -- SLASH COMMANDS -- ##
    
    """
    ! WARNINGS
    
    The warning system, such as viewing warnings, and obviously adding warnings.
    """
    
    @commands.slash_command(name="warn", description="Add/remove warnings on a member.")
    async def slash_warn(self, inter: disnake.ApplicationCommandInteraction):
        pass
    
    @slash_warn.sub_command(name="add", description="Warn a member for their bad actions!")
    @is_moderator(manage_guild=True)
    async def slash_warn_add(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, reason: str = "No reason provided."):
        """Warn a member for their bad actions!"""
        
        warns_data_obj = WarnsData(inter.guild)

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
            
        warns_data_obj.add_warning(member, inter.author, reason)

        embed = disnake.Embed(description=f"{config.yes} **{member.name}#{member.discriminator}** has been warned. | {reason}", color=config.success_embed_color)
        dm_embed = disnake.Embed(description=f"{config.moderator} You have been warned in **{inter.guild.name}**.\n**Reason**: {reason}", color=config.logs_embed_color)
        
        await member.send(dm_embed)
        await inter.send(embed=embed)
        
    @slash_warn.sub_command(name="remove", description="Remove a warning from a member.")
    @is_moderator(manage_guild=True)
    async def slash_warn_remove(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, warning_id: str, reason: str = "No reason provided."):
        """Remove a warning from a member."""
        
        warns_data_obj = WarnsData(inter.guild)
        
        if member == inter.author:
            embed = disnake.Embed(description=f"{config.no} You can't remove warnings from yourself!", color=config.error_embed_color)
            await inter.send(embed=embed, ephemeral=True)
            return
        elif member.bot:
            embed = disnake.Embed(description=f"{config.no} Bots cannot have warnings!", color=config.error_embed_color)
            await inter.send(embed=embed, ephemeral=True)
            return
        elif functions.is_role_above_role(member.top_role, inter.author.top_role) or member.top_role == inter.author.top_role:
            embed = disnake.Embed(description=f"{config.no} You don't have permission to remove a warning from this member!", color=config.error_embed_color)
            await inter.send(embed=embed, ephemeral=True)
            return
            
        result = warns_data_obj.remove_warning(member, warning_id)
        
        if not result:
            embed = disnake.Embed(description=f"{config.no} Please provice a valid warning ID.", color=config.error_embed_color)
            return await inter.send(embed=embed, ephemeral=True)
        
        embed = disnake.Embed(description=f"{config.yes} Warning with ID {warning_id} has been removed from {member.mention}.", color=config.success_embed_color)    
        await inter.send(embed=embed)
        
    
    @commands.slash_command(name="warnings", description="Manage/view the warnings of a member.")
    async def slash_warnings(self, inter: disnake.ApplicationCommandInteraction):
        pass
    
    @slash_warnings.sub_command(name="view", description="View how many warnings you or another member has.")
    async def slash_warnings_view(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member = None):
        """View how many warnings you or another member has.
        Parameters
        ----------
        member: The member you want to view warnings for.
        """

        warns_data_obj = WarnsData(inter.guild)

        if not member:
            member = inter.author

        if len(warnings) == 0:
            embed = disnake.Embed(title=f"0 warnings for {member}", description=f"{config.info} This user doesn't have any warnings.", color=config.embed_color)
        else:
            warnings = warns_data_obj.get_member_warnings(member)
            description = ""

            for warning in warnings:
                warning = warnings[warning]
                
                reason = warning["reason"]
                moderator = warning["moderator"]
                warn_time = warning["time"]

                description +=  f"**{warning['id']} | Moderator: {self.bot.get_user(moderator)}**\n" + f"{reason} | {warn_time[:16]} UTC\n"

            embed = disnake.Embed(title=f"{len(warnings)} warnings for {member}", 
            description=description, color=config.embed_color)

        embed.set_footer(text=f"Requested by {inter.author}", icon_url=inter.author.avatar or config.default_avatar_url)
        await inter.send(embed=embed)
        
    @slash_warnings.sub_command(name="clear")
    @is_moderator(manage_guild=True)
    async def warnings_clear(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, reason: str = "No reason provided."):
        """Clear all warnings of a member."""

        warns_data_obj = WarnsData(inter.guild)
        warnings = warns_data_obj.get_member_warnings(member)
            
        if len(warnings) == 0:
            embed = disnake.Embed(description=f"{config.no} This user doesn't have any warnings!", color=config.error_embed_color)
            return await inter.send(embed=embed, ephemeral=True)
        
        warns_data_obj.update_warnings(member, {})
        functions.log_moderation(inter.guild.id, inter.author.id, f"Cleared warnings for <@{member.id}>", reason=reason)
        
        embed = disnake.Embed(description=f"{config.yes} Cleared all warnings for {member.mention} successfully.", color=config.success_embed_color)
        await inter.send(embed=embed)
    
    
    """
    ! PUNISH COMMANDS
    
    Commands for punishment, such as banning and kicking.
    """
    
    @commands.slash_command(name="ban", description="Ban a member from the guild.")
    @is_moderator(ban_members=True)
    async def slash_ban(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, reason: str = "No reason provided."):
        """Ban a member from the guild.
        Parameters
        ----------
        member: The member you want to ban.
        reason: The reason for the ban.
        """
        if member == inter.author:
            embed = disnake.Embed(description=f"{config.no} You can't ban yourself!", color=config.error_embed_color)
            await inter.send(embed=embed)
        elif member == self.bot.user:
            embed = disnake.Embed(description=f"{config.no} I can't ban myself!", color=config.error_embed_color)
            await inter.send(embed=embed)
            return
        
        embed = disnake.Embed(description=f"{config.yes} **{member}** was banned.", color=config.success_embed_color)
        dm_fail_embed = disnake.Embed(description=f"{config.yes} **{member}** was banned. I couldn't DM them though.", color=config.success_embed_color)
        dm_embed = disnake.Embed(description=f"{config.moderator} You was banned in **{inter.guild.name}**. \nReason: {reason}", color=config.embed_color)
        
        try:
            await member.send(embed=dm_embed)
            await member.ban(reason=reason)
            await inter.send(embed=embed)
        except disnake.errors.HTTPException as e:
            if e.status == 400:
                await member.ban(reason=reason)
                await inter.send(embed=dm_fail_embed)
    
    ## -- TEXT COMMAND HANDLERS -- ##
    
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
                embed.description = "Please specify who to remove a warning from!"
            elif missing_argument == "warning_id":
                embed.description += "Please specify what warning to remove!"
    
            await ctx.send(embed=embed)
        elif isinstance(error, SettingsLocked):
            embed = disnake.Embed(description=f"{config.no} The server's settings are locked.", color=config.error_embed_color)
            await ctx.send(embed=embed)
            
    @warnings_clear.error
    async def warnings_clear_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions[0].capitalize()}` permission.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            missing_argument = error.param.name
            embed = disnake.Embed(description=f"{config.no} ", color=config.error_embed_color)
    
            if missing_argument == "member":
                embed.description = "Please specify whose warnings to clear."
    
            await ctx.send(embed=embed)
        elif isinstance(error, SettingsLocked):
            embed = disnake.Embed(description=f"{config.no} The server's settings are locked.", color=config.error_embed_color)
            await ctx.send(embed=embed)
    
    @ban.error 
    async def ban_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions[0].capitalize()}` permission.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = disnake.Embed(description=f"{config.no} You need to specify who you want to ban.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error.original, disnake.errors.Forbidden):
            is_role_above_role = functions.is_role_above_role(ctx.guild.get_member(self.bot.user.id).top_role, ctx.author.top_role)
            
            if is_role_above_role:
                embed = disnake.Embed(description=f"{config.no} You don't have permission to ban this member.", color=config.error_embed_color)
                await ctx.send(embed=embed)
            elif is_role_above_role == False:
                embed = disnake.Embed(description=f"{config.no} I don't have permission to ban this member.", color=config.error_embed_color)
                await ctx.send(embed=embed)
                
    ## -- SLASH COMMAND HANDLERS -- ##

    @slash_warn_add.error
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
                
    @slash_warn_remove.error
    async def slash_warnremove_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions[0].capitalize()}` permission.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == "member":
                embed = disnake.Embed(description=f"{config.no} Please specify the member you want to remove a warn from.", color=config.error_embed_color)
                await inter.response.send_message(embed=embed, ephemeral=True)
            elif error.param.name == "warning_id":
                embed = disnake.Embed(description=f"{config.no} Please specify the warning you want to remove.", color=config.error_embed_color)
                await inter.response.send_message(embed=embed, ephemeral=True)
    
    @slash_ban.error 
    async def slash_ban_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions[0].capitalize()}` permission.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = disnake.Embed(description=f"{config.no} You need to specify who you want to ban.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error.original, disnake.errors.Forbidden):
            is_role_above_role = functions.is_role_above_role(inter.guild.get_member(self.bot.user.id).top_role, inter.author.top_role)
            if is_role_above_role:
                embed = disnake.Embed(description=f"{config.no} You don't have permission to ban this member.", color=config.error_embed_color)
                await inter.response.send_message(embed=embed)
            elif is_role_above_role == False:
                embed = disnake.Embed(description=f"{config.no} I don't have permission to ban this member.", color=config.error_embed_color)
                await inter.response.send_message(embed=embed)


def setup(bot):
    bot.add_cog(Moderation(bot))