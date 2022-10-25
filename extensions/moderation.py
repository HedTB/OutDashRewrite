## -- IMPORTING -- ##

# MODULES
import datetime
import disnake
import typing

from disnake.ext import commands
from dotenv import load_dotenv

# FILES
from utils import config, functions, colors, enums, converters
from utils.data import WarnsData
from utils.checks import is_staff
from utils.emojis import yes, no, info, moderator

## -- VARIABLES -- ##

load_dotenv()

CASES_PER_PAGE = 10

## -- FUNCTIONS -- ##


def clamp(x, a, b):
    return max(a, min(x, b))


def split_into_pages(full_list: list[typing.Any], size: int) -> list[typing.Any]:
    return [full_list[i * size : (i + 1) * size] for i in range((len(full_list) + size - 1) // size)]


## -- VIEWS -- ##


class MemberCasesPaginator(disnake.ui.View):
    def __init__(self, *, page: int, author: disnake.Member, member: disnake.Member, cases: list[dict]):
        print("initializing MemberCasesPaginator")

        super().__init__(timeout=None)

        self.page = page
        self.author = author
        self.member = member

        self.cases = cases
        self.pages = split_into_pages(self.cases, CASES_PER_PAGE)

        self.children[0].disabled = self.page <= 1
        self.children[1].disabled = self.page >= len(self.pages)

    def __del__(self):
        print("destroying MemberCasesPaginator")

    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        return inter.author == self.author

    async def update_message(self, inter: disnake.MessageInteraction):
        self.cases = inter.bot.get_member_cases(self.member)
        self.pages = split_into_pages(self.cases, CASES_PER_PAGE)
        self.page = clamp(self.page, 1, len(self.pages))

        description = (
            f"{info} For more information on a case, run `/moderation case <case>`\n"
            "To view more pages, use the buttons or run `/moderation cases <member> <page>`\n"
        )
        page_cases = self.pages[self.page - 1]

        for case in page_cases:
            moderator = case["moderator"]
            offender = case["offender"]

            moderator = inter.guild.get_member(moderator) or inter.bot.get_user(moderator)
            offender = inter.guild.get_member(offender) or inter.bot.get_user(offender)

            moderator_mention = moderator.mention if isinstance(moderator, disnake.Member) else str(moderator)

            action = enums.Moderation(case["action"])
            reason = case["reason"]
            id = case["id"]

            description += (
                f"\n**{action.name.title()} | Case {id}**" + f"\nModerator - {moderator_mention}\nReason - {reason}"
            )

        self.children[0].disabled = self.page <= 1
        self.children[1].disabled = self.page >= len(self.pages)

        await inter.edit_original_message(
            embed=disnake.Embed(
                title=f"{len(self.cases)} moderation cases for {self.member}",
                description=description,
                color=colors.embed_color,
                timestamp=datetime.datetime.utcnow(),
            ).set_footer(
                text=f"Page {self.page} of {len(self.pages)}", icon_url=inter.author.avatar or config.DEFAULT_AVATAR_URL
            ),
            view=self,
        )

    @disnake.ui.button(style=disnake.ButtonStyle.gray, emoji="⬅️")
    async def left_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        self.page -= 1

        await inter.response.defer()
        await self.update_message(inter)

    @disnake.ui.button(style=disnake.ButtonStyle.gray, emoji="➡️")
    async def right_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        self.page += 1

        await inter.response.defer()
        await self.update_message(inter)


## -- COG -- ##


class Moderation(commands.Cog):
    name = f"{moderator} Moderation"
    description = "The moderation commands, such as mute and ban."
    emoji = moderator

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def is_banned(self, guild: disnake.Guild, user: disnake.User):
        try:
            return True if await guild.fetch_ban(user) else False
        except Exception:
            return False

    ## -- SLASH COMMANDS -- ##

    """
    ! WARNINGS

    The warning system, such as viewing warnings, and obviously adding warnings.
    """

    @commands.slash_command(name="warn", description="Add/remove warnings on a member.")
    async def warn(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @warn.sub_command(name="add", description="Warn a member for their bad actions!")
    @is_staff(manage_guild=True)
    async def warn_add(
        self,
        inter: disnake.ApplicationCommandInteraction,
        member: disnake.Member,
        reason: str = "No reason provided.",
    ):
        """Warn a member for their bad actions!"""

        warns_data_obj = WarnsData(inter.guild)

        if member == inter.author:
            return await inter.send(
                embed=disnake.Embed(
                    description=f"{no} You can't warn yourself!",
                    color=colors.error_embed_color,
                ),
                ephemeral=True,
            )
        elif member.bot:
            return await inter.send(
                embed=disnake.Embed(
                    description=f"{no} You can't warn a bot!",
                    color=colors.error_embed_color,
                ),
                ephemeral=True,
            )
        elif member.top_role == inter.author.top_role or functions.is_role_above_role(
            member.top_role, inter.author.top_role
        ):
            return await inter.send(
                embed=disnake.Embed(
                    description=f"{no} You don't have permission to warn this member!",
                    color=colors.error_embed_color,
                ),
                ephemeral=True,
            )

        await member.send(
            disnake.Embed(
                description=f"{yes} **{member.name}#{member.discriminator}** has been warned. | {reason}",
                color=colors.success_embed_color,
            )
        )
        await inter.send(
            embed=disnake.Embed(
                description=f"{moderator} You have been warned in **{inter.guild.name}**.\n**Reason**: {reason}",
                color=colors.logs_embed_color,
            )
        )

        warns_data_obj.add_warning(member, inter.author, reason)
        self.bot.log_moderation(moderator=inter.author, offender=member, action=enums.Moderation.WARNING, reason=reason)

    @warn.sub_command(name="remove", description="Remove a warning from a member.")
    @is_staff(manage_guild=True)
    async def warn_remove(
        self,
        inter: disnake.ApplicationCommandInteraction,
        member: disnake.Member,
        warning_id: str,
    ):
        """Remove a warning from a member."""

        warns_data_obj = WarnsData(inter.guild)

        if member == inter.author:
            return await inter.send(
                embed=disnake.Embed(
                    description=f"{no} You can't remove warnings from yourself!",
                    color=colors.error_embed_color,
                ),
                ephemeral=True,
            )
        elif member.bot:
            return await inter.send(
                embed=disnake.Embed(
                    description=f"{no} Bots cannot have warnings!",
                    color=colors.error_embed_color,
                ),
                ephemeral=True,
            )

        elif member.top_role == inter.author.top_role or functions.is_role_above_role(
            member.top_role, inter.author.top_role
        ):
            return await inter.send(
                embed=disnake.Embed(
                    description=f"{no} You don't have permission to remove a warning from this member!",
                    color=colors.error_embed_color,
                ),
                ephemeral=True,
            )

        result = warns_data_obj.remove_warning(member, warning_id)

        if not result:
            return await inter.send(
                embed=disnake.Embed(
                    description=f"{no} Please provice a valid warning ID.",
                    color=colors.error_embed_color,
                ),
                ephemeral=True,
            )

        await inter.send(
            embed=disnake.Embed(
                description=f"{yes} Warning with ID {warning_id} has been removed from {member.mention}.",
                color=colors.success_embed_color,
            )
        )

    @commands.slash_command(name="warnings", description="Manage/view the warnings of a member.")
    async def warnings(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @warnings.sub_command(name="view", description="View how many warnings you or another member has.")
    async def warnings_view(
        self,
        inter: disnake.ApplicationCommandInteraction,
        member: disnake.Member = None,
    ):
        """View how many warnings you or another member has.
        Parameters
        ----------
        member: The member you want to view warnings for.
        """

        if not member:
            member = inter.author

        warns_data_obj = WarnsData(inter.guild)
        warnings = warns_data_obj.get_member_warnings(member)

        if len(warnings) == 0:
            embed = disnake.Embed(
                title=f"0 warnings for {member}",
                description=f"{info} This user doesn't have any warnings.",
                color=colors.embed_color,
            )
        else:
            description = ""

            for warning in warnings:
                warning = warnings[warning]

                reason = warning["reason"]
                moderator = warning["moderator"]
                warn_time = warning["time"]

                description += (
                    f"**{warning['id']} | Moderator: {self.bot.get_user(moderator)}**\n"
                    f"{reason} | {warn_time[:16]} UTC\n"
                )

            embed = disnake.Embed(
                title=f"{len(warnings)} warnings for {member}",
                description=description,
                color=colors.embed_color,
            )

        await inter.send(
            embed=embed.set_footer(
                text=f"Requested by {inter.author}",
                icon_url=inter.author.avatar or config.DEFAULT_AVATAR_URL,
            )
        )

    @warnings.sub_command(name="clear")
    @is_staff(manage_guild=True)
    async def warnings_clear(
        self,
        inter: disnake.ApplicationCommandInteraction,
        member: disnake.Member,
        reason: str = "No reason provided.",
    ):
        """Clear all warnings of a member."""

        warns_data_obj = WarnsData(inter.guild)
        warnings = warns_data_obj.get_member_warnings(member)

        if len(warnings) == 0:
            return await inter.send(
                embed=disnake.Embed(
                    description=f"{no} This user doesn't have any warnings!",
                    color=colors.error_embed_color,
                ),
                ephemeral=True,
            )

        warns_data_obj.update_warnings(member, {})

        await inter.send(
            embed=disnake.Embed(
                description=f"{yes} Cleared all warnings for {member.mention} successfully.",
                color=colors.success_embed_color,
            )
        )

    """
    ! PUNISH COMMANDS

    Commands for punishment, such as banning and kicking.
    """

    @commands.slash_command(name="softban")
    @is_staff(ban_members=True)
    async def softban(
        self,
        inter: disnake.ApplicationCommandInteraction,
        member: disnake.Member,
        reason: str = "No reason provided.",
        send_invite: bool = False,
    ):
        """Ban and immediately unban a member to delete their messages
        Parameters
        ----------
        member: The member to softban.
        reason: The reason for the softban.
        send_invite: Whether to send an invite to the member or not. Creates an invite if you don't have a vanity link.
        """

        if member == inter.author:
            return await inter.send(
                embed=disnake.Embed(
                    description=f"{no} You can't softban yourself!",
                    color=colors.error_embed_color,
                ),
                ephemeral=True,
            )
        elif member == self.bot.user:
            return await inter.send(
                embed=disnake.Embed(
                    description=f"{no} I can't softban myself!",
                    color=colors.error_embed_color,
                ),
                ephemeral=True,
            )

        description = f"""
            {moderator} You have been softbanned from **{inter.guild.name}**.
            You're not banned, but your messages have been deleted.

            **Reason:** {reason}
        """

        if send_invite:
            invite = await functions.get_or_make_invite(inter.guild)

            if invite:
                description += f"**Join back:** {invite}"

        try:
            await member.send(
                embed=disnake.Embed(
                    description=description,
                    color=colors.embed_color,
                )
            )

            await member.ban(reason="Softban | " + reason)
            await member.unban(reason="Softban | " + reason)

            await inter.send(
                embed=disnake.Embed(
                    description=f"{yes} **{member}** has been softbanned. | {reason}",
                    color=colors.success_embed_color,
                )
            )

        except disnake.errors.HTTPException:
            await member.ban(reason="Softban | " + reason)
            await member.unban(reason="Softban | " + reason)

            await inter.send(
                embed=disnake.Embed(
                    description=f"{yes} **{member}** has been softbanned. I couldn't DM them though. | {reason}",
                    color=colors.success_embed_color,
                )
            )

        self.bot.log_moderation(moderator=inter.author, offender=member, action=enums.Moderation.SOFTBAN, reason=reason)

    @commands.slash_command(name="ban", description="Ban a member from the guild.")
    @commands.default_member_permissions(ban_members=True)
    @is_staff(ban_members=True)
    async def ban(
        self,
        inter: disnake.ApplicationCommandInteraction,
        member: disnake.Member,
        reason: str = "No reason provided.",
        duration: str = commands.Param("0s", converter=converters.convert_time),
    ):
        """Ban a member from the guild.
        Parameters
        ----------
        member: The member you want to ban.
        reason: The reason for the ban.
        """
        if member == inter.author:
            return await inter.send(
                embed=disnake.Embed(
                    description=f"{no} You can't ban yourself!",
                    color=colors.error_embed_color,
                ),
                ephemeral=True,
            )
        elif member == self.bot.user:
            return await inter.send(
                embed=disnake.Embed(description=f"{no} I can't ban myself!", color=colors.error_embed_color),
                ephemeral=True,
            )

        try:
            await member.send(
                embed=disnake.Embed(
                    description=f"{moderator} You was banned in **{inter.guild.name}**. \nReason: {reason}",
                    color=colors.embed_color,
                )
            )

            await member.ban(reason=reason)
            await inter.send(
                embed=disnake.Embed(
                    description=f"{yes} **{member}** was banned.",
                    color=colors.success_embed_color,
                )
            )

        except disnake.errors.HTTPException:
            await member.ban(reason=reason)
            await inter.send(
                embed=disnake.Embed(
                    description=f"{yes} **{member}** was banned. I couldn't DM them though.",
                    color=colors.success_embed_color,
                )
            )

        self.bot.log_moderation(
            moderator=inter.author, offender=member, action=enums.Moderation.BAN, reason=reason, duration=duration
        )

    @commands.slash_command(name="unban", description="Unban a member from the server.")
    @is_staff(ban_members=True)
    async def unban(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User,
        *,
        reason="No reason provided.",
    ):
        """Unban a member from the server.
        Parameters
        ----------
        user: The user to unban.
        reason: The reason for the unban.
        """

        if not await self.is_banned(inter.guild, user):
            embed = disnake.Embed(description=f"{no} This user isn't banned!")
            return await inter.send(embed=embed, ephemeral=True)

        await inter.guild.unban(user, reason=reason)
        await inter.send(
            embed=disnake.Embed(
                description=f"{yes} **{user}** was unbanned.",
                color=colors.success_embed_color,
            )
        )

    @commands.slash_command(name="kick", description="Kicks a member from the guild.")
    @is_staff(kick_members=True)
    async def kick(
        self,
        inter: disnake.ApplicationCommandInteraction,
        member: disnake.Member,
        reason: str = "No reason provided.",
    ):
        """Kicks a member from the guild.
        Parameters
        ----------
        member: The member you want to kick.
        reason: The reason for the kick.
        """
        if member == inter.author:
            return await inter.send(
                embed=disnake.Embed(
                    description=f"{no} You can't kick yourself!",
                    color=colors.error_embed_color,
                ),
                ephemeral=True,
            )

        elif member == self.bot.user:
            return await inter.send(
                embed=disnake.Embed(
                    description=f"{no} I can't kick myself!",
                    color=colors.error_embed_color,
                ),
                ephemeral=True,
            )

        try:
            await member.send(
                embed=disnake.Embed(
                    description=f"{moderator} You have been kicked in **{inter.guild.name}**. \nReason: {reason}",
                    color=colors.embed_color,
                )
            )

            await member.kick(reason=reason)
            await inter.send(
                embed=disnake.Embed(
                    description=f"{yes} **{member}** was kicked.",
                    color=colors.success_embed_color,
                )
            )

        except disnake.errors.HTTPException:
            await member.kick(reason=reason)
            await inter.send(
                embed=disnake.Embed(
                    description=f"{yes} **{member}** was kicked. I couldn't DM them though.",
                    color=colors.success_embed_color,
                )
            )

    @commands.slash_command(name="mute", description="Mute a member who's breaking the rules!")
    @is_staff(moderate_members=True)
    async def mute(
        self,
        inter: disnake.ApplicationCommandInteraction,
        member: disnake.Member,
        length: str,
        *,
        reason: str = "No reason provided.",
    ):
        """Mute a member who's breaking the rules!"""

        if member == inter.author:
            return await inter.send(
                embed=disnake.Embed(
                    description=f"{no} You can't mute yourself!",
                    color=colors.error_embed_color,
                ),
                ephemeral=True,
            )

        elif member == self.bot.user:
            return await inter.send(
                embed=disnake.Embed(
                    description=f"{no} I can't mute myself!",
                    color=colors.error_embed_color,
                ),
                ephemeral=True,
            )

        seconds = functions.manipulate_time(length, return_type="seconds")

        if not seconds:
            await inter.send(
                embed=disnake.Embed(
                    description=f"{no} Please provide a valid time format."
                    f"\nExample:\n```10s = 10 seconds\n1m = 1 minute\n3h = 3 hours\n2d = 2 days```",
                    color=colors.error_embed_color,
                ),
                ephemeral=True,
            )

        await member.timeout(duration=int(seconds), reason=reason)
        await inter.send(
            embed=disnake.Embed(
                description=f"{yes} **{member.name}#{member.discriminator}** has been muted.\n**Reason:** {reason}",
                color=colors.success_embed_color,
            )
        )

    @commands.slash_command(name="unmute", description="Unmute a member and allow them to talk again.")
    @is_staff(moderate_members=True)
    async def unmute(
        self,
        inter: disnake.ApplicationCommandInteraction,
        member: disnake.Member,
        reason: str = "No reason provided.",
    ):
        """Unmute a member and allow them to talk again.
        Parameters
        ----------
        member: The member you want to unmute.
        reason: The reason for the unmute.
        """

        if not member.current_timeout:
            return await inter.send(
                embed=disnake.Embed(
                    description=f"{no} This member isn't muted!",
                    color=colors.error_embed_color,
                ),
                ephemeral=True,
            )

        await member.timeout(duration=None, reason=reason)
        await inter.send(
            embed=disnake.Embed(
                description=f"{yes} **{member.name}#{member.discriminator}** has been unmuted.",
                color=colors.success_embed_color,
            )
        )

    """
    ! CHANNEL MANAGEMENT

    These commands manages all channels.
    """

    @commands.slash_command(name="slowmode", description="Change the slowmode of a channel.")
    @is_staff(manage_channels=True)
    async def slowmode(
        self,
        inter: disnake.ApplicationCommandInteraction,
        seconds: int,
        channel: disnake.TextChannel = None,
    ):
        """Change the slowmode of a channel.
        Parameters
        ----------
        seconds: How many seconds the slowmode should be set to.
        channel: What channel to change slowmode of. Defaults to current channel.
        """

        embed = disnake.Embed(
            description=f"{yes} The slowmode has been set to `{seconds}` seconds.",
            color=colors.success_embed_color,
        )

        if not channel:
            channel = inter.channel
        if seconds > 21600:
            return await inter.send(
                embed=disnake.Embed(
                    description=f"{no} The slowmode can't be over 21600 seconds.",
                    color=colors.error_embed_color,
                ),
                ephemeral=True,
            )

        if channel != inter.channel:
            embed.description = f"{yes} The slowmode for {channel.mention} has been set to `{seconds}` seconds."

        await channel.edit(slowmode_delay=seconds)
        await inter.send(embed=embed)

    """
    ! MODERATOR MANAGEMENT

    Manage the moderators of the server.
    """

    @commands.slash_command(name="staff", description="View and manage the staff members of the server.")
    @is_staff(type="administrator", administrator=True)
    async def staff(self, inter: disnake.ApplicationCommandInteraction):
        """View and manage the moderators of the server."""
        pass

    @staff.sub_command(name="view", description="View the staff members of the server.")
    @is_staff(type="administrator", administrator=True)
    async def moderators_view(self, inter: disnake.ApplicationCommandInteraction):
        """View the moderators of the server."""

    @staff.sub_command(name="add", description="Add a staff member to the server.")
    @is_staff(type="administrator", administrator=True)
    async def moderators_add(
        self,
        inter: disnake.ApplicationCommandInteraction,
        member: disnake.Member,
        type: commands.option_enum({"Moderator": "moderator", "Administrator": "administrator"}),
    ):
        """Add a moderator to the server.
        Parameters
        ----------
        member: The member you want to add as a moderator.
        """

        if member == inter.author:
            return await inter.send(
                embed=disnake.Embed(
                    description=f"{no} You can't add yourself as a moderator!",
                    color=colors.error_embed_color,
                )
            )

        author_rank = await self.bot.get_staff_rank(inter.author)
        member_rank = await self.bot.get_staff_rank(member)

        print(author_rank)
        print(member_rank)

        if member in inter.guild.moderators:
            return await inter.send(
                embed=disnake.Embed(
                    description=f"{no} This member is already a staff member!",
                    color=colors.error_embed_color,
                )
            )

        await inter.guild.moderators.add(member)
        await inter.send(
            embed=disnake.Embed(
                description=f"{yes} **{member}** has been added as a moderator.",
                color=colors.success_embed_color,
            )
        )

    """
    ! MODERATION DATA

    """

    @commands.slash_command(name="moderation", description="")
    @is_staff(type="moderator", manage_guild=True)
    async def moderation(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @moderation.sub_command(name="cases", description="View all cases opened against a given member.")
    @is_staff(type="moderator", manage_guild=True)
    async def moderation_cases(
        self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member = None, page: int = 1
    ):
        """
        Parameters
        ----------
        member: What member you want to view cases of. Defaults to yourself.
        """

        if not member:
            member = inter.author

        cases = self.bot.get_member_cases(member)
        pages = split_into_pages(cases, CASES_PER_PAGE)

        description = (
            f"{info} For more information on a case, run `/moderation case <case>`\n"
            "To view more pages, use the buttons or run `/moderation cases <member> <page>`\n"
        )

        if len(pages) == 0:
            return await inter.send(
                embed=disnake.Embed(
                    title=f"0 moderation cases for {member}",
                    description=f"{info} This member doesn't have any moderation cases opened against them.",
                    color=colors.embed_color,
                    timestamp=datetime.datetime.utcnow(),
                ).set_footer(text="Page 0 of 0", icon_url=inter.author.avatar or config.DEFAULT_AVATAR_URL)
            )

        page = clamp(page, 1, len(pages))
        page_cases = pages[page - 1]

        for case in page_cases:
            moderator = case["moderator"]
            offender = case["offender"]

            moderator = inter.guild.get_member(moderator) or self.bot.get_user(moderator)
            offender = inter.guild.get_member(offender) or self.bot.get_user(offender)

            moderator_mention = moderator.mention if isinstance(moderator, disnake.Member) else str(moderator)

            action = enums.Moderation(case["action"])
            reason = case["reason"]
            id = case["id"]

            description += (
                f"\n**{action.name.title()} | Case {id}**" + f"\nModerator - {moderator_mention} | Reason - {reason}"
            )

        await inter.send(
            embed=disnake.Embed(
                title=f"{len(cases)} moderation cases for {member}",
                description=description,
                color=colors.embed_color,
                timestamp=datetime.datetime.utcnow(),
            ).set_footer(
                text=f"Page {page} of {len(pages)}", icon_url=inter.author.avatar or config.DEFAULT_AVATAR_URL
            ),
            view=MemberCasesPaginator(page=page, author=inter.author, member=member, cases=cases),
        )

    """
    ! OTHER MODERATION

    All other moderation commands.
    """

    @commands.slash_command(name="clear", description="Clear up some messages from your channels!")
    @is_staff(manage_messages=True)
    async def clear(
        self,
        inter: disnake.ApplicationCommandInteraction,
        amount: int,
        channel: disnake.TextChannel = None,
    ):
        """Clear up some messages from your channels!
        Parameters
        ----------
        amount: The amount of messages you want to delete.
        channel: The channel you want to delete from. Default is the current channel.
        """
        embed = disnake.Embed(description=f"{yes} ", color=colors.success_embed_color)

        if not channel or channel and channel == inter.channel:
            channel = inter.channel
            deleted = await channel.purge(limit=amount)
            deleted = len(deleted)

            embed.description += f"Deleted {deleted} messsages." if not deleted == 1 else f"Deleted {deleted} messsage."
            await inter.send(embed=embed, ephemeral=True)

        else:
            deleted = len(await channel.purge(limit=amount))

            embed.description += (
                f"Deleted {deleted} messsages in <#{channel.id}>."
                if deleted != 1
                else f"Deleted 1 messsage in <#{channel.id}>."
            )
            await inter.send(embed=embed)


def setup(bot):
    bot.add_cog(Moderation(bot))
