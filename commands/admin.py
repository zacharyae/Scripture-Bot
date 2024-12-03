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
    @commands.has_permissions(administrator=True)
    async def getServers(self, ctx):
        listOfServers = []
        for guild in self.bot.guilds:
            listOfServers.append(guild)
        await ctx.send(listOfServers)
        
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