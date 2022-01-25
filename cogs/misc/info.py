## -- IMPORTING -- ##

# MODULES
import disnake
import datetime
import os

from disnake.ext import commands
from dotenv import load_dotenv

load_dotenv()

# FILES
import extra.config as config

## -- VARAIBLES -- ##

permissions = int(os.environ.get("PERMISSIONS"))

## -- COG -- ##

class Info(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    async def info(self, ctx):
        """Get to know about OutDash!"""
        embed = disnake.Embed(title="Information",
                        description=f"**Main Developer:** {self.bot.get_user(config.owners[0])}\n**Web Developer:** {self.bot.get_user(config.owners[1])}\n\n"
                        f"Upvote OutDash **[here.](https://bit.ly/UpvoteOD1)**\nTo support us, go **[here.](https://bit.ly/SupportOutDash)**\nJoin the **[support server](https://discord.com/invite/4pfUqEufUm)** to report bugs and ask questions.\n\n**[Invite OutDash!](https://discord.com/api/oauth2/authorize?client_id=836494578135072778&permissions={permissions}&scope=bot%20applications.commands)**\n\n"
                        "Thanks for using our bot, it means a lot :heart:",
                        color=config.embed_color)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar or "https://cdn.discordapp.com/embed/avatars/1.png")
        embed.timestamp = datetime.datetime.utcnow()
        
        await ctx.send(embed=embed)
        
    
    @commands.slash_command(name="info", description="Get to know about OutDash!", guild_ids=[config.bot_server])
    async def slash_info(self, inter):
        embed = disnake.Embed(title="Information",
                        description=f"**Main Developer:** {self.bot.get_user(config.owners[0])}\n**Web Developer:** {self.bot.get_user(config.owners[1])}\n\n"
                        f"Upvote OutDash **[here.](https://bit.ly/UpvoteOD1)**\nTo support us, go **[here.](https://bit.ly/SupportOutDash)**\nJoin the **[support server](https://discord.com/invite/4pfUqEufUm)** to report bugs and ask questions.\n\n**[Invite OutDash!](https://discord.com/api/oauth2/authorize?client_id=836494578135072778&permissions={permissions}&scope=bot%20applications.commands)**\n\n"
                        "Thanks for using our bot, it means a lot :heart:",
                        color=config.embed_color)
        embed.set_footer(text=f"Requested by {inter.author}", icon_url=inter.author.avatar or "https://cdn.discordapp.com/embed/avatars/1.png")
        embed.timestamp = datetime.datetime.utcnow()
        
        await inter.send(embed=embed)
        
    
def setup(bot):
    bot.add_cog(Info(bot))