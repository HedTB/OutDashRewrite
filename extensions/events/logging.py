## -- IMPORTING -- ##

# MODULES
import disnake
import os
import datetime
import certifi

from disnake.ext import commands
from pymongo import MongoClient
# from googleapiclient import discovery
from dotenv import load_dotenv

# FILES
from utils import config
from utils import functions
from utils.checks import *
from utils.webhooks import *
from utils.classes import *

## -- VARIABLES -- ##

load_dotenv()

mongo_login = os.environ.get("MONGO_LOGIN")
rapid_api_key = os.environ.get("RAPID_API_KEY")
google_api_key = os.environ.get("GOOGLE_API_KEY")
randomstuff_key = os.environ.get("RANDOMSTUFF_KEY")

client = MongoClient(mongo_login, tlsCAFile=certifi.where())
db = client["db2"]


"""
perspective_client = discovery.build(
    "commentanalyzer",
    "v1alpha1",
    developerKey=google_api_key,
    discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
    static_discovery=False,
)
"""

guild_data_col = db["guild_data"]
user_data_col = db["user_data"]
privacy_settings_col = db["privacy_settings"]

## -- FUNCTIONS -- ##

def get_response_score(response, attribute: str):
    attribute = attribute.upper()
    attribute_scores = response["attributeScores"]

    if attribute_scores[attribute]:
        return round(attribute_scores[attribute]["summaryScore"]["value"], 3)
    else:
        return None


## -- COG -- ##

class LoggingEvents(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    ## -- MESSAGES -- ##
    
    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages: list[disnake.Message]):
        try:
            webhook = LoggingWebhook(self.bot.user.avatar, messages[0].guild, "message_bulk_delete")
        except InvalidWebhook:
            return
        
        embed = disnake.Embed(description=f"**Bulk delete in <#{messages[0].channel.id}>, {len(messages)} messages deleted**", color=config.logs_embed_color)
        
        embed.set_author(name=messages[0].guild.name, icon_url=messages[0].guild.icon or config.default_avatar_url)
        embed.timestamp = datetime.datetime.utcnow()
        
        webhook.add_embed(embed)
        webhook.post()
        
    @commands.Cog.listener()
    async def on_message_edit(self, before: disnake.Message, after: disnake.Message):
        if before.content == after.content:
            return
        if before.author.bot or after.author.bot:
            return
        
        try:
            webhook = LoggingWebhook(self.bot.user.avatar, before.guild, "message_bulk_delete")
        except InvalidWebhook:
            return
        
        user_data_obj = UserData(before.author)
        
        user_data = user_data_obj.get_data() 
        message_content_privacy = user_data.get("message_content_privacy")
        
        before_text = before.content if len(before.content) < 1021 else f"{before.content[:1021]}..."
        if len(before.embeds) >= 1:
            before_text = f"{before_text}\n**[EMBED]**" if len(before.embeds) == 1 else f"{before_text}\n**[EMBEDS]**"
        after_text = after.content if len(after.content) < 1021 else f"{after.content[:1021]}..."
        if len(after.embeds) >= 1:
            after_text = f"{after_text}\n**[EMBED]**" if len(after.embeds) == 1 else f"{after_text}\n**[EMBEDS]**"
        
        if not before_text or not after_text:
            return

        if message_content_privacy != "true":
            embed = disnake.Embed(description=f"**Message edited in <#{before.channel.id}>**\n[Jump to message](https://discordapp.com/channels/{after.guild.id}/{after.channel.id}/{after.id})", color=config.logs_embed_color)
            embed.add_field(name="Before", value=before_text, inline=False)
            embed.add_field(name="After", value=after_text, inline=False)

            embed.set_author(name=f"{before.author.name}#{before.author.discriminator}", icon_url=before.author.avatar or config.default_avatar_url)
            embed.set_footer(text=f"Message ID: {before.id}")
            embed.timestamp = datetime.datetime.utcnow()
        else:
            embed = disnake.Embed(description=f"**Message edited in <#{before.channel.id}>** \n[Jump to message](https://discordapp.com/channels/{after.guild.id}/{after.channel.id}/{after.id})", color=config.logs_embed_color)
            embed.add_field(name="Notice", value="`This user has message content privacy enabled.`")
            
            embed.set_author(name=f"{before.author.name}#{before.author.discriminator}", icon_url=before.author.avatar or config.default_avatar_url)
            embed.set_footer(text=f"Message ID: {before.id}")
            embed.timestamp = datetime.datetime.utcnow()

        webhook.add_embed(embed)
        webhook.post()
        
    @commands.Cog.listener()
    async def on_message_delete(self, message: disnake.Message):
        if message.author.bot:
            return
        
        user_data_obj = UserData(message.author)
        user_data = user_data_obj.get_data()
        
        try:
            webhook = LoggingWebhook(self.bot.user.avatar, message.guild, "message_delete")
        except InvalidWebhook:
            return
            
        message_content_privacy = user_data["message_content_privacy"]
        message_text = message.content if len(message.content) < 2000 else f"{message.content[:2000]}..."
        
        if len(message.embeds) >= 1:
            message_text = f"{message_text}\n**[EMBED]**" if len(message.embeds) == 1 else f"{message_text}\n**[EMBEDS]**"
        if message_content_privacy == "true":
            message_text = "`This user has message content privacy enabled.`"

        embed = disnake.Embed(description=f"**Message deleted in {message.channel.mention}**"
                              f"\n{message_text}", color=config.logs_delete_embed_color)

        embed.set_author(name=f"{message.author.name}#{message.author.discriminator}", icon_url=message.author.avatar or config.default_avatar_url)
        embed.set_footer(text=f"Message ID: {message.id}")
        embed.timestamp = datetime.datetime.utcnow()

        webhook.add_embed(embed)
        webhook.post()
    
    ## -- MEMBERS -- ##
    
    @commands.Cog.listener()
    async def on_member_join(self, member: disnake.Member):
        try:
            webhook = LoggingWebhook(self.bot.user.avatar, member.guild, "member_join")
        except InvalidWebhook:
            return
        
        await self.bot.dispatch("welcome_member", member)
        embed = disnake.Embed(description="**Member joined**", color=config.logs_add_embed_color, timestamp=datetime.datetime.utcnow())
        
        created_ago_native = datetime.datetime.replace(member.created_at, tzinfo=None)
        created_ago = (datetime.datetime.now() - created_ago_native)
        created_seconds_ago = created_ago.total_seconds()
        
        embed.set_author(name=f"{member.name}#{member.discriminator}", icon_url=member.avatar or config.default_avatar_url)
        embed.add_field(name="Account Created", value=f"{functions.seconds_to_text(created_seconds_ago, 3)} ago", inline=False)
        
        webhook.add_embed(embed)
        webhook.post()
        
    @commands.Cog.listener()
    async def on_member_remove(self, member: disnake.Member):
        try:
            webhook = LoggingWebhook(self.bot.user.avatar, member.guild, "member_remove")
        except InvalidWebhook:
            return
        
        member_roles = []
        for role in member.roles:
            if role.name != "@everyone":
                member_roles.append(role.mention + " ")
                
        member_roles = "".join(member_roles)
        
        joined_at_native = datetime.datetime.replace(member.joined_at, tzinfo=None)
        joined_at = (datetime.datetime.now() - joined_at_native)
        joined_seconds_ago = joined_at.total_seconds()
        
        embed = disnake.Embed(description=f"**Member left**", color=config.logs_delete_embed_color, timestamp=datetime.datetime.utcnow())

        embed.add_field(name="Member Since", value=f"{functions.seconds_to_text(joined_seconds_ago, 3)} ago", inline=False)
        embed.add_field(name="Roles", value=str(member_roles), inline=False)
        embed.set_author(name=f"{member.name}#{member.discriminator}", icon_url=member.avatar or config.default_avatar_url)
        
        webhook.add_embed(embed)
        webhook.post()
        
    @commands.Cog.listener()
    async def on_member_update(self, before: disnake.Member, after: disnake.Member):
        try:
            webhook = LoggingWebhook(self.bot.user.avatar, before.guild, "member_update")
        except InvalidWebhook:
            return
        
        if before.nick != after.nick:
            embed = disnake.Embed(description="Nickname changed", color=config.logs_embed_color)
            
            embed.add_field("Before", disnake.utils.escape_markdown(before.nick if before.nick else before.name))
            embed.add_field("After", disnake.utils.escape_markdown(after.nick if after.nick else after.name))
            
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_author(name=str(before), icon_url=before.avatar.url)
        
        webhook.add_embed(embed)
        webhook.post()
        
        
        
    
    
def setup(bot):
    bot.add_cog(LoggingEvents(bot))