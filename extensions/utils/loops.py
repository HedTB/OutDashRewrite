## -- IMPORTING -- ##

# MODULES
import disnake
import os
import certifi
import requests

from disnake.ext import commands, tasks
from pymongo import MongoClient
from dotenv import load_dotenv

# FILES
from utils import config
from utils import functions
from utils.checks import *
from utils.statcord import StatcordClient

## -- VARIABLES -- ##

load_dotenv()

mongo_login = os.environ.get("MONGO_LOGIN")
google_api_key = os.environ.get("GOOGLE_API_KEY")
statcord_api_key = os.environ.get("STATCORD_API_KEY")

client = MongoClient(mongo_login, tlsCAFile=certifi.where())
db = client[config.database_collection]

youtube_uploads_col = db["youtube_uploads"]

## -- COG -- ##

class Loops(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.statcord_client = StatcordClient(bot, statcord_api_key, self.custom_graph_1)
        
        self.presence_loop.start()
        self.youtube_upload_loop.start()
        
    def cog_unload(self):
        self.statcord_client.close()
        
        self.presence_loop.stop()
        self.youtube_upload_loop.stop()

    async def custom_graph_1(self):
        return 1 + 2 + 3
    
    @tasks.loop(minutes=5)
    async def youtube_upload_loop(self):
        for document in youtube_uploads_col.find():
            channels = [document.get("channel1"), document.get("channel2")]
            query = {"guild_id": document["guild_id"]}

            for channel_index, channel in enumerate(channels):
                channel_index += 1
                
                if not channel:
                    continue

                published_videos = document.get(str(channel_index) + "_videos")
                ping_channel = self.bot.get_channel(config.messages_channel)
                
                str_list = channel.split("/")
                channel_id = str_list[-1]

                response = requests.get(
                    f"https://youtube.googleapis.com/youtube/v3/channels?part=contentDetails&id={channel_id}&key={google_api_key}"
                ).json()
                playlist_id = response.get("items")[0]["contentDetails"]["relatedPlaylists"]["uploads"]

                videos_response = requests.get(
                    url=f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=5000&playlistId={playlist_id}&key={google_api_key}"
                ).json()

                if published_videos:
                    published_videos = published_videos.split("|")
                    newest_video_url = "https://youtube.com/watch?v=" + videos_response.get("items")[0]["snippet"]["resourceId"]["videoId"]

                    if not newest_video_url in published_videos:
                        await ping_channel.send(newest_video_url)

                published_videos = []

                for video in videos_response.get("items"):
                    video_id = video["snippet"]["resourceId"]["videoId"]
                    url = "https://youtube.com/watch?v=" + video_id

                    published_videos.append(url)

                str_list = "|".join(i for i in published_videos)

                youtube_uploads_col.update_one(
                    filter = query,
                    update = {"$set": {
                        str(channel_index) + "_videos": str_list
                    }}
                )

    @tasks.loop(seconds=30)
    async def presence_loop(self):
        if not self.bot.is_ready():
            await self.bot.wait_until_ready()
            
        presence_list = [
            f"{len(self.bot.guilds)} servers | {config.default_prefix}help",
            f"{len(self.bot.users)} users | {config.default_prefix}help",
            f"outdash.ga | {config.default_prefix}help",
        ]
        
        if self.bot.presence_index + 1 > len(presence_list) - 1:
            self.bot.presence_index = 0
        else:
            self.bot.presence_index += 1
            
        await self.bot.change_presence(activity=disnake.Activity(
            type = disnake.ActivityType.watching,
            name = presence_list[self.bot.presence_index],
            status = disnake.Status.online
        ))


def setup(bot):
    bot.add_cog(Loops(bot))