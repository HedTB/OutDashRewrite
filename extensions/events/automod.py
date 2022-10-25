## -- IMPORTING -- ##

# MODULES
import re
import disnake

from disnake.ext import commands
from dotenv import load_dotenv

# FILES
from utils import functions, colors
from utils.data import GuildData
from utils.emojis import moderator

## -- VARIABLES -- ##

load_dotenv()

automod_type_warnings = {
    "banned_words": "Watch your language, {}!",
    "all_caps": "Keep your caps down, {}!",
    "fast_spam": "Slow down, {}!",
    "text_flood": "Don't flood the chat, {}!",
}

## -- COG -- ##


class Automod(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    ## -- FUNCTIONS -- ##

    async def log_automod(self, ctx: commands.Context, automod_type: str) -> None:
        data_obj = GuildData(ctx.author.guild.id)
        data = data_obj.get_data()

        embed = disnake.Embed(
            description=moderator + " " + automod_type_warnings[automod_type].format(ctx.author.mention),
            color=colors.embed_color,
        )

        if ctx.author.id not in self.bot.automod_warnings:
            self.bot.automod_warnings[ctx.author.id] = []

        self.bot.automod_warnings[ctx.author.id].append(data)
        self.bot.moderated_messages.append(ctx.message.id)

        await ctx.message.delete()
        await ctx.send(
            content=f"{ctx.author.mention},",
            embed=embed,
            delete_after=7,
        )

        automod_warning_rules = data["automod_warning_rules"][automod_type]

        if len(self.bot.automod_warnings[ctx.author.id]) >= automod_warning_rules["warnings"]:
            action = automod_warning_rules["action"]

            if action == "mute":
                try:
                    await ctx.author.timeout(
                        duration=functions.manipulate_time(
                            time_str=automod_warning_rules["duration"],
                            return_type="seconds",
                        ),
                    )

                except disnake.errors.Forbidden:
                    pass

    ## -- AUTOMOD CHECKS -- ##

    async def banned_words(self, ctx: commands.Context, data: dict) -> bool:
        if ctx.message.id in self.bot.moderated_messages:
            return False
        elif not data["automod_toggle"]["banned_words"]:
            return False

        automod_filters = data["automod_settings"]["banned_words"]

        for word in ctx.message.content.split():
            if word in automod_filters["exact"]:
                await self.log_automod(ctx, "banned_words")
                return True

        if len(automod_filters["wildcard"]) < 1:
            return False

        search = re.match(
            pattern=r"^.*(?:{}).*$".format("|".join(automod_filters["wildcard"])),
            string=ctx.message.content,
            flags=re.IGNORECASE,
        )
        if bool(search):
            await self.log_automod(ctx, "banned_words")
            return True

    async def all_caps(self, ctx: commands.Context, data: dict) -> bool:
        if ctx.message.id in self.bot.moderated_messages:
            return
        elif not data["automod_toggle"]["all_caps"]:
            return

        caps_percentage = data["automod_settings"]["caps_percentage"]
        message_caps = 0

        for character in ctx.message.content:
            if character.isupper():
                message_caps += 1

        message_caps_percentage = message_caps / len(ctx.message.content) * 100
        print(message_caps_percentage)

    ## -- MAIN EVENT HANDLER -- ##

    @commands.Cog.listener("on_message")
    async def automod_trigger(self, message: disnake.Message):
        if message.author.bot:
            return

        ctx = commands.Context(message=message, bot=self.bot, view=None)

        data_obj = GuildData(ctx.guild.id)
        data = data_obj.get_data()

        if not data["automod_toggle"]["global"]:
            return

        await self.banned_words(ctx, data)
        await self.all_caps(ctx, data)

    @commands.Cog.listener("on_message_edit")
    async def automod_edit_trigger(self, _: disnake.Message, after: disnake.Message):
        await self.automod_trigger(after)

    ## -- SPAM FILTERS -- ##

    @commands.Cog.listener("on_message_spam")
    async def automod_message_spam(self, message: disnake.Message):
        ctx = commands.Context(message=message, bot=self.bot, view=None)

        data_obj = GuildData(ctx.guild.id)
        data = data_obj.get_data()

        if message.id in self.bot.moderated_messages:
            return
        elif not data["automod_toggle"]["global"] or not data["automod_toggle"]["fast_spam"]:
            return

    @commands.Cog.listener("on_message_flood")
    async def automod_flood(self, message: disnake.Message):
        ctx = commands.Context(message=message, bot=self.bot, view=None)

        data_obj = GuildData(ctx.guild.id)
        data = data_obj.get_data()

        if message.id in self.bot.moderated_messages:
            return
        elif not data["automod_toggle"]["global"] or not data["automod_toggle"]["text_flood"]:
            return

    @commands.Cog.listener("on_message")
    async def automod_caps(self, message: disnake.Message):
        ctx = commands.Context(message=message, bot=self.bot, view=None)

        data_obj = GuildData(ctx.guild.id)
        data = data_obj.get_data()


def setup(bot):
    bot.add_cog(Automod(bot))
