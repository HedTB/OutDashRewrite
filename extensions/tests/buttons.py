## -- IMPORTING -- ##

# MODULES
import typing
import disnake
import os
import certifi

from disnake.ext import commands
from pymongo import MongoClient
from dotenv import load_dotenv

# FILES
from utils import config, functions, colors

from utils.checks import *
from utils.data import *

## -- VARIABLES -- ##

load_dotenv()

## -- VIEWS -- ##


class Confirm(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=10)
        self.value = None

    def disable_view(self):
        for child in self.children:
            if isinstance(child, disnake.ui.Button):
                child.disabled = True

    @disnake.ui.button(label="Confirm", style=disnake.ButtonStyle.green)
    async def confirm(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        self.value = True
        self.disable_view()

        await interaction.edit_original_message("sus", view=self)
        await interaction.response.send_message("Confirmed!", ephemeral=True)

        # await interaction.message.edit(view=self)
        # await interaction.edit_original_message(view=self)
        self.stop()

    @disnake.ui.button(label="Cancel", style=disnake.ButtonStyle.red)
    async def cancel(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        await interaction.response.send_message("Cancelled!", ephemeral=True)

        self.value = True
        self.disable_view()

        await interaction.edit_original_message(view=self)
        self.stop()


## -- COG -- ##


class Buttons(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(name="ask", guild_ids=[config.BOT_SERVER])
    async def ask(self, ctx):
        view = Confirm()
        embed = disnake.Embed(
            description="Do you want to continue?", color=colors.logs_embed_color
        )

        await ctx.send(embed=embed, view=view, ephemeral=False)
        await view.wait()

        if not view.value:
            print("Timed out!")
        elif view.value:
            print("Confirmed!")
        else:
            print("Cancelled!")


def setup(bot):
    bot.add_cog(Buttons(bot))
