import json
import re
import discord
import ast
import requests
import asyncio
import random

from datetime import datetime

from discord import Embed
from discord.ext import commands
from discord import app_commands


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def help(self, ctx):
        try:
            embed = discord.Embed(
                title="Help",
                url="https://www.churchofjesuschrist.org/study/scriptures?lang=eng&platform=web",
                color = 0x011738)
            embed.add_field(name='-setServer', value='Enables/disables the bible.', inline=False)
            embed.add_field(name='-ltw', value='Generates an act of kindness you can do for someone!', inline=False)
            embed.add_field(name='-votd', value='Brings up the verse of the day!', inline=False)
            embed.add_field(name='-qotd', value='Brings up the quote of the day!', inline=False)
            embed.add_field(name='-mhl', value='Pulls up a link to find your local chapel!', inline=False)
            embed.add_field(name='-mtm', value='Pulls up a link to request a missionary visit!', inline=False)
            embed.add_field(name='-nyk', value='Pulls up the Know You Know series', inline=False)
            
            await ctx.send(embed=embed)
        except:
            print('hey there')
        
        
        
    @commands.command(aliases=['wipe'])
    async def wipeserver(self, ctx):
        if ctx.author.id == 615710462989828096:
            await ctx.send("https://tenor.com/view/nope-internet-gif-5115830")
        else:
            await ctx.send('skill issue :troll:')
            
    @commands.command(aliases=['meetinghouselocator'])
    async def mhl(self, ctx):
        print('hey')
        embed = discord.Embed(title="Find your local church!", color = 0x011738, url="https://maps.churchofjesuschrist.org/")
        await ctx.send(embed = embed)
                    
    @commands.command(aliases=['meetthemissionaries'])
    async def mtm(self, ctx):
        embed = discord.Embed(title="Meet your local missionaries!", color = 0x011738, url="https://www.churchofjesuschrist.org/comeuntochrist/sg/form/request-missionary-visit")
        await ctx.send(embed = embed)
            
    @commands.command(aliases=['nyk'])
    async def now_you_know(self, ctx):
        await ctx.send("[Now You Know](https://www.youtube.com/playlist?list=PLAYgY8SPtEWE_fFTRP2TQmOXaQh1TeQ-p)")
        
         
async def setup(bot):
    await bot.add_cog(General(bot))
