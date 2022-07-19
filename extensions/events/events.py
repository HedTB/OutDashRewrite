## -- IMPORTING	-- ##

# MODULES
import asyncio
import datetime
import re
import time
import logging
import random
import disnake
import os
import requests
import json

from disnake.ext import commands
from dotenv import load_dotenv

# FILES
from utils import config, functions, colors
from utils.classes import *
from utils.emojis import *

from .. import leveling
from . import errors

## -- VARIABLES	-- ##

load_dotenv()

rapid_api_key = os.environ.get("RAPID_API_KEY")
randomstuff_key = os.environ.get("RANDOMSTUFF_KEY")

logger = logging.getLogger("OutDash")

ignored = (
    commands.CommandNotFound,
    commands.MissingPermissions,
    disnake.errors.Forbidden,
    disnake.errors.HTTPException,
    commands.MissingRequiredArgument,
)

## -- FUNCTIONS	-- ##


def get_variables(member: disnake.Member, guild: disnake.Guild):
    return {
        # member variables
        "{member_username}": str(member),
        "{member_name}": member.name,
        "{member_discriminator}": member.discriminator,
        "{member_mention}":	member.mention,
        "{member_avatar}": str(member.avatar) or config.DEFAULT_AVATAR_URL,
        # guild	variables
        "{guild_name}":	guild.name,
        "{guild_icon}":	str(guild.icon) or config.DEFAULT_AVATAR_URL,
        "{guild_member_count}":	guild.member_count,
    }


def format_variables(string: str, original_variables: dict):
    variables = {}
    result = re.findall(r"{(\w+)}",	string)

    for value in result:
        variables.update({value: original_variables["{" + value + "}"]})

    return str.format(string, **variables)


def insert_variables(message: dict | str, **kwargs):
    ctx: commands.Context = kwargs.get("ctx")
    member:	disnake.Member = kwargs.get("member")
    variables: dict = kwargs.get("variables", None)

    if not member and not ctx:
        return None

    try:
        guild = ctx.guild
        member = ctx.author
    except AttributeError:
        guild = member.guild

    variables = variables or get_variables(member, guild)

    if isinstance(message, dict):
        to_pop = {}

        for key in message:
            value = message[key]

            if isinstance(value, dict):
                message[key] = insert_variables(value, **kwargs)
                continue

            elif isinstance(value, str):
                message[key] = format_variables(value, variables)
                continue

    elif isinstance(message, str):
        message = format_variables(message,	variables)

    # to_pop = {}
    # for key in embed:
    #	  value	= embed[key]

    #	  if isinstance(value, dict):
    #		  for key2 in value:
    #			  value2 = value[key2]

    #			  if value2	== None:
    #				  to_pop[key] =	[]
    #				  to_pop[key].append(key2)
    #				  continue
    #			  elif type(value2)	!= str:
    #				  continue

    #			  embed[key][key2] = format_variables(value2, variables)
    #		  continue

    #	  elif value == None:
    #		  to_pop["all"]	= []
    #		  to_pop["all"].append(key)
    #		  continue
    #	  elif type(value) != str:
    #		  continue

    #	  embed[key] = format_variables(value, variables)

    # for key in to_pop:
    #	  value	= to_pop[key]

    #	  for key2 in value:
    #		  if key == "all":
    #			  embed.pop(key2)
    #		  else:
    #			  embed[key].pop(key2)

    return message


## -- COG -- ##


class Events(commands.Cog):
    def __init__(self, bot:	commands.Bot):
        self.bot = bot

    ## -- COMMANDS -- ##

    @commands.Cog.listener()
    async def on_command(self, ctx):
        with open("data/stats.json", "r") as file:
            data = json.load(file)

        commands_run = data.get("commands_run")
        data["commands_run"] = commands_run + 1 if commands_run != None else 1

        with open("data/stats.json", "w") as file:
            json.dump(data,	file)

    @commands.Cog.listener()
    async def on_slash_command(self, inter):
        with open("data/stats.json", "r") as file:
            data = json.load(file)

        commands_run = data.get("commands_run")
        data["commands_run"] = commands_run + 1 if commands_run != None else 1

        with open("data/stats.json", "w") as file:
            json.dump(data,	file)

    ## -- ERRORS -- ##

    @commands.Cog.listener()
    async def on_slash_command_error(
        self, inter: disnake.ApplicationCommandInteraction,	error
    ):
        channel = self.bot.get_channel(config.ERROR_CHANNEL)

        if isinstance(error, ignored):
            return

        elif isinstance(error, commands.CommandInvokeError):
            embed = disnake.Embed(
                title="Slash Command Error",
                description=f"```py\n{error}\n```\n_ _",
                color=colors.error_embed_color,
            )
            error_embed = disnake.Embed(
                description=f"{no} Oh no! Something	went wrong while running the command! Please join our [support server](https://discord.com/invite/4pfUqEufUm) and report the bug.",
                color=colors.error_embed_color,
            )

            embed.add_field(
                name="Occured in:",
                value=f"{inter.guild.name} ({inter.guild.id})",
                inline=False,
            )
            embed.add_field(
                name="Occured by:",
                value=f"{inter.author.name}	({inter.author.id})",
                inline=False,
            )
            embed.add_field(
                name="Command run:", value=f"/{inter.data.name}", inline=False
            )

            logging.error(error)
            await channel.send(embed=embed)

            try:
                await inter.response.send_message(embed=error_embed, ephemeral=True)
            except:
                await inter.channel.send(embed=error_embed)

    @commands.Cog.listener()
    async def on_command_error(
        self, ctx: commands.Context, error:	commands.CommandError
    ):
        channel = self.bot.get_channel(config.ERROR_CHANNEL)

        if isinstance(error, ignored) or str(error).find("Missing Permissions"):
            return

        elif isinstance(error, commands.CommandOnCooldown):
            embed = disnake.Embed(
                description=f"{no} You're on a cooldown. Please	try	again after	**{str(round(error.retry_after,	1))} seconds.**",
                color=colors.error_embed_color,
            )
            await ctx.send(embed=embed)

        elif isinstance(error, commands.CommandInvokeError):
            embed = disnake.Embed(
                title="Command Error",
                description=f"```py\n{error}\n```\n_	_",
                color=colors.error_embed_color,
            )
            error_embed = disnake.Embed(
                description=f"{no} Oh no! Something	went wrong while running the command! Please join our [support server](https://discord.com/invite/4pfUqEufUm) and report the bug.",
                color=colors.error_embed_color,
            )

            embed.add_field(
                name="Occured in:",
                value=f"{ctx.guild.name} ({ctx.guild.id})",
                inline=False,
            )
            embed.add_field(
                name="Occured by:",
                value=f"{ctx.author.name} ({ctx.author.id})",
                inline=False,
            )
            embed.add_field(
                name="Command run:", value=f"{ctx.message.content}", inline=False
            )

            logging.error(error)

            await channel.send(embed=embed)
            await ctx.send(embed=error_embed)

    ## -- MESSAGES -- ##

    @commands.Cog.listener()
    async def on_message(self, message:	disnake.Message):
        if message.author == self.bot.user or message.author.bot or not message.guild:
            return

        data_obj = GuildData(message.guild)
        guild_data = data_obj.get_data()

        if message.id in self.bot.moderated_messages:
            return

        if (
            message.content == f"<@{self.bot.user.id}>"
            or message.content == f"<@!{self.bot.user.id}>"
        ):
            prefix = guild_data.get("prefix")
            embed = disnake.Embed(
                description=f"{info} The prefix	for	this server	is `{prefix}`.",
                color=colors.embed_color,
            )

            try:
                await message.channel.send(embed=embed)
            except disnake.errors.Forbidden as error:
                await errors.Errors.handle_bot_missing_perms(
                    self=errors.Errors,
                    ctx=commands.Context(
                        message=message, bot=self.bot, view=None),
                    error=error,
                )

    @commands.Cog.listener("on_message")
    async def chatbot_responder(self, message: disnake.Message):
        if message.author == self.bot.user or message.author.bot or not message.guild:
            return

        data_obj = GuildData(message.guild)
        guild_data = data_obj.get_data()

        if message.id in self.bot.moderated_messages:
            return

        chat_bot_channel = guild_data.get("chat_bot_channel")

        if chat_bot_channel and message.content:
            channel = self.bot.get_channel(int(chat_bot_channel))

            if message.content.startswith(guild_data.get("prefix")):
                return
            elif not channel or message.channel != channel:
                return

            embed = disnake.Embed(
                description=f"{no} The API we're using to fetch	responses is currently down. Please	try	again later.",
                color=colors.error_embed_color,
                timestamp=datetime.datetime.utcnow(),
            )

            embed.set_footer(
                text=f"Requested by {message.author}",
                icon_url=message.author.avatar or config.DEFAULT_AVATAR_URL,
            )
            #await message.channel.send(embed=embed)

            #return

            try:
                response = requests.get(
                    url="https://random-stuff-api.p.rapidapi.com/ai",
                    headers={
                        "authorization": randomstuff_key,
                        "x-rapidapi-host": "random-stuff-api.p.rapidapi.com",
                        "x-rapidapi-key": rapid_api_key,
                    },
                    params={
                        "msg": message.content,
                        "bot_name":	"OutDash",
                        "bot_gender": "male",
                        "bot_master": "HedTB",
                        "bot_location":	"Sweden",
                        "bot_birth_year": "2021",
                        "bot_birth_place": "Sweden",
                        "bot_favorite_color": "Blue",
                        "id": str(message.author.id),
                    },
                ).json()

                print(response)

                await message.reply(response.get("AIResponse"))
            except Exception as error:
                logging.warn(
                    "Error occurred	while getting/sending chatbot response | "
                    + str(error)
                )
                pass

    @commands.Cog.listener("on_message")
    async def award_xp(self, message: disnake.Message):
        if message.author.bot:
            return

        data_obj = GuildData(message.guild)
        data = data_obj.get_data()

        if message.id in self.bot.moderated_messages:
            return
        elif not data["leveling_toggle"]:
            return
        elif message.content.startswith(data["prefix"]):
            return

        try:
            last_xp_award = self.bot.leveling_awards[message.guild.id][
                message.author.id
            ]
        except:
            last_xp_award = None

        if (
            not last_xp_award
            or last_xp_award
            and time.time() - last_xp_award["awarded_at"]
            > last_xp_award["COOLDOWN_TIME"]
        ):
            xp_amount = random.randint(17, 27)

            result,	potential_level = leveling.add_xp(
                message.author,	xp_amount if config.IS_SERVER else xp_amount * 5
            )
            if result == "level_up":
                try:
                    member_data_obj = MemberData(message.author)
                    member_data = member_data_obj.get_guild_data()

                    variables = get_variables(message.author, message.guild)
                    variables.update(
                        {
                            "{new_level}": potential_level,
                            "{previous_level}":	potential_level - 1,
                            "{new_xp}":	member_data["xp"],
                            "{previous_xp}": member_data["xp"] - xp_amount,
                            "{total_xp}": member_data["total_xp"],
                        }
                    )

                    levelup_message = insert_variables(
                        data["leveling_message"]["content"],
                        variables=variables,
                        member=message.author,
                    )

                    await message.channel.send(
                        levelup_message,
                        delete_after=data["leveling_message"]["delete_after"],
                    )

                except Exception as error:
                    if isinstance(error, commands.MissingPermissions):
                        return

                    logger.warn(
                        "Failed	sending	levelup	message	| " + str(error))

            if not self.bot.leveling_awards.get(message.guild.id):
                self.bot.leveling_awards[message.guild.id] = {}

            self.bot.leveling_awards[message.guild.id][message.author.id] = {
                "awarded_at": time.time(),
                "COOLDOWN_TIME": 1 if not config.IS_SERVER else random.randint(55, 65),
            }

    @commands.Cog.listener("on_message_delete")
    async def snipe_logging(self, message: disnake.Message):
        if not message.guild:
            return
        if message.stickers:
            message.content += f"\n*Sticker* -  {message.stickers[0].name}"

        self.bot.snipes[message.channel.id] = {
            "message": message.content,
            "deleted_at": datetime.datetime.utcnow(),
            "author": message.author.id,
            "nsfw":	message.channel.is_nsfw(),
        }

    ## -- GUILDS -- ##

    @commands.Cog.listener()
    async def on_guild_join(self, guild: disnake.Guild):
        data_obj = GuildData(guild)
        data_obj.get_data()

        embed = disnake.Embed(
            title="New Server",
            description=f"OutDash was added	to a new server!\n\nWe're now in `{len(self.bot.guilds)}` guilds.",
            color=colors.logs_add_embed_color,
        )

        embed.add_field(name="Server Name",	value=f"`{guild.name}`")
        embed.add_field(name="Server ID", value=f"`{guild.id}`")
        embed.add_field(
            name="Server Members",
            value=f"`{len(guild.members)}` total members",
            inline=False,
        )

        embed.set_thumbnail(url=guild.icon.url)
        embed.timestamp = datetime.datetime.utcnow()

        await self.bot.get_channel(config.MESSAGES_CHANNEL).send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_remove(self,	guild: disnake.Guild):
        embed = disnake.Embed(
            title="Server Left",
            description=f"OutDash was removed from	a server..\n\nWe're	now	in `{len(self.bot.guilds)}`	guilds.",
            color=colors.logs_delete_embed_color,
        )

        embed.add_field(name="Server Name",	value=f"`{guild.name}`")
        embed.add_field(name="Server ID", value=f"`{guild.id}`")

        embed.set_thumbnail(url=guild.icon.url)
        embed.timestamp = datetime.datetime.utcnow()

        await self.bot.get_channel(config.MESSAGES_CHANNEL).send(embed=embed)

    ## -- MEMBERS -- ##

    @commands.Cog.listener("on_member_join")
    async def insert_member_data(self, member: disnake.Member):
        member_data_obj = MemberData(member)

        member_data_obj.get_data()
        member_data_obj.get_guild_data()

    @commands.Cog.listener("on_welcome_member")
    async def welcome_member(self, member: disnake.Member, **kwargs):
        guild = member.guild

        data_obj = GuildData(guild)
        data = data_obj.get_data()

        toggle = data["welcome_toggle"]
        channel = data["welcome_channel"]

        data["welcome_message"] = insert_variables(
            data["welcome_message"], member=member
        )

        message = data["welcome_message"]
        content = message["content"]

        embed = message["embed"]
        if embed["timestamp"]:
            embed["timestamp"] = str(datetime.datetime.utcnow())

        if toggle == True and not channel:
            return data_obj.update_data({"welcome_toggle": False})
        elif not toggle:
            return

        channel = kwargs.get("channel") or self.bot.get_channel(channel)
        if not channel:
            return data_obj.update_data(
                {"welcome_toggle": False, "welcome_channel": None}
            )

        message_embed = disnake.Embed().from_dict(embed)
        await channel.send(content=content,	embed=message_embed)

    ## -- VOICE	CHANNELS -- ##

    @commands.Cog.listener("on_voice_state_update")
    async def leave_voice_channel(
        self,
        member:	disnake.Member,
        before:	disnake.VoiceState,
        after: disnake.VoiceState,
    ):
        voice_client = member.guild.voice_client
        humans = []

        if (
            not voice_client
            or after.channel != None
            or before.channel != voice_client.channel
        ):
            return

        if voice_client and voice_client.is_connected():
            await asyncio.sleep(10)

            for member in voice_client.channel.members:
                if not member.bot:
                    humans.append(member)

            if len(humans) < 1:
                await voice_client.disconnect()


def setup(bot):
    bot.add_cog(Events(bot))
