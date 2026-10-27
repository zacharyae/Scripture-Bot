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
        embed = discord.Embed(
            title="Help",
            description="Here's everything I can do! You can also just type a scripture "
                        "reference like `John 3:16` or `Alma 32:21` in chat and I'll look it up.",
            url="https://www.churchofjesuschrist.org/study/scriptures?lang=eng&platform=web",
            color=0x011738)
 
        embed.add_field(
            name='📖 Daily Scripture',
            value=(
                '`-votd` — Verse of the day\n'
                '`-qotd` — Quote of the day\n'
                '`-randomverse` — A random scripture'
            ),
            inline=False)
 
        embed.add_field(
            name='📚 Books & Proclamations',
            value=(
                '`-bom` `-old` `-new` `-pgp` `-apoc` — List the books in each volume of scripture\n'
                '`-family` — The Family: A Proclamation to the World\n'
                '`-livingChrist` (`-lc`) — The Living Christ\n'
                '`-aof` — The Articles of Faith\n'
                '`-restoration` — The Restoration Proclamation\n'
                '`-od1` — Official Declaration 1'
            ),
            inline=False)
 
        embed.add_field(
            name='💙 Get Involved',
            value=(
                '`-ltw` — Light the World act-of-kindness generator\n'
                '`-mhl` — Find your local meetinghouse\n'
                '`-mtm` — Request a missionary visit\n'
                '`-nyk` — Now You Know video series'
            ),
            inline=False)
 
        embed.add_field(
            name='⚙️ Server Settings (admin only)',
            value='`-setServer yes/no` — Enable or disable Bible references on this server',
            inline=False)
 
        embed.set_footer(text='Prefix: -  •  Suggestions? Let us know!')
 
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException as e:
            print(f'Failed to send help embed: {e}')
            await ctx.send('Sorry, something went wrong showing the help menu.')

        
        
        
    @commands.command(aliases=['wipe'])
    async def wipeserver(self, ctx):
        if ctx.author.id == 615710462989828096:
            await ctx.send("https://tenor.com/view/nope-internet-gif-5115830")
        else:
            await ctx.send('skill issue :troll:')
            
    @commands.command(aliases=['meetinghouselocator'])
    async def mhl(self, ctx):
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
