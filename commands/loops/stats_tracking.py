import requests

from statcord import StatcordClient
from disnake.ext import commands, tasks

class StatsTracking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.statcord_client = StatcordClient(bot, "statcord.com-pA1Iet9GBe9D8lq1b5WD", self.custom_graph_1)
        
        self.statcord_loop.start()

    def cog_unload(self):
        self.statcord_client.close()

    async def custom_graph_1(self):
        return 1 + 2 + 3
    
    @tasks.loop(minutes=30)
    async def statcord_loop(self):
        response = requests.post(
            url = "https://statcord.com/bot/836494578135072778/clearcache",
            headers = {"cookie": "_gid=GA1.2.306018653.1646068095; connect.sid=s%3A7g9VQBYdQgvgyKSSsVq2uIZY7e2D8Toa.lYSN0MMxOLrCffnM%2Foym4bfL0DLogLfPv3uGnjxAIow; _ga=GA1.2.572428963.1646068094; _gat_gtag_UA_170926897_1=1; _ga_JT5NSL8623=GS1.1.1646072266.3.1.1646073702.0"}
        )
        
        if response.status_code != 200:
            print(response.json())


def setup(bot):
    bot.add_cog(StatsTracking(bot))
