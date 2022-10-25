## -- IMPORTING -- ##

# MODULES
import os
import disnake
import requests
import logging

from disnake.ext import commands, tasks
from dotenv import load_dotenv

# FILES
from utils import config
from utils.data import YouTubeData, get_all_documents
from utils.statcord import StatcordClient

## -- VARIABLES -- ##

load_dotenv()

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
statcord_api_key = os.environ.get("STATCORD_API_KEY")

logger = logging.getLogger("OutDash")

## -- COG -- ##


class Loops(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.statcord_client = StatcordClient(bot, statcord_api_key, lambda: 1 + 2 + 3)

        self.presence_loop.start()
        self.youtube_upload_loop.start()

    def cog_unload(self):
        self.statcord_client.close()

        self.presence_loop.stop()
        self.youtube_upload_loop.stop()

    @tasks.loop(minutes=1)
    async def youtube_upload_loop(self):
        await self.bot.wait_until_ready()

        for document in get_all_documents("youtube_data"):
            youtubeData = YouTubeData(document.get("guild_id"))
            channels = youtubeData.get_youtube_channels()

            for index, channel in enumerate(channels):
                index += 1

                channel_id = channel.get("channel_id")
                posted_videos: list = channel.get("posted_videos")
                ping_channel = self.bot.get_channel(config.MESSAGES_CHANNEL)

                response = requests.get(
                    f"https://youtube.googleapis.com/youtube/v3/channels"
                    f"?part=contentDetails&id={channel_id}&key={GOOGLE_API_KEY}"
                ).json()
                playlist_id = response.get("items")[0]["contentDetails"]["relatedPlaylists"]["uploads"]

                videos_response = requests.get(
                    url=f"https://www.googleapis.com/youtube/v3/playlistItems"
                    f"?part=snippet&maxResults={config.MAX_VIDEOS_STORED}&playlistId={playlist_id}&key={GOOGLE_API_KEY}"
                ).json()
                videos = videos_response.get("items")

                if posted_videos and len(posted_videos) == len(videos) - 1:
                    video_id = videos[0]["snippet"]["resourceId"]["videoId"]
                    video_url = "https://youtube.com/watch?v=" + video_id

                    if video_id not in posted_videos:
                        logger.info("New video found for channel of ID {}".format(channel_id))

                        await ping_channel.send(video_url)
                        posted_videos.append(video_id)
                elif posted_videos is None:
                    channel["posted_videos"] = []
                else:
                    logger.info("No new video found for channel of ID {}".format(channel_id))

                for video in videos:
                    video_id = video["snippet"]["resourceId"]["videoId"]

                    if video_id in posted_videos:
                        continue

                    posted_videos.append(video_id)

                while len(posted_videos) > config.MAX_VIDEOS_STORED:
                    posted_videos.pop()

                youtubeData.update_youtube_channel(channel_id, channel)

    @tasks.loop(seconds=30)
    async def presence_loop(self):
        await self.bot.wait_until_ready()

        presence_list = [
            f"{len(self.bot.guilds)} servers | /help",
            f"{len(self.bot.users)} users | /help",
            "you | /help",
        ]

        if self.bot.presence_index + 1 > len(presence_list) - 1:
            self.bot.presence_index = 0
        else:
            self.bot.presence_index += 1

        await self.bot.change_presence(
            activity=disnake.Activity(
                type=disnake.ActivityType.watching,
                name=presence_list[self.bot.presence_index],
                status=disnake.Status.online,
            )
        )


def setup(bot):
    bot.add_cog(Loops(bot))
