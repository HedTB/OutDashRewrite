## -- IMPORTING -- ##

# MODULES
import disnake

from disnake.ext import commands
from dotenv import load_dotenv

# FILES
from utils import colors

from utils.checks import is_staff, server_setting
from utils.data import GuildData, UserData
from utils.emojis import yes, no

## -- VARIABLES -- ##

load_dotenv()

# OTHER
categories = {
    "messages": {
        "message_delete": "Message deletion",
        "message_edit": "Bulk message deletion",
        "message_bulk_delete": "Message edit",
    },
    "members": {
        "member_join": "Member join",
        "member_remove": "Member leave",
        "member_kick": "Member kick",
        "member_ban": "Member ban",
        "member_unban": "Member unban",
        "member_roles_update": "Member roles update",
        "member_update": "Member update",
    },
    "channels": {
        "guild_channel_delete": "Channel deletion",
        "guild_channel_create": "Channel creation",
        "guild_channel_update": "Channel update",
    },
    "roles": {
        "guild_role_create": "Role creation",
        "guild_role_delete": "Role deletion",
        "guild_role_update": "Role update",
    },
    "guild": {
        "guild_update": "Guild update",
        "guild_emojis_update": "Guild emojis update",
        "guild_stickers_update": "Guild stickers update",
    },
    "voice_channels": {
        "voice_channel_join": "Voice channel join",
        "voice_channel_leave": "Voice channel leave",
    },
}
embed_values = [
    "title",
    "description",
    "author_name",
    "author_icon",
    "footer_text",
    "footer_icon",
    "timestamp",
    "thumbnail",
    "color",
]
message_settings_description = {"message_content": "message content"}

embed_parts_choices = commands.option_enum(
    {
        "Title": "title",
        "Description": "description",
        "Timestamp": "timestamp",
        "Thumbnail": "thumbnail",
        "Color": "color",
        "Author name": "author_name",
        "Author url": "author_url",
        "Author icon": "author_icon",
        "Footer text": "footer_text",
        "Footer icon": "footer_icon",
    }
)
message_settings_types = commands.option_enum({"message content": "message_content"})
type_list = commands.option_enum(
    {
        "Message deletion": "message_delete",
        "Message bulk deletion": "message_bulk_delete",
        "Message edit": "message_edit",
        "Member join": "member_join",
        "Member leave": "member_remove",
        "Member kick": "member_kick",
        "Member ban": "member_ban",
        "Member unban": "member_unban",
        "Member roles update": "member_roles_update",
        "Member update": "member_update",
        "Channel creation": "guild_channel_create",
        "Channel deletion": "guild_channel_delete",
        "Channel update": "guild_channel_update",
        "Role creation": "guild_role_create",
        "Role deletion": "guild_role_delete",
        "Role update": "guild_role_update",
        "Server update": "guild_update",
        "Voice channel join": "voice_channel_join",
        "Voice leave": "voice_channel_leave",
    }
)
category_list = commands.option_enum(
    {
        # "All": "all",
        "Messages": "messages",
        "Members": "members",
        "Channels": "channels",
        "Roles": "roles",
        "Server": "guild",
    }
)

## -- FUNCTIONS -- ##


def find_log_type(log_type_search: str):
    for category in categories:
        for log_type in categories[category]:
            if log_type == log_type_search:
                return log_type, categories[category][log_type]

    return None


def get_embed_update(current_embed: dict, embed_part: str, value: str):
    if embed_part.startswith("author") or embed_part.startswith("footer"):
        top_part = embed_part[0:6]
        sub_part = embed_part[:7]

        current_embed[top_part][sub_part] = value
    else:
        current_embed[embed_part] = value

    return current_embed


async def get_update_dictionary(bot, category_name: str, channel: disnake.TextChannel | None) -> dict:
    category = categories.get(category_name)
    dictionary = dict()

    if channel:
        webhook = await get_webhook(bot, channel)

    for log_type in category:
        if channel:
            dictionary.update({log_type: {"url": webhook.url, "toggle": True}})
        else:
            dictionary.update({log_type: {"url": None, "toggle": False}})

    return dictionary


async def get_webhook(
    bot: commands.Bot, channel: disnake.TextChannel, can_create: bool = True
) -> disnake.Webhook | None:
    webhooks = await channel.webhooks()
    webhook = disnake.utils.get(webhooks, name=f"{bot.user.name} Logging")

    if webhook:
        return webhook
    elif can_create:
        return await channel.create_webhook(name=f"{bot.user.name} Logging", avatar=bot.avatar)

    return None


## -- COG -- ##


class Settings(commands.Cog):
    name = ":gear: Settings"
    description = "These commands allow you to change how OutDash behaves."
    emoji = "⚙️"

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    ## -- SLASH COMMANDS -- ##

    """
    ! SETTING LOCKING

    These commands locks/unlocks the settings for the server.
    """

    @commands.slash_command(name="settings")
    @commands.has_permissions(administrator=True)
    async def settings(self, inter):
        pass

    @settings.sub_command(name="lock", description="Locks the server's settings.")
    async def settings_lock(self, inter: disnake.ApplicationCommandInteraction):
        """Locks the server's settings."""

        data_obj = GuildData(inter.guild.id)
        guild_data = data_obj.get_data()

        if guild_data.get("settings_locked") is True:
            embed = disnake.Embed(
                description=f"{no} The server's settings are already locked!",
                color=colors.error_embed_color,
            )
            return await inter.send(embed=embed, ephemeral=True)

        embed = disnake.Embed(
            description=f"{yes} The server's settings are now locked.",
            color=colors.success_embed_color,
        )

        data_obj.update_data({"settings_locked": True})
        await inter.send(embed=embed)

    @settings.sub_command(name="unlock", description="Unlocks the server's settings.")
    async def settings_unlock(self, inter: disnake.ApplicationCommandInteraction):
        """Unlocks the server's settings."""

        data_obj = GuildData(inter.guild.id)
        guild_data = data_obj.get_data()

        if guild_data.get("settings_locked") is False:
            embed = disnake.Embed(
                description=f"{no} The server's settings aren't locked!",
                color=colors.error_embed_color,
            )
            return await inter.send(embed=embed, ephemeral=True)

        embed = disnake.Embed(
            description=f"{yes} The server's settings are now unlocked.",
            color=colors.success_embed_color,
        )

        data_obj.update_data({"settings_locked": False})
        await inter.send(embed=embed)

    """
    ! SERVER SETTINGS

    These commands changes the way OutDash behaves in servers.
    """

    """
    ! LOGS SETTINGS

    These commands changes how OutDash logs events in servers.
    """

    @commands.slash_command(name="logs")
    async def logs(self, inter):
        pass

    @logs.sub_command_group(name="edit")
    async def logs_edit(self, inter):
        pass

    @logs_edit.sub_command(
        name="category",
        description="Edit log categories, changing channel for each log type in the category.",
    )
    @is_staff(manage_guild=True)
    @server_setting()
    async def edit_logs_category(
        self,
        inter: disnake.ApplicationCommandInteraction,
        category: category_list,
        channel: disnake.TextChannel = None,
    ):
        """Edit log categories, changing channel for each log type in the category..
        Parameters
        ----------
        category: The category you want to edit logs for.
        channel: The channel to send the logs to. If none, the log types will be disabled.
        """

        data_obj = GuildData(inter.guild.id)
        embed = disnake.Embed(
            description=f"{yes} All {category.lower()[:-1]} logs have been disabled",
            color=colors.success_embed_color,
        )

        if not channel:
            update = await get_update_dictionary(self.bot, category, None)
        else:
            update = await get_update_dictionary(self.bot, category, channel)
            embed.description = f"{yes} All {category.lower()[:-1]} logs will now be sent in {channel.mention}."

        data_obj.update_log_webhooks(update)
        await inter.send(embed=embed)

    @logs_edit.sub_command(name="channel", description="Change where a log type should be sent.")
    @is_staff(manage_guild=True)
    @server_setting()
    async def edit_logs_channel(
        self,
        inter: disnake.ApplicationCommandInteraction,
        type: type_list,
        channel: disnake.TextChannel = None,
    ):
        """Change where a log type should be sent.
        Parameters
        ----------
        type: What you want to edit. Example: "message_delete" would edit where deleted messages should be sent.
        channel: Where the selected log type should be sent. If none, the log type will be disabled.
        """

        data_obj = GuildData(inter.guild.id)
        log_type, log_description = find_log_type(type.lower())

        if not channel:
            embed = disnake.Embed(
                description=f"{yes} {log_description} logs have now been disabled.",
                color=colors.success_embed_color,
            )

            data_obj.update_data({log_type: None})
            return await inter.send(embed=embed)

        webhook = await get_webhook(self.bot, channel)
        embed = disnake.Embed(
            description=f"{yes} {log_description} logs will now be sent in {channel.mention}.",
            color=colors.success_embed_color,
        )

        data_obj.update_log_webhook(log_type, {"url": webhook.url, "toggle": True})
        await inter.send(embed=embed)

    """
    ! WELCOME/GOODBYE SETTINGS

    These commands manages the welcome/goodbye features
    """

    @commands.slash_command(name="editwelcome")
    async def editwelcome(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @editwelcome.sub_command(name="toggle")
    @is_staff(manage_guild=True)
    @server_setting()
    async def editwelcome_toggle(self, inter: disnake.ApplicationCommandInteraction, toggle: bool):
        """Toggles if welcome messages should be sent."""

        data_obj = GuildData(inter.guild.id)
        embed = disnake.Embed(
            description=f"{yes} Welcome messages have been {'disabled' if not toggle else 'enabled'}.",
            color=colors.success_embed_color,
        )

        data_obj.update_data({"welcome_toggle": toggle})
        await inter.send(embed=embed)

    @editwelcome.sub_command(name="content")
    @is_staff(manage_guild=True)
    @server_setting()
    async def editwelcome_content(self, inter: disnake.ApplicationCommandInteraction, *, content: str):
        """Edit the welcome message content."""

        data_obj = GuildData(inter.guild.id)
        data = data_obj.get_data()

        welcome_message = data["welcome_message"]
        welcome_message["content"] = content

        embed = disnake.Embed(
            description=f"{yes} The welcome message content has been set to:\n`{content}`",
            color=colors.success_embed_color,
        )

        data_obj.update_data({"welcome_message": welcome_message})
        await inter.send(embed=embed)

    @editwelcome.sub_command(name="embed")
    @is_staff(manage_guild=True)
    @server_setting()
    async def editwelcome_embed(
        self,
        inter: disnake.ApplicationCommandInteraction,
        embed_part: embed_parts_choices,
        *,
        value: str,
    ):
        """Edit the welcome message embed."""

        embed_part = embed_part.lower()
        data_obj = GuildData(inter.guild.id)
        data = data_obj.get_data()

        embed_update = get_embed_update(data["welcome_message"]["embed"], embed_part, value)
        data["welcome_message"]["embed"] = embed_update

        embed = disnake.Embed(description=f"{yes} ", color=colors.success_embed_color)

        if embed_part.startswith("author") or embed_part.startswith("footer"):
            top_part = embed_part[0:6]
            sub_part = embed_part[:7]

            embed.description += f"The {top_part} {sub_part} has been changed to `{value}`"
        else:
            embed.description += f"The {embed_part} has been changed to `{value}`"

        data_obj.update_data({"welcome_message": data})
        await inter.send(embed=embed)

    @editwelcome.sub_command(name="channel")
    @is_staff(manage_guild=True)
    @server_setting()
    async def editwelcome_channel(self, inter: disnake.ApplicationCommandInteraction, channel: disnake.TextChannel):
        """Set the channel where welcome messages should be sent."""

        data_obj = GuildData(inter.guild.id)

        embed = disnake.Embed(
            description=f"{yes} Welcome messages will now be sent in <#{channel.id}>.",
            color=colors.success_embed_color,
        )

        data_obj.update_data({"welcome_channel": str(channel.id), "welcome_toggle": True})
        await inter.send(embed=embed)

    @editwelcome.sub_command(name="trigger", description="Trigger the welcome message for testing.")
    @is_staff(manage_guild=True)
    async def editwelcome_trigger(self, inter: disnake.ApplicationCommandInteraction):
        """Trigger the welcome message for testing."""

        data_obj = GuildData(inter.guild.id)
        data = data_obj.get_data()

        if not data["welcome_toggle"]:
            embed = disnake.Embed(
                description=f"{no} Welcome messages are disabled for this guild.",
                color=colors.error_embed_color,
            )
            return await inter.send(embed=embed)

        await self.bot.dispatch("welcome_member", inter.author, kwargs={"channel": inter.channel})
        await inter.send("The welcome message has been triggered.", ephemeral=True)

    """
    ! CHATBOT SETTINGS

    These settings manages the chatbot feature.
    """

    @commands.slash_command(name="chatbot")
    async def chatbot(self, inter):
        pass

    @chatbot.sub_command(name="channel", description="Set where the chat bot should respond to messages.")
    @is_staff(manage_guild=True)
    @server_setting()
    async def chatbot_channel(self, inter: disnake.ApplicationCommandInteraction, channel: disnake.TextChannel):
        """Set where the chat bot should respond to messages.
        Parameters
        ----------
        channel: The channel where the bot should respond to messages.
        ----------
        """

        data_obj = GuildData(inter.guild.id)
        embed = disnake.Embed(
            description=f"{yes} The chat bot will now respond to messages in {channel.mention}.",
            color=colors.success_embed_color,
        )

        data_obj.update_data({"chat_bot_channel": channel.id, "chat_bot_toggle": True})
        await inter.send(embed=embed)

    @chatbot.sub_command(name="toggle", description="Toggle the chat bot feature.")
    @is_staff(manage_guild=True)
    @server_setting()
    async def chatbot_toggle(self, inter: disnake.ApplicationCommandInteraction, toggle: bool):
        """Toggle the chat bot feature.
        Parameters
        ----------
        toggle: Whether the chat bot should be enabled or not.
        """

        data_obj = GuildData(inter.guild.id)
        data = data_obj.get_data()

        embed = disnake.Embed(
            description=f"{yes} The chat bot feature has been " + "enabled" if toggle else "disabled" + ".",
            color=colors.success_embed_color,
        )

        if data["chat_bot_toggle"] == toggle:
            embed = disnake.Embed(
                description=f"{no} The chat bot feature is already " + "enabled" if toggle else "disabled" + "!",
                color=colors.error_embed_color,
            )
        else:
            data_obj.update_data({"chat_bot_toggle": toggle})

        await inter.send(embed=embed)

    """
    ! USER SETTINGS

    These settings manages user's settings.
    """

    @commands.slash_command(name="privacy", description="Manage your privacy settings.")
    async def privacy(self, inter):
        """Manage your privacy settings."""
        pass

    @privacy.sub_command(name="messages", description="Edit you message privacy settings.")
    async def privacymessages(
        self,
        inter: disnake.ApplicationCommandInteraction,
        type: message_settings_types,
        toggle: bool,
    ):
        """Edit your message privacy settings.
        Parameters
        ----------
        type: The message privacy setting you want to edit.
        toggle: Whether the privacy setting should be on or not.
        """

        data_obj = UserData(inter.author.id)
        embed = disnake.Embed(
            description=f"{yes} The {message_settings_description[type]} privacy setting has been "
            f"{'enabled' if toggle else 'disabled'}.",
            color=colors.success_embed_color,
        )

        data_obj.update({"message_content_privacy": str(toggle).lower()})
        await inter.send(embed=embed)


def setup(bot):
    bot.add_cog(Settings(bot))
