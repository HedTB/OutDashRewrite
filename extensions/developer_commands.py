## -- IMPORTING -- ##

# MODULES
import disnake
import os
import random
import asyncio
import datetime
import certifi
import string

from disnake.ext import commands
from disnake.errors import Forbidden, HTTPException
from disnake.ext.commands import errors
from pymongo import MongoClient
from dotenv import load_dotenv

# FILES
from utils import config, functions, colors

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
        code = inter.text_values.get("code-text-input")
        code_to_run = code[code.find("```py") + len("```py") : code.rfind("```")]

        if not code_to_run:
            return await inter.send(
                embed=disnake.Embed(
                    description=f"{no} There's no code I can run!",
                    color=colors.error_embed_color,
                ),
                ephemeral=True,
            )

        await inter.send("Executing code..", ephemeral=True)
        await aexec(
            code_to_run,
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

    @commands.slash_command(name="execute", auto_sync=False, guild_ids=[config.BOT_SERVER])
    async def execute(self, inter: disnake.ApplicationCommandInteraction):
        if inter.author.id not in config.OWNERS:
            return await inter.send(
                embed=disnake.Embed(
                    description=f"{no} You can't run this command!",
                    color=colors.error_embed_color,
                )
            )

        await inter.response.send_modal(CodeInput())

    # @commands.slash_command()
    # async def generatecaptcha(self, inter: disnake.ApplicationCommandInteraction):
    #     if inter.author.id not in config.OWNERS:
    #         return

    #     captcha = functions.generate_captcha()

    #     await inter.send(file=disnake.File(f"{captcha}.png"))
    #     os.remove(f"{captcha}.png")

    #     def check(message2):
    #         return message2.author == inter.message.author and message2.content.upper() == captcha

    #     try:
    #         await self.bot.wait_for("message", timeout=15.0, check=check)
    #     except asyncio.TimeoutError:
    #         await inter.send(f"{no} the captcha was: `" + captcha + "`")
    #     else:
    #         await inter.send(yes)

    # @commands.slash_command()
    # async def getguilddata(self, inter: disnake.ApplicationCommandInteraction, guild_id: int = 836495137651294258):
    #     if inter.author.id not in config.OWNERS:
    #         return

    #     guild = self.bot.get_guild(guild_id)
    #     embed = disnake.Embed(title=guild.name, description="")

    #     embed.set_thumbnail(guild.icon or config.DEFAULT_AVATAR_URL)
    #     embed.add_field("Member Count", len(guild.members))

    #     await inter.send(embed=embed)

    # @commands.slash_command()
    # async def getbotguilds(self, inter: disnake.ApplicationCommandInteraction):
    #     if inter.author.id not in config.OWNERS:
    #         return

    #     guilds = self.bot.guilds
    #     message = ""

    #     for guild in guilds:
    #         message += f"**{guild.name}**\n`{guild.id}`\n\n"

    #     await inter.send(message)


def setup(bot):
    bot.add_cog(DeveloperCommands(bot))
