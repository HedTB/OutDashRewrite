## -- IMPORTING -- ##

# MODULES
import disnake
import os
import random
import asyncio
import datetime
import certifi

from disnake.ext import commands, menus
from disnake.ext import menus
from disnake import ui
from disnake.errors import Forbidden, HTTPException
from disnake.ext.commands import errors
from pymongo import MongoClient
from itertools import starmap, chain

# FILES
import config

class HelpPageSource(menus.ListPageSource):
    def __init__(self, data, helpcommand):
        super().__init__(data, per_page=2)
        self.helpcommand = helpcommand

    def format_command_help(self, no, command: commands.Command):
        signature = self.helpcommand.get_command_signature(command)
        docs = self.helpcommand.get_command_brief(command)
        if docs == "DontShow":
            return None
        return f"**{signature}**\n{docs}"
    
    async def format_page(self, menu, entries):
        page = menu.current_page
        max_page = self.get_max_pages()
        starting_number = page * self.per_page + 1
        iterator = starmap(self.format_command_help, enumerate(entries, start=starting_number))
        page_content = "\n".join(iterator)
        embed = disnake.Embed(
            title=f"Help Command [{page + 1}/{max_page}]", 
            description=page_content,
            color=config.embed_color
        )
        author = menu.ctx.author
        embed.set_footer(text=f"Requested by {author}", icon_url=author.avatar or "https://cdn.discordapp.com/embed/avatars/1.png")
        return embed

class MyMenuPages(ui.View, menus.MenuPages):
    def __init__(self, source, *, delete_message_after=False):
        super().__init__(timeout=60)
        self._source = source
        self.current_page = 0
        self.ctx = None
        self.message = None
        self.delete_message_after = delete_message_after

    async def start(self, ctx, *, channel=None, wait=False):
        await self._source._prepare_once()
        self.ctx = ctx
        self.message = await self.send_initial_message(ctx, ctx.channel)

    async def _get_kwargs_from_page(self, page):
        """This method calls ListPageSource.format_page class"""
        value = await super()._get_kwargs_from_page(page)
        if 'view' not in value:
            value.update({'view': self})
        return value

    async def interaction_check(self, interaction):
        """Only allow the author that invoke the command to be able to use the interaction"""
        return interaction.user == self.ctx.author

    @ui.button(emoji='⏪', style=disnake.ButtonStyle.gray)
    async def first_page(self, button, interaction):
        await self.show_page(0)
        await interaction.response.defer()

    @ui.button(emoji='◀️', style=disnake.ButtonStyle.gray)
    async def before_page(self, button, interaction):
        await self.show_checked_page(self.current_page - 1)
        await interaction.response.defer()

    @ui.button(emoji='❌', style=disnake.ButtonStyle.gray)
    async def stop_page(self, button, interaction):
        self.stop()
        if self.delete_message_after:
            await self.message.delete(delay=0)

    @ui.button(emoji='▶️', style=disnake.ButtonStyle.gray)
    async def next_page(self, button, interaction):
        await self.show_checked_page(self.current_page + 1)
        await interaction.response.defer()

    @ui.button(emoji='⏩', style=disnake.ButtonStyle.gray)
    async def last_page(self, button, interaction):
        await self.show_page(self._source.get_max_pages() - 1)
        await interaction.response.defer()
    
class Help(commands.HelpCommand):
    def get_command_brief(self, command):
        return "Shows this message." if command.short_doc == "Shows this message" else command.short_doc or "Command is not documented."
    
    async def send_bot_help(self, mapping):
        all_commands = list(chain.from_iterable(mapping.values()))
        for i in all_commands:
            if i.name in config.hidden_commands:
                all_commands.remove(i)
            
        formatter = HelpPageSource(all_commands, self)
        menu = MyMenuPages(formatter, delete_message_after=True)
        await menu.start(self.context)
        
    async def on_help_command_error(self, ctx, error):
        print(error)
        if isinstance(error, commands.BadArgument):
            embed = disnake.Embed(title="Error", description=f"{config.yes} {str(error)}")
            await ctx.send(embed=embed)
        else:
            raise error

class HelpCog(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        help_command = Help()
        help_command.cog = self
        bot.help_command = help_command
        
    @commands.slash_command(name="help", description="Lost? Use this command!")
    async def slash_help(self, inter: disnake.ApplicationCommandInteraction):
        await self.bot.help_command.send_bot_help()

def setup(bot):
    bot.add_cog(HelpCog(bot))