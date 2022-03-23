## -- IMPORTING -- ##

# MODULES
import disnake

from disnake.ext import commands

# FILES
from utils import config
from utils.checks import is_moderator

class Clear(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=["purge"])
    @commands.cooldown(rate=1, per=config.cooldown_time, type=commands.BucketType.member)
    @is_moderator(manage_messages=True)
    async def clear(self, ctx: commands.Context,amount: int, channel: disnake.TextChannel = None):
        """Clear up some messages from this channel!"""
        embed = disnake.Embed(description=f"{config.yes} Deleted {amount} messsages." if not amount == 1 else f"{config.yes} Deleted {amount} messsage.", color=config.success_embed_color)
        if not channel:
            await ctx.message.delete()
            await ctx.channel.purge(limit=amount)
            await ctx.channel.send(embed=embed, delete_after=3)
        elif channel and channel == ctx.channel:
            await ctx.message.delete()
            await channel.purge(limit=amount)
            await ctx.send(embed=embed, delete_after=3)
        elif channel and channel != ctx.channel:
            embed2 = disnake.Embed(description=f"{config.yes} Deleted {amount} messages in <#{channel.id}>.", color=config.success_embed_color)
            await channel.purge(limit=amount)
            await ctx.send(embed=embed2)

    
    @clear.error 
    async def clear_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions[0].capitalize()}` permission.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        if isinstance(error, commands.MissingRequiredArgument):
            embed = disnake.Embed(description=f"{config.no} Please specify how many messages you want to delete.", color=config.error_embed_color)
            await ctx.send(embed=embed)
        
    
    @commands.slash_command(name="clear", description="Clear up some messages from this channel!")
    @is_moderator(manage_messages=True)
    async def slash_clear(self, inter: disnake.ApplicationCommandInteraction, amount: int, channel: disnake.TextChannel = None):
        """Clear up some messages from this channel!
        Parameters
        ----------
        amount: The amount of messages you want to delete.
        channel: The channel you want to delete from. Default is the current channel.
        """
        embed = disnake.Embed(description=f"{config.yes} Deleted {amount} messsages." if not amount == 1 else f"{config.yes} Deleted {amount} messsage.", color=config.success_embed_color)
        if not channel:
            await inter.channel.purge(limit=amount)
            await inter.send(embed=embed, ephemeral=True)
        elif channel and channel == inter.channel:
            await channel.purge(limit=amount)
            await inter.send(embed=embed, ephemeral=True)
        elif channel and channel != inter.channel:
            embed2 = disnake.Embed(description=f"{config.yes} Deleted {amount} messages in <#{channel.id}>.", color=config.success_embed_color)
            await channel.purge(limit=amount)
            await inter.send(embed=embed2, ephemeral=True)
            
    
    @slash_clear.error 
    async def slash_clear_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            embed = disnake.Embed(description=f"{config.no} You're missing the `{error.missing_permissions[0].capitalize()}` permission.", color=config.error_embed_color)
            await ctx.response.send_message(embed=embed, ephemeral=True)
        if isinstance(error, commands.MissingRequiredArgument):
            embed = disnake.Embed(description=f"{config.no} Please specify how many messages you want to delete.", color=config.error_embed_color)
            await ctx.response.send_message(embed=embed, ephemeral=True)
        
    
def setup(bot):
    bot.add_cog(Clear(bot))