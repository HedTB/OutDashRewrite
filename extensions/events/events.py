## -- IMPORTING -- ##

# MODULES
import asyncio
import datetime
import functools
import logging
import random
import disnake
import os
import certifi
import requests
import json

from disnake.ext import commands
from pymongo import MongoClient
from dotenv import load_dotenv
from time import time

# FILES
from utils import config
from utils import functions
from utils.classes import *
from extensions import leveling

## -- VARIABLES -- ##

load_dotenv()

mongo_token = os.environ.get("MONGO_LOGIN")
rapid_api_key = os.environ.get("RAPID_API_KEY")
randomstuff_key = os.environ.get("RANDOMSTUFF_KEY")

logger = logging.getLogger("OutDash")

client = MongoClient(mongo_token, tlsCAFile=certifi.where())
db = client[config.database_collection]

server_data_col = db["server_data"]
user_data_col = db["user_data"]

ignored = (commands.CommandNotFound, commands.MissingPermissions, disnake.errors.Forbidden, disnake.errors.HTTPException, commands.MissingRequiredArgument, )

## -- FUNCTIONS -- ##

## -- COG -- ##

class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    ## -- COMMANDS -- ##
    
    @commands.Cog.listener()
    async def on_command(self, ctx):
        with open("data/stats.json", "r") as file_object:
            data = json.load(file_object)
        
        number = data.get("commands_run") or 0
        new_data = {"commands_run" : number + 1}

        with open("data/stats.json", 'w') as jsonfile:
            json.dump(new_data, jsonfile, indent=4)

    @commands.Cog.listener()
    async def on_slash_command(self, inter):
        with open("data/stats.json", "r") as file_object:
            data = json.load(file_object)
        
        number = data.get("commands_run") or 0
        new_data = {"commands_run" : number + 1}

        with open("data/stats.json", 'w') as jsonfile:
            json.dump(new_data, jsonfile, indent=4)
            
            
    @commands.Cog.listener()
    async def on_slash_command_error(self, inter: disnake.ApplicationCommandInteraction, error):
        channel = self.bot.get_channel(config.error_channel)
        
        if isinstance(error, ignored):
            return
            
        elif isinstance(error, commands.CommandInvokeError):
            embed = disnake.Embed(title="Slash Command Error", description=f"```py\n{error}\n```\n_ _", color=config.error_embed_color)
            error_embed = disnake.Embed(description=f"{config.no} Oh no! Something went wrong while running the command! Please join our [support server](https://discord.com/invite/4pfUqEufUm) and report the bug.", color=config.error_embed_color)
            
            embed.add_field(name="Occured in:", value=f"{inter.guild.name} ({inter.guild.id})", inline=False)
            embed.add_field(name="Occured by:", value=f"{inter.author.name} ({inter.author.id})", inline=False)
            embed.add_field(name="Command run:", value=f"/{inter.data.name}", inline=False)
            
            logging.error(error)
            await channel.send(embed=embed)
            
            try:
                await inter.response.send_message(embed=error_embed, ephemeral=True)
            except AttributeError:
                await inter.send(embed=error_embed)

    
    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        channel = self.bot.get_channel(config.error_channel)
        
        if isinstance(error, ignored) or str(error).find("Missing Permissions"):
            return
            
        elif isinstance(error, commands.CommandOnCooldown):
            embed = disnake.Embed(description=f"{config.no} You're on a cooldown. Please try again after **{str(round(error.retry_after, 1))} seconds.**", color=config.error_embed_color)
            await ctx.send(embed=embed)
            
        elif isinstance(error, commands.CommandInvokeError):
            embed = disnake.Embed(title="Command Error", description=f"```py\n{error}\n```\n_ _", color=config.error_embed_color)
            error_embed = disnake.Embed(description=f"{config.no} Oh no! Something went wrong while running the command! Please join our [support server](https://discord.com/invite/4pfUqEufUm) and report the bug.", color=config.error_embed_color)
            
            embed.add_field(name="Occured in:", value=f"{ctx.guild.name} ({ctx.guild.id})", inline=False)
            embed.add_field(name="Occured by:", value=f"{ctx.author.name} ({ctx.author.id})", inline=False)
            embed.add_field(name="Command run:", value=f"{ctx.message.content}", inline=False)
            
            logging.error(error)

            await channel.send(embed=embed)
            await ctx.send(embed=error_embed)
        
    ## -- MESSAGES -- ##
        
    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.author == self.bot.user or message.author.bot or not message.guild:
            return
        
        guild_data_obj = GuildData(message.guild)
        guild_data = guild_data_obj.get_data()
        
        await self.bot.process_commands(message)

        if message.content == f"<@{self.bot.user.id}>" or message.content == f"<@!{self.bot.user.id}>":
            prefix = guild_data.get("prefix")
            embed = disnake.Embed(description=f"{config.info} The prefix for this server is `{prefix}`.", color=config.embed_color)
            
            await message.channel.send(embed=embed)

            
    @commands.Cog.listener("on_message")
    async def chatbot_responder(self, message: disnake.Message):
        if message.author == self.bot.user or message.author.bot or not message.guild:
            return
        
        guild_data_obj = GuildData(message.guild)
        guild_data = guild_data_obj.get_data()
        
        chat_bot_channel = guild_data.get("chat_bot_channel")
        
        if chat_bot_channel and chat_bot_channel != "None" and message.content:
            channel = self.bot.get_channel(int(chat_bot_channel))
            
            if message.content.startswith(guild_data.get("prefix")):
                return
            elif not channel or message.channel != channel:
                return

            response = requests.get(
                url = "https://random-stuff-api.p.rapidapi.com/ai",
                headers = {
                    "authorization": randomstuff_key,
                    "x-rapidapi-host": "random-stuff-api.p.rapidapi.com",
                    "x-rapidapi-key": rapid_api_key
                },
                params = {
                    "msg": message.content, "bot_name": "OutDash", "bot_gender": "male", 
                    "bot_master": "HedTB", "bot_age": "1", "bot_location": "Sweden", 
                    "bot_birth_year": "2021", "bot_birth_place": "Sweden", "bot_favorite_color": "Blue", "id": str(message.author.id)
                }
            )

            try:
                await message.reply(response.json().get("AIResponse"))
            except Exception as error:
                logging.warn("Error occurred while getting/sending chatbot response | " + str(error))
                pass
            
        await self.bot.process_commands(message)
        
    @commands.Cog.listener("on_message")
    async def award_xp(self, message: disnake.Message):
        if message.author.bot:
            return
        
        last_xp_award = self.bot.leveling_awards.get(message.author.id)
        
        if not last_xp_award or last_xp_award and time() - last_xp_award["awarded_at"] > last_xp_award["cooldown_time"]:
            xp_amount = random.randint(17, 27)
            
            result, potential_level = leveling.add_xp(message.author, xp_amount)
            if result == "level_up":
                await message.channel.send(f"{message.author.mention} is now **level {potential_level}!** :tada:")

            self.bot.leveling_awards[message.author.id] = {
                "awarded_at": time(),
                "cooldown_time": random.randint(55, 65)
            }
            
        await self.bot.process_commands(message)
            
    @commands.Cog.listener("on_message_delete")
    async def snipe_logging(self, message: disnake.Message):
        if not message.guild:
            return
        if message.stickers:
            message.content += (f"\n*Sticker* - {message.stickers[0].name}")
        
        self.bot.snipes[message.channel.id] = {
            "message": message.content,
            "deleted_at": datetime.datetime.utcnow(),
            "author": message.author.id,
            "nsfw": message.channel.is_nsfw()
        }
            

    ## -- GUILDS -- ##

    @commands.Cog.listener()
    async def on_guild_join(self, guild: disnake.Guild):
        guild_data_obj = GuildData(guild)
        guild_data_obj.get_data()

        embed = disnake.Embed(title="New Server", description=f"OutDash was added to a new server!\n\nWe're now in `{len(self.bot.guilds)}` guilds.", color=config.logs_add_embed_color)
        
        embed.add_field(name="Server Name", value=f"`{guild.name}`")
        embed.add_field(name="Server ID", value=f"`{guild.id}`")
        embed.add_field(name="Server Members", value=f"`{len(guild.members)}` total members", inline=False)
        
        embed.set_thumbnail(url=guild.icon.url)
        embed.timestamp = datetime.datetime.utcnow()

        await self.bot.get_channel(config.messages_channel).send(embed=embed)
        
    @commands.Cog.listener()
    async def on_guild_remove(self, guild: disnake.Guild):
        embed = disnake.Embed(title="Server Left", description=f"OutDash was removed from a server..\n\nWe're now in `{len(self.bot.guilds)}` guilds.", color=config.logs_delete_embed_color)
        
        embed.add_field(name="Server Name", value=f"`{guild.name}`")
        embed.add_field(name="Server ID", value=f"`{guild.id}`")
        
        embed.set_thumbnail(url=guild.icon.url)
        embed.timestamp = datetime.datetime.utcnow()

        await self.bot.get_channel(config.messages_channel).send(embed=embed)
        
        
    ## -- MEMBERS -- ##
    
    @commands.Cog.listener("on_member_join")
    async def insert_member_data(self, member: disnake.Member):
        member_data_obj = MemberData(member)
        
        member_data_obj.get_data()
        member_data_obj.get_guild_data()


def setup(bot):
    bot.add_cog(Events(bot))