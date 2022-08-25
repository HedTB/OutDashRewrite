## -- IMPORTING -- ##

# MODULES
from typing import Dict
import disnake
import os
import datetime
import certifi

from disnake.ext import commands
from pymongo import MongoClient

# from googleapiclient import discovery
from dotenv import load_dotenv

# FILES
from utils import config, functions, colors

from utils.checks import *
from utils.webhooks import *
from utils.classes import *
from utils.data import *

## -- VARIABLES -- ##

load_dotenv()

Channel = disnake.TextChannel | disnake.VoiceChannel | disnake.NewsChannel | disnake.ForumChannel | disnake.StageChannel

MONGO_LOGIN = os.environ.get("MONGO_LOGIN")
RAPID_API_KEY = os.environ.get("RAPID_API_KEY")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
RANDOMSTUFF_KEY = os.environ.get("RANDOMSTUFF_KEY")

client = MongoClient(MONGO_LOGIN, tlsCAFile=certifi.where())
db = client["db2"]


"""
perspective_client = discovery.build(
    "commentanalyzer",
    "v1alpha1",
    developerKey=GOOGLE_API_KEY,
    discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
    static_discovery=False,
)
"""

guild_data_col = db["guild_data"]
user_data_col = db["user_data"]
privacy_settings_col = db["privacy_settings"]


## -- FUNCTIONS -- ##


def get_response_score(response, attribute: str):
    attribute = attribute.upper()
    attribute_scores = response["attributeScores"]

    if attribute_scores[attribute]:
        return round(attribute_scores[attribute]["summaryScore"]["value"], 3)
    else:
        return None


def get_permissions(permissions: disnake.Permissions, granted: bool = True):
    return [permission for permission, is_granted in permissions if is_granted == granted]


def get_channel_permissions(channel: Channel, granted: bool = True):
    permissions = {"roles": {}, "members": {}}

    for overwrite_type, overwrite in channel.overwrites.items():
        overwrite_type_str = "roles" if isinstance(overwrite_type, disnake.Role) else "members"
        overwrites = [permission for permission, is_granted in overwrite if is_granted == granted]

        permissions[overwrite_type_str][overwrite_type] = overwrites

    return permissions


def get_permission_differences(before: disnake.Permissions, after: disnake.Permissions, granted: bool = True):
    before_permissions = get_permissions(before, granted)
    after_permissions = get_permissions(after, granted)

    return list(set(before_permissions) - set(after_permissions))


def get_channel_permission_differences(
    before: Channel, after: Channel, granted: bool = True
) -> Dict[str, Dict[disnake.Member | disnake.Role, list]]:
    before_overwrites = get_channel_permissions(before, granted)
    after_overwrites = get_channel_permissions(after, granted)

    return {
        "roles": {
            key: after_overwrites["roles"][key]
            for key in set(after_overwrites["roles"]) - set(before_overwrites["roles"])
        },
        "members": {
            key: after_overwrites["members"][key]
            for key in set(after_overwrites["members"]) - set(before_overwrites["members"])
        },
    }


## -- COG -- ##


class LoggingEvents(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    ## -- MESSAGES -- ##

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages: list[disnake.Message]):
        logger.debug(f"{len(messages)} messages were deleted in {messages[0].channel.guild.name}")

        try:
            webhook = LoggingWebhook(self.bot.user.avatar, messages[0].guild, "message_bulk_delete")
        except InvalidWebhook:
            logger.warning(f"Invalid bulk message deletion webhook for {messages[0].guild.name}")
            return

        embed = disnake.Embed(
            description=f"**Bulk delete in <#{messages[0].channel.id}>, {len(messages)} messages deleted**",
            color=colors.logs_embed_color,
        )

        embed.set_author(
            name=messages[0].guild.name,
            icon_url=messages[0].guild.icon or config.DEFAULT_AVATAR_URL,
        )
        embed.timestamp = datetime.datetime.utcnow()

        webhook.add_embed(embed)
        webhook.post()

    @commands.Cog.listener()
    async def on_message_edit(self, before: disnake.Message, after: disnake.Message):
        if before.content == after.content:
            return
        if before.author.bot or after.author.bot:
            return

        logger.debug(f"{before.author.name} edited a message in {before.channel.name}")

        try:
            webhook = LoggingWebhook(self.bot.user.avatar, before.guild, "message_edit")
        except InvalidWebhook:
            logger.warning(f"Invalid message edit webhook for {before.guild.name}")
            return

        user_data_obj = UserData(before.author)

        user_data = user_data_obj.get_data()
        message_content_privacy = user_data.get("message_content_privacy")

        before_text = before.content if len(before.content) < 1021 else f"{before.content[:1021]}..."
        after_text = after.content if len(after.content) < 1021 else f"{after.content[:1021]}..."

        if len(before.embeds) >= 1:
            before_text = f"{before_text}\n**[EMBED]**" if len(before.embeds) == 1 else f"{before_text}\n**[EMBEDS]**"

        if len(after.embeds) >= 1:
            after_text = f"{after_text}\n**[EMBED]**" if len(after.embeds) == 1 else f"{after_text}\n**[EMBEDS]**"

        if not before_text or not after_text:
            return

        if not message_content_privacy:
            embed = disnake.Embed(
                description=f"**Message edited in <#{before.channel.id}>**\n[Jump to message](https://discordapp.com/channels/{after.guild.id}/{after.channel.id}/{after.id})",
                color=colors.logs_embed_color,
            )
            embed.add_field(name="Before", value=before_text, inline=False)
            embed.add_field(name="After", value=after_text, inline=False)

            embed.set_author(
                name=f"{before.author.name}#{before.author.discriminator}",
                icon_url=before.author.avatar or config.DEFAULT_AVATAR_URL,
            )
            embed.set_footer(text=f"Message ID: {before.id}")
            embed.timestamp = datetime.datetime.utcnow()
        else:
            embed = disnake.Embed(
                description=f"**Message edited in <#{before.channel.id}>** \n[Jump to message](https://discordapp.com/channels/{after.guild.id}/{after.channel.id}/{after.id})",
                color=colors.logs_embed_color,
            )
            embed.add_field(name="Notice", value="`This user has message content privacy enabled.`")

            embed.set_author(
                name=f"{before.author.name}#{before.author.discriminator}",
                icon_url=before.author.avatar or config.DEFAULT_AVATAR_URL,
            )
            embed.set_footer(text=f"Message ID: {before.id}")
            embed.timestamp = datetime.datetime.utcnow()

        webhook.add_embed(embed)
        webhook.post()

    @commands.Cog.listener()
    async def on_message_delete(self, message: disnake.Message):
        if message.author.bot:
            return

        user_data_obj = UserData(message.author)
        user_data = user_data_obj.get_data()

        logger.debug(f"{message.author} deleted message {message.id} in {message.channel}")

        try:
            webhook = LoggingWebhook(self.bot.user.avatar, message.guild, "message_delete")
        except InvalidWebhook:
            logger.warning(f"Invalid message deletion webhook for {message.guild.name}")
            return

        message_content_privacy = user_data["message_content_privacy"]
        message_text = message.content if len(message.content) < 2000 else f"{message.content[:2000]}..."

        if len(message.embeds) >= 1:
            message_text = (
                f"{message_text}\n**[EMBED]**" if len(message.embeds) == 1 else f"{message_text}\n**[EMBEDS]**"
            )
        if message_content_privacy:
            message_text = "`This user has message content privacy enabled.`"

        embed = disnake.Embed(
            description=f"**Message deleted in {message.channel.mention}**" f"\n{message_text}",
            color=colors.logs_delete_embed_color,
        )

        embed.set_author(
            name=f"{message.author.name}#{message.author.discriminator}",
            icon_url=message.author.avatar or config.DEFAULT_AVATAR_URL,
        )
        embed.set_footer(text=f"Message ID: {message.id}")
        embed.timestamp = datetime.datetime.utcnow()

        webhook.add_embed(embed)
        webhook.post()

    ## -- MEMBERS -- ##

    @commands.Cog.listener()
    async def on_member_join(self, member: disnake.Member):
        logger.debug(f"{member.name} joined {member.guild.name}")

        try:
            webhook = LoggingWebhook(self.bot.user.avatar, member.guild, "member_join")
        except InvalidWebhook:
            logger.warning(f"Invalid member join webhook for {member.guild.name}")
            return

        self.bot.dispatch("welcome_member", member)

        embed = disnake.Embed(
            description="**Member joined**",
            color=colors.logs_add_embed_color,
            timestamp=datetime.datetime.utcnow(),
        ).set_author(
            name=f"{member.name}#{member.discriminator}",
            icon_url=member.avatar or config.DEFAULT_AVATAR_URL,
        )

        created_ago_native = datetime.datetime.replace(member.created_at, tzinfo=None)
        created_ago = datetime.datetime.now() - created_ago_native
        created_seconds_ago = created_ago.total_seconds()

        embed.add_field(
            name="Account Created",
            value=f"{functions.seconds_to_text(created_seconds_ago, 3)} ago",
            inline=False,
        )

        webhook.add_embed(embed)
        webhook.post()

    @commands.Cog.listener()
    async def on_member_remove(self, member: disnake.Member):
        logger.debug(f"{member.name} left {member.guild.name}")

        try:
            webhook = LoggingWebhook(self.bot.user.avatar, member.guild, "member_remove")
        except InvalidWebhook:
            logger.warning(f"Invalid member remove webhook for {member.guild.name}")
            return

        member_roles = " ".join([role.mention for role in member.roles if role.name != "@everyone"])
        kick_log = await self.bot.get_audit_log(disnake.AuditLogAction.kick, member.guild, member)

        joined_at_native = datetime.datetime.replace(member.joined_at, tzinfo=None)
        joined_at = datetime.datetime.now() - joined_at_native

        if kick_log:
            self.bot.dispatch("member_kick", member, kick_log)

        embed = (
            disnake.Embed(
                description=f"**Member left**",
                color=colors.logs_delete_embed_color,
                timestamp=datetime.datetime.utcnow(),
            )
            .add_field(
                name="Member Since",
                value=f"{functions.seconds_to_text(joined_at.total_seconds(), 3)} ago",
                inline=False,
            )
            .add_field(name="Roles", value=member_roles, inline=False)
            .set_author(
                name=f"{member.name}#{member.discriminator}",
                icon_url=member.avatar or config.DEFAULT_AVATAR_URL,
            )
        )

        webhook.add_embed(embed)
        webhook.post()

    @commands.Cog.listener()
    async def on_member_kick(self, member: disnake.Member, audit_log: disnake.AuditLogEntry):
        logger.debug(f"{member.name} was kicked from {member.guild.name}")

        try:
            webhook = LoggingWebhook(self.bot.user.avatar, member.guild, "member_kick")
        except InvalidWebhook:
            logger.warning(f"Invalid member kick webhook for {member.guild.name}")
            return

        embed = (
            disnake.Embed(
                description=f"**Member kicked**",
                color=colors.logs_delete_embed_color,
                timestamp=datetime.datetime.utcnow(),
            )
            .set_author(
                name=f"{member.name}#{member.discriminator}",
                icon_url=member.avatar or config.DEFAULT_AVATAR_URL,
            )
            .add_field(
                name="Reason",
                value=audit_log.reason,
                inline=False,
            )
            .add_field(
                name="Moderator",
                value=audit_log.user.mention,
                inline=False,
            )
        )

        webhook.add_embed(embed)
        webhook.post()

    @commands.Cog.listener()
    async def on_member_ban(self, guild: disnake.Guild, user: disnake.User):
        logger.debug(f"{user.name} was banned from {guild.name}")

        try:
            webhook = LoggingWebhook(self.bot.user.avatar, guild, "member_ban")
        except InvalidWebhook:
            logger.warning(f"Invalid member ban webhook for {guild.name}")
            return

        audit_log = await self.bot.get_audit_log(disnake.AuditLogAction.ban, guild, user)

        embed = (
            disnake.Embed(
                description=f"**Member banned**",
                color=colors.logs_delete_embed_color,
                timestamp=datetime.datetime.utcnow(),
            )
            .set_author(
                name=f"{user.name}#{user.discriminator}",
                icon_url=user.avatar or config.DEFAULT_AVATAR_URL,
            )
            .add_field(
                name="Reason",
                value=audit_log.reason if audit_log else "N/A",
                inline=False,
            )
            .add_field(
                name="Moderator",
                value=audit_log.user.mention if audit_log else "N/A",
                inline=False,
            )
        )

        webhook.add_embed(embed)
        webhook.post()

    @commands.Cog.listener()
    async def on_member_unban(self, guild: disnake.Guild, user: disnake.User):
        logger.debug(f"{user.name} was unbanned from {guild.name}")

        try:
            webhook = LoggingWebhook(self.bot.user.avatar, guild, "member_unban")
        except InvalidWebhook:
            logger.warning(f"Invalid member unban webhook for {guild.name}")
            return

        audit_log = await self.bot.get_audit_log(disnake.AuditLogAction.unban, guild, user)

        embed = (
            disnake.Embed(
                description=f"**Member unbanned**",
                color=colors.logs_embed_color,
                timestamp=datetime.datetime.utcnow(),
            )
            .set_author(
                name=f"{user.name}#{user.discriminator}",
                icon_url=user.avatar or config.DEFAULT_AVATAR_URL,
            )
            .add_field(
                name="Reason",
                value=audit_log.reason if audit_log else "N/A",
                inline=False,
            )
            .add_field(
                name="Moderator",
                value=audit_log.user.mention if audit_log else "N/A",
                inline=False,
            )
        )

        webhook.add_embed(embed)
        webhook.post()

    @commands.Cog.listener()
    async def on_member_roles_update(self, before: disnake.Member, after: disnake.Member):
        logger.debug(f"{before.name} roles updated in {before.guild.name}")

        try:
            webhook = LoggingWebhook(self.bot.user.avatar, before.guild, "member_roles_update")
        except InvalidWebhook:
            logger.warning(f"Invalid member roles update webhook for {before.guild.name}")
            return

        added_roles = list(filter(lambda r: r not in before.roles, after.roles))
        removed_roles = list(filter(lambda r: r not in after.roles, before.roles))

        embed = disnake.Embed(
            description=f"**Roles updated**",
            color=colors.logs_embed_color,
            timestamp=datetime.datetime.utcnow(),
        ).set_author(
            name=f"{before.name}#{before.discriminator}",
            icon_url=before.avatar or config.DEFAULT_AVATAR_URL,
        )

        if len(added_roles) > 0:
            embed.add_field(
                name="Added roles",
                value=" ".join([r.mention for r in added_roles]),
                inline=False,
            )
        if len(removed_roles) > 0:
            embed.add_field(
                name="Removed roles",
                value=" ".join([r.mention for r in removed_roles]),
                inline=False,
            )

        webhook.add_embed(embed)
        webhook.post()

    @commands.Cog.listener()
    async def on_member_update(self, before: disnake.Member, after: disnake.Member):
        logger.debug(f"{before.name} updated their profile in {before.guild.name}")

        embeds = []

        if before.roles != after.roles:
            self.bot.dispatch("member_roles_update", before, after)
        if before.nick != after.nick:
            embeds.append(
                disnake.Embed(
                    description="Nickname changed", color=colors.logs_embed_color, timestamp=datetime.datetime.utcnow()
                )
                .set_author(name=str(before), icon_url=after.avatar.url)
                .add_field(
                    "Before",
                    disnake.utils.escape_markdown(before.nick if before.nick else "None"),
                )
                .add_field(
                    "After",
                    disnake.utils.escape_markdown(after.nick if after.nick else "None"),
                )
            )
        if before.guild_avatar != after.guild_avatar:
            embeds.append(
                disnake.Embed(
                    description="Guild avatar changed",
                    color=colors.logs_embed_color,
                    timestamp=datetime.datetime.utcnow(),
                )
                .set_author(name=str(before), icon_url=after.avatar.url)
                .set_image(url=after.guild_avatar)
            )
        if before.avatar != after.avatar:
            embeds.append(
                disnake.Embed(
                    description="Avatar changed", color=colors.logs_embed_color, timestamp=datetime.datetime.utcnow()
                )
                .set_author(name=str(before), icon_url=after.avatar.url)
                .set_image(url=after.avatar)
            )
        if before.name != after.name or before.discriminator != after.discriminator:
            embeds.append(
                disnake.Embed(
                    description="Username changed", color=colors.logs_embed_color, timestamp=datetime.datetime.utcnow()
                )
                .set_author(name=str(before), icon_url=after.avatar.url)
                .add_field(
                    "Before",
                    disnake.utils.escape_markdown(str(before)),
                )
                .add_field(
                    "After",
                    disnake.utils.escape_markdown(str(after)),
                )
            )

        if len(embeds) == 0:
            return

        try:
            webhook = LoggingWebhook(self.bot.user.avatar, before.guild, "member_update")
        except InvalidWebhook:
            logger.warning(f"Invalid member update webhook for {before.guild.name}")
            return

        webhook.add_embeds(embeds)
        webhook.post()

    @commands.Cog.listener()
    async def on_user_update(self, before: disnake.User, after: disnake.User):
        logger.debug(f"{before.name} updated their profile")

        for guild in after.mutual_guilds:
            before = guild.get_member(before.id)
            after = guild.get_member(after.id)

            self.bot.dispatch("member_update", before, after)

    ## -- ROLES -- ##

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: disnake.Role):
        logger.debug(f"{role.name} was created in {role.guild.name}")

        try:
            webhook = LoggingWebhook(self.bot.user.avatar, role.guild, "guild_role_create")
        except InvalidWebhook:
            logger.warning(f"Invalid role create webhook for {role.guild.name}")
            return

        embed = (
            disnake.Embed(
                description=f"**Role created**",
                color=colors.logs_add_embed_color,
                timestamp=datetime.datetime.utcnow(),
            )
            .add_field(name="Name", value=role.mention, inline=False)
            .set_author(name=str(role.guild), icon_url=role.guild.icon.url)
            .set_footer(text=f"ID: {role.id}")
        )

        webhook.add_embed(embed)
        webhook.post()

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: disnake.Role):
        logger.debug(f"{role.name} was deleted in {role.guild.name}")

        try:
            webhook = LoggingWebhook(self.bot.user.avatar, role.guild, "guild_role_delete")
        except InvalidWebhook:
            logger.warning(f"Invalid role deletion webhook for {role.guild.name}")
            return

        embed = (
            disnake.Embed(
                description=f"**Role deleted**",
                color=colors.logs_delete_embed_color,
                timestamp=datetime.datetime.utcnow(),
            )
            .add_field(name="Name", value=role.mention, inline=False)
            .set_author(name=str(role.guild), icon_url=str(role.guild.icon or config.DEFAULT_AVATAR_URL))
            .set_footer(text=f"ID: {role.id}")
        )

        webhook.add_embed(embed)
        webhook.post()

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: disnake.Role, after: disnake.Role):
        logger.debug(f"Role {after.name} was updated in {after.guild.name}")

        try:
            webhook = LoggingWebhook(self.bot.user.avatar, after.guild, "guild_role_update")
        except:
            logger.warning(f"Invalid role update webhook for {after.guild.name}")
            return

        embeds = []

        if before.name != after.name:
            embeds.append(
                disnake.Embed(
                    description=f"**Role name updated**",
                )
                .add_field(name="Before", value=before.name, inline=False)
                .add_field(
                    name="After",
                    value=after.name,
                    inline=False,
                )
            )
        if before.color != after.color:
            embeds.append(
                disnake.Embed(description="**Role color updated**", color=after.color)
                .add_field(name="Before", value=str(before.color), inline=False)
                .add_field(name="After", value=str(after.color), inline=False)
            )
        if before.permissions != after.permissions:
            added_permissions = get_permission_differences(before.permissions, after.permissions, True)
            removed_permissions = get_permission_differences(before.permissions, after.permissions, False)

            embed = disnake.Embed(description="**Role permissions updated**")

            if len(added_permissions) > 0:
                embed.add_field(
                    name="Added",
                    value=", ".join(added_permissions).replace("_", " ").title(),
                    inline=False,
                )
            if len(removed_permissions) > 0:
                embed.add_field(
                    name="Removed",
                    value=", ".join(removed_permissions).replace("_", " ").title(),
                    inline=False,
                )

            embeds.append(embed)
        if before.emoji != after.emoji:
            embeds.append(
                disnake.Embed(description="**Role emoji updated**")
                .add_field(name="Before", value=str(before.emoji), inline=False)
                .add_field(name="After", value=str(after.emoji), inline=False)
            )

        if len(embeds) == 0:
            return

        for embed in embeds:
            if embed.color is disnake.Embed.Empty:
                embed.color = colors.logs_embed_color

            embed.timestamp = datetime.datetime.utcnow()

            embed.set_author(
                name=str(before.guild), icon_url=str(before.guild.icon or config.DEFAULT_AVATAR_URL)
            ).set_footer(text=f"ID: {after.id}")

        webhook.add_embeds(embeds)
        webhook.post()

    ## -- CHANNELS -- ##

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: disnake.TextChannel):
        logger.debug(f"Channel {channel.name} was created in {channel.guild.name}")

        try:
            webhook = LoggingWebhook(self.bot.user.avatar, channel.guild, "guild_channel_create")
        except:
            logger.warning(f"Invalid channel creation webhook in {channel.guild.name}")
            return

        embed = (
            disnake.Embed(
                description=f"**Channel created**",
                color=colors.logs_add_embed_color,
                timestamp=datetime.datetime.utcnow(),
            )
            .add_field(name="Name", value=channel.mention, inline=False)
            .set_author(name=str(channel.guild), icon_url=str(channel.guild.icon or config.DEFAULT_AVATAR_URL))
            .set_footer(text=f"ID: {channel.id}")
        )

        webhook.add_embed(embed)
        webhook.post()

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: disnake.TextChannel):
        logger.debug(f"Channel {channel.name} was deleted in {channel.guild.name}")

        try:
            webhook = LoggingWebhook(self.bot.user.avatar, channel.guild, "guild_channel_delete")
        except:
            logger.warning(f"Invalid channel deletion webhook in {channel.guild.name}")
            return

        embed = (
            disnake.Embed(
                description=f"**Channel deleted**",
                color=colors.logs_delete_embed_color,
                timestamp=datetime.datetime.utcnow(),
            )
            .add_field(name="Name", value=channel.name, inline=False)
            .set_author(name=str(channel.guild), icon_url=str(channel.guild.icon or config.DEFAULT_AVATAR_URL))
            .set_footer(text=f"ID: {channel.id}")
        )

        webhook.add_embed(embed)
        webhook.post()

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: disnake.TextChannel, after: disnake.TextChannel):
        logger.debug(f"Channel {after.name} was updated in {after.guild.name}")

        try:
            webhook = LoggingWebhook(self.bot.user.avatar, after.guild, "guild_channel_update")
        except:
            logger.warning(f"Invalid channel creation webhook in {after.guild.name}")
            return

        embeds = []

        if before.category != after.category:
            embeds.append(
                disnake.Embed(description=f"**Channel category updated**")
                .add_field(name="Before", value=before.category.name if before.category else "None", inline=False)
                .add_field(name="After", value=after.category.name if after.category else "None", inline=False)
            )
        if before.name != after.name:
            embeds.append(
                disnake.Embed(description=f"**Channel name updated**")
                .add_field(name="Before", value=before.name, inline=False)
                .add_field(name="After", value=after.name, inline=False)
            )
        if before.nsfw != after.nsfw:
            embeds.append(
                disnake.Embed(description=f"**Channel NSFW state updated**")
                .add_field(name="Before", value=before.nsfw, inline=False)
                .add_field(name="After", value=after.nsfw, inline=False)
            )
        if before.topic != after.topic:
            embeds.append(
                disnake.Embed(description=f"**Channel description updated**")
                .add_field(name="Before", value=before.topic or "None", inline=False)
                .add_field(name="After", value=after.topic or "None", inline=False)
            )
        if before.slowmode_delay != after.slowmode_delay:
            embeds.append(
                disnake.Embed(description=f"**Channel slowmode updated**")
                .add_field(name="Before", value=functions.seconds_to_text(before.slowmode_delay), inline=False)
                .add_field(name="After", value=functions.seconds_to_text(after.slowmode_delay), inline=False)
            )
        if before.overwrites != after.overwrites:
            added_overwrites = get_channel_permission_differences(before, after, True)
            removed_overwrites = get_channel_permission_differences(before, after, False)

            added_roles = [role.mention for role, _ in added_overwrites["roles"].items()]
            removed_roles = [role.mention for role, _ in removed_overwrites["roles"].items()]

            added_members = [member.mention for member, _ in added_overwrites["members"].items()]
            removed_members = [member.mention for member, _ in removed_overwrites["members"].items()]

            embeds.append(
                disnake.Embed(description=f"**Channel permission overwrites updated**")
                .add_field(name="Roles Added", value=", ".join(added_roles), inline=False)
                .add_field(name="Roles Removed", value=", ".join(removed_roles), inline=False)
                .add_field(name="Members Added", value=", ".join(added_members), inline=False)
                .add_field(name="Members Removed", value=", ".join(removed_members), inline=False)
            )

        if len(embeds) == 0:
            return

        for embed in embeds:
            if embed.color is disnake.Embed.Empty:
                embed.color = colors.logs_embed_color

            embed.timestamp = datetime.datetime.utcnow()

            embed.set_author(
                name=str(before.guild), icon_url=str(before.guild.icon or config.DEFAULT_AVATAR_URL)
            ).set_footer(text=f"ID: {after.id}")

        webhook.add_embeds(embeds)
        webhook.post()


def setup(bot):
    bot.add_cog(LoggingEvents(bot))
