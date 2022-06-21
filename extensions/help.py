## -- IMPORTING -- ##

# MODULES
import typing
import disnake
import os

from disnake.ext import commands, menus
from dotenv import load_dotenv

# FILES
from utils import config, functions, colors
from utils.checks import *
from utils.classes import *
from utils.emojis import *

from . import fun, leveling, miscellaneous, moderation, music, settings

## -- VARIABLES -- ##

load_dotenv()

AnyContext = typing.Union[commands.Context, disnake.ApplicationCommandInteraction]

pages = [
    1,
    settings.Settings,
    fun.Fun,
    leveling.Leveling,
    miscellaneous.Miscellaneous,
    moderation.Moderation,
    music.Music,
]
empty_group_bases = [
    "settings",
    "leveling",
    "editwelcome",
    "chatbot",
    "level",
    "xp",
    "privacy",
]

permissions = os.environ.get("PERMISSIONS")

help_description = """
    The prefix for this bot is `{prefix}`.
    
    For module help, use `{prefix}help <Module>`. (CASE-SENSITIVTE)
    For command help, use `{prefix}help <command>`.

    [**Invite OutDash!**](https://discord.com/api/oauth2/authorize?client_id=836494578135072778&permissions={permissions}&scope=bot%20applications.commands)
"""

## -- FUNCTIONS -- ##


def get_group_commands(
    group: commands.Group, *, original_group: commands.Group = None
) -> typing.List[str]:
    group_commands = []

    if group.name not in empty_group_bases:
        group_commands.append(group.qualified_name)

    for command in group.commands:
        group_commands.append(command.qualified_name)

    return group_commands


def get_extension_commands(extension: commands.Cog):
    commands_list = []

    for command in extension.walk_commands(extension):
        if isinstance(command, commands.Group) and command.name in empty_group_bases:
            continue

        commands_list.append(command.qualified_name)

    return commands_list


## -- VIEWS -- ##


class HelpPageSource(menus.ListPageSource):
    def __init__(self, entries: dict):
        super().__init__(entries, per_page=1)

    @staticmethod
    def format_page(menu: menus.MenuPages, entry: int | commands.Cog) -> disnake.Embed:
        ctx = menu.ctx

        if isinstance(entry, int):
            embed = disnake.Embed(
                title="Help",
                description=help_description.format(
                    prefix=ctx.bot.get_bot_prefix(ctx.guild), permissions=permissions
                ),
                color=colors.embed_color,
                timestamp=datetime.datetime.utcnow(),
            )

            for extension in pages:
                if extension == 1:
                    continue

                embed.add_field(
                    name=getattr(extension, "name", extension.__name__.title()),
                    value=getattr(
                        extension, "description", "No description has been provided."
                    ),
                    inline=True,
                )

            embed.set_footer(
                text=f"Requested by {ctx.author}",
                icon_url=ctx.author.avatar or config.DEFAULT_AVATAR_URL,
            )
            embed.timestamp = datetime.datetime.utcnow()

        else:
            embed = disnake.Embed(
                title=entry.name,
                description=entry.description,
                color=colors.embed_color,
                timestamp=datetime.datetime.utcnow(),
            )

            embed.add_field(
                name="Commands",
                value=", ".join(
                    f"`{command}`" for command in get_extension_commands(entry)
                ),
            )

            embed.set_footer(
                text=f"Requested by {ctx.author}",
                icon_url=ctx.author.avatar or config.DEFAULT_AVATAR_URL,
            )

        return embed


class HelpPaginator(disnake.ui.View, menus.MenuPages):
    def __init__(
        self,
        source: menus.PageSource,
        *,
        delete_message_after: bool = False,
        message: disnake.Message | None = None,
    ):
        super().__init__(timeout=60)

        self._source = source
        self.current_page = 0
        self.ctx = None
        self.message = message
        self.delete_message_after = delete_message_after

        self.add_item(
            disnake.ui.Button(
                label="Invite me!",
                url=f"https://discord.com/api/oauth2/authorize?client_id=836494578135072778&permissions={permissions}&scope=bot%20applications.commands",
                row=0,
            )
        )

    @staticmethod
    def get_extension_embed(extension_index: int = 1):
        extension: commands.Cog = pages[extension_index]

        embed = disnake.Embed(
            title=extension.name,
            description=extension.description,
            color=colors.embed_color,
        )

        embed.add_field(
            name="Commands",
            value=", ".join(
                f"`{command}`" for command in get_extension_commands(extension)
            ),
        )

        return embed

    async def start(
        self, ctx: AnyContext, *, channel: disnake.TextChannel | None = None
    ):
        self.ctx = ctx

        await self._source._prepare_once()
        await self.send_initial_message(ctx, channel or ctx.channel)

    async def send_initial_message(self, ctx: AnyContext, channel: disnake.TextChannel):
        embed = HelpPageSource.format_page(self, 1)

        if self.message:
            self.current_page = 0
            await self.message.edit(embed=embed, view=self)
        else:
            self.message = await ctx.send(embed=embed, view=self)

            if isinstance(ctx, disnake.Interaction):
                self.message = await ctx.original_message()

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        return interaction.user == self.ctx.author

    @disnake.ui.button(emoji="🏠", style=disnake.ButtonStyle.secondary, row=1)
    async def home_button(
        self, button: disnake.Button, interaction: disnake.MessageInteraction
    ):
        await self.show_page(0)
        await interaction.response.defer()

    @disnake.ui.button(emoji=pages[1].emoji, style=disnake.ButtonStyle.secondary, row=1)
    async def button_one(
        self, button: disnake.Button, interaction: disnake.MessageInteraction
    ):
        await self.show_page(1)
        await interaction.response.defer()

    @disnake.ui.button(emoji=pages[2].emoji, style=disnake.ButtonStyle.secondary, row=1)
    async def button_two(
        self, button: disnake.Button, interaction: disnake.MessageInteraction
    ):
        await self.show_page(2)
        await interaction.response.defer()

    @disnake.ui.button(emoji=pages[3].emoji, style=disnake.ButtonStyle.secondary, row=1)
    async def button_three(
        self, button: disnake.Button, interaction: disnake.MessageInteraction
    ):
        await self.show_page(3)
        await interaction.response.defer()

    @disnake.ui.button(emoji=pages[4].emoji, style=disnake.ButtonStyle.secondary, row=1)
    async def button_four(
        self, button: disnake.Button, interaction: disnake.MessageInteraction
    ):
        await self.show_page(4)
        await interaction.response.defer()

    @disnake.ui.button(emoji=pages[5].emoji, style=disnake.ButtonStyle.secondary, row=2)
    async def button_five(
        self, button: disnake.Button, interaction: disnake.MessageInteraction
    ):
        await self.show_page(5)
        await interaction.response.defer()

    @disnake.ui.button(emoji=pages[6].emoji, style=disnake.ButtonStyle.secondary, row=2)
    async def button_six(
        self, button: disnake.Button, interaction: disnake.MessageInteraction
    ):
        await self.show_page(6)
        await interaction.response.defer()


class HelpView(disnake.ui.View):
    def __init__(self):
        super().__init__()

        self.add_item(
            disnake.ui.Button(
                label="Invite me!",
                url=f"https://discord.com/api/oauth2/authorize?client_id=836494578135072778&permissions={permissions}&scope=bot%20applications.commands",
            )
        )


class CommandHelpView(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

        self.add_item(
            disnake.ui.Button(
                label="Invite me!",
                url=f"https://discord.com/api/oauth2/authorize?client_id=836494578135072778&permissions={permissions}&scope=bot%20applications.commands",
            )
        )

    @disnake.ui.button(emoji="🏠", style=disnake.ButtonStyle.secondary, row=1)
    async def home_button(
        self, button: disnake.Button, interaction: disnake.MessageInteraction
    ):
        formatter = HelpPageSource(pages)
        menu = HelpPaginator(formatter, message=interaction.message)

        await menu.start(interaction)
        await interaction.response.defer()


## -- CLASSES -- ##


class HelpCommand(commands.HelpCommand):
    @staticmethod
    def get_command_signature(prefix: str, command: commands.Command) -> str:
        return "%s%s %s" % (prefix, command.qualified_name, command.signature)

    async def send_bot_help(self, mapping: dict):
        ctx = self.context

        formatter = HelpPageSource(pages)
        menu = HelpPaginator(formatter)

        await menu.start(ctx, channel=ctx.channel)

    async def send_command_help(self, command: commands.Command):
        ctx = self.context
        docstring = disnake.utils.parse_docstring(command.callback)
        description = (
            docstring.get("description") or "No description has been provided."
        )

        prefix = ctx.bot.get_bot_prefix(ctx.channel.guild)
        embed = disnake.Embed(
            title=command.qualified_name.title(),
            description="`<>` means that the argument is required.\n`[]` means that the argument is optional.",
            color=colors.embed_color,
            timestamp=datetime.datetime.utcnow(),
        )

        embed.add_field(
            name="Usage",
            value=self.get_command_signature(prefix, command),
            inline=False,
        )
        embed.add_field(name="Description", value=description, inline=False)

        if len(command.aliases) >= 1:
            embed.add_field(
                name="Aliases", value=", ".join(command.aliases), inline=False
            )

        await ctx.send(embed=embed, view=CommandHelpView())

    async def send_group_help(self, group: commands.Group):
        ctx = self.context

        embed = disnake.Embed(
            title=group.name.title() + " Group",
            description="`<>` means that the argument is required.\n`[]` means that the argument is optional.",
            color=colors.embed_color,
            timestamp=datetime.datetime.utcnow(),
        )

        embed.add_field(
            name="Commands",
            value=", ".join(f"`{command}`" for command in get_group_commands(group)),
        )

        embed.set_footer(
            text=f"Requested by {ctx.author}",
            icon_url=ctx.author.avatar or config.DEFAULT_AVATAR_URL,
        )

        await ctx.send(embed=embed)

    async def send_cog_help(self, cog: commands.Cog):
        ctx = self.context
        valid_module = False
        extension_index = None

        for extension in pages:
            if extension == 1:
                continue

            if extension.__name__ == cog.__cog_name__:
                valid_module = True
                extension_index = pages.index(extension)

                break

        if not valid_module:
            embed = disnake.Embed(
                description=f"{no} Please provide a valid module.",
                color=colors.error_embed_color,
            )

            if isinstance(ctx, disnake.ApplicationCommandInteraction):
                return await ctx.send(embed=embed, ephemeral=True)
            else:
                return await ctx.send(embed=embed)

        embed = HelpPaginator.get_extension_embed(extension_index)
        await ctx.send(embed=embed, view=CommandHelpView())

    async def command_not_found(self, error: str):
        return f"There's no command called `{error}`."

    async def subcommand_not_found(self, command: commands.Command, error: str):
        if isinstance(command, commands.Group) and len(command.all_commands) > 0:
            return f"There's no subcommands named `{error}` associated with the command `{command.qualified_name}`."

        return f"There's no subcommands associated with the command `{command.qualified_name}`."

    async def send_error_message(self, error: str):
        ctx = self.context
        embed = disnake.Embed(
            description=f"{no} {error}", color=colors.error_embed_color
        )

        if isinstance(ctx, disnake.Interaction):
            await ctx.send(embed=embed, ephemeral=True)
        else:
            await ctx.send(embed=embed)


## -- COG -- ##


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._original_help_command = bot.help_command

        bot.help_command = HelpCommand()
        bot.help_command.cog = self

    def cog_unload(self) -> None:
        self.bot.help_command = self._original_help_command

    def get_slash_command_signature(self, command: commands.InvokableSlashCommand):
        parameters = ""

        for option in command.options:
            bracket1 = "<" if option.required else "["
            bracket2 = ">" if option.required else "]"

            parameters += f"{bracket1}{option.name}{bracket2} "

        parameters[:-1]
        return "/%s %s" % (command.name, parameters)

    ## -- SLASH COMMANDS -- ##

    @commands.slash_command(name="help")
    async def slash_help(self, inter: disnake.ApplicationCommandInteraction):
        """Lost? Check out this command!"""
        pass

    @slash_help.sub_command(name="menu")
    async def slash_help_menu(self, inter: disnake.ApplicationCommandInteraction):
        """Open up the interactive help menu."""

        formatter = HelpPageSource(pages)
        menu = HelpPaginator(formatter)

        await menu.start(inter, channel=inter.channel)

    @slash_help.sub_command(name="command")
    async def slash_help_command(
        self, inter: disnake.ApplicationCommandInteraction, command: str
    ):
        """Get information about a specific command.
        Parameters
        ----------
        command: The command you want information on.
        """

        command_obj = self.bot.get_slash_command(command)

        if not command_obj:
            embed = disnake.Embed(
                description=f"{no} There's no command called `{command}`.",
                color=colors.error_embed_color,
            )
            return await inter.send(embed=embed, ephemeral=True)

        embed = disnake.Embed(
            title=command_obj.qualified_name.title(),
            description="`<>` means that the argument is required.\n`[]` means that the argument is optional.",
            color=colors.embed_color,
            timestamp=datetime.datetime.utcnow(),
        )

        embed.add_field(
            name="Usage",
            value=self.get_slash_command_signature(command_obj),
            inline=False,
        )
        embed.add_field(name="Description", value=command_obj.description, inline=False)

        await inter.send(embed=embed, view=CommandHelpView())


def setup(bot):
    bot.add_cog(Help(bot))
