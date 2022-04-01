## -- IMPORTING -- ##

# MODULES
import functools
import typing
import disnake
import os
import certifi

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

logger = logging.getLogger("OutDash")

IGNORED_ERRORS = (commands.NotOwner, commands.CommandNotFound)
ERROR_TITLE_REGEX = re.compile(r"((?<=[a-z])[A-Z]|(?<=[a-zA-Z])[A-Z](?=[a-z]))")

command_types = {
    "member": [
        "unban", "ban", "kick", "unmute", "mute", "warn",
    ]
}

typing.TYPE_CHECKING = True
if typing.TYPE_CHECKING:
    AnyContext = typing.Union[commands.Context, disnake.Interaction]

## -- COG -- ##

class Errors(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def error_embed(description: str) -> disnake.Embed:
        return disnake.Embed(description=config.no + " " + description, color=config.error_embed_color)
    
    @staticmethod
    def get_title_from_name(error: typing.Union[Exception, str]) -> str:
        if not isinstance(error, str):
            error = error.__class__.__name__
        return re.sub(ERROR_TITLE_REGEX, r" \1", error)
    
    @staticmethod
    def get_partial_command(ctx: AnyContext) -> typing.Optional[tuple[str, str]]:
        invoked_command = None
        partial_command_name = None
        command_type = None
        
        if isinstance(ctx, disnake.ApplicationCommandInteraction):
            invoked_command = ctx.data.name
        elif isinstance(ctx, commands.Context):
            invoked_command = ctx.invoked_with
        
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
    def _reset_command_cooldown(ctx: AnyContext):
        if return_value := isinstance(ctx, commands.Context):
            ctx.command.reset_cooldown(ctx)
        return return_value
    
    async def handle_user_input_error(self, ctx: AnyContext, error: commands.UserInputError, reset_cooldown: bool = True) -> disnake.Embed:
        if reset_cooldown:
            self._reset_command_cooldown(ctx)

        sub_str = " is a required argument that is missing."
        missing_argument = str(error).replace(sub_str, "")
        missing_argument = "`" + missing_argument + "`"
        
        description = f"Please specify the {missing_argument}."
        
        if isinstance(error, commands.BadUnionArgument):
            description = self.get_title_from_name(str(error))
            
        return self.error_embed(description)
    
    async def handle_bot_missing_perms(self, ctx: AnyContext, error: commands.BotMissingPermissions) -> disnake.Embed:
        bot_permissions = ctx.channel.permissions_for(ctx.me)
        partial_command_name, command_type = self.get_partial_command(ctx)
        
        if command_type == "member":
            embed = self.error_embed(f"I don't have permission to {partial_command_name} this member.")
        else:
            embed = self.error_embed("I don't have the required permission to run this command.")
        
        if bot_permissions >= disnake.Permissions(send_messages=True, embed_links=True):
            await ctx.send(embed=embed)
            
        elif bot_permissions >= disnake.Permissions(send_messages=True):
            await ctx.send("**Permissions Failure**\n Please give me the `Embed Links` permission, otherwise I won't work properly.")
            
            logger.warning(
                f"Missing partial required permissions for {ctx.channel}. "
                "I am able to send messages, but not embeds."
            )
        else:
            logger.error(f"Unable to send messages to {ctx.channel}.")
            
    async def handle_check_failure(self, ctx: AnyContext, error: commands.CheckFailure) -> typing.Optional[disnake.Embed]:
        description = ""
        
        if isinstance(error, commands.CheckAnyFailure):
            description = self.get_title_from_name(error.checks[-1])
        elif isinstance(error, commands.PrivateMessageOnly):
            description = "This command can only be run in DMs."
            
        elif isinstance(error, commands.NoPrivateMessage):
            description = "This command can only be run in servers."
        elif isinstance(error, commands.BotMissingPermissions):
            await self.handle_bot_missing_perms(ctx, error)
            return None
        
        elif isinstance(error, commands.MissingPermissions):
            if len(error.missing_permissions) == 1:
                description = "You're missing the `{}` permission.".format(error.missing_permissions[0].title().replace("_", " ") )

            else:
                missing_permissions = ""
                for missing_permission in error.missing_permissions:
                    missing_permissions += f"{missing_permission.title().replace('_', ' ')}, "

                missing_permissions = missing_permissions[:-2]
                description = f"You're missing the `{missing_permissions}` permissions."
        
        elif isinstance(error, SettingsLocked):
            description = "The server's settings are locked."
        else:
            description = str(error)
        
        return self.error_embed(description)
    
    async def on_command_error(self, ctx: AnyContext, error: commands.CommandError) -> None:
        if getattr(error, "handled", False):
            logging.debug(f"Command {ctx.command} had its error handled locally, ignoring.")
            return

        if isinstance(error, IGNORED_ERRORS):
            return

        embed: typing.Optional[disnake.Embed] = None
        should_respond = True

        if isinstance(error, commands.UserInputError):
            embed = await self.handle_user_input_error(ctx, error)
        elif isinstance(error, commands.CheckFailure):
            embed = await self.handle_check_failure(ctx, error)
            if embed is None:
                should_respond = False
        
        elif isinstance(error, commands.ConversionError):
            error = error.original
        elif isinstance(error, commands.DisabledCommand):
            if ctx.command.hidden:
                should_respond = False
            else:
                msg = f"Command `{ctx.invoked_with}` is disabled."
                if reason := ctx.command.extras.get("disabled_reason", None):
                    msg += f"\nReason: {reason}"
                embed = self.error_embed(msg)

        elif isinstance(error, commands.CommandInvokeError):
            if isinstance(error.original, disnake.Forbidden):
                logger.warn(f"Permissions error occurred in {ctx.command}.")
                await self.handle_bot_missing_perms(ctx, error.original)
                should_respond = False
            else:
                logger.error("Error occurred in command or message component", exc_info=error.original)

                error_str = str(error.original).replace("``", "`\u200b`")
                msg = (
                    "Something went wrong internally in the action you were trying to execute. "
                    "Please report this error and the code below and what you were trying to do in "
                    f"the [support server](https://discord.gg/{config.bot_server})."
                    f"\n\n``{error_str}``"
                )

                embed = self.error_embed(msg)

        if not should_respond:
            logger.debug(
                "Not responding to error since should_respond is falsey because either "
                "the embed has already been sent or belongs to a hidden command and thus should be hidden."
            )
            return

        if embed is None:
            embed = self.error_embed(self.get_title_from_name(error), str(error))

        await ctx.send(embeds=[embed])

    @commands.Cog.listener(name="on_command_error")
    @commands.Cog.listener(name="on_slash_command_error")
    @commands.Cog.listener(name="on_message_command_error")
    async def on_error(self, ctx: AnyContext, error: Exception) -> None:
        if isinstance(ctx, commands.Context):
            # view = DeleteView(ctx.author)
            # if ctx.channel.permissions_for(ctx.me).read_message_history:
            #     ctx.send = functools.partial(ctx.reply, fail_if_not_exists=False)
            # else:
            ctx.send = functools.partial(ctx.send)
        elif isinstance(ctx, disnake.Interaction):
            if ctx.response.is_done():
                ctx.send = functools.partial(ctx.followup.send, ephemeral=True)
            else:
                ctx.send = functools.partial(ctx.send, ephemeral=True)

            if isinstance(
                ctx,
                (
                    disnake.ApplicationCommandInteraction,
                    disnake.MessageCommandInteraction,
                    disnake.UserCommandInteraction,
                ),
            ):
                ctx.command = ctx.application_command
            elif isinstance(ctx, (disnake.MessageInteraction, disnake.ModalInteraction)):
                ctx.command = ctx.message
            else:
                ctx.command = ctx
        try:
            await self.on_command_error(ctx, error)
        except Exception as e:
            logger.exception("Error occurred in error handler", exc_info=e)
    

def setup(bot):
    bot.add_cog(Errors(bot))