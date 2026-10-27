import io
import json
import re
import discord
import ast
import requests
import asyncio
import random
import json

from datetime import datetime

from discord import Embed
from discord.ext import commands
from discord import app_commands


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command()
    async def getServers(self, ctx):
        """Owner only. Lists every server the bot is in. (It used to be open
        to any server's admin, who could see every other server the bot is in.)"""
        if not await self.bot.is_owner(ctx.author):
            await ctx.send('I am sorry but you do not have permission to do that.')
            return

        lines = [f"{guild.name.replace('`', chr(39))} ({guild.id}) - {guild.member_count} members" for guild in self.bot.guilds]  # backticks in a name would break the code block
        text = f'{len(lines)} servers:\n' + '\n'.join(lines)
        if len(text) <= 1900:
            await ctx.send(f'```\n{text}\n```', allowed_mentions=discord.AllowedMentions.none())
        else:
            # Too long for one message (Discord's limit is 2,000 characters): send it as a file.
            await ctx.send(
                f'{len(lines)} servers:',
                file=discord.File(io.BytesIO('\n'.join(lines).encode('utf-8')), filename='servers.txt')
            )
        
    @commands.command()
    async def refreshServers(self, ctx):
        if ctx.author.id != 615710462989828096:
            await ctx.send('I am sorry but you do not have permission to do that.')
        else:
            print('Yes sir!')
            listOfServers = []
            serversDict = {}
            for guild in self.bot.guilds:
                serversDict[guild.id] = {'bible':True}
            json_object = json.dumps(serversDict, indent=4)
            with open('././data/servers.json', 'w') as f:
                print('created file')
                f.write(json_object)
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setServer(self, ctx, bible):
        id = ctx.guild.id
        with open('././data/servers.json', 'r') as f:
            serverDict = json.load(f)
        serverDict2 = serverDict
        if bible.lower() == 'yes':
            for item in serverDict:
                print(item)
                if item == str(id):
                    print(item)
                    if serverDict[item]['bible'] != True:
                        del serverDict[item]
                        print(serverDict)
                        serverDict[id] = {'bible':True}
                        print(serverDict)
                        serverDict = json.dumps(serverDict, indent=4)
                        with open('././data/servers.json', 'w') as f:
                            print('created file')
                            f.write(serverDict)
                        await ctx.send('done')
        elif bible.lower() == 'no':
            for item in serverDict:
                print(item)
                if item == str(id):
                    print(item)
                    if serverDict[item]['bible'] != False:
                        del serverDict[item]
                        print(serverDict)
                        serverDict[id] = {'bible':False}
                        print(serverDict)
                        serverDict = json.dumps(serverDict, indent=4)
                        with open('././data/servers.json', 'w') as f:
                            print('created file')
                            f.write(serverDict)
                        await ctx.send('done')
        else:
            await ctx.send('Don\'t forget to add yes or no')
         
            
        
async def setup(bot):
    await bot.add_cog(Admin(bot))