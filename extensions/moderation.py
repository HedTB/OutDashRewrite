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

## -- FUNCTIONS -- ##

async def is_banned(guild: disnake.Guild, user: disnake.User):
    try:
        return True if await guild.fetch_ban(user) else False
    except:
        return False

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
    @commands.cooldown(1, config.cooldown_time, commands.BucketType.member)
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
    @commands.cooldown(1, config.cooldown_time, commands.BucketType.member)
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
    @commands.cooldown(1, config.cooldown_time, commands.BucketType.member)
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
    @commands.cooldown(1, config.cooldown_time, commands.BucketType.member)
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
    @commands.cooldown(1, config.cooldown_time, commands.BucketType.member)
    @is_moderator(ban_members=True)
    async def ban(self, ctx: commands.Context, member: disnake.Member, *, reason="No reason provided."):
        """Bans a member from the server."""
        
        if member == ctx.author:
            embed = disnake.Embed(description=f"{config.no} You can't ban yourself!", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif member == self.bot.user:
            embed = disnake.Embed(description=f"{config.no} I can't ban myself!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return

        embed = disnake.Embed(description=f"{config.yes} **{member}** was banned.", color=config.success_embed_color)
        dm_fail_embed = disnake.Embed(description=f"{config.yes} **{member}** was banned. I couldn't DM them though.", color=config.success_embed_color)
        dm_embed = disnake.Embed(description=f"{config.moderator} You have been banned from **{ctx.guild.name}**. \nReason: {reason}", color=config.embed_color)
        
        try:
            await member.send(embed=dm_embed)
            await member.ban(reason=reason)
            await ctx.send(embed=embed)
            
        except disnake.errors.HTTPException:
            await member.ban(reason=reason)
            await ctx.send(embed=dm_fail_embed)
            
    @commands.command()
    @commands.cooldown(1, config.cooldown_time, commands.BucketType.member)
    @is_moderator(ban_members=True)
    async def unban(self, ctx: commands.Context, user: disnake.User, *, reason="No reason provided."):
        """Unban a member from the server."""
        
        if not await is_banned(ctx.guild, user):
            embed = disnake.Embed(description=f"{config.no} This user isn't banned!")
            return await ctx.send(embed=embed)

        embed = disnake.Embed(description=f"{config.yes} **{user}** was unbanned.", color=config.success_embed_color)
        dm_fail_embed = disnake.Embed(description=f"{config.yes} **{user}** was unbanned. I couldn't DM them though.", color=config.success_embed_color)
        dm_embed = disnake.Embed(description=f"{config.moderator} You have been unbanned from **{ctx.guild.name}**.", color=config.embed_color)
        
        try:
            await ctx.guild.unban(user, reason=reason)
            await user.send(embed=dm_embed)
            await ctx.send(embed=embed)
            
        except disnake.errors.HTTPException:
            await ctx.guild.unban(user, reason=reason)
            await ctx.send(embed=dm_fail_embed)
            
    @commands.command()
    @commands.cooldown(1, config.cooldown_time, commands.BucketType.member)
    @is_moderator(kick_members=True)
    async def kick(self, ctx: commands.Context, member: disnake.Member, *, reason="No reason provided."):
        """Kicks a member from the server."""
        
        if member == ctx.author:
            embed = disnake.Embed(description=f"{config.no} You can't kick yourself!", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif member == self.bot.user:
            embed = disnake.Embed(description=f"{config.no} I can't kick myself!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return

        embed = disnake.Embed(description=f"{config.yes} **{member}** was kicked.", color=config.success_embed_color)
        dm_fail_embed = disnake.Embed(description=f"{config.yes} **{member}** was kicked. I couldn't DM them though.", color=config.success_embed_color)
        dm_embed = disnake.Embed(description=f"{config.moderator} You have been kicked from **{ctx.guild.name}**. \nReason: {reason}", color=config.embed_color)
        
        try:
            await member.send(embed=dm_embed)
            await member.kick(reason=reason)
            await ctx.send(embed=embed)
            
        except disnake.errors.HTTPException:
            await member.kick(reason=reason)
            await ctx.send(embed=dm_fail_embed)
            
    
    @commands.command(aliases=["timeout"])
    @commands.cooldown(1, config.cooldown_time, commands.BucketType.member)
    @is_moderator(timeout_members=True)
    async def mute(self, ctx: commands.Context, member: disnake.Member, length: str, *, reason: str = "No reason provided."):
        """Mute a member who's breaking the rules!"""
        
        if member == ctx.author:
            embed = disnake.Embed(description=f"{config.no} You can't mute yourself!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
        elif member == self.bot.user:
            embed = disnake.Embed(description=f"{config.no} I can't mute myself!", color=config.error_embed_color)
            await ctx.send(embed=embed)
            return
        
        seconds = functions.manipulate_time(length, return_type="seconds")
        if not seconds:
            embed = disnake.Embed(description=f"{config.no} Please provide a valid time format. \nExample:\n```10s = 10 seconds\n1m = 1 minute\n3h = 3 hours\n2d = 2 days```",
                                    color=config.error_embed_color)
            await ctx.send(embed=embed)

        embed = disnake.Embed(description=f"{config.yes} **{member.name}#{member.discriminator}** has been muted.\n**Reason:** {reason}", color=config.success_embed_color)
        
        await member.timeout(duration=int(seconds), reason=reason)
        await ctx.send(embed=embed)
    
    @commands.command(aliases=["untimeout"])
    @commands.cooldown(1, config.cooldown_time, commands.BucketType.member)
    @is_moderator(timeout_members=True)
    async def unmute(self, ctx: commands.Context, member: disnake.Member, *, reason: str = "No reason provided."):
        """Unmute a member and allow them to talk again."""
        
        if not member.current_timeout:
            embed = disnake.Embed(description=f"{config.no} This member isn't muted!", color=config.error_embed_color)
            return await ctx.send(embed=embed)

        embed = disnake.Embed(description=f"{config.yes} **{member.name}#{member.discriminator}** has been unmuted.", color=config.success_embed_color)
        await member.timeout(duration=None, reason=reason)
        await ctx.send(embed=embed)
        
    """
    ! CHANNEL MANAGEMENT
    
    These commands manages all channels.
    """
    
    @commands.command()
    @commands.cooldown(1, config.cooldown_time, commands.BucketType.member)
    @is_moderator(manage_channels=True)
    async def slowmode(self, ctx: commands.Context, seconds: int, channel: disnake.TextChannel = None):
        """Change the slowmode of a channel."""
        
        if not channel:
            channel = ctx.channel
        if seconds > 21600:
            embed = disnake.Embed(description=f"{config.no} The slowmode can't be over 21600 seconds.", color=config.error_embed_color)
            return await ctx.send(embed=embed)
        
        if channel == ctx.channel:
            embed = disnake.Embed(description=f"{config.yes} The slowmode has been set to `{seconds}` seconds.", color=config.success_embed_color)
        else:
            embed = disnake.Embed(description=f"{config.yes} The slowmode for {channel.mention} has been set to `{seconds}` seconds.", color=config.success_embed_color)
        
        await channel.edit(slowmode_delay=seconds)
        await ctx.send(embed=embed)
        
        
    """
    ! OTHER MODERATION
    
    All other moderation commands.
    """
    
    @commands.command(name="clear")
    @commands.cooldown(1, 10, commands.BucketType.member)
    @is_moderator(manage_messages=True)
    async def clear(self, ctx: commands.Context, amount: int, channel: disnake.TextChannel = None):
        """Clear up some messages from your channels!"""
        
        embed = disnake.Embed(description=f"{config.yes} ", color=config.success_embed_color)
        
        if not channel or channel and channel == ctx.channel:
            channel = ctx.channel
            deleted = await channel.purge(limit=amount)
            
            embed.description += f"Deleted {deleted} messsages." if not deleted == 1 else f"{config.yes} Deleted {deleted} messsage."
            await ctx.send(embed=embed)
            
        else:
            deleted = await channel.purge(limit=amount)
            embed.description += f"Deleted {deleted} messsages in <#{channel.id}>." if deleted != 1 else f"{config.yes} Deleted {deleted} messsage in <#{channel.id}>."
            
            await ctx.send(embed=embed)
    
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
        warnings = warns_data_obj.get_member_warnings(member)

        if not member:
            member = inter.author

        if len(warnings) == 0:
            embed = disnake.Embed(title=f"0 warnings for {member}", description=f"{config.info} This user doesn't have any warnings.", color=config.embed_color)
        else:
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
    async def slash_warnings_clear(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, reason: str = "No reason provided."):
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
            return await inter.send(embed=embed, ephemeral=True)
        
        elif member == self.bot.user:
            embed = disnake.Embed(description=f"{config.no} I can't ban myself!", color=config.error_embed_color)
            return await inter.send(embed=embed, ephemeral=True)
        
        embed = disnake.Embed(description=f"{config.yes} **{member}** was banned.", color=config.success_embed_color)
        dm_fail_embed = disnake.Embed(description=f"{config.yes} **{member}** was banned. I couldn't DM them though.", color=config.success_embed_color)
        dm_embed = disnake.Embed(description=f"{config.moderator} You was banned in **{inter.guild.name}**. \nReason: {reason}", color=config.embed_color)
        
        try:
            await member.send(embed=dm_embed)
            await member.ban(reason=reason)
            await inter.send(embed=embed)
            
        except disnake.errors.HTTPException:
            await member.ban(reason=reason)
            await inter.send(embed=dm_fail_embed)
            
    @commands.slash_command(name="unban", description="Unban a member from the server.")
    @is_moderator(ban_members=True)
    async def slash_unban(self, inter: disnake.ApplicationCommandInteraction, user: disnake.User, *, reason="No reason provided."):
        """Unban a member from the server.
        Parameters
        ----------
        user: The user to unban.
        reason: The reason for the unban.
        """
        
        if not await is_banned(inter.guild, user):
            embed = disnake.Embed(description=f"{config.no} This user isn't banned!")
            return await inter.send(embed=embed, ephemeral=True)

        embed = disnake.Embed(description=f"{config.yes} **{user}** was unbanned.", color=config.success_embed_color)
        dm_fail_embed = disnake.Embed(description=f"{config.yes} **{user}** was unbanned. I couldn't DM them though.", color=config.success_embed_color)
        dm_embed = disnake.Embed(description=f"{config.moderator} You have been unbanned from **{inter.guild.name}**.", color=config.embed_color)
        
        try:
            await inter.guild.unban(user, reason=reason)
            await inter.send(embed=embed)
            await user.send(embed=dm_embed)
            
        except disnake.errors.HTTPException:
            await inter.guild.unban(user, reason=reason)
            await inter.send(embed=dm_fail_embed)
    
    @commands.slash_command(name="kick", description="Kicks a member from the guild.")
    @is_moderator(kick_members=True)
    async def slash_kick(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, reason: str = "No reason provided."):
        """Kicks a member from the guild.
        Parameters
        ----------
        member: The member you want to kick.
        reason: The reason for the kick.
        """
        if member == inter.author:
            embed = disnake.Embed(description=f"{config.no} You can't kick yourself!", color=config.error_embed_color)
            return await inter.send(embed=embed, ephemeral=True)
        
        elif member == self.bot.user:
            embed = disnake.Embed(description=f"{config.no} I can't ban myself!", color=config.error_embed_color)
            return await inter.send(embed=embed, ephemeral=True)
        
        embed = disnake.Embed(description=f"{config.yes} **{member}** was banned.", color=config.success_embed_color)
        dm_fail_embed = disnake.Embed(description=f"{config.yes} **{member}** was banned. I couldn't DM them though.", color=config.success_embed_color)
        dm_embed = disnake.Embed(description=f"{config.moderator} You was banned in **{inter.guild.name}**. \nReason: {reason}", color=config.embed_color)
        
        try:
            await member.send(embed=dm_embed)
            await member.kick(reason=reason)
            await inter.send(embed=embed)
            
        except disnake.errors.HTTPException:
            await member.kick(reason=reason)
            await inter.send(embed=dm_fail_embed)
             
    @commands.slash_command(name="mute", description="Mute a member who's breaking the rules!")
    @is_moderator(timeout_members=True)
    async def slash_mute(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, length: str, *, reason: str = "No reason provided."):
        """Mute a member who's breaking the rules!"""
        
        if member == inter.author:
            embed = disnake.Embed(description=f"{config.no} You can't mute yourself!", color=config.error_embed_color)
            await inter.send(embed=embed)
            return
        elif member == self.bot.user:
            embed = disnake.Embed(description=f"{config.no} I can't mute myself!", color=config.error_embed_color)
            await inter.send(embed=embed)
            return
        
        seconds = functions.manipulate_time(length, return_type="seconds")
        if not seconds:
            embed = disnake.Embed(description=f"{config.no} Please provide a valid time format. \nExample:\n```10s = 10 seconds\n1m = 1 minute\n3h = 3 hours\n2d = 2 days```",
                                    color=config.error_embed_color)
            await inter.send(embed=embed, ephemeral=True)

        embed = disnake.Embed(description=f"{config.yes} **{member.name}#{member.discriminator}** has been muted.\n**Reason:** {reason}", color=config.success_embed_color)
        
        await member.timeout(duration=int(seconds), reason=reason)
        await inter.send(embed=embed)
    
    @commands.slash_command(name="unmute", description="Unmute a member and allow them to talk again.")
    @is_moderator(timeout_members=True)
    async def slash_unmute(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, reason: str = "No reason provided."):
        """Unmute a member and allow them to talk again.
        Parameters
        ----------
        member: The member you want to unmute.
        reason: The reason for the unmute.
        """
        
        if not member.current_timeout:
            embed = disnake.Embed(description=f"{config.no} This member isn't muted!", color=config.error_embed_color)
            return await inter.send(embed=embed, ephemeral=True)

        embed = disnake.Embed(description=f"{config.yes} **{member.name}#{member.discriminator}** has been unmuted.", color=config.success_embed_color)
        await member.timeout(duration=None, reason=reason)
        await inter.send(embed=embed)
    
    """
    ! CHANNEL MANAGEMENT
    
    These commands manages all channels.
    """
    
    @commands.slash_command(name="slowmode", description="Change the slowmode of a channel.")
    @is_moderator(manage_channels=True)
    async def slash_slowmode(self, inter: disnake.ApplicationCommandInteraction, seconds: int, channel: disnake.TextChannel = None):
        """Change the slowmode of a channel.
        Parameters
        ----------
        seconds: How many seconds the slowmode should be set to.
        channel: What channel to change slowmode of. Defaults to current channel.
        """
        
        if not channel:
            channel = inter.channel
        if seconds > 21600:
            embed = disnake.Embed(description=f"{config.no} The slowmode can't be over 21600 seconds.", color=config.error_embed_color)
            return await inter.send(embed=embed, ephemeral=True)
        
        if channel == inter.channel:
            embed = disnake.Embed(description=f"{config.yes} The slowmode has been set to `{seconds}` seconds.", color=config.success_embed_color)
        else:
            embed = disnake.Embed(description=f"{config.yes} The slowmode for {channel.mention} has been set to `{seconds}` seconds.", color=config.success_embed_color)
        
        await channel.edit(slowmode_delay=seconds)
        await inter.send(embed=embed)
     
    """
    ! OTHER MODERATION
    
    All other moderation commands.
    """
    
    @commands.slash_command(name="clear", description="Clear up some messages from your channels!")
    @is_moderator(manage_messages=True)
    async def slash_clear(self, inter: disnake.ApplicationCommandInteraction, amount: int, channel: disnake.TextChannel = None):
        """Clear up some messages from your channels!
        Parameters
        ----------
        amount: The amount of messages you want to delete.
        channel: The channel you want to delete from. Default is the current channel.
        """
        embed = disnake.Embed(description=f"{config.yes} ", color=config.success_embed_color)
        
        if not channel or channel and channel == inter.channel:
            channel = inter.channel
            deleted = await channel.purge(limit=amount)
            
            embed.description += f"Deleted {deleted} messsages." if not deleted == 1 else f"{config.yes} Deleted {deleted} messsage."
            await inter.send(embed=embed, ephemeral=True)
            
        else:
            deleted = await channel.purge(limit=amount)
            embed.description += f"Deleted {deleted} messsages in <#{channel.id}>." if deleted != 1 else f"{config.yes} Deleted {deleted} messsage in <#{channel.id}>."
            
            await inter.send(embed=embed)
    
    ## -- TEXT COMMAND HANDLERS -- ##
    
    @warn.error
    async def warn_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description="{emoji} You're missing the `{permission}` permission.".format(emoji=config.no, permission=error.missing_permissions[0].title().replace("_", " ")), color=config.error_embed_color)
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
            embed = disnake.Embed(description="{emoji} You're missing the `{permission}` permission.".format(emoji=config.no, permission=error.missing_permissions[0].title().replace("_", " ")), color=config.error_embed_color)
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
            embed = disnake.Embed(description="{emoji} You're missing the `{permission}` permission.".format(emoji=config.no, permission=error.missing_permissions[0].title().replace("_", " ")), color=config.error_embed_color)
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
            embed = disnake.Embed(description="{emoji} You're missing the `{permission}` permission.".format(emoji=config.no, permission=error.missing_permissions[0].title().replace("_", " ")), color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = disnake.Embed(description=f"{config.no} You need to specify who you want to ban.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error.original, disnake.errors.Forbidden):
            is_role_above_role = functions.is_role_above_role(ctx.guild.get_member(self.bot.user.id).top_role, ctx.author.top_role)
            
            if is_role_above_role:
                embed = disnake.Embed(description=f"{config.no} You don't have permission to ban this member.", color=config.error_embed_color)
                await ctx.send(embed=embed)
            else:
                embed = disnake.Embed(description=f"{config.no} I don't have permission to ban this member.", color=config.error_embed_color)
                await ctx.send(embed=embed)
                
    @unban.error
    async def unban_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description="{emoji} You're missing the `{permission}` permission.".format(emoji=config.no, permission=error.missing_permissions[0].title().replace("_", " ")), color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = disnake.Embed(description=f"{config.no} Please specify who you want to unban.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error.original, disnake.errors.Forbidden):
            embed = disnake.Embed(description=f"{config.no} I don't have permission to unban this user.", color=config.error_embed_color)
            await ctx.send(embed=embed)
                
    @kick.error 
    async def kick_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description="{emoji} You're missing the `{permission}` permission.".format(emoji=config.no, permission=error.missing_permissions[0].title().replace("_", " ")), color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = disnake.Embed(description=f"{config.no} You need to specify who you want to kick.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error.original, disnake.errors.Forbidden):
            is_role_above_role = functions.is_role_above_role(ctx.guild.get_member(self.bot.user.id).top_role, ctx.author.top_role)
            
            if is_role_above_role:
                embed = disnake.Embed(description=f"{config.no} You don't have permission to kick this member.", color=config.error_embed_color)
                await ctx.send(embed=embed)
            else:
                embed = disnake.Embed(description=f"{config.no} I don't have permission to kick this member.", color=config.error_embed_color)
                await ctx.send(embed=embed)
                
    @mute.error
    async def mute_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description="{emoji} You're missing the `{permission}` permission.".format(emoji=config.no, permission=error.missing_permissions[0].title().replace("_", " ")), color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == "member":
                embed = disnake.Embed(description=f"{config.no} Please specify the member you want to mute.", color=config.error_embed_color)
                await ctx.send(embed=embed)
            elif error.param.name == "length":
                embed = disnake.Embed(description=f"{config.no} Please specify for how long they should be muted.", color=config.error_embed_color)
                await ctx.send(embed=embed)
        elif isinstance(error.original, disnake.errors.Forbidden):
            is_role_above_role = functions.is_role_above_role(ctx.guild.get_member(self.bot.user.id).top_role, ctx.author.top_role)
            
            if is_role_above_role:
                embed = disnake.Embed(description=f"{config.no} You don't have permission to mute this member.", color=config.error_embed_color)
                await ctx.send(embed=embed)
            else:
                embed = disnake.Embed(description=f"{config.no} I don't have permission to mute this member.", color=config.error_embed_color)
                await ctx.send(embed=embed)
            
    @unmute.error
    async def unmute_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description="{emoji} You're missing the `{permission}` permission.".format(emoji=config.no, permission=error.missing_permissions[0].title().replace("_", " ")), color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == "member":
                embed = disnake.Embed(description=f"{config.no} Please specify the member you want to unmute.", color=config.error_embed_color)
                await ctx.send(embed=embed)
        elif isinstance(error.original, disnake.errors.Forbidden):
            is_role_above_role = functions.is_role_above_role(ctx.guild.get_member(self.bot.user.id).top_role, ctx.author.top_role)
            
            if is_role_above_role:
                embed = disnake.Embed(description=f"{config.no} You don't have permission to unmute this member.", color=config.error_embed_color)
                await ctx.send(embed=embed)
            else:
                embed = disnake.Embed(description=f"{config.no} I don't have permission to unmute this member.", color=config.error_embed_color)
                await ctx.send(embed=embed)
               
    @slowmode.error
    async def slowmode_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions[0].lower()}` permission.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = disnake.Embed(description=f"{config.no} Please specify what the slowmode should be set to.", color=config.error_embed_color)
            await ctx.send(embed=embed)
                
    @clear.error
    async def clear_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description="{emoji} You're missing the `{permission}` permission.".format(emoji=config.no, permission=error.missing_permissions[0].title().replace("_", " ")), color=config.error_embed_color)
            await ctx.send(embed=embed)
        if isinstance(error, commands.MissingRequiredArgument):
            embed = disnake.Embed(description=f"{config.no} Please specify how many messages you want to delete.", color=config.error_embed_color)
            await ctx.send(embed=embed)
                
    ## -- SLASH COMMAND HANDLERS -- ##

    @slash_warn_add.error
    async def slash_warn_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description="{emoji} You're missing the `{permission}` permission.".format(emoji=config.no, permission=error.missing_permissions[0].title().replace("_", " ")), color=config.error_embed_color)
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
            embed = disnake.Embed(description="{emoji} You're missing the `{permission}` permission.".format(emoji=config.no, permission=error.missing_permissions[0].title().replace("_", " ")), color=config.error_embed_color)
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
            embed = disnake.Embed(description="{emoji} You're missing the `{permission}` permission.".format(emoji=config.no, permission=error.missing_permissions[0].title().replace("_", " ")), color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = disnake.Embed(description=f"{config.no} You need to specify who you want to ban.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error.original, disnake.errors.Forbidden):
            is_role_above_role = functions.is_role_above_role(inter.guild.get_member(self.bot.user.id).top_role, inter.author.top_role)
            
            if is_role_above_role:
                embed = disnake.Embed(description=f"{config.no} You don't have permission to ban this member.", color=config.error_embed_color)
                await inter.response.send_message(embed=embed)
            else:
                embed = disnake.Embed(description=f"{config.no} I don't have permission to ban this member.", color=config.error_embed_color)
                await inter.response.send_message(embed=embed)
                
    @slash_unban.error
    async def slash_unban_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description="{emoji} You're missing the `{permission}` permission.".format(emoji=config.no, permission=error.missing_permissions[0].title().replace("_", " ")), color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = disnake.Embed(description=f"{config.no} You need to specify who you want to unban.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error.original, disnake.errors.Forbidden):
            embed = disnake.Embed(description=f"{config.no} I don't have permission to unban this user.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
    
    @slash_kick.error 
    async def slash_kick_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description="{emoji} You're missing the `{permission}` permission.".format(emoji=config.no, permission=error.missing_permissions[0].title().replace("_", " ")), color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = disnake.Embed(description=f"{config.no} You need to specify who you want to kick.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error.original, disnake.errors.Forbidden):
            is_role_above_role = functions.is_role_above_role(inter.guild.get_member(self.bot.user.id).top_role, inter.author.top_role)
            
            if is_role_above_role:
                embed = disnake.Embed(description=f"{config.no} You don't have permission to kick this member.", color=config.error_embed_color)
                await inter.response.send_message(embed=embed)
            else:
                embed = disnake.Embed(description=f"{config.no} I don't have permission to kick this member.", color=config.error_embed_color)
                await inter.response.send_message(embed=embed)
                
    @slash_mute.error
    async def slash_mute_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description="{emoji} You're missing the `{permission}` permission.".format(emoji=config.no, permission=error.missing_permissions[0].title().replace("_", " ")), color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == "member":
                embed = disnake.Embed(description=f"{config.no} Please specify the member you want to mute.", color=config.error_embed_color)
                await inter.response.send_message(embed=embed, ephemeral=True)
            elif error.param.name == "length":
                embed = disnake.Embed(description=f"{config.no} Please specify how long they should be muted.", color=config.error_embed_color)
                await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error.original, disnake.errors.Forbidden):
            is_role_above_role = functions.is_role_above_role(inter.guild.get_member(self.bot.user.id).top_role, inter.author.top_role)
            if is_role_above_role:
                embed = disnake.Embed(description=f"{config.no} You don't have permission to mute this member.", color=config.error_embed_color)
                await inter.response.send_message(embed=embed)
            elif is_role_above_role == False:
                embed = disnake.Embed(description=f"{config.no} I don't have permission to mute this member.", color=config.error_embed_color)
                await inter.response.send_message(embed=embed)
       
    @slash_unmute.error 
    async def slash_unmute_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description="{emoji} You're missing the `{permission}` permission.".format(emoji=config.no, permission=error.missing_permissions[0].title().replace("_", " ")), color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == "member":
                embed = disnake.Embed(description=f"{config.no} Please specify the member you want to unmute.", color=config.error_embed_color)
                await inter.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error.original, disnake.errors.Forbidden):
            is_role_above_role = functions.is_role_above_role(inter.guild.get_member(self.bot.user.id).top_role, inter.author.top_role)
            if is_role_above_role:
                embed = disnake.Embed(description=f"{config.no} You don't have permission to unmute this member.", color=config.error_embed_color)
                await inter.response.send_message(embed=embed)
            elif is_role_above_role == False:
                embed = disnake.Embed(description=f"{config.no} I don't have permission to unmute this member.", color=config.error_embed_color)
                await inter.response.send_message(embed=embed)
                
    @slash_slowmode.error 
    async def slash_slowmode_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `Manage Channels` permission.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
                
    @slash_clear.error 
    async def slash_clear_error(self, inter: disnake.ApplicationCommandInteraction, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description="{emoji} You're missing the `{permission}` permission.".format(emoji=config.no, permission=error.missing_permissions[0].title().replace("_", " ")), color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)
        if isinstance(error, commands.MissingRequiredArgument):
            embed = disnake.Embed(description=f"{config.no} Please specify how many messages you want to delete.", color=config.error_embed_color)
            await inter.response.send_message(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(Moderation(bot))