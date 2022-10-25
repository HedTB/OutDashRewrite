## -- IMPORTING -- ##

# MODULES
import functools
import typing
import disnake
import re
import logging

from disnake.ext import commands
from dotenv import load_dotenv

# FILES
from utils import config, colors

from utils.checks import SettingsLocked, NotAdministrator, NotModerator
from utils.emojis import no

## -- VARIABLES -- ##

load_dotenv()

logger = logging.getLogger("OutDash")

IGNORED_ERRORS = (commands.NotOwner, commands.CommandNotFound)
ERROR_TITLE_REGEX = re.compile(r"((?<=[a-z])[A-Z]|(?<=[a-zA-Z])[A-Z](?=[a-z]))")

command_types = {
    "member": [
        "softban",
        "unban",
        "ban",
        "kick",
        "unmute",
        "mute",
        "warn",
    ]
}

argument_descriptions = {
    # MODERATION
    "clear": {"amount": "how many messages you want to delete"},
    "slowmode": {"seconds": "what the slowmode should be set to"},
    "mute": {"length": "how long you want to mute the member for"},
    "warn": {"reason": "the reason for the warning"},
    "warn_remove": {
        "member": "who to remove a warning from",
        "warning_id": "the ID of the warning to remove",
    },
    "warnings_clear": {"member": "whose warnings to clear"},
    # BOT SETTINGS
    "chatbot_channel": {"channel": "where the chatbot should respond to messages"},
    "editwelcome_content": {"content": "what the welcome message content should be set to"},
    # LEVELING
    "leveling_message_deletion": {"delay": "the levelup message deletion delay"},
    "leveling_message_content": {"content": "what the levelup message content should be set to"},
    "level_set": {
        "member": "whose level to set",
        "level": "what the level should be set to",
    },
    "level_add": {"member": "who to add levels to", "levels": "how many levels to add"},
    "level_remove": {
        "member": "who to remove levels from",
        "levels": "how many levels to remove",
    },
}

## -- COG -- ##


class Errors(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def error_embed(description: str) -> disnake.Embed:
        return disnake.Embed(description=f"{no} {description}", color=colors.error_embed_color)

    @staticmethod
    def get_argument_description(command: str, argument: str) -> typing.Optional[str]:
        if command in command_types["member"] and argument == "member":
            return "the member you want to " + command

        command_arguments = argument_descriptions.get(command)
        if not command_arguments:
            return None

        return command_arguments.get(argument)

    @staticmethod
    def get_command_name(command: commands.Command) -> str:
        return command.callback.__name__

    @staticmethod
    def get_title_from_name(error: typing.Union[Exception, str]) -> str:
        if not isinstance(error, str):
            error = error.__class__.__name__
        return re.sub(ERROR_TITLE_REGEX, r" \1", error)

    @staticmethod
    def get_partial_command(inter: disnake.Interaction) -> typing.Optional[tuple[str, str]]:
        invoked_command = inter.data.name
        command_type = None

        if not invoked_command:
            return None

        for command_type in command_types:
            partial_commands = command_types[command_type]

            for partial_command in partial_commands:
                if invoked_command.find(partial_command):
                    command_name = partial_command
                    command_type = command_type

                    break

        if not command_name:
            return None

        return command_name, command_type

    @staticmethod
    def reset_command_cooldown(inter: disnake.Interaction):
        if return_value := isinstance(inter, commands.Context):
            inter.command.reset_cooldown(inter)
        return return_value

    async def handle_bot_missing_perms(
        self, inter: disnake.Interaction, error: commands.BotMissingPermissions
    ) -> disnake.Embed:
        bot_permissions = inter.channel.permissions_for(inter.me)

        if inter.invoked_with is not None:
            partial_command_name, command_type = self.get_partial_command(inter)

            if command_type == "member":
                embed = self.error_embed(description=f"I don't have permission to {partial_command_name} this member.")
            else:
                embed = self.error_embed(description="I don't have the required permission to run this command.")

        if bot_permissions >= disnake.Permissions(send_messages=True, embed_links=True, external_emojis=True):
            await inter.send(embed=embed)

        elif bot_permissions >= disnake.Permissions(send_messages=True):
            await inter.send(f"{no} Please give me the `Embed Links` permission, otherwise I won't work properly.")

            logger.warning(
                f"Missing partial required permissions for {inter.channel.id}. "
                "I am able to send messages, but not embeds."
            )
        else:
            logger.error(f"Unable to send messages to {inter.channel}.")

    async def handle_check_failure(
        self, inter: disnake.Interaction, error: commands.CheckFailure
    ) -> typing.Optional[disnake.Embed]:
        description = ""

        if isinstance(error, commands.CheckAnyFailure):
            description = self.get_title_from_name(error.checks[-1])
        elif isinstance(error, commands.BotMissingPermissions):
            await self.handle_bot_missing_perms(inter, error)
            return None

        elif isinstance(error, commands.MissingPermissions):
            if len(error.missing_permissions) == 1:
                description = "You're missing the `{}` permission.".format(
                    error.missing_permissions[0].title().replace("_", " ")
                )

            else:
                missing_permissions = ""
                for missing_permission in error.missing_permissions:
                    missing_permissions += f"{missing_permission.title().replace('_', ' ')}, "

                missing_permissions = missing_permissions[:-2]
                description = f"You're missing the `{missing_permissions}` permissions."

        elif isinstance(error, SettingsLocked):
            description = "The server's settings are locked."
        elif isinstance(error, (NotModerator, NotAdministrator)):
            description = "You don't have permission to do that."
        else:
            description = str(error)

        return self.error_embed(description)

    async def on_command_error(self, inter: disnake.Interaction, error: commands.CommandError) -> None:
        if getattr(error, "handled", False):
            return logging.debug(f"Command {inter.command} had its error handled locally, ignoring.")
        elif isinstance(error, IGNORED_ERRORS):
            return

        embed: typing.Optional[disnake.Embed] = None
        should_respond = True

        if isinstance(error, commands.CheckFailure):
            embed = await self.handle_check_failure(inter, error)
            if embed is None:
                should_respond = False

        elif isinstance(error, commands.ConversionError):
            error = error.original

        elif isinstance(error, commands.CommandInvokeError):
            if isinstance(error.original, disnake.Forbidden):
                logger.warn(f"Permissions error occurred in {inter.command}.")
                await self.handle_bot_missing_perms(inter, error.original)
                should_respond = False
            else:
                logger.error(
                    "Error occurred in command or message component",
                    exc_info=error.original,
                )

                error_str = str(error.original).replace("``", "`\u200b`")

                embed = self.error_embed(
                    (
                        "Something went wrong while trying to execute the command. "
                        "Please report this bug, the error below and what you were trying to do in "
                        f"the [support server](https://discord.gg/{config.BOT_SERVER})."
                        f"\n\n``{error_str}``"
                    )
                )

        if not should_respond:
            return logger.debug(
                "Not responding to error since should_respond is falsey because either "
                "the embed has already been sent or belongs to a hidden command and thus should be hidden."
            )

        if embed is None:
            embed = self.error_embed(self.get_title_from_name(error), str(error))

        print(inter.response.is_done())

        if isinstance(inter, disnake.Interaction) and not inter.response.is_done():
            await inter.send(embed=embed, ephemeral=True)

    @commands.Cog.listener(name="on_slash_command_error")
    @commands.Cog.listener(name="on_message_command_error")
    async def on_error(self, inter: disnake.Interaction, error: Exception) -> None:
        if isinstance(inter, disnake.Interaction):
            if inter.response.is_done():
                inter.send = functools.partial(inter.followup.send, ephemeral=True)
            else:
                inter.send = functools.partial(inter.send, ephemeral=True)

            if isinstance(
                inter,
                (
                    disnake.Interaction,
                    disnake.MessageCommandInteraction,
                    disnake.UserCommandInteraction,
                ),
            ):
                inter.command = inter.application_command
            elif isinstance(inter, (disnake.MessageInteraction, disnake.ModalInteraction)):
                inter.command = inter.message
            else:
                inter.command = inter
        try:
            await self.on_command_error(inter, error)
        except Exception as e:
            logger.exception("Error occurred in error handler", exc_info=e)


def setup(bot):
    bot.add_cog(Errors(bot))
