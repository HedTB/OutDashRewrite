## -- IMPORTING -- ##

# MODULES
import asyncio
import functools
import typing
import disnake
import os
import certifi
import random
import logging

from disnake.ext import commands
from dotenv import load_dotenv
from disrank.generator import Generator

# FILES
from utils import config
from utils import functions
from utils.checks import *
from utils.classes import *

## -- VARIABLES -- ##

load_dotenv()

logger = logging.getLogger("OutDash")

AnyContext = typing.Union[commands.Context, disnake.ApplicationCommandInteraction]

## -- FUNCTIONS -- ##

def get_variables(member: disnake.Member, guild: disnake.Guild):
    return {
        # member variables
        "{member_username}": str(member), "{member_name}": member.name, "{member_discriminator}": member.discriminator, "{member_mention}": member.mention, "{member_avatar}": member.avatar.url,

        # guild variables
        "{guild_name}": guild.name, "{guild_icon}": guild.icon.url, "{guild_member_count}": guild.member_count,
    }

def format_variables(string: str, original_variables: dict):
    variables = {}
    result = re.findall(r"{(\w+)}", string)

    for value in result:
        variables.update({value: original_variables["{" + value + "}"]})

    return str.format(string, **variables)

def insert_variables(message: dict | str, **kwargs):
    ctx: commands.Context = kwargs.get("ctx")
    member: disnake.Member = kwargs.get("member")
    variables: dict = kwargs.get("variables", None)

    if not member and not ctx:
        return None

    try:
        guild = ctx.guild
        member = ctx.author
    except AttributeError:
        guild = member.guild

    variables = variables or get_variables(member, guild)

    if isinstance(message, dict):
        to_pop = {}

        for key in message:
            value = message[key]

            if isinstance(value, dict):
                message[key] = insert_variables(value, **kwargs)
                continue

            elif isinstance(value, str):
                message[key] = format_variables(value, variables)
                continue

    elif isinstance(message, str):
        message = format_variables(message, variables)

    return message

def xp_to_levelup(lvl, xp=0):
    lvl -= 1
    return 5 * (lvl ** 2) + (50 * lvl) + 100 - xp

def total_xp_for_level(lvl, current_total_xp):
    total_xp = 0

    for level in range(0, lvl):
        total_xp += xp_to_levelup(level, 0)

    return total_xp - current_total_xp

def add_xp(member: disnake.Member, amount: int):
    member_data_obj = MemberData(member)
    member_data = member_data_obj.get_guild_data()

    level = member_data["level"]
    total_xp = member_data["total_xp"]
    xp = member_data["xp"]

    update = {}
    xp_for_levelup = xp_to_levelup(level, xp)

    update["total_xp"] = total_xp + amount

    if xp_for_levelup <= 0:
        update["level"] = level + 1
        update["xp"] = 0

        logger.debug(f"{member} is now level {level + 1}!")
    else:
        update["xp"] = xp + amount
        logger.debug(
            f"{member} has been given {amount} XP, they now have a total of {total_xp + amount} XP!")

    member_data_obj.update_guild_data(update)

    if xp_for_levelup <= 0:
        return "level_up", level + 1
    else:
        return "xp_add", None

def generate_card(args):
    return Generator().generate_profile(**args)

## -- COG -- ##


class Leveling(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    ## -- FUNCTIONS -- ##
    
    @staticmethod
    def get_levelup_message(ctx: AnyContext, **kwargs):
        data_obj = GuildData(ctx.guild)
        member_data_obj = MemberData(ctx.author)

        data = data_obj.get_data()
        member_data = member_data_obj.get_guild_data()
        
        raw_message = kwargs.get("raw_message", data["leveling_message"]["content"])
        
        variables = get_variables(ctx.author, ctx.guild)
        variables.update({
            "{new_level}": member_data["level"],
            "{previous_level}": member_data["level"] - 1,

            "{new_xp}": member_data["xp"],
            "{previous_xp}": member_data["xp"] - random.randint(17, 27),

            "{total_xp}": member_data["total_xp"],
        })

        return insert_variables(
            raw_message, variables=variables, member=ctx.author
        )

    ## -- TEXT COMMANDS -- ##

    """
    ! USER COMMANDS
    
    The user commands, such as rank.
    """

    @commands.command(name="rank")
    @commands.cooldown(1, config.cooldown_time, commands.BucketType.member)
    async def rank(self, ctx: commands.Context, member: disnake.Member = None):
        if not member:
            member = ctx.author

        member_data_obj = MemberData(member)
        member_data = member_data_obj.get_guild_data()

        level = member_data.get("level")
        xp = member_data.get("xp")

        func = functools.partial(generate_card, {
            "profile_image": member.avatar.url,
            "level": level,

            "current_xp": 0,
            "user_xp": xp,
            "next_xp": xp_to_levelup(level + 1),

            "user_position": 1,
            "user_name": str(member),
            "user_status": member.status.name
        })
        image = await asyncio.get_event_loop().run_in_executor(None, func)

        file = disnake.File(fp=image, filename="card.png")
        await ctx.send(file=file)

    """
    ! SETTING COMMANDS
    
    The commands which manages the way OutDash levels users in guilds.
    """

    @commands.group(name="leveling", aliases=["level"])
    async def leveling(self, ctx: commands.Context):
        pass

    @leveling.command(name="enable")
    @commands.cooldown(1, config.cooldown_time, commands.BucketType.member)
    @is_moderator(manage_guild=True)
    async def leveling_enable(self, ctx: commands.Context):
        """Enable the leveling feature on your guild."""

        data_obj = GuildData(ctx.guild)
        embed = disnake.Embed(
            description=f"{config.yes} The leveling feature has been enabled.",
            color=config.success_embed_color,
        )

        data_obj.update_data({"leveling_toggle": True})
        await ctx.send(embed=embed)

    @leveling.command(name="disable")
    @commands.cooldown(1, config.cooldown_time, commands.BucketType.member)
    @is_moderator(manage_guild=True)
    async def leveling_disable(self, ctx: commands.Context):
        """Disable the leveling feature on your guild."""

        data_obj = GuildData(ctx.guild)
        embed = disnake.Embed(
            description = f"{config.yes} The leveling feature has been disabled.",
            color = config.success_embed_color,
        )

        data_obj.update_data({"leveling_toggle": False})
        await ctx.send(embed=embed)

    @leveling.group(name="message")
    @commands.cooldown(1, config.cooldown_time, commands.BucketType.member)
    @is_moderator(manage_guild=True)
    async def leveling_message(self, ctx: commands.Context):
        if ctx.invoked_subcommand != None:
            return

        levelup_message = self.get_levelup_message(ctx)
        embed = disnake.Embed(
            description=f"{config.info} A levelup message would look like this:\n\n{levelup_message}",
            color=config.embed_color,
        )
        await ctx.send(embed=embed)

    @leveling_message.command(name="deletion", aliases=["delete_after"])
    @commands.cooldown(1, config.cooldown_time, commands.BucketType.member)
    @is_moderator(manage_guild=True)
    async def leveling_message_deletion(self, ctx: commands.Context, delay: int):
        """Set the levelup message deletion delay."""

        data_obj = GuildData(ctx.guild)
        data = data_obj.get_data()

        embed = disnake.Embed(
            description=f"{config.yes} The levelup message deletion delay has been set to {str(delay)} seconds.",
            color=config.success_embed_color,
        )

        if isinstance(delay, (int, float)) and delay > 60:
            embed.description = f"{config.no} The levelup message deletion delay cannot be more than 60 seconds."
            embed.color = config.error_embed_color
        else:
            data["leveling_message"]["delete_after"] = delay
            data_obj.update_data(data)

        await ctx.send(embed=embed)

    @leveling_message.command(name="content")
    @is_moderator(manage_guild=True)
    async def leveling_message_content(self, ctx: commands.Context, content: str):
        """Edit the levelup message content."""

        data_obj = GuildData(ctx.guild)
        data = data_obj.get_data()

        levelup_message = self.get_levelup_message(ctx, raw_message=content)
        embed = disnake.Embed(
            description=f"{config.yes} A levelup message would now look like:\n\n{levelup_message}",
            color=config.success_embed_color,
        )

        data["leveling_message"]["content"] = content
        data_obj.update_data(data)

        await ctx.send(embed=embed)

    ## -- SLASH COMMANDS -- ##

    """
    ! USER COMMANDS
    
    The user commands, such as rank.
    """

    @commands.slash_command()
    @commands.cooldown(1, config.cooldown_time, commands.BucketType.member)
    async def rank(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member = None):
        if not member:
            member = inter.author

        member_data_obj = MemberData(member)
        member_data = member_data_obj.get_guild_data()

        level = member_data.get("level")
        xp = member_data.get("xp")

        func = functools.partial(generate_card, {
            "profile_image": member.avatar.url,
            "level": level,

            "current_xp": 0,
            "user_xp": xp,
            "next_xp": xp_to_levelup(level + 1),

            "user_position": 1,
            "user_name": str(member),
            "user_status": member.status.name
        })
        image = await asyncio.get_event_loop().run_in_executor(None, func)

        file = disnake.File(fp=image, filename="card.png")
        await inter.send(file=file)

    """
    ! SETTING COMMANDS
    
    The commands which manages the way OutDash levels users in guilds.
    """

    @commands.slash_command(name="leveling")
    async def slash_leveling(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @slash_leveling.sub_command(name="toggle")
    @is_moderator(manage_guild=True)
    async def slash_leveling_toggle(self, inter: disnake.ApplicationCommandInteraction, toggle: bool):
        """Disable the leveling feature on your guild.
        Parameters
        ----------
        toggle: Whether to enable or disable the leveling feature.
        """

        data_obj = GuildData(inter.guild)
        embed = disnake.Embed(
            description=f"{config.yes} The leveling feature has been {'disabled' if not toggle else 'enabled'}.",
            color=config.success_embed_color,
        )

        data_obj.update_data({"leveling_toggle": toggle})
        await inter.send(embed=embed)

    @slash_leveling.sub_command_group(name="message")
    async def slash_leveling_message(self, inter: disnake.ApplicationCommandInteraction):
        """View or manage the levelup message."""
        pass

    @slash_leveling_message.sub_command(name="view")
    @is_moderator(manage_guild=True)
    async def slash_leveling_message_view(self, inter: disnake.ApplicationCommandInteraction):
        """View the current levelup message."""

        levelup_message = self.get_levelup_message(inter)
        embed = disnake.Embed(
            f"{config.info} A levelup message would look like this:\n\n{levelup_message}"
        )
        await inter.send(embed=embed)

    @slash_leveling_message.sub_command(name="deletion")
    @is_moderator(manage_guild=True)
    async def slash_leveling_message_deletion(self, inter: disnake.ApplicationCommandInteraction, delay: int):
        """Set the levelup message deletion delay.
        Parameters
        ----------
        delay: The levelup message deletion delay.
        """

        data_obj = GuildData(inter.guild)
        data = data_obj.get_data()

        embed = disnake.Embed(
            description=f"{config.yes} The levelup message deletion delay has been set to {str(delay)} seconds.",
            color=config.success_embed_color,
        )

        if isinstance(delay, (int, float)) and delay > 60:
            embed.description = f"{config.no} The levelup message deletion delay cannot be more than 60 seconds."
            embed.color = config.error_embed_color
        else:
            data["leveling_message"]["delete_after"] = delay
            data_obj.update_data(data)

        await inter.send(embed=embed, ephemeral=delay > 60)

    @slash_leveling_message.sub_command(name="content")
    @is_moderator(manage_guild=True)
    async def slash_leveling_message_content(self, inter: disnake.ApplicationCommandInteraction, content: str):
        """Edit the levelup message content.
        Parameters
        ----------
        content: What the levelup message content should be set to.
        """

        data_obj = GuildData(inter.guild)
        data = data_obj.get_data()
        
        levelup_message = self.get_levelup_message(inter, raw_message=content)
        embed = disnake.Embed(
            description=f"{config.yes} A levelup message would now look like:\n\n{levelup_message}",
            color=config.success_embed_color,
        )

        data["leveling_message"]["content"] = content
        data_obj.update_data(data)

        await inter.send(embed=embed)


def setup(bot):
    bot.add_cog(Leveling(bot))