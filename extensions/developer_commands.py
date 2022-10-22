## -- IMPORTING -- ##

# MODULES
import disnake
import os
import asyncio

from disnake.ext import commands
from dotenv import load_dotenv

# FILES
from utils import config, functions, colors, enums, converters

from utils.checks import *
from utils.emojis import *

## -- VARIABLES -- ##

load_dotenv()

## -- FUNCTIONS -- ##


async def aexec(code, global_variables, **kwargs):
    locs = {}

    globs = globals().copy()
    args = ", ".join(list(kwargs.keys()))

    exec(
        f"async def func({args}):\n    " + code.replace("\n", "\n    "),
        global_variables,
        locs,
    )

    result = await locs["func"](**kwargs)

    try:
        globals().clear()
    finally:
        globals().update(**globs)

    return result


## -- COG -- ##


class CodeInput(disnake.ui.Modal):
    def __init__(self) -> None:
        super().__init__(
            title="Input Code",
            components=[
                disnake.ui.TextInput(
                    label="Code",
                    placeholder="Input the code you want to execute",
                    custom_id="code-text-input",
                    style=disnake.TextInputStyle.paragraph,
                    min_length=10,
                )
            ],
            custom_id="input-code-modal",
            timeout=600,
        )

    async def callback(self, inter: disnake.ModalInteraction, /) -> None:
        await inter.send("Executing code..", ephemeral=True)

        await aexec(
            inter.text_values.get("code-text-input"),
            {
                "inter": inter,
                "bot": inter.bot,
            },
        )

        await inter.edit_original_message("Code executed successfully!")


class DeveloperCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    ## -- COMMANDS -- ##

    @commands.slash_command(
        name="format_time",
        auto_sync=False,
        guild_ids=[config.BOT_SERVER],
        default_member_permissions=disnake.Permissions.advanced(),
    )
    async def convert_time(
        self,
        inter: disnake.ApplicationCommandInteraction,
        time: str = commands.Param("0s", converter=converters.convert_time),
    ):
        await inter.send(f"Formatted time: `{time}`")

    @commands.slash_command(
        name="execute",
        auto_sync=False,
        guild_ids=[config.BOT_SERVER],
        default_member_permissions=disnake.Permissions.advanced(),
    )
    async def execute(self, inter: disnake.ApplicationCommandInteraction):
        if inter.author.id not in config.OWNERS:
            return await inter.send(
                embed=disnake.Embed(
                    description=f"{no} You don't have permission to run this command.",
                    color=colors.error_embed_color,
                ),
                ephemeral=True,
            )

        await inter.response.send_modal(CodeInput())

    @commands.slash_command(
        name="generate_captcha",
        auto_sync=False,
        guild_ids=[config.BOT_SERVER],
        default_member_permissions=disnake.Permissions.advanced(),
    )
    async def generate_captcha(self, inter: disnake.ApplicationCommandInteraction):
        if inter.author.id not in config.OWNERS:
            return await inter.send(
                embed=disnake.Embed(
                    description=f"{no} You don't have permission to run this command.",
                    color=colors.error_embed_color,
                ),
                ephemeral=True,
            )

        captcha = functions.generate_captcha()

        await inter.send(file=disnake.File(f"{captcha}.png"), ephemeral=True)
        os.remove(f"{captcha}.png")

        try:
            message = await self.bot.wait_for(
                "message",
                timeout=15.0,
                check=lambda message: message.author == inter.author
                and message.channel == inter.channel
                and message.content.upper() == captcha,
            )

            try:
                await message.delete()
            except:
                pass
        except asyncio.TimeoutError:
            await inter.edit_original_message(f"{no} the captcha was: `" + captcha + "`")
        else:
            await inter.edit_original_message(yes)

    @commands.slash_command(
        name="get_guild_data",
        auto_sync=False,
        guild_ids=[config.BOT_SERVER],
        default_member_permissions=disnake.Permissions.advanced(),
    )
    async def get_guild_data(self, inter: disnake.ApplicationCommandInteraction, guild_id: float = config.BOT_SERVER):
        if inter.author.id not in config.OWNERS:
            return await inter.send(
                embed=disnake.Embed(
                    description=f"{no} You don't have permission to run this command.",
                    color=colors.error_embed_color,
                ),
                ephemeral=True,
            )

        guild = self.bot.get_guild(guild_id)
        embed = disnake.Embed(title=guild.name, description="")

        embed.set_thumbnail(guild.icon or config.DEFAULT_AVATAR_URL)
        embed.add_field("Member Count", len(guild.members))

        await inter.send(embed=embed, ephemeral=True)

    @commands.slash_command(
        name="get_bot_guilds",
        auto_sync=False,
        guild_ids=[config.BOT_SERVER],
        default_member_permissions=disnake.Permissions.advanced(),
    )
    async def get_bot_guilds(self, inter: disnake.ApplicationCommandInteraction):
        if inter.author.id not in config.OWNERS:
            return await inter.send(
                embed=disnake.Embed(
                    description=f"{no} You don't have permission to run this command.",
                    color=colors.error_embed_color,
                ),
                ephemeral=True,
            )

        guilds = self.bot.guilds
        message = ""

        for guild in guilds:
            message += f"**{guild.name}**\n`{guild.id}`\n\n"

        await inter.send(message, ephemeral=True)


def setup(bot):
    bot.add_cog(DeveloperCommands(bot))
