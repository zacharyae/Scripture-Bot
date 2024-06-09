import json
import re
import discord
import ast
import requests
import asyncio
import random

from datetime import datetime


from discord.ext import commands
from discord import app_commands
from discord import Embed

from config import TOKEN

client = discord.ext.commands.Bot(command_prefix="-", intents=discord.Intents.all())

bomList = ["1 nephi", "2 nephi", "jacob", "enos", "jarom", "omni", "words of mormon", "mosiah", "alma", "helaman", 
        "3 nephi", "4 nephi", "mormon", "ether", "moroni"]

dcList = ["doctrine and covenants", "d&c", "doctrine & covenants"]

pgpList = ["moses", "abraham", "joseph smith history", "joseph smith-history", "jsh", "articles of faith", "aof", "jsm", "joseph smith matthew", "joseph smith-matthew"]

oldTestList = ["genesis", "exodus", "leviticus", "numbers", "deuteronomy", "joshua", "judges", "ruth", "1 samuel",
              "2 samuel", "1 kings", "2 kings", "1 chronicles", "2 chronicles", "ezra", "nehemiah", "esther", "job",
              "psalms", "proverbs", "ecclesiastes", "song of solomon", "isaiah", "jeremiah", "lamentations", "ezekiel",
              "daniel", "hosea", "joel", "amos", "obadiah", "jonah", "micah", "nahum", "habakkuk", "zephaniah",
              "haggai", "zechariah", "malachi"]

newTestList = ["matthew", "mark", "luke", "john", "acts", "romans", "1 corinthians", "2 corinthians", "galatians",
       "ephesians", "philippians", "colossians", "1 thessalonians", "2 thessalonians", "1 timothy", "2 timothy",
       "titus", "philemon", "hebrews", "james", "1 peter", "2 peter", "1 john", "2 john", "3 john", "jude",
       "revelation"]

apocryphaList = ["tobit", "judith", "wisdom of solomon", "additions to esther", "sirach", "baruch", "letter of jeremiah", "prayer of azariah", "susanna", 
                 "bel and the dragon", "1 maccabees", "2 maccabees", "1 esdras", "2 esdras", "prayer of manasseh"]

procList = ["living christ", "the family", "family proclamation", "restoration proclamation", "official declaration", "od"]

book_name_map = {"Genesis": "gen", "Exodus": "ex", "Leviticus": "lev", "Numbers": "num", "Deuteronomy": "deut", "Joshua": "josh", "Judges": "judg", "Ruth": "ruth", "1 Samuel": "1-sam", "2 Samuel": "2-sam", "1 Kings": "1-kgs", "2 Kings": "2-kgs", "1 Chronicles": "1-chr", "2 Chronicles": "2-chr", "Ezra": "ezra", "Nehemiah": "neh", "Esther": "esth", "Job": "job", "Psalms": "ps", "Proverbs": "prov", "Ecclesiastes": "eccl", "Song of Solomon": "song", "Isaiah": "isa", "Jeremiah": "jer", "Lamentations": "lam", "Ezekiel": "ezek", "Daniel": "dan", "Hosea": "hosea", "Joel": "joel", "Amos": "amos", "Obadiah": "obad", "Jonah": "jonah", "Micah": "micah", "Nahum": "nahum", "Habakkuk": "hab", "Zephaniah": "zeph", "Haggai": "hag", "Zechariah": "zech", "Malachi": "mal", "Matthew": "matt", "Mark": "mark", "Luke": "luke", "John": "john", "Acts": "acts", "Romans": "rom", "1 Corinthians": "1-cor", "2 Corinthians": "2-cor", "Galatians": "gal", "Ephesians": "eph", "Philippians": "philip", "Colossians": "col", "1 Thessalonians": "1-thes", "2 Thessalonians": "2-thes", "1 Timothy": "1-tim", "2 Timothy": "2-tim", "Titus": "titus", "Philemon": "philem", "Hebrews": "heb", "James": "james", "1 Peter": "1-pet", "2 Peter": "2-pet", "1 John": "1-jn", "2 John": "2-jn", "3 John": "3-jn", "Jude": "jude", "Revelation": "rev", "1 Nephi": "1-ne", "2 Nephi": "2-ne", "Jacob": "jacob", "Enos": "enos", "Jarom": "jarom", "Omni": "omni", "Words Of Mormon": "w-of-m", "Mosiah": "mosiah", "Alma": "alma", "Helaman": "hel", "3 Nephi": "3-ne", "4 Nephi": "4-ne", "Mormon": "morm", "Ether": "ether", "Moroni": "moro", "Moses": "moses", "Abraham": "abr", "Joseph Smith—Matthew": "js-m", "Joseph Smith—History": "js-h", "Articles Of Faith": "a-of-f"}

MAX_EMBED_LENGTH = 1200
MAX_FIELD_LENGTH = 1024

def format_scripture_message(book, chapterNumber, verses, page_num, items_per_page):
    print(verses)
#    embed = discord.Embed(title=f"{book} Chapter {chapterNumber}", color=0x00ff00)
#    for verse in verses:
#        embed.add_field(name=f"{verse['verse']}", value=verse['text'], inline=False)
    embed = discord.Embed(
        title=f"{book.title()} {chapterNumber}",
        color=0x011738
    )
    
    # Calculate the start and end indices of items for the current page
    start_idx = (page_num - 1) * items_per_page
    end_idx = start_idx + items_per_page
    
    # Add items to the embed
    for item in verses[start_idx:end_idx]:
        verse = item['verse']
        text = item['text']
        formatted_item = f"{verse} - {text}"
        embed.add_field(name="", value=formatted_item, inline=False)
    
    return embed

def calculate_items_per_page(data):
    items_per_page = 0
    current_length = 0
    
    for item in data:
        verse = item['verse']
        text = item['text']
        formatted_item = f"{verse} - {text}\n\n"
        item_length = len(formatted_item)
        
        if current_length + item_length <= MAX_EMBED_LENGTH and item_length <= MAX_FIELD_LENGTH:
            current_length += item_length
            items_per_page += 1
        else:
            break
    
    return items_per_page    
    
    
@client.event
async def on_ready():
    print("Scriptures ready to be referenced.")

#ig I should either have it scan all messages for a book in scriptures
#or make it so when pinged it will check message for reference

    #check if it is a book
        #checking
            #look for reference and split number
            #get reference from json file
            #send message of scripture

def get_scripture(book, chapterNumber, lowVerse, highVerse, scripture):
    script = ''
    #open json file
    if scripture == "old":
        with open("old-testament.json", "r") as f:
            script = "ot"
            data = json.load(f)
    elif scripture == "new":
        with open("new-testament.json", "r") as f:
            script = "nt"
            data = json.load(f)
    elif scripture == "bom":
        with open("book-of-mormon.json", "r") as f:
            script = "bofm"
            data = json.load(f)
    elif scripture == "pgp":
        script = "pgp"
        with open("pearl-of-great-price.json", "r") as f:
            if book == "jsh" or book == "joseph smith history" or book == "joseph smith-history":
                print('here am i')
                book = "Joseph Smith—History"
            elif book == "aof" or book == "articles of faith":
                book = "Articles of Faith"
            elif book == "jsm" or book == "joseph smith matthew" or book == "joseph smith-matthew":
                book = "Joseph Smith—Matthew"
            data = json.load(f)
    elif scripture == "proc":
        script = "proc"
        with open("proclamations.json", "r") as f:
            data = json.load(f)
        if book == "family proclamation" or book == "the family":
            book = "the family proclamation"
        elif book == "living christ":
            book = "the living christ"
        elif book == "od":
            book = "official declaration"
                
    elif scripture == "apoc":
        script = "apoc"
        with open("apocrypha.json", "r") as f:
            script = "apoc"
            data = json.load(f)
    #[book][chapter][verse]
    dataList = data["books"]
    #loop through books
    for d in dataList:
        if d["book"] == book.title():
            #loop through chapters
            for chapter in d["chapters"]:
                if chapter["chapter"] == int(chapterNumber):
                    relevant_verses = []
                    for verse in chapter["verses"]:
                        #print(highVerse)
                        if highVerse is None:
                            if verse["verse"] == int(lowVerse):
                                relevant_verses.append({"verse": verse["verse"], "text": verse["text"]})
                        else:
                            if verse["verse"] >= int(lowVerse) and verse["verse"] <= int(highVerse):
                                relevant_verses.append({"verse": verse["verse"], "text": verse["text"]})

                    return book.title(), int(chapterNumber), relevant_verses, script, lowVerse, highVerse

def make_link(book, chapterNumber, script, lowVerse, highVerse):
    abbrevBook = book_name_map.get(book, "Unknown")
    link = ""
    
    if script == "apoc":
        link = None
        
    #elif book == "Articles Of Faith":
        #link = f"[{book}](https://www.churchofjesuschrist.org/study/scriptures/af-poster/1?lang=eng)"
    elif book == "The Family Proclamation":
        link = f"[{book}](https://www.churchofjesuschrist.org/study/scriptures/the-family-a-proclamation-to-the-world/the-family-a-proclamation-to-the-world?lang=eng)"
    elif book == "The Living Christ":
        link = f"[{book}](https://www.churchofjesuschrist.org/study/scriptures/the-living-christ-the-testimony-of-the-apostles/the-living-christ-the-testimony-of-the-apostles?lang=eng)"
    elif book == "Restoration Proclamation":
        link = f"[{book}](https://www.churchofjesuschrist.org/study/scriptures/the-restoration-of-the-fulness-of-the-gospel-of-jesus-christ/a-bicentennial-proclamation-to-the-world?lang=eng)"
    elif book == "Official Declaration":
        link = f"[{book} {chapterNumber}](https://www.churchofjesuschrist.org/study/scriptures/dc-testament/od/{chapterNumber}?lang=eng)"

    else:
        if highVerse is None:
            link = f"[{book.title()} {chapterNumber}:{lowVerse}](https://www.churchofjesuschrist.org/study/scriptures/{script}/{abbrevBook}/{chapterNumber}?lang=eng&id=p{lowVerse}#p{lowVerse})"
        else:
            link = f"[{book.title()} {chapterNumber}:{lowVerse}-{highVerse}](https://www.churchofjesuschrist.org/study/scriptures/{script}/{abbrevBook}/{chapterNumber}?lang=eng&id=p{lowVerse}-p{highVerse}#p{lowVerse})"

    return link


@client.event
async def on_message(message):
    if message.author.id in [975539509280243712, 866118123731025921]:
        await client.process_commands(message)
        return

    msg = message.content
    script = msg.lower()

    pattern_single = r'\b((?:genesis|exodus|leviticus|numbers|deuteronomy|joshua|judges|ruth|1\ssamuel|2\ssamuel|1\skings|2\skings|1\schronicles|2\schronicles|ezra|nehemiah|esther|job|psalms|proverbs|ecclesiastes|song\sof\ssolomon|isaiah|jeremiah|lamentations|ezekiel|daniel|hosea|joel|amos|obadiah|jonah|micah|nahum|habakkuk|zephaniah|haggai|zechariah|malachi|matthew|mark|luke|john|acts|romans|1\scorinthians|2\scorinthians|galatians|ephesians|philippians|colossians|1\sthessalonians|2\sthessalonians|1\stimothy|2\stimothy|titus|philemon|hebrews|james|1\speter|2\speter|1\sjohn|2\sjohn|3\sjohn|jude|revelation|1\snephi|2\snephi|jacob|enos|jarom|omni|words\sof\smormon|mosiah|alma|helaman|3\snephi|4\snephi|mormon|ether|moroni|doctrine\s&\scovenants|doctrine\sand\scovenants|d&c|moses|abraham|jsm|joseph\ssmith\smatthew|joseph\ssmith-matthew|joseph\ssmith\shistory|joseph\ssmith-history|jsh|articles\sof\sfaith|aof|tobit|judith|wisdom\sof\ssolomon|sirach|baruch|letter\sof\sjeremiah|prayer\sof\sazariah|susanna|bel\sand\sthe\sdragon|1\smaccabees|2\smaccabees|1\sesdras|2\sesdras|prayer\sof\smanasseh|additions\sto\sesther|living\schrist|the\sfamily|family\sproclamation|restoration\sproclamation|official\sdeclaration|od)\b)\s+(\d+):(\d+)(?!\s*(?:−|-|–|–|—)\d+)\b'
    pattern_range = r'\b((?:genesis|exodus|leviticus|numbers|deuteronomy|joshua|judges|ruth|1\ssamuel|2\ssamuel|1\skings|2\skings|1\schronicles|2\schronicles|ezra|nehemiah|esther|job|psalms|proverbs|ecclesiastes|song\sof\ssolomon|isaiah|jeremiah|lamentations|ezekiel|daniel|hosea|joel|amos|obadiah|jonah|micah|nahum|habakkuk|zephaniah|haggai|zechariah|malachi|matthew|mark|luke|john|acts|romans|1\scorinthians|2\scorinthians|galatians|ephesians|philippians|colossians|1\sthessalonians|2\sthessalonians|1\stimothy|2\stimothy|titus|philemon|hebrews|james|1\speter|2\speter|1\sjohn|2\sjohn|3\sjohn|jude|revelation|1\snephi|2\snephi|jacob|enos|jarom|omni|words\sof\smormon|mosiah|alma|helaman|3\snephi|4\snephi|mormon|ether|moroni|doctrine\s&\scovenants|doctrine\sand\scovenants|d&c|moses|abraham|jsm|joseph\ssmith\smatthew|joseph\ssmith-matthew|joseph\ssmith\shistory|joseph\ssmith-history|jsh|articles\sof\sfaith|aof|tobit|judith|wisdom\sof\ssolomon|sirach|baruch|letter\sof\sjeremiah|prayer\sof\sazariah|susanna|bel\sand\sthe\sdragon|1\smaccabees|2\smaccabees|1\sesdras|2\sesdras|prayer\sof\smanasseh|additions\sto\sesther|living\schrist|the\sfamily|family\sproclamation|restoration\sproclamation|official\sdeclaration|od)\b)\s+(\d+):(\d+)(?:−|-|–|–|—)(\d+)\b'

    matches_range = re.findall(pattern_range, script)
    single_verse_refs = re.findall(pattern_single, script)

    print(single_verse_refs)

    for match in single_verse_refs:
        print('single verses')
        book_name, chapter, verse = match[0], match[1], match[2]
        for book in bomList:
            if book_name == book:
                embed_msg = get_scripture(book_name, int(chapter), int(verse), None, "bom")

        for book in pgpList:
            if book_name == book:
                embed_msg = get_scripture(book_name, int(chapter), int(verse), None, "pgp")

        for book in oldTestList:
            if book_name == book:
                embed_msg = get_scripture(book_name, int(chapter), int(verse), None, "old")

        for book in newTestList:
            if book_name == book:
                embed_msg = get_scripture(book_name, int(chapter), int(verse), None, "new")

        for book in apocryphaList:
            if book_name == book:
                embed_msg = get_scripture(book_name, int(chapter), int(verse), None, "apoc")
        
        for book in procList:
            if book_name == book:
                print("hey")
                embed_msg = get_scripture(book_name, int(chapter), int(verse), None, "proc")

        if book_name in dcList:
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

                    link = f"[D&C {chapter}:{verse}](https://www.churchofjesuschrist.org/study/scriptures/dc-testament/dc/{chapter}?lang=eng&id=p{verse}#p{verse})"
                    #book.title(), int(chapterNumber), relevant_verses, script, lowVerse, highVerse
                    
                    items_per_page = calculate_items_per_page(relevant_verses)
                    page_number = 1
                    max_pages = (len(relevant_verses) + items_per_page - 1) // items_per_page  # Calculate total number of pages


                    print(relevant_verses)
                    embed = format_scripture_message(book_name.title(), int(chapter), relevant_verses, page_number, items_per_page)
                    
        else:
            items_per_page = calculate_items_per_page(embed_msg[2])
            page_number = 1
            max_pages = (len(embed_msg[2]) + items_per_page - 1) // items_per_page  # Calculate total number of pages

            embed = format_scripture_message(embed_msg[0], embed_msg[1], embed_msg[2], page_number, items_per_page)
            link = make_link(embed_msg[0], embed_msg[1], embed_msg[3], embed_msg[4], embed_msg[5])
        
        current_time = datetime.now()
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M")
        try:
            print(formatted_time)
            message_sent = await message.channel.send(embed=embed)
            if max_pages > 1:
                await message_sent.add_reaction("◀️")
                await message_sent.add_reaction("▶️")
            
                def check(reaction, user):
                    return user == message.author and str(reaction.emoji) in ["◀️", "▶️"]
                
                while True:
                    try:
                        reaction, user = await client.wait_for('reaction_add', timeout=60.0, check=check)
                        
                        if str(reaction.emoji) == "▶️" and page_number < max_pages:
                            page_number += 1
                        elif str(reaction.emoji) == "◀️" and page_number > 1:
                            page_number -= 1
                        
                        new_embed = format_scripture_message(embed_msg[0], embed_msg[1], embed_msg[2], page_number, items_per_page)
                        await message_sent.edit(embed=new_embed)
                        await message_sent.remove_reaction(reaction, user)
                    
                    except asyncio.TimeoutError:
                        break
            print(formatted_time)
            if link is not None:
                await message.channel.send(link)
        except Exception as e:
            print(formatted_time, e)
            await message.channel.send(formatted_time)
            await message.channel.send(e)


    for match in matches_range:
        print('matches range')
        book_name, chapter, start_verse, end_verse = match[0], match[1], match[2], match[3]
        for book in bomList:
            if book_name == book:
                embed_msg = get_scripture(book_name, int(chapter), int(start_verse), end_verse, "bom")

        for book in pgpList:
            if book_name == book:
                embed_msg = get_scripture(book_name, int(chapter), int(start_verse), end_verse, "pgp")

        for book in oldTestList:
            if book_name == book:
                embed_msg = get_scripture(book_name, int(chapter), int(start_verse), end_verse, "old")

        for book in newTestList:
            if book_name == book:
                embed_msg = get_scripture(book_name, int(chapter), int(start_verse), end_verse, "new")

        for book in apocryphaList:
            if book_name == book:
                embed_msg = get_scripture(book_name, int(chapter), int(start_verse), end_verse, "apoc")
        
        for book in procList:
            if book_name == book:
                embed_msg = get_scripture(book_name, int(chapter), int(start_verse), end_verse, "proc")

        if book_name in dcList:
            with open("doctrine-and-covenants.json", "r") as f:
                data = json.load(f)
            dataList = data["sections"]
            for sections in dataList:
                if sections["section"] == int(chapter):
                    print(sections["section"])
                    relevant_verses = []
                    for searchingVerse in sections["verses"]:
                        print(searchingVerse)
                        if searchingVerse["verse"] >= int(start_verse) and searchingVerse["verse"] <= int(end_verse):
                            print(f'verse: {searchingVerse["verse"]}')
                            relevant_verses.append({"verse": searchingVerse["verse"], "text": searchingVerse["text"]})

                    link = f"[D&C {chapter}:{start_verse}-{end_verse}](https://www.churchofjesuschrist.org/study/scriptures/dc-testament/dc/{chapter}?lang=eng&id=p{start_verse}-p{end_verse}#p{start_verse})"

                    print(relevant_verses)
                    items_per_page = calculate_items_per_page(relevant_verses)
                    page_number = 1
                    max_pages = (len(relevant_verses) + items_per_page - 1) // items_per_page  # Calculate total number of pages

                    embed = format_scripture_message('Doctrine and Covenants', chapter, relevant_verses, page_number, items_per_page)
                    embed_msg = 'Doctrine and Covenants', chapter, relevant_verses, script, start_verse, end_verse

        #link = embed_msg[1].replace(' ', '%20')
        else:
            items_per_page = calculate_items_per_page(embed_msg[2])
            page_number = 1
            max_pages = (len(embed_msg[2]) + items_per_page - 1) // items_per_page  # Calculate total number of pages

            embed = format_scripture_message(embed_msg[0], embed_msg[1], embed_msg[2], page_number, items_per_page)
            link = make_link(embed_msg[0], embed_msg[1], embed_msg[3], embed_msg[4], embed_msg[5])

        current_time = datetime.now()
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M")
        try:
            print(formatted_time)
            message_sent = await message.channel.send(embed=embed)
            if link is not None:
                await message.channel.send(link)
            if max_pages > 1:
                await message_sent.add_reaction("◀️")
                await message_sent.add_reaction("▶️")
            
                def check(reaction, user):
                    return user == message.author and str(reaction.emoji) in ["◀️", "▶️"]
                
                while True:
                    try:
                        reaction, user = await client.wait_for('reaction_add', timeout=60.0, check=check)
                        
                        if str(reaction.emoji) == "▶️" and page_number < max_pages:
                            page_number += 1
                        elif str(reaction.emoji) == "◀️" and page_number > 1:
                            page_number -= 1
                        
                        new_embed = format_scripture_message(embed_msg[0], embed_msg[1], embed_msg[2], page_number, items_per_page)
                        await message_sent.edit(embed=new_embed)
                        await message_sent.remove_reaction(reaction, user)
                    
                    except asyncio.TimeoutError:
                        break
            print(formatted_time)
        except Exception as e:
            print(formatted_time, e)
            await message.channel.send(formatted_time)
            await message.channel.send(e)
    await client.process_commands(message)
    
@client.command(aliases=['Verse', 'votd', 'Votd', 'dailyverse'])
async def verse(ctx):
    url = 'https://www.churchofjesuschrist.org/my-home?lang=eng'
    response = requests.get(url)
    if response.status_code == 200:
        # Get the raw HTML content of the page
        html_content = response.text

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
        
        if book_name.lower() in dcList:
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

                    link = f"[D&C {chapter}:{verse}](https://www.churchofjesuschrist.org/study/scriptures/dc-testament/dc/{chapter}?lang=eng&id=p{verse}#p{verse})"
                    #book.title(), int(chapterNumber), relevant_verses, script, lowVerse, highVerse
                    
                    items_per_page = calculate_items_per_page(relevant_verses)
                    page_number = 1
                    max_pages = (len(relevant_verses) + items_per_page - 1) // items_per_page  # Calculate total number of pages


                    print(relevant_verses)
                    embed = format_scripture_message(book_name.title(), int(chapter), relevant_verses, page_number, items_per_page)
        else:
            if book_name.lower() in bomList:
                scripture = 'bom'
            elif book_name.lower() in oldTestList:
                scripture = 'old'
            elif book_name.lower() in newTestList:
                scripture = 'new'
            elif book_name.lower() in pgpList:
                scripture = 'pgp'
            else:
                await ctx.send('error')
                return
                
            embed_msg = get_scripture(book_name, chapter, lowVerse, highVerse, scripture)
            
            items_per_page = calculate_items_per_page(embed_msg[2])
            page_number = 1
            max_pages = (len(embed_msg[2]) + items_per_page - 1) // items_per_page  # Calculate total number of pages
    
            embed = format_scripture_message(embed_msg[0], embed_msg[1], embed_msg[2], page_number, items_per_page)
            link = make_link(embed_msg[0], embed_msg[1], embed_msg[3], embed_msg[4], embed_msg[5])
        
            link = make_link(embed_msg[0], embed_msg[1], embed_msg[3], embed_msg[4], embed_msg[5])
        await ctx.send(embed=embed)
        await ctx.send(link)
        
@client.command(aliases=['Quote', 'qotd', 'Qotd', 'dailyquote'])
async def quote(ctx):
    url = 'https://www.churchofjesuschrist.org/my-home?lang=eng'
    response = requests.get(url)
    if response.status_code == 200:
        # Get the raw HTML content of the page
        html_content = response.text

        pattern = r'"quote"(?:[^"]*"){12}'
        matches = re.findall(pattern, html_content)

        if matches:
            for match in matches:
                quote = match[8:] + '}'
        else:
            print(f'No text found within the element "{target_element}"')
    
        quote_dict = ast.literal_eval(quote)
        print(quote_dict)
        await ctx.send(quote_dict['title'])
        embed = discord.Embed(color=0x011738)
        embed.add_field(name = quote_dict['title'], value = str(quote_dict['text']), inline = False)
        await ctx.send(embed=embed)
	
	
def helpBookEmbed(lst):
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
    
@client.command()
async def bom(ctx):
    embed = helpBookEmbed(bomList)
    await ctx.send(embed = embed)
 
@client.command()
async def old(ctx):
    embed = helpBookEmbed(oldTestList)
    await ctx.send(embed = embed)
        
@client.command()
async def new(ctx):
    embed = helpBookEmbed(newTestList)
    await ctx.send(embed = embed)
        
@client.command()
async def pgp(ctx):
    embed = helpBookEmbed(pgpList)
    await ctx.send(embed = embed)
        
@client.command(aliases=['apocrypha'])
async def apoc(ctx):
    embed = helpBookEmbed(apocryphaList)
    await ctx.send(embed = embed)
    
    

@client.command(aliases=['meetthemissionaries'])
async def mtm(ctx):
    embed = discord.Embed(title="Meet your local missionaries!", color = 0x011738, url="https://www.churchofjesuschrist.org/comeuntochrist/sg/form/request-missionary-visit")
    await ctx.send(embed = embed)

@client.command(aliases=['meetinghouselocator'])
async def mhl(ctx):
    embed = discord.Embed(title="Find your local church!", color = 0x011738, url="https://maps.churchofjesuschrist.org/")
    await ctx.send(embed = embed)


@client.command()
async def randomverse(ctx):
    with open ('reference.txt', 'r+') as ref:
        allscripture = ref.read()
    scriptureList = allscripture.split(', ')
    script = random.choice(scriptureList)
    print(script)
    pattern_single = r'\b((?:genesis|exodus|leviticus|numbers|deuteronomy|joshua|judges|ruth|1\ssamuel|2\ssamuel|1\skings|2\skings|1\schronicles|2\schronicles|ezra|nehemiah|esther|job|psalms|proverbs|ecclesiastes|song\sof\ssolomon|isaiah|jeremiah|lamentations|ezekiel|daniel|hosea|joel|amos|obadiah|jonah|micah|nahum|habakkuk|zephaniah|haggai|zechariah|malachi|matthew|mark|luke|john|acts|romans|1\scorinthians|2\scorinthians|galatians|ephesians|philippians|colossians|1\sthessalonians|2\sthessalonians|1\stimothy|2\stimothy|titus|philemon|hebrews|james|1\speter|2\speter|1\sjohn|2\sjohn|3\sjohn|jude|revelation|1\snephi|2\snephi|jacob|enos|jarom|omni|words\sof\smormon|mosiah|alma|helaman|3\snephi|4\snephi|mormon|ether|moroni|doctrine\s&\scovenants|doctrine\sand\scovenants|d&c|moses|abraham|jsm|joseph\ssmith\smatthew|joseph\ssmith-matthew|joseph\ssmith\shistory|joseph\ssmith-history|jsh|articles\sof\sfaith|aof|tobit|judith|wisdom\sof\ssolomon|sirach|baruch|letter\sof\sjeremiah|prayer\sof\sazariah|susanna|bel\sand\sthe\sdragon|1\smaccabees|2\smaccabees|1\sesdras|2\sesdras|prayer\sof\smanasseh|additions\sto\sesther|living\schrist|the\sfamily|family\sproclamation|restoration\sproclamation|official\sdeclaration|od)\b)\s+(\d+):(\d+)(?!\s*(?:−|-|–|–|—)\d+)\b'

    single_verse_refs = re.findall(pattern_single, script.lower())

    for match in single_verse_refs:
        print(match)
        book_name, chapter, lowVerse = match[0], match[1], match[2]
    highVerse = None
    
    if book_name.lower() in dcList:
        if book_name.lower() in dcList:
            with open("doctrine-and-covenants.json", "r") as f:
                data = json.load(f)
            dataList = data["sections"]
            for sections in dataList:
                if sections["section"] == int(str(chapter)):
                    print(sections["section"])
                    relevant_verses = []
                    for searchingVerse in sections["verses"]:
                        print(f'verse: {verse}')
                        if searchingVerse["verse"] == int(str(lowVerse)):
                            relevant_verses.append({"verse": searchingVerse["verse"], "text": searchingVerse["text"]})
                            print(f'found verse {searchingVerse["verse"], searchingVerse["text"]}')

                    link = f"[D&C {chapter}:{lowVerse}](https://www.churchofjesuschrist.org/study/scriptures/dc-testament/dc/{chapter}?lang=eng&id=p{verse}#p{verse})"
                    #book.title(), int(chapterNumber), relevant_verses, script, lowVerse, highVerse
                    
                    items_per_page = calculate_items_per_page(relevant_verses)
                    page_number = 1
                    max_pages = (len(relevant_verses) + items_per_page - 1) // items_per_page  # Calculate total number of pages


                    print(relevant_verses)
                    embed = format_scripture_message(book_name.title(), int(chapter), relevant_verses, page_number, items_per_page)
                 
    else:
        if book_name.lower() in bomList:
            scripture = 'bom'
        elif book_name.lower() in oldTestList:
            scripture = 'old'
        elif book_name.lower() in newTestList:
            scripture = 'new'
        elif book_name.lower() in pgpList:
            scripture = 'pgp'
        elif book_name.lower() in apocryphaList:
            scripture = 'apoc'
        else:
            await ctx.send('error')
            return
            
        embed_msg = get_scripture(book_name, chapter, lowVerse, highVerse, scripture)
        
        items_per_page = calculate_items_per_page(embed_msg[2])
        page_number = 1
        max_pages = (len(embed_msg[2]) + items_per_page - 1) // items_per_page  # Calculate total number of pages
    
        embed = format_scripture_message(embed_msg[0], embed_msg[1], embed_msg[2], page_number, items_per_page)
        link = make_link(embed_msg[0], embed_msg[1], embed_msg[3], embed_msg[4], embed_msg[5])
    
        link = make_link(embed_msg[0], embed_msg[1], embed_msg[3], embed_msg[4], embed_msg[5])
    await ctx.send(embed=embed)
    await ctx.send(link)
        
        
@client.command()
async def family(ctx):
    await ctx.send(file=discord.File('./posters/family_proclamation.png'))
@client.command(aliases=['lc', 'living', 'christ'])
async def livingChrist(ctx):
    await ctx.send(file=discord.File('./posters/the_living_christ_2015.png'))
@client.command()
async def aof(ctx):
    await ctx.send(file=discord.File('./posters/faith_articles_lds.jpeg'))
@client.command()
async def restoration(ctx):
    await ctx.send(file=discord.File('./posters/restoration_bicentennial_proclamation.png'))

client.remove_command('help')

@client.command()
async def servers(ctx):
    servers = list(self.client.servers)
    await ctx.send(f"Connected on {str(len(servers))} servers:")

@client.command()
async def help(ctx):
    embed = discord.Embed(title="Help",
                      url="https://www.churchofjesuschrist.org/study/scriptures?lang=eng&platform=web",
                      color = 0x011738)
    embed.add_field(name="-bom",
                    value="Brings up the books in the Book of Mormon",
                    inline=False)
    embed.add_field(name="-old",
                    value="Brings up the books in the Old Testament",
                    inline=False)
    embed.add_field(name="-new",
                    value="Brings up the books in the New Testament",
                    inline=False)
    embed.add_field(name="-pgp",
                    value="Brings up the books in the Pearl of Great Price",
                    inline=False)
    embed.add_field(name="-apoc",
                    value="Brings up the books in the Apocrypha available",
                    inline=False)
    embed.add_field(name="-votd",
                    value="Brings up the verse of the day!",
                    inline=False)
    embed.add_field(name="-qotd",
                    value="Brings up the quote of the day!",
                    inline=False)
    embed.add_field(name="-mhl",
                    value="Pulls up a link to find your local chapel!",
                    inline=False)
    embed.add_field(name="-mtm",
                    value="Pulls up a link to request a missionary visit!",
                    inline=False)
    
    embed.set_footer(text="The bot to bring you your scripture references!")
    
    await ctx.send(embed=embed)


client.run(TOKEN)