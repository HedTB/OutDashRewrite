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
from utils.data import *
from utils.emojis import *

from . import fun, leveling, miscellaneous, moderation, music, settings

## -- VARIABLES -- ##

load_dotenv()

disnake.ApplicationCommandInteraction = typing.Union[commands.Context, disnake.ApplicationCommandInteraction]

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
    The prefix for this bot is `/`.
    
    For module help, use `/help category <Module>`.
    For command help, use `/help command <command>`.

    [**Invite OutDash!**](https://discord.com/api/oauth2/authorize?client_id=836494578135072778&permissions={permissions}&scope=bot%20applications.commands)
"""

## -- FUNCTIONS -- ##


def get_group_commands(group: commands.Group, *, original_group: commands.Group = None) -> typing.List[str]:
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


def get_slash_command_signature(
    command: commands.InvokableSlashCommand, *, options: list[disnake.Option] | None = None
):
    parameters = ""

    for option in options or command.options:
        bracket1 = "<" if option.required else "["
        bracket2 = ">" if option.required else "]"

        parameters += f"{bracket1}{option.name}{bracket2} "

    return f"/{command.qualified_name} {parameters}".rstrip()


## -- VIEWS -- ##


class HelpPageSource(menus.ListPageSource):
    def __init__(self, entries: dict):
        super().__init__(entries, per_page=1)

    @staticmethod
    def format_page(menu: menus.MenuPages, entry: int | commands.Cog) -> disnake.Embed:
        inter = menu.inter

        if isinstance(entry, int):
            embed = disnake.Embed(
                title="Help",
                description=help_description,
                color=colors.embed_color,
                timestamp=datetime.datetime.utcnow(),
            )

            for extension in pages:
                if extension == 1:
                    continue

                embed.add_field(
                    name=getattr(extension, "name", extension.__name__.title()),
                    value=getattr(extension, "description", "No description has been provided."),
                    inline=True,
                )

            embed.set_footer(
                text=f"Requested by {inter.author}",
                icon_url=inter.author.avatar or config.DEFAULT_AVATAR_URL,
            )
            embed.timestamp = datetime.datetime.utcnow()

        else:
            embed = (
                disnake.Embed(
                    title=entry.name,
                    description=entry.description,
                    color=colors.embed_color,
                    timestamp=datetime.datetime.utcnow(),
                )
                .add_field(
                    name="Commands",
                    value=", ".join(f"`{command}`" for command in get_extension_commands(entry)),
                )
                .set_footer(
                    text=f"Requested by {inter.author}",
                    icon_url=inter.author.avatar or config.DEFAULT_AVATAR_URL,
                )
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
        super().__init__(timeout=None)

        self._source = source
        self.current_page = 0
        self.inter = None
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

        return disnake.Embed(
            title=extension.name,
            description=extension.description,
            color=colors.embed_color,
        ).add_field(
            name="Commands",
            value=", ".join(f"`{command}`" for command in get_extension_commands(extension)),
        )

    async def start(self, inter: disnake.ApplicationCommandInteraction):
        self.inter = inter

        await self._source._prepare_once()
        await self.send_initial_message(inter)

    async def send_initial_message(self, inter: disnake.ApplicationCommandInteraction):
        embed = HelpPageSource.format_page(self, 1)

        if self.message:
            self.current_page = 0
            await self.message.edit(embed=embed, view=self)
        else:
            self.message = await inter.send(embed=embed, view=self)
            self.message = await inter.original_message()

    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        return inter.user == self.inter.author

    @disnake.ui.button(emoji="🏠", style=disnake.ButtonStyle.secondary, row=1)
    async def home_button(self, button: disnake.Button, inter: disnake.MessageInteraction):
        await self.show_page(0)
        await inter.response.defer()

    @disnake.ui.button(emoji=pages[1].emoji, style=disnake.ButtonStyle.secondary, row=1)
    async def button_one(self, button: disnake.Button, inter: disnake.MessageInteraction):
        await self.show_page(1)
        await inter.response.defer()

    @disnake.ui.button(emoji=pages[2].emoji, style=disnake.ButtonStyle.secondary, row=1)
    async def button_two(self, button: disnake.Button, inter: disnake.MessageInteraction):
        await self.show_page(2)
        await inter.response.defer()

    @disnake.ui.button(emoji=pages[3].emoji, style=disnake.ButtonStyle.secondary, row=1)
    async def button_three(self, button: disnake.Button, inter: disnake.MessageInteraction):
        await self.show_page(3)
        await inter.response.defer()

    @disnake.ui.button(emoji=pages[4].emoji, style=disnake.ButtonStyle.secondary, row=1)
    async def button_four(self, button: disnake.Button, inter: disnake.MessageInteraction):
        await self.show_page(4)
        await inter.response.defer()

    @disnake.ui.button(emoji=pages[5].emoji, style=disnake.ButtonStyle.secondary, row=2)
    async def button_five(self, button: disnake.Button, inter: disnake.MessageInteraction):
        await self.show_page(5)
        await inter.response.defer()

    @disnake.ui.button(emoji=pages[6].emoji, style=disnake.ButtonStyle.secondary, row=2)
    async def button_six(self, button: disnake.Button, inter: disnake.MessageInteraction):
        await self.show_page(6)
        await inter.response.defer()


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
    def __init__(
        self,
        *,
        has_sub_commands: bool = False,
        sub_commands: typing.Dict[
            str,
            commands.InvokableSlashCommand,
        ]
        | None = None,
    ):
        super().__init__(timeout=None)

        self.add_item(
            disnake.ui.Button(
                label="Invite me!",
                url=f"https://discord.com/api/oauth2/authorize?client_id=836494578135072778&permissions={permissions}&scope=bot%20applications.commands",
                row=2,
            )
        )

        select_menu = self.children[1]

        if not has_sub_commands:
            return self.remove_item(select_menu)

        select_menu.options = [
            disnake.SelectOption(label=f"/{sub_command.qualified_name}", value=sub_command.qualified_name)
            for sub_command in sub_commands.values()
        ]

    @disnake.ui.button(emoji="🏠", style=disnake.ButtonStyle.secondary, row=3)
    async def home_button(self, button: disnake.Button, inter: disnake.MessageInteraction):
        formatter = HelpPageSource(pages)
        menu = HelpPaginator(formatter, message=inter.message)

        await menu.start(inter)
        await inter.response.defer()

    @disnake.ui.select(placeholder="Select a sub-command", row=1)
    async def sub_command_selector(self, select_menu: disnake.SelectMenu, inter: disnake.MessageInteraction):
        sub_command_name = inter.values[0]
        sub_command = inter.bot.get_slash_command(sub_command_name)

        await inter.response.defer()

        if not sub_command:
            return

        embed = (
            disnake.Embed(
                title=sub_command.qualified_name.title(),
                description="`<>` means that the argument is required.\n`[]` means that the argument is optional.",
                color=colors.embed_color,
                timestamp=datetime.datetime.utcnow(),
            )
            .add_field(
                name="Usage",
                value=f"`{get_slash_command_signature(sub_command, options=sub_command.option.options)}`",
                inline=False,
            )
            .add_field(name="Description", value=sub_command.description or "N/A", inline=False)
            .set_footer(
                text=f"Requested by {inter.author}",
                icon_url=inter.author.avatar or config.DEFAULT_AVATAR_URL,
            )
        )

        if len(sub_command.option.options) > 0:
            embed.add_field(
                name="Parameters",
                value="\n".join(
                    f"`{parameter.name}`: {parameter.description}" for parameter in sub_command.option.options
                ),
                inline=False,
            )

        await inter.edit_original_message(embed=embed)


## -- COG -- ##


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.commands = [slash_command.qualified_name for slash_command in bot.slash_commands]

    ## -- SLASH COMMANDS -- ##

    @commands.slash_command(name="help")
    async def help(self, inter: disnake.ApplicationCommandInteraction):
        """Lost? Check out this command!"""
        pass

    @help.sub_command(name="menu")
    async def help_menu(self, inter: disnake.ApplicationCommandInteraction):
        """Open up the interactive help menu."""

        formatter = HelpPageSource(pages)
        menu = HelpPaginator(formatter)

        await menu.start(inter)

    @help.sub_command(name="command")
    async def help_command(self, inter: disnake.ApplicationCommandInteraction, command: str):
        """Get information about a specific command.
        Parameters
        ----------
        command: The command you want information on.
        """

        command_obj = self.bot.get_slash_command(command)

        if not command_obj:
            return await inter.send(
                embed=disnake.Embed(
                    description=f"{no} There's no command called `{command}`.",
                    color=colors.error_embed_color,
                ),
                ephemeral=True,
            )

        sub_commands = getattr(command_obj, "children")

        if sub_commands and len(sub_commands) > 0:
            return await inter.send(
                embed=disnake.Embed(
                    title=command_obj.qualified_name.title(),
                    description="This is a command group, meaning you can only run its sub-commands.",
                    color=colors.embed_color,
                    timestamp=datetime.datetime.utcnow(),
                )
                .add_field(
                    name="Sub Commands",
                    value=", ".join([f"`{sub_command.qualified_name}`" for sub_command in sub_commands.values()]),
                )
                .set_footer(
                    text=f"Requested by {inter.author}",
                    icon_url=inter.author.avatar or config.DEFAULT_AVATAR_URL,
                ),
                view=CommandHelpView(has_sub_commands=True, sub_commands=sub_commands),
            )

        embed = (
            disnake.Embed(
                title=command_obj.qualified_name.title(),
                description="`<>` means that the argument is required.\n`[]` means that the argument is optional.",
                color=colors.embed_color,
                timestamp=datetime.datetime.utcnow(),
            )
            .add_field(
                name="Usage",
                value=f"`{get_slash_command_signature(command_obj)}`",
                inline=False,
            )
            .add_field(name="Description", value=command_obj.description or "N/A", inline=False)
            .set_footer(
                text=f"Requested by {inter.author}",
                icon_url=inter.author.avatar or config.DEFAULT_AVATAR_URL,
            )
        )

        if len(command_obj.options) > 0:
            embed.add_field(
                name="Parameters",
                value="\n".join(f"`{parameter.name}`: {parameter.description}" for parameter in command_obj.options),
                inline=False,
            )

        await inter.send(
            embed=embed,
            view=CommandHelpView(has_sub_commands=False),
        )

    @help_command.autocomplete("command")
    async def command_autocomplete(self, inter: disnake.ApplicationCommandInteraction, input: str):
        return [command for command in self.commands if input.lower() in command.lower()][:25]


def setup(bot):
    bot.add_cog(Help(bot))
