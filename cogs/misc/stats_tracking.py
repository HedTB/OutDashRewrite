from disnake.ext import commands

import disnake


class StatcordPost(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.key = "statcord.com-pA1Iet9GBe9D8lq1b5WD"
        self.api = statcord.Client(self.bot,self.key)
        self.api.start_loop()


    @commands.Cog.listener()
    async def on_command(self,ctx):
        self.api.command_run(ctx)


def setup(bot):
    bot.add_cog(StatcordPost(bot))
