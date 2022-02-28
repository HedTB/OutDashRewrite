from statcord import StatcordClient
from discord.ext import commands


class StatsTracking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.statcord_client = StatcordClient(bot, "statcord.com-pA1Iet9GBe9D8lq1b5WD", self.custom_graph_1)

    def cog_unload(self):
        self.statcord_client.close()

    async def custom_graph_1(self):
        return 1 + 2 + 3


def setup(bot):
    bot.add_cog(StatsTracking(bot))