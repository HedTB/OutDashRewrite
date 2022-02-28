## -- IMPORTING -- ##

# MODULES
import disnake
import datetime

from disnake.ext import commands
from dotenv import load_dotenv

# FILES
import extra.config as config

load_dotenv()

class MemberCount(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    async def membercount(self, ctx):
        """Returns your current member count!"""
            
        guild = ctx.guild
        bots = []
        humans = []
        
        online = sum(member.status==disnake.Status.online or member.status==disnake.Status.do_not_disturb or member.status==disnake.Status.idle for member in guild.members)
        offline = sum(member.status==disnake.Status.offline for member in guild.members)
        
        for i in guild.members:
            if i.bot:
                bots.append(i)
            if i.bot == False:
                humans.append(i)
                
        embed = disnake.Embed(title=f"Member Count",
        description=f":white_check_mark: Total - {guild.member_count}\n:bust_in_silhouette: Humans - {len(humans)}\n:robot: Bots - {len(bots)}"
        f"\n\n**User Statuses**\n{config.online} Online - {online}\n{config.offline} Offline - {offline}", color=config.embed_color)
        
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar or "https://cdn.discordapp.com/embed/avatars/1.png")
        embed.timestamp = datetime.datetime.utcnow()
        
        await ctx.send(embed=embed)
        
    
    @commands.slash_command(name="membercount", description="Returns your current member count!")
    async def slash_membercount(self, inter):
        """Returns your current member count!"""
            
        guild = inter.guild
        bots = []
        humans = []
        
        online = sum(member.status==disnake.Status.online or member.status==disnake.Status.do_not_disturb or member.status==disnake.Status.idle for member in guild.members)
        offline = sum(member.status==disnake.Status.offline for member in guild.members)
        
        for i in guild.members:
            if i.bot:
                bots.append(i)
            if i.bot == False:
                humans.append(i)
                
        embed = disnake.Embed(title=f"Member Count",
        description=f":white_check_mark: Total - {guild.member_count}\n:bust_in_silhouette: Humans - {len(humans)}\n:robot: Bots - {len(bots)}"
        f"\n\n**User Statuses**\n{config.online} Online - {online}\n{config.offline} Offline - {offline}", color=config.embed_color)
        
        embed.set_footer(text=f"Requested by {inter.author}", icon_url=inter.author.avatar or "https://cdn.discordapp.com/embed/avatars/1.png")
        embed.timestamp = datetime.datetime.utcnow()
        
        await inter.send(embed=embed)
        
    
def setup(bot):
    bot.add_cog(MemberCount(bot))