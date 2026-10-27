import json
import re
import discord
import ast
import requests
import aiohttp
import asyncio
import random

from datetime import datetime
from bs4 import BeautifulSoup

import discord
from discord import Embed
from discord.ext import commands

from utils.scripture_utils import get_scripture, make_link
from utils.embed_helpers import format_scripture_message, calculate_items_per_page, count_pages
from utils.constants import BOMLIST, DCLIST, PGPLIST, OLDTESTLIST, NEWTESTLIST, APOCRYPHALIST, PROCLIST, BOOKNAMEMAP

MY_HOME_BASE_URL = 'https://www.churchofjesuschrist.org'
MY_HOME_URL = f'{MY_HOME_BASE_URL}/my-home?lang=eng'

# Cache so we only hit the Church's site once per calendar day, not on every
# -votd/-qotd call across every server.
_daily_content_cache = {'date': None, 'verse': None, 'quote': None}


async def fetch_daily_scripture_content():
    """Fetch and parse the Verse of the Day / Quote of the Day from the
    Church's My Home page.

    Returns (verse, quote), where each is a dict with 'reference', 'text',
    and 'link' keys, or None if that section couldn't be found/parsed.
    Cached per calendar day to avoid hammering the site.
    """
    today = datetime.now().strftime('%Y-%m-%d')
    if _daily_content_cache['date'] == today:
        return _daily_content_cache['verse'], _daily_content_cache['quote']

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                MY_HOME_URL, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status != 200:
                    return None, None
                html = await resp.text()
    except (aiohttp.ClientError, asyncio.TimeoutError):
        return None, None

    soup = BeautifulSoup(html, 'html.parser')
    # This id is a stable, semantic anchor (it also appears in the page's
    # own widget config as the section's key), unlike the hashed CSS module
    # class names nearby (e.g. "_card_e9pnv_1"), which change on every
    # deploy and shouldn't be relied on.
    container = soup.find(id='of-the-day')
    if container is None:
        return None, None

    verse_data, quote_data = None, None
    for card in container.find_all('div', recursive=False):
        heading = card.find('h3')
        if heading is None:
            continue
        title = heading.get_text(strip=True)

        text_el = card.find(lambda tag: tag.name == 'div' and tag.get('class')
                             and any('eden-text' in c for c in tag.get('class')))
        text = text_el.get_text(strip=True).strip('"') if text_el else None

        link_tag = card.find('a', href=True)
        link = f"{MY_HOME_BASE_URL}{link_tag['href']}" if link_tag else None

        # For quotes, prefer the speaker/date attribution (e.g. "Elder Aaron
        # T. Hall | 1 Apr 2026") over the link text (just "General
        # Conference"), since it's the more useful label.
        attribution_el = card.find('span')
        if attribution_el is not None:
            reference = attribution_el.get_text(strip=True)
        elif link_tag is not None:
            reference = link_tag.get_text(strip=True)
        else:
            reference = None

        entry = {'reference': reference, 'text': text, 'link': link}
        if 'Verse' in title:
            verse_data = entry
        elif 'Quote' in title:
            quote_data = entry

    _daily_content_cache.update(date=today, verse=verse_data, quote=quote_data)
    return verse_data, quote_data

def text_embed(title, text, link=None):
    """An embed with a clickable title and the text underneath. The text goes in
    the description, which holds up to 4,096 characters (a field value only holds
    1,024, so a long verse or quote would fail to send as a field). A link only
    shows on a title, so the title is what carries it."""
    embed = discord.Embed(title=title[:256], description=text[:4096], color=0x011738)
    if link:
        embed.url = link
    return embed


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
    async def od1(self, ctx):
        await ctx.send(file=discord.File('././data/posters/OD1.png'))

    def helpBookEmbed(self, name, lst):
        """Embed listing the books in one volume of scripture."""
        books = [item.title() for item in lst if item != 'songs of solomon']
        value = ', '.join(books)
        embed = discord.Embed(color=0x011738)
        if len(value) <= 1024:
            embed.add_field(name=name, value=value, inline=False)
        else:
            # A field value tops out at 1,024 characters; the description allows 4,096.
            embed.title = name
            embed.description = value[:4096]
        return embed

    @commands.command()
    async def bom(self, ctx):
        embed = self.helpBookEmbed('Book of Mormon', BOMLIST)
        await ctx.send(embed = embed)
    
    @commands.command()
    async def old(self, ctx):
        embed = self.helpBookEmbed('Old Testament', OLDTESTLIST)
        await ctx.send(embed = embed)
    
    @commands.command()
    async def new(self, ctx):
        embed = self.helpBookEmbed('New Testament', NEWTESTLIST)
        await ctx.send(embed = embed)
    
    @commands.command()
    async def pgp(self, ctx):
        embed = self.helpBookEmbed('Pearl of Great Price', PGPLIST)
        await ctx.send(embed = embed)
    
    @commands.command(aliases=['apocrypha'])
    async def apoc(self, ctx):
        embed = self.helpBookEmbed('Apocrypha', APOCRYPHALIST)
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
                        max_pages = count_pages(relevant_verses)  # Calculate total number of pages
                        if max_pages == 0:
                            await ctx.send("Sorry, I couldn't find that verse. Try again!")
                            return
    
    
                        print(relevant_verses)
                        print(book_name.title(), int(chapter), relevant_verses, page_number, items_per_page, link)
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
            max_pages = count_pages(embed_msg[2])  # Calculate total number of pages
            if max_pages == 0:
                await ctx.send("Sorry, I couldn't find that verse. Try again!")
                return
            print('smooth sailing')
    
            link = make_link(embed_msg[0], embed_msg[1], embed_msg[3], embed_msg[4], embed_msg[5])
            print(link)
            embed = format_scripture_message(embed_msg[0], embed_msg[1], embed_msg[2], page_number, items_per_page, link)
            print(embed)
        await ctx.send(embed=embed)
        
    @commands.command(aliases=['Quote', 'qotd', 'Qotd', 'dailyquote'])
    async def quote(self, ctx):
        _, quote_data = await fetch_daily_scripture_content()
        if not quote_data or not quote_data.get('text'):
            await ctx.send("Couldn't fetch today's quote right now — try again in a bit.")
            return

        embed = text_embed(quote_data.get('reference') or 'Quote of the Day', quote_data['text'], quote_data.get('link'))
        await ctx.send(embed=embed)

            
    @commands.command(aliases=['Verse', 'votd', 'Votd', 'dailyverse'])
    async def verse(self, ctx):
        verse_data, _ = await fetch_daily_scripture_content()
        if not verse_data or not verse_data.get('text'):
            await ctx.send("Couldn't fetch today's verse right now — try again in a bit.")
            return

        embed = text_embed(verse_data.get('reference') or 'Verse of the Day', verse_data['text'], verse_data.get('link'))
        await ctx.send(embed=embed)





async def setup(bot):
    await bot.add_cog(Scripture(bot))
