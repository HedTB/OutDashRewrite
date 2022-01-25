## -- IMPORTING -- ##

# MODULES
import disnake
import os
import random
import asyncio
import datetime
import certifi
import re
import requests
import googleapiclient.discovery
import googleapiclient.errors

from disnake.ext import commands, tasks
from disnake.errors import Forbidden, HTTPException
from disnake.ext.commands import errors
from pymongo import MongoClient
from dotenv import load_dotenv

# FILES
import extra.config as config
import extra.functions as functions

## -- VARIABLES -- ##

google_api_key = os.environ.get("GOOGLE_API_KEY")
mongo_login = os.environ.get("MONGO_LOGIN")
client = MongoClient(f"{mongo_login}", tlsCAFile=certifi.where())
db = client["db"]

youtube_uploads_col = db["youtube_uploads"]

load_dotenv()

####### UCIcIotC2ETMrFK-t510su0g

## -- COG -- ##


class YouTubeUploadLoop(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.youtube_upload_loop.start()

    @tasks.loop(seconds=60)
    async def youtube_upload_loop(self):
        for index, document in enumerate(youtube_uploads_col.find()):
            channels = [
                document.get("channel1"),
                document.get("channel2"),
                document.get("channel3")
            ]
            query = {
                "guild_id": document["guild_id"]
            }

            for channel_index, channel in enumerate(channels):
                channel_index += 1
                if not channel: continue

                published_videos = document.get(str(channel_index) + "_videos")
                message_channel = self.bot.get_channel(config.messages_channel)
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
                    newest_video = videos_response.get("items")[0]
                    newest_video_url = "https://youtube.com/watch?v=" + newest_video["snippet"]["resourceId"]["videoId"]

                    if not newest_video_url in published_videos:

                        await message_channel.send(newest_video_url)

                published_videos = []

                for video in videos_response.get("items"):
                    video_id = video["snippet"]["resourceId"]["videoId"]
                    url = "https://youtube.com/watch?v=" + video_id

                    published_videos.append(url)

                str_list = "|".join(e for e in published_videos)

                youtube_uploads_col.update_one(
                        filter = query,
                        update = {"$set": {
                            str(channel_index) + "_videos": str_list
                        }}
                    )
                        
                    


def setup(bot):
    bot.add_cog(YouTubeUploadLoop(bot))