## -- IMPORTING -- ##

# MODULES
import disnake
import json
import datetime

from disnake.ext import commands

# FILES
import extra.config as config

class OnCommand(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command(self, ctx):
        filename = "stats.json"
        with open(filename, "r") as file_object:
            data = json.load(file_object)
        
        number = data.get("commands_run", 0)
        new_data = {"commands_run" : number + 1}

        with open(filename, 'w') as jsonfile:
            json.dump(new_data, jsonfile)

    @commands.Cog.listener()
    async def on_slash_command(self, inter):
        filename = "stats.json"
        with open(filename, "r") as file_object:
            data = json.load(file_object)
        
        number = data.get("commands_run", 0)
        new_data = {"commands_run" : number + 1}

        with open(filename, 'w') as jsonfile:
            json.dump(new_data, jsonfile)
    
    
def setup(bot):
    bot.add_cog(OnCommand(bot))
