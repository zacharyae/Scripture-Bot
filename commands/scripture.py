import json
import re
import discord
import ast
import requests
import asyncio
import random

from datetime import datetime

import discord
from discord import Embed
from discord.ext import commands

from utils.scripture_utils import get_scripture, make_link
from utils.embed_helpers import format_scripture_message, calculate_items_per_page
from utils.constants import BOMLIST, DCLIST, PGPLIST, OLDTESTLIST, NEWTESTLIST, APOCRYPHALIST, PROCLIST, BOOKNAMEMAP

class Scripture(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command()
    async def family(self, ctx):
        await ctx.send(file=discord.File('././data/posters/family_proclamation.png'))
    @commands.command(aliases=['lc', 'living', 'christ'])
    async def livingChrist(self, ctx):
        await ctx.send(file=discord.File('././data/posters/the_living_christ_2015.png'))
    @commands.command()
    async def aof(self, ctx):
        await ctx.send(file=discord.File('././data/posters/faith_articles_lds.jpeg'))
    @commands.command()
    async def restoration(self, ctx):
        await ctx.send(file=discord.File('././data/posters/restoration_bicentennial_proclamation.png'))
    @commands.command()
    async def ltw(self, ctx):

        who = ['Your mom', 'Your dad', 'Your next-door neighbor', 'Your neighbor down the street', 'A cashier', 'A construction worker', 'The owner of your favorite small business', 'A waiter or waitress', 'Your best friend', 'A coworker', 'Your boss', 'Your employee', 'A friend you’ve lost touch with', 'Your crush', 'A new acquaintance', 'Someone you haven’t talked to in years', 'A sibling', 'An old friend', 'A grandparent', 'Someone you follow online', 'A cousin', 'A former teacher', 'A mentor of yours', 'Someone sitting alone', 'Your mail carrier', 'A health care worker', 'A delivery person', 'Someone wearing blue', 'Someone wearing red', 'Someone wearing green', 'A teenager', 'An elderly person', 'Your significant other', 'Someone you talked to yesterday', 'A high school classmate', 'A childhood friend', 'Someone you’ve seen around but never talked to', 'Someone you don’t understand very well', 'Someone different from you', 'An acquaintance', 'Someone you disagree with', 'A janitor', 'A friend of a friend', 'A customer service worker', 'Someone you’ve forgiven', 'Someone younger than you', 'Someone older than you', 'Someone you feel impatient with', 'Someone walking on the street', 'Anyone of your choice', 'Someone wearing white', 'Someone wearing black', 'Someone wearing a hat', 'Someone who seems lonely', 'A random stranger', 'Someone you love', 'Someone who loves you', 'Someone you struggle with', 'Someone who makes you happy', 'The next person to text you']

        what = ['Research family history with', 'Show compassion for', 'Make dinner plans with', 'Make a phone call to', 'Share a laugh with', 'Do an art project with', 'Take lunch over to', 'Plan a fun activity with', 'Share an encouraging scripture with', 'Deliver hot chocolate to', 'Make a donation in behalf of', 'Draw a funny picture for', 'Ask for advice from', 'Share an inspiring quote with', 'Hold the door open for', 'Fist bump', 'Smile at', 'Say a prayer for', 'Share a funny video with', 'Share a happy memory with', 'Give a compliment to', 'Tell a joke to', 'Genuinely thank', 'Offer a listening ear for', 'Offer a hug to', 'Write a nice comment on social media about', 'Buy a gift for', 'Lend your favorite book to', 'Make a custom playlist for', 'Share your favorite recipe with', 'Bring your favorite treat to', 'Say something nice about', 'Offer forgiveness to', 'Write a kind letter for', 'Buy a meal for', 'Buy groceries for', 'Recommend something you love to', 'Pick up trash for', 'Clean the yard for', 'Give flowers to', 'Show support for', 'Ask for help from', 'Go caroling to', 'Share a Christmas story with', 'Babysit for', 'Have an open conversation with', 'Share a treat with', 'Share a spiritual experience with', 'Provide service for', 'Give the benefit of the doubt to', 'Send a card to', 'Show patience for', 'Give gratitude for', 'Say something encouraging to', 'Send a kind text to', 'Save a seat for']
        
        when = ['Before you go to bed', 'Before sunrise', 'Before sunset', 'Before noon', 'During lunch', 'During dinner', 'Before you turn on the TV today', 'Right after you wake up next', 'Before you leave work', 'Next time you go to the store', 'Before Christmas', 'The week of Christmas', 'On Christmas Eve', 'In the next 5 minutes', 'In the next 30 minutes', 'In the next hour', 'In the next 2 hours', 'In the next 3 hours', 'In the next 4 hours', 'Before you get on social media', 'Before you use your phone again', 'Before you enter another building', 'Within the next week', 'Sometime today', 'In the next 24 hours', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday', '2:00 today', 'First thing in the morning', 'Before your next meal', 'In the next 2 weeks', 'Tomorrow', 'The end of the day', 'Before noon tomorrow', 'During work', 'At school', 'The next time you’re home', 'Before you get in the car', 'The next time you’re in public', 'In the morning', 'Before you go outside', 'Before your next meal', 'Before you open your mouth again', 'Before you watch another show on TV', 'Before you leave your house']
        embed = discord.Embed(title='Light The World Idea Generator', url='https://www.churchofjesuschrist.org/comeuntochrist/light-the-world', color=0x011738)
        embed.add_field(name='What: ', value=random.choice(what), inline=True)
        embed.add_field(name='Who: ', value=random.choice(who), inline=True)
        embed.add_field(name='When: ', value=random.choice(when), inline=True)
        
        await ctx.send(embed=embed)
        await ctx.send(file=discord.File('././data/posters/light_the_world.png'))

    def helpBookEmbed(self, lst):
        if lst[0] == '1 nephi':
            name = 'Book of Mormon'
        elif lst[0] == 'moses':
            name = 'Pearl of Great Price'
        elif lst[0] == 'tobit':
            name = 'Apocrypha'
        elif lst[0] == 'matthew':
            name = 'New Testament'
        elif lst[0] == 'genesis':
            name = 'Old Testament'
    
        embed = discord.Embed(color=0x011738)

        value = ''
        for item in lst:
            if item == 'songs of solomon':
                pass
            else:
                value += item.title() + ', '
        embed.add_field(name = name, value = value, inline = False)
        return embed
    
    @commands.command()
    async def bom(self, ctx):
        embed = helpBookEmbed(BOMLIST)
        await ctx.send(embed = embed)
    
    @commands.command()
    async def old(self, ctx):
        embed = helpBookEmbed(OLDTESTLIST)
        await ctx.send(embed = embed)
    
    @commands.command()
    async def new(self, ctx):
        embed = helpBookEmbed(NEWTESTLIST)
        await ctx.send(embed = embed)
    
    @commands.command()
    async def pgp(self, ctx):
        embed = helpBookEmbed(PGPLIST)
        await ctx.send(embed = embed)
    
    @commands.command(aliases=['apocrypha'])
    async def apoc(self, ctx):
        embed = helpBookEmbed(APOCRYPHALIST)
        await ctx.send(embed = embed)    
        
    @commands.command()
    async def randomverse(self, ctx):
        with open ('././data/reference.txt', 'r+') as ref:
            allscripture = ref.read()
        scriptureList = allscripture.split(', ')
        script = random.choice(scriptureList)
        pattern_single = r'\b((?:genesis|exodus|leviticus|numbers|deuteronomy|joshua|judges|ruth|1\ssamuel|2\ssamuel|1\skings|2\skings|1\schronicles|2\schronicles|ezra|nehemiah|esther|job|psalms|proverbs|ecclesiastes|song\sof\ssolomon|isaiah|jeremiah|lamentations|ezekiel|daniel|hosea|joel|amos|obadiah|jonah|micah|nahum|habakkuk|zephaniah|haggai|zechariah|malachi|matthew|mark|luke|john|acts|romans|1\scorinthians|2\scorinthians|galatians|ephesians|philippians|colossians|1\sthessalonians|2\sthessalonians|1\stimothy|2\stimothy|titus|philemon|hebrews|james|1\speter|2\speter|1\sjohn|2\sjohn|3\sjohn|jude|revelation|1\snephi|2\snephi|jacob|enos|jarom|omni|words\sof\smormon|mosiah|alma|helaman|3\snephi|4\snephi|mormon|ether|moroni|doctrine\s&\scovenants|doctrine\sand\scovenants|d&c|moses|abraham|jsm|joseph\ssmith\smatthew|joseph\ssmith-matthew|joseph\ssmith\shistory|joseph\ssmith-history|jsh|articles\sof\sfaith|aof|tobit|judith|wisdom\sof\ssolomon|sirach|baruch|letter\sof\sjeremiah|prayer\sof\sazariah|susanna|bel\sand\sthe\sdragon|1\smaccabees|2\smaccabees|1\sesdras|2\sesdras|prayer\sof\smanasseh|additions\sto\sesther|living\schrist|the\sfamily|family\sproclamation|restoration\sproclamation|official\sdeclaration|od)\b)\s+(\d+):(\d+)(?!\s*(?:−|-|–|–|—)\d+)\b'
    
        single_verse_refs = re.findall(pattern_single, script.lower())

    
        for match in single_verse_refs:
            book_name, chapter, lowVerse = match[0], match[1], match[2]
        highVerse = None
    
        if book_name.lower() in DCLIST:
            if book_name.lower() in DCLIST:
                with open("././data/doctrine-and-covenants.json", "r") as f:
                    data = json.load(f)
                dataList = data["sections"]
                for sections in dataList:
                    if sections["section"] == int(str(chapter)):
                        print(sections["section"])
                        relevant_verses = []
                        for searchingVerse in sections["verses"]:
                            if searchingVerse["verse"] == int(str(lowVerse)):
                                print('test')
                                relevant_verses.append({"verse": searchingVerse["verse"], "text": searchingVerse["text"]})
                                print(f'found verse {searchingVerse["verse"], searchingVerse["text"]}')
    
                        link = f"https://www.churchofjesuschrist.org/study/scriptures/dc-testament/dc/{chapter}?lang=eng&id=p{lowVerse}#p{lowVerse}"
                        #book.title(), int(chapterNumber), relevant_verses, script, lowVerse, highVerse
    
                        items_per_page = calculate_items_per_page(relevant_verses)
                        page_number = 1
                        max_pages = (len(relevant_verses) + items_per_page - 1) // items_per_page  # Calculate total number of pages
    
    
                        print(relevant_verses)
                        embed = format_scripture_message(book_name.title(), int(chapter), relevant_verses, page_number, items_per_page, link)

                        
    
        else:
            if book_name.lower() in BOMLIST:
                scripture = 'bom'
            elif book_name.lower() in OLDTESTLIST:
                scripture = 'old'
            elif book_name.lower() in NEWTESTLIST:
                scripture = 'new'
            elif book_name.lower() in PGPLIST:
                scripture = 'pgp'
            elif book_name.lower() in APOCRYPHALIST:
                scripture = 'apoc'
            else:
                await ctx.send('error')
                return
                
            embed_msg = get_scripture(book_name, chapter, lowVerse, highVerse, scripture)
    
            items_per_page = calculate_items_per_page(embed_msg[2])
            page_number = 1
            max_pages = (len(embed_msg[2]) + items_per_page - 1) // items_per_page  # Calculate total number of pages
            print('smooth sailing')
    
            link = make_link(embed_msg[0], embed_msg[1], embed_msg[3], embed_msg[4], embed_msg[5])
            print(link)
            embed = format_scripture_message(embed_msg[0], embed_msg[1], embed_msg[2], page_number, items_per_page, link)
            print(embed)
        await ctx.send(embed=embed)
        
    @commands.command(aliases=['Quote', 'qotd', 'Qotd', 'dailyquote'])
    async def quote(self, ctx):
        url = 'https://www.churchofjesuschrist.org/my-home?lang=eng'
        response = requests.get(url)
        
        if response.status_code == 200:
            # Ensure proper encoding
            if not response.encoding:
                response.encoding = 'utf-8'  # Default to utf-8
            
            # Get the raw HTML content
            html_content = response.text
            
            # Regex pattern to match "quote" JSON-like object
            pattern = r'"quote":\{.*?\}'
            matches = re.findall(pattern, html_content)
            
            if matches:
                for match in matches:
                    # Extract the JSON-like object
                    quote_json = match[8:]  # Trim to extract the content after "quote":
                    quote_json = quote_json.encode('latin1').decode('utf-8')
                    
                    try:
                        # Convert to a Python dictionary
                        quote_dict = json.loads(quote_json)
                        
                        # Extract title and text from the dictionary
                        title = quote_dict.get('title', 'No title')
                        text = quote_dict.get('text', 'No text')
                        
                        # Build and send the embed message
                        embed = discord.Embed(color=0x011738)
                        embed.add_field(name=title, value=text, inline=False)
                        await ctx.send(embed=embed)
                        
                    except (ValueError, SyntaxError) as e:
                        print(f"Error parsing quote JSON: {e}")
                        await ctx.send("Error parsing quote content.")
            else:
                await ctx.send("No quotes found on the page.")
        else:
            await ctx.send(f"Failed to fetch the webpage. Status code: {response.status_code}")

            
    @commands.command(aliases=['Verse', 'votd', 'Votd', 'dailyverse'])
    async def verse(self, ctx):
        url = 'https://www.churchofjesuschrist.org/my-home?lang=eng'
        response = requests.get(url)
        print(response.encoding)
        if response.status_code == 200:
            # Get the raw HTML content of the page
            html_content = response.content.decode('ISO-8859-1')
    
            pattern = r'"scripture"(?:[^"]*"){12}'
            matches = re.findall(pattern, html_content)
    
            if matches:
                for match in matches:
                    verse = match[12:] + '}'
            else:
                print(f'No text found within the element "{target_element}"')
    
            verse_dict = ast.literal_eval(verse)
            print(verse_dict['title'])
            pattern_single = r'\b((?:genesis|exodus|leviticus|numbers|deuteronomy|joshua|judges|ruth|1\ssamuel|2\ssamuel|1\skings|2\skings|1\schronicles|2\schronicles|ezra|nehemiah|esther|job|psalms|proverbs|ecclesiastes|song\sof\ssolomon|isaiah|jeremiah|lamentations|ezekiel|daniel|hosea|joel|amos|obadiah|jonah|micah|nahum|habakkuk|zephaniah|haggai|zechariah|malachi|matthew|mark|luke|john|acts|romans|1\scorinthians|2\scorinthians|galatians|ephesians|philippians|colossians|1\sthessalonians|2\sthessalonians|1\stimothy|2\stimothy|titus|philemon|hebrews|james|1\speter|2\speter|1\sjohn|2\sjohn|3\sjohn|jude|revelation|1\snephi|2\snephi|jacob|enos|jarom|omni|words\sof\smormon|mosiah|alma|helaman|3\snephi|4\snephi|mormon|ether|moroni|doctrine\s&\scovenants|doctrine\sand\scovenants|d&c|moses|abraham|jsm|joseph\ssmith\smatthew|joseph\ssmith-matthew|joseph\ssmith\shistory|joseph\ssmith-history|jsh|articles\sof\sfaith|aof|tobit|judith|wisdom\sof\ssolomon|sirach|baruch|letter\sof\sjeremiah|prayer\sof\sazariah|susanna|bel\sand\sthe\sdragon|1\smaccabees|2\smaccabees|1\sesdras|2\sesdras|prayer\sof\smanasseh|additions\sto\sesther|living\schrist|the\sfamily|family\sproclamation|restoration\sproclamation|official\sdeclaration|od)\b)\s+(\d+):(\d+)(?!\s*(?:−|-|–|–|—)\d+)\b'
            single_verse_refs = re.findall(pattern_single, verse_dict['title'].lower())
    
            book_name, chapter, lowVerse = '', '', ''
            print(single_verse_refs)
            for match in single_verse_refs:
                print('hey')
                book_name, chapter, lowVerse = match[0], match[1], match[2]
            highVerse = None
            print(book_name)
    
            if book_name.lower() in DCLIST:
                with open("doctrine-and-covenants.json", "r") as f:
                    data = json.load(f)
                dataList = data["sections"]
                for sections in dataList:
                    if sections["section"] == int(chapter):
                        print(sections["section"])
                        relevant_verses = []
                        for searchingVerse in sections["verses"]:
                            print(f'verse: {verse}')
                            if searchingVerse["verse"] == int(verse):
                                relevant_verses.append({"verse": searchingVerse["verse"], "text": searchingVerse["text"]})
                                print(f'found verse {searchingVerse["verse"], searchingVerse["text"]}')
    
                        link = f"https://www.churchofjesuschrist.org/study/scriptures/dc-testament/dc/{chapter}?lang=eng&id=p{verse}#p{verse}"
                        #book.title(), int(chapterNumber), relevant_verses, script, lowVerse, highVerse
    
                        items_per_page = calculate_items_per_page(relevant_verses)
                        page_number = 1
                        max_pages = (len(relevant_verses) + items_per_page - 1) // items_per_page  # Calculate total number of pages
    
    
                        print(relevant_verses)
                        embed = format_scripture_message(book_name.title(), int(chapter), relevant_verses, page_number, items_per_page, link)
            else:
                if book_name.lower() in BOMLIST:
                    scripture = 'bom'
                elif book_name.lower() in OLDTESTLIST:
                    scripture = 'old'
                elif book_name.lower() in NEWTESTLIST:
                    scripture = 'new'
                elif book_name.lower() in PGPLIST:
                    scripture = 'pgp'
                else:
                    await ctx.send('error')
                    return
    
                embed_msg = get_scripture(book_name, chapter, lowVerse, highVerse, scripture)
    
                items_per_page = calculate_items_per_page(embed_msg[2])
                page_number = 1
                max_pages = (len(embed_msg[2]) + items_per_page - 1) // items_per_page  # Calculate total number of pages
                
                link = make_link(embed_msg[0], embed_msg[1], embed_msg[3], embed_msg[4], embed_msg[5])
                embed = format_scripture_message(embed_msg[0], embed_msg[1], embed_msg[2], page_number, items_per_page, link)
            await ctx.send(embed=embed)





async def setup(bot):
    await bot.add_cog(Scripture(bot))
