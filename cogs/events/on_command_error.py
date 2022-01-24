## -- IMPORTING -- ##

# MODULES
import disnake
import os
import random
import asyncio
import datetime
import certifi
import logging

from disnake.ext import commands
from disnake.errors import Forbidden, HTTPException
from disnake.ext.commands import errors

# FILES
import config

ignored = (commands.CommandNotFound, commands.MissingPermissions, Forbidden, HTTPException, commands.MissingRequiredArgument, )

class OnCommandError(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_slash_command_error(self, inter: disnake.ApplicationCommandInteraction, error):
        channel = self.bot.get_channel(config.error_channel)
        options_data = inter.data.options
        options = []
        if len(options_data) == 0:
            options = ""
        else:
            for i in options_data:
                options.append(f"{i.name}: {i.value}")
        
        if isinstance(error, ignored):
            return
            
        elif isinstance(error, commands.CommandOnCooldown):
            embed1 = disnake.Embed(description=f"{config.no} This command is on cooldown. Please try again after **{round(error.retry_after, 1)} seconds.**", color=config.error_embed_color)
            await inter.send(embed=embed1)
            
        elif isinstance(error, errors.CommandInvokeError):
            embed = disnake.Embed(title="Slash Command Error", description=f"```py\n{error}\n```\n_ _", color=config.error_embed_color)
            embed.add_field(name="Occured in:", value=f"{inter.guild.name} ({inter.guild.id})", inline=False)
            embed.add_field(name="Occured by:", value=f"{inter.author.name} ({inter.author.id})", inline=False)
            embed.add_field(name="Command run:", value=f"/{inter.data.name} `{str(options)[2:-2]}`", inline=False)
            
            print(inter.data.options)
            logging.error(error)

            await channel.send(embed=embed)
            embed4 = disnake.Embed(description=f"{config.no} Oh no! Something went wrong while running the command! Please join our [support server](https://discord.com/invite/4pfUqEufUm) and report the bug.", color=config.error_embed_color)
            try:
                await inter.response.send_message(embed=embed4, ephemeral=True)
            except AttributeError:
                await inter.send(embed=embed4)

    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        print(error)
        channel = self.bot.get_channel(config.error_channel)
        
        if isinstance(error, ignored):
            return
        elif str(error).find("Missing Permissions"):
            return
            
        elif isinstance(error, commands.CommandOnCooldown):
            embed1 = disnake.Embed(description=f"{config.no} This command is on cooldown. Please try again after **{str(round(error.retry_after, 1))} seconds.**", color=config.error_embed_color)
            await ctx.send(embed=embed1)
            
        elif isinstance(error, errors.CommandInvokeError):
            embed = disnake.Embed(title="Command Error", description=f"```py\n{error}\n```\n_ _", color=config.error_embed_color)
            embed.add_field(name="Occured in:", value=f"{ctx.guild.name} ({ctx.guild.id})", inline=False)
            embed.add_field(name="Occured by:", value=f"{ctx.author.name} ({ctx.author.id})", inline=False)
            embed.add_field(name="Command run:", value=f"{ctx.message.content}", inline=False)
            
            logging.error(error)

            await channel.send(embed=embed)
            embed4 = disnake.Embed(description=f"{config.no} Oh no! Something went wrong while running the command! Please join our [support server](https://discord.com/invite/4pfUqEufUm) and report the bug.", color=config.error_embed_color)
            await ctx.send(embed=embed4)
    

        
    
    
def setup(bot):
    bot.add_cog(OnCommandError(bot))