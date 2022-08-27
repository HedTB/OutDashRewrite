## -- IMPORTING -- ##

# MODULES
import typing
import disnake
import random
import logging

from disnake.ext import commands
from dotenv import load_dotenv
from typing import *

# FILES
from utils import config, functions, colors

from utils.checks import *
from utils.data import *
from utils.emojis import *
from utils import rankcard

## -- VARIABLES -- ##

load_dotenv()

logger = logging.getLogger("OutDash")

AnyContext = typing.Union[commands.Context,
                          disnake.ApplicationCommandInteraction]

## -- FUNCTIONS -- ##


def get_variables(member: disnake.Member, guild: disnake.Guild):
    return {
        # member variables
        "{member_username}": str(member),
        "{member_name}": member.name,
        "{member_discriminator}": member.discriminator,
        "{member_mention}": member.mention,
        "{member_avatar}": member.avatar.url,
        # guild variables
        "{guild_name}": guild.name,
        "{guild_icon}": guild.icon.url,
        "{guild_member_count}": guild.member_count,
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


def xp_to_levelup(lvl: int, xp: int = 0) -> int:
    lvl -= 1
    return 5 * (lvl ** 2) + (50 * lvl) + 100 - xp


def total_xp_for_level(lvl: int, current_total_xp: int = 0) -> int:
    total_xp = 0

    for level in range(0, lvl):
        total_xp += xp_to_levelup(level, 0)

    return total_xp - current_total_xp


def add_xp(member: disnake.Member, amount: int) -> tuple[bool, int | None]:
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
            f"{member} has been given {amount} XP, they now have a total of {total_xp + amount} XP!"
        )

    member_data_obj.update_guild_data(update)

    if xp_for_levelup <= 0:
        return True, level + 1
    else:
        return False, level


def remove_xp(member: disnake.Member, amount: int) -> tuple[bool, int | None]:
    member_data_obj = MemberData(member)
    member_data = member_data_obj.get_guild_data()

    level = member_data["level"]
    total_xp = member_data["total_xp"]
    xp = member_data["xp"]

    update = {}
    xp_for_levelup = xp_to_levelup(level, xp)

    update["total_xp"] = total_xp - amount

    if xp_for_levelup <= 0:
        update["level"] = level - 1
        update["xp"] = 0

        logger.debug(f"{member} is now level {level - 1}!")
    else:
        update["xp"] = xp - amount
        logger.debug(
            f"{member} has lost {amount} XP, they now have a total of {total_xp - amount} XP!"
        )

    member_data_obj.update_guild_data(update)

    if xp_for_levelup <= 0:
        return True, level - 1
    else:
        return False, None


## -- COG -- ##


class Leveling(commands.Cog):
    name = ":bar_chart: Leveling"
    description = "Leveling commands for viewing and managing your level."
    emoji = "📊"

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    ## -- FUNCTIONS -- ##

    @staticmethod
    def get_levelup_message(ctx: AnyContext, **kwargs):
        data_obj = GuildData(ctx.guild)
        member_data_obj = MemberData(ctx.author)

        data = data_obj.get_data()
        member_data = member_data_obj.get_guild_data()

        raw_message = kwargs.get(
            "raw_message",
            data["leveling_message"]["content"]
        )

        variables = get_variables(ctx.author, ctx.guild)
        variables.update({
            "{new_level}": member_data["level"],
            "{previous_level}": member_data["level"] - 1,
            "{new_xp}": member_data["xp"],
            "{previous_xp}": member_data["xp"] - random.randint(17, 27),
            "{total_xp}": member_data["total_xp"],
        })

        return insert_variables(raw_message, variables=variables, member=ctx.author)

    def generate_card(self, args: dict):
        return disnake.File(fp=rankcard.generate_card(**args), filename="card.png")

    ## -- SLASH COMMANDS -- ##

    """
    ! USER COMMANDS
    
    The user commands, such as rank.
    """

    @commands.slash_command(name="rank")
    async def rank(
        self,
        inter: disnake.ApplicationCommandInteraction,
        member: disnake.Member = None,
    ):
        """View the rank card of a member.
        Parameters
        ----------
        member: The member to view the rank of.
        """

        if not member:
            member = inter.author

        member_data_obj = MemberData(member)
        member_data = member_data_obj.get_guild_data()

        level = member_data.get("level")
        xp = member_data.get("xp")

        await inter.send(file=self.generate_card(
            {
                "username": inter.author.__str__(),
                "avatar": inter.author.avatar.url,
                "level": level,
                "rank": 1,
                "current_xp": xp,
                # "xp_color": "#FF7A7A",
                "next_level_xp": xp_to_levelup(level + 1),
            }
        ))

    """
    ! LEVEL COMMANDS
    
    Commands such as setting member's level.
    """

    @commands.slash_command(name="level")
    async def level(self, inter: disnake.ApplicationCommandInteraction):
        """Manage member's levels."""
        pass

    @level.sub_command(name="set")
    @is_staff(administrator=True)
    async def level_set(
        self,
        inter: disnake.ApplicationCommandInteraction,
        member: disnake.Member,
        level: int,
    ):
        """Set the level of a member.
        Parameters
        ----------
        member: The member to change the level of.
        level: The level the member should be.
        """

        data_obj = MemberData(member)

        if level > config.MAX_MANUAL_LEVEL:
            return await inter.send(embed=disnake.Embed(
                description=f"{no} You can't manually set member's levels above {config.MAX_MANUAL_LEVEL}.",
                color=colors.error_embed_color,
            ), ephemeral=True)

        elif level < 0:
            return await inter.send(embed=disnake.Embed(
                description=f"{no} The member's level cannot be lower than 0.",
                color=colors.error_embed_color,
            ), ephemeral=True)

        data_obj.update_guild_data(
            {"level": level, "xp": 0, "total_xp": total_xp_for_level(level)}
        )
        await inter.send(embed=disnake.Embed(
            description=f"{yes} The level of {member.mention} has been set to {level}.",
            color=colors.success_embed_color,
        ))

    @level.sub_command(name="add")
    @is_staff(administrator=True)
    async def level_add(
        self,
        inter: disnake.ApplicationCommandInteraction,
        member: disnake.Member,
        levels: int,
    ):
        """Add a specific amount of level to a member.
        Parameters
        ----------
        member: The member to add levels to.
        levels: How many levels to add.
        """

        data_obj = MemberData(member)
        data = data_obj.get_guild_data()

        if data["level"] + levels > config.MAX_MANUAL_LEVEL:
            return await inter.send(embed=disnake.Embed(
                description=f"{no} You can't manually set member's levels above {config.MAX_MANUAL_LEVEL}.",
                color=colors.error_embed_color,
            ), ephemeral=True)

        data["level"] += levels
        data["xp"] = 0
        data["total_xp"] = total_xp_for_level(data["level"], data["total_xp"])

        data_obj.update_guild_data(data)
        await inter.send(embed=disnake.Embed(
            description=f"{yes} {member.mention} has been given {levels} levels. They are now level {data['level']}.",
            color=colors.success_embed_color,
        ))

    @level.sub_command(name="remove")
    @is_staff(administrator=True)
    async def level_remove(
        self,
        inter: disnake.ApplicationCommandInteraction,
        member: disnake.Member,
        levels: int,
    ):
        """Remove a specific amount of levels from a member.
        Parameters
        ----------
        member: The member to remove levels from.
        levels: How many levels to remove.
        """

        data_obj = MemberData(member)
        data = data_obj.get_guild_data()

        if data["level"] - levels < 0:
            return await inter.send(embed=disnake.Embed(
                description=f"{yes} {member.mention} has been given {levels} levels. They are now level {data['level']}.",
                color=colors.success_embed_color,
            ), ephemeral=True)

        data["level"] -= levels
        data["xp"] = 0
        data["total_xp"] = total_xp_for_level(data["level"], data["total_xp"])

        data_obj.update_guild_data(data)
        await inter.send(embed=disnake.Embed(
            description=f"{yes} {member.mention} has been given {levels} levels. They are now level {data['level']}.",
            color=colors.success_embed_color,
        ))

    @commands.slash_command(name="xp")
    async def xp(self, inter: disnake.ApplicationCommandInteraction):
        """Manage member's XP."""
        pass

    @xp.sub_command(name="give")
    async def xp_give(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, xp: int):
        """Give a member XP.
        Parameters
        ----------
        member: The member to give XP to.
        xp: How much XP to give.
        """

        if xp > config.MAX_MANUAL_XP:
            return await inter.send(embed=disnake.Embed(
                description=f"{no} You can't manually give members more XP than {config.MAX_MANUAL_XP}.",
                color=colors.error_embed_color,
            ), ephemeral=True)
        elif xp < 0:
            return await inter.send(embed=disnake.Embed(
                description=f"{no} You can't give members negative XP.",
                color=colors.error_embed_color,
            ), ephemeral=True)

        leveled_up, new_level = add_xp(member, xp)

        if leveled_up:
            await inter.send(embed=disnake.Embed(
                description=f"{yes} {member.mention} has been given {xp} XP. They are now level {new_level}.",
                color=colors.success_embed_color,
            ))
        else:
            await inter.send(embed=disnake.Embed(
                description=f"{yes} {member.mention} has been given {xp} XP.",
                color=colors.success_embed_color,
            ))

    @xp.sub_command(name="remove")
    async def xp_remove(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, xp: int):
        """Remove XP from a member.
        Parameters
        ----------
        member: The member to remove XP from.
        xp: How much XP to remove.
        """

        if xp > config.MAX_MANUAL_XP:
            return await inter.send(embed=disnake.Embed(
                description=f"{no} You can't manually remove more XP than {config.MAX_MANUAL_XP}.",
                color=colors.error_embed_color,
            ), ephemeral=True)
        elif xp < 0:
            return await inter.send(embed=disnake.Embed(
                description=f"{no} You can't remove negative XP.",
                color=colors.error_embed_color,
            ), ephemeral=True)

        leveled_down, new_level = remove_xp(member, xp)

        if leveled_down:
            await inter.send(embed=disnake.Embed(
                description=f"{yes} {member.mention} has lost {xp} XP. They are now level {new_level}.",
                color=colors.success_embed_color,
            ))
        else:
            await inter.send(embed=disnake.Embed(
                description=f"{yes} {member.mention} has lost {xp} XP.",
                color=colors.success_embed_color,
            ))

    """
    ! SETTING COMMANDS
    
    The commands which manages the way OutDash levels users in guilds.
    """

    @commands.slash_command(name="leveling")
    async def leveling(self, inter: disnake.ApplicationCommandInteraction):
        """Manage how OutDash levels users in guilds."""
        pass

    @leveling.sub_command(name="toggle")
    @is_staff(manage_guild=True)
    async def leveling_toggle(
        self, inter: disnake.ApplicationCommandInteraction, toggle: bool
    ):
        """Toggle the leveling system.
        Parameters
        ----------
        toggle: Whether to enable or disable the leveling system.
        """

        data_obj = GuildData(inter.guild)

        data_obj.update_data({"leveling_toggle": toggle})
        await inter.send(embed=disnake.Embed(
            description=f"{yes} The leveling system has been {'disabled' if not toggle else 'enabled'}.",
            color=colors.success_embed_color,
        ))

    @leveling.sub_command_group(name="message")
    async def leveling_message(
        self, inter: disnake.ApplicationCommandInteraction
    ):
        """View or manage the levelup message."""
        pass

    @leveling_message.sub_command(name="view")
    @is_staff(manage_guild=True)
    async def leveling_message_view(
        self, inter: disnake.ApplicationCommandInteraction
    ):
        """View the current levelup message."""

        await inter.send(embed=disnake.Embed(
            description=f"{info} A levelup message would look like this:\n\n{self.get_levelup_message(inter)}",
            color=colors.embed_color,
        ))

    @leveling_message.sub_command(name="deletion")
    @is_staff(manage_guild=True)
    async def leveling_message_deletion(
        self, inter: disnake.ApplicationCommandInteraction, delay: int
    ):
        """Set the levelup message deletion delay.
        Parameters
        ----------
        delay: The levelup message deletion delay.
        """

        data_obj = GuildData(inter.guild)
        data = data_obj.get_data()

        embed = disnake.Embed(
            description=f"{yes} The levelup message deletion delay has been set to {str(delay)} seconds.",
            color=colors.success_embed_color,
        )

        if isinstance(delay, (int, float)) and delay > 60:
            embed.description = f"{no} The levelup message deletion delay cannot be more than 60 seconds."
            embed.color = colors.error_embed_color
        else:
            data["leveling_message"]["delete_after"] = delay
            data_obj.update_data(data)

        await inter.send(embed=embed, ephemeral=delay > 60)

    @leveling_message.sub_command(name="content")
    @is_staff(manage_guild=True)
    async def leveling_message_content(
        self, inter: disnake.ApplicationCommandInteraction, content: str
    ):
        """Edit the levelup message content.
        Parameters
        ----------
        content: What the levelup message content should be set to.
        """

        data_obj = GuildData(inter.guild)
        data = data_obj.get_data()

        data["leveling_message"]["content"] = content
        data_obj.update_data(data)

        await inter.send(embed=disnake.Embed(
            description=f"{yes} A levelup message would now look like:\n\n{self.get_levelup_message(inter, raw_message=content)}",
            color=colors.success_embed_color,
        ))


def setup(bot):
    bot.add_cog(Leveling(bot))
