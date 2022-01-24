import disnake
from disnake.ext import commands, tasks

class PresenceLoop(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.presence_loop.start()

    @tasks.loop(seconds = 30)
    async def presence_loop(self):
        
        global bot
        bot = self.bot
        
        await bot.wait_until_ready()
        
        bot.presence_list = [f"{len(bot.guilds)} servers | ?help", f"{len(bot.users)} users | ?help", f"outdash.ga | ?help"]
        try:
            if not bot.current_index:
                bot.current_index = 0
        except AttributeError:
            bot.current_index = 0

        if bot.current_index + 1 > len(bot.presence_list) - 1:
            bot.current_index = 0
        else:
            bot.current_index += 1
            
        await bot.change_presence(activity=disnake.Activity(type=disnake.ActivityType.watching, name=bot.presence_list[bot.current_index]), status=disnake.Status.online)

def setup(bot):
  bot.add_cog(PresenceLoop(bot))