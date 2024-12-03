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
from discord.ui import View, Button

from config import TOKEN

from utils.constants import BOMLIST, DCLIST, PGPLIST, OLDTESTLIST, NEWTESTLIST, APOCRYPHALIST, PROCLIST, BOOKNAMEMAP
from utils.scripture_utils import get_scripture, make_link, is_biblical_references_allowed
from utils.embed_helpers import format_scripture_message, calculate_items_per_page

client = discord.ext.commands.Bot(command_prefix="-", intents=discord.Intents.all())

global embed_msg
MAX_EMBED_LENGTH = 1200
MAX_FIELD_LENGTH = 1024

async def load_extensions():
    # List of command files to load
    extensions = [
        "commands.scripture",  # All scripture-related commands
        "commands.general",    # General commands (help, quotes, etc.)
        "commands.admin"       # Admin-related commands (if any)
    ]

    for extension in extensions:
        try:
            await client.load_extension(extension)  # Use await here
            print(f"Loaded extension: {extension}")
        except Exception as e:
            print(f"Failed to load extension {extension}: {e}")

  

async def send_paginated_scripture(channel, embed_msg, max_pages, link, items_per_page):
    """
    Sends a paginated embed to a Discord channel with buttons for navigation.

    Parameters:
        channel (discord.TextChannel): The channel to send the message in.
        embed_msg (tuple): Data needed for the embed (book, chapter, verses, etc.).
        max_pages (int): The total number of pages.
        link (str): The URL link to include in the embed.
        items_per_page (int): Number of verses/items to show per page.
    """
    # Start with the first page
    print('hello there')
    page_number = 1
    embed = format_scripture_message(embed_msg[0], embed_msg[1], embed_msg[2], page_number, items_per_page, link)

    # Create the view for the buttons
    view = View()

    async def update_message(interaction, next_page):
        """
        Updates the embed based on the new page number.
        """
        nonlocal page_number
        if next_page:
            page_number += 1
        else:
            page_number -= 1

        # Create a new embed with updated page
        new_embed = format_scripture_message(embed_msg[0], embed_msg[1], embed_msg[2], page_number, items_per_page, link)
        await interaction.response.edit_message(embed=new_embed, view=view)
        update_buttons()  # Update the button states based on the current page
        await interaction.message.edit(view=view)

    # Define button callbacks
    async def on_prev_button(interaction):
        if page_number > 1:
            await update_message(interaction, next_page=False)

    async def on_next_button(interaction):
        if page_number < max_pages:
            await update_message(interaction, next_page=True)

    # Create buttons
    prev_button = Button(label="Previous", style=discord.ButtonStyle.primary, emoji="◀️")
    next_button = Button(label="Next", style=discord.ButtonStyle.primary, emoji="▶️")

    prev_button.callback = on_prev_button
    next_button.callback = on_next_button

    def update_buttons():
        """
        Enable or disable buttons based on the current page.
        """
        prev_button.disabled = page_number <= 1
        next_button.disabled = page_number >= max_pages

    # Set the initial button states
    update_buttons()

    # Add buttons to the view
    view.add_item(prev_button)
    view.add_item(next_button)

    # Send the embed with the buttons
    await channel.send(embed=embed, view=view)



@client.event
async def on_ready():
    print("Scriptures ready to be referenced.")
    await client.change_presence(activity=discord.Game(name="Get involved. Join the server! https://discord.gg/aKpEyxFJsB"))
#ig I should either have it scan all messages for a book in scriptures
#or make it so when pinged it will check message for reference

    #check if it is a book
        #checking
            #look for reference and split number
            #get reference from json file
            #send message of scripture

@client.event
async def on_guild_join(guild):
    listOfServers = []
    with open('./data/servers.json', 'r') as f:
        serverDict = json.load(f)
    for item in serverDict:
        listOfServers.append(item)
        print(item)
    print(listOfServers)
    if str(guild.id) not in listOfServers:
        serverDict[guild.id] = {'bible':True}
        serverDict = json.dumps(serverDict, indent=4)
        with open('./data/servers.json', 'w') as f:
            f.write(serverDict)
            


@client.event
async def on_message(message):
    if message.author.id in [975539509280243712, 866118123731025921, 96840576950890496]:
        await client.process_commands(message)
        return

    msg = message.content
    script = msg.lower()

    pattern_single = r'\b((?:genesis|exodus|leviticus|numbers|deuteronomy|joshua|judges|ruth|1\ssamuel|2\ssamuel|1\skings|2\skings|1\schronicles|2\schronicles|ezra|nehemiah|esther|job|psalms|proverbs|ecclesiastes|song\sof\ssolomon|isaiah|jeremiah|lamentations|ezekiel|daniel|hosea|joel|amos|obadiah|jonah|micah|nahum|habakkuk|zephaniah|haggai|zechariah|malachi|matthew|mark|luke|john|acts|romans|1\scorinthians|2\scorinthians|galatians|ephesians|philippians|colossians|1\sthessalonians|2\sthessalonians|1\stimothy|2\stimothy|titus|philemon|hebrews|james|1\speter|2\speter|1\sjohn|2\sjohn|3\sjohn|jude|revelation|1\snephi|2\snephi|jacob|enos|jarom|omni|words\sof\smormon|mosiah|alma|helaman|3\snephi|4\snephi|mormon|ether|moroni|doctrine\s&\scovenants|doctrine\sand\scovenants|d&c|moses|abraham|jsm|joseph\ssmith\smatthew|joseph\ssmith-matthew|joseph\ssmith\shistory|joseph\ssmith-history|jsh|articles\sof\sfaith|aof|tobit|judith|wisdom\sof\ssolomon|sirach|baruch|letter\sof\sjeremiah|prayer\sof\sazariah|susanna|bel\sand\sthe\sdragon|1\smaccabees|2\smaccabees|1\sesdras|2\sesdras|prayer\sof\smanasseh|additions\sto\sesther|living\schrist|the\sfamily|family\sproclamation|restoration\sproclamation|official\sdeclaration|od)\b)\s+(\d+):(\d+)(?!\s*(?:−|-|–|–|—)\d+)\b'
    pattern_range = r'\b((?:genesis|exodus|leviticus|numbers|deuteronomy|joshua|judges|ruth|1\ssamuel|2\ssamuel|1\skings|2\skings|1\schronicles|2\schronicles|ezra|nehemiah|esther|job|psalms|proverbs|ecclesiastes|song\sof\ssolomon|isaiah|jeremiah|lamentations|ezekiel|daniel|hosea|joel|amos|obadiah|jonah|micah|nahum|habakkuk|zephaniah|haggai|zechariah|malachi|matthew|mark|luke|john|acts|romans|1\scorinthians|2\scorinthians|galatians|ephesians|philippians|colossians|1\sthessalonians|2\sthessalonians|1\stimothy|2\stimothy|titus|philemon|hebrews|james|1\speter|2\speter|1\sjohn|2\sjohn|3\sjohn|jude|revelation|1\snephi|2\snephi|jacob|enos|jarom|omni|words\sof\smormon|mosiah|alma|helaman|3\snephi|4\snephi|mormon|ether|moroni|doctrine\s&\scovenants|doctrine\sand\scovenants|d&c|moses|abraham|jsm|joseph\ssmith\smatthew|joseph\ssmith-matthew|joseph\ssmith\shistory|joseph\ssmith-history|jsh|articles\sof\sfaith|aof|tobit|judith|wisdom\sof\ssolomon|sirach|baruch|letter\sof\sjeremiah|prayer\sof\sazariah|susanna|bel\sand\sthe\sdragon|1\smaccabees|2\smaccabees|1\sesdras|2\sesdras|prayer\sof\smanasseh|additions\sto\sesther|living\schrist|the\sfamily|family\sproclamation|restoration\sproclamation|official\sdeclaration|od)\b)\s+(\d+):(\d+)(?:−|-|–|–|—)(\d+)\b'

    matches_range = re.findall(pattern_range, script)
    single_verse_refs = re.findall(pattern_single, script)

    if len(matches_range) + len(single_verse_refs) > 4:
        #break
        pass

    print(single_verse_refs)

    for match in single_verse_refs:
        print('single verses')
        book_name, chapter, verse = match[0], match[1], match[2]
        for book in BOMLIST:
            if book_name == book:
                embed_msg = get_scripture(book_name, int(chapter), int(verse), None, "bom")

        for book in PGPLIST:
            if book_name == book:
                embed_msg = get_scripture(book_name, int(chapter), int(verse), None, "pgp")

        for book in OLDTESTLIST:
            if book_name == book:
                embed_msg = get_scripture(book_name, int(chapter), int(verse), None, "old")
            if not is_biblical_references_allowed(message.guild.id):
                return

        for book in NEWTESTLIST:
            if book_name == book:
                embed_msg = get_scripture(book_name, int(chapter), int(verse), None, "new")
            if not is_biblical_references_allowed(message.guild.id):
                return

        for book in APOCRYPHALIST:
            if book_name == book:
                embed_msg = get_scripture(book_name, int(chapter), int(verse), None, "apoc")

        for book in PROCLIST:
            if book_name == book:
                print("hey")
                embed_msg = get_scripture(book_name, int(chapter), int(verse), None, "proc")

        if book_name in DCLIST:
            with open("./data/doctrine-and-covenants.json", "r") as f:
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
                    await message.channel.send(embed=embed)

        else:
            link = make_link(embed_msg[0], embed_msg[1], embed_msg[3], embed_msg[4], embed_msg[5])
            items_per_page = calculate_items_per_page(embed_msg[2])
            page_number = 1
            max_pages = (len(embed_msg[2]) + items_per_page - 1) // items_per_page  # Calculate total number of pages

            embed = format_scripture_message(embed_msg[0], embed_msg[1], embed_msg[2], page_number, items_per_page, link)
            print(embed)


            current_time = datetime.now()
            formatted_time = current_time.strftime("%Y-%m-%d %H:%M")
            try:
                print(f'{formatted_time} hey')
                if max_pages > 1:
                    await send_paginated_scripture(message.channel, embed_msg, max_pages, link, items_per_page)
                elif max_pages == 1:
                    page_number = 1
                    embed = format_scripture_message(embed_msg[0], embed_msg[1], embed_msg[2], page_number, items_per_page, link)
                    await message.channel.send(embed=embed)
            except Exception as e:
                print(formatted_time, e)
                await message.channel.send(formatted_time)
                await message.channel.send(e)


    for match in matches_range:
        print('matches range')
        book_name, chapter, start_verse, end_verse = match[0], match[1], match[2], match[3]
        for book in BOMLIST:
            if book_name == book:
                embed_msg = get_scripture(book_name, int(chapter), int(start_verse), end_verse, "bom")

        for book in PGPLIST:
            if book_name == book:
                embed_msg = get_scripture(book_name, int(chapter), int(start_verse), end_verse, "pgp")

        for book in OLDTESTLIST:
            if book_name == book:
                embed_msg = get_scripture(book_name, int(chapter), int(start_verse), end_verse, "old")

        for book in NEWTESTLIST:
            if book_name == book:
                embed_msg = get_scripture(book_name, int(chapter), int(start_verse), end_verse, "new")

        for book in APOCRYPHALIST:
            if book_name == book:
                embed_msg = get_scripture(book_name, int(chapter), int(start_verse), end_verse, "apoc")

        for book in PROCLIST:
            if book_name == book:
                embed_msg = get_scripture(book_name, int(chapter), int(start_verse), end_verse, "proc")

        if book_name in DCLIST:
            embed_msg = []
            print('yo')
            with open("./data/doctrine-and-covenants.json", "r") as f:
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

                    link = f"https://www.churchofjesuschrist.org/study/scriptures/dc-testament/dc/{chapter}?lang=eng&id=p{start_verse}-p{end_verse}#p{start_verse}"

                    print(relevant_verses)
                    items_per_page = calculate_items_per_page(relevant_verses)
                    page_number = 1
                    max_pages = (len(relevant_verses) + items_per_page - 1) // items_per_page  # Calculate total number of pages

                    embed = format_scripture_message('Doctrine and Covenants', chapter, relevant_verses, page_number, items_per_page, link)
                    
                    embed_msg = ['Doctrine and Covenants', chapter, relevant_verses, script, start_verse, end_verse]

        #link = embed_msg[1].replace(' ', '%20')
        else:
            link = make_link(embed_msg[0], embed_msg[1], embed_msg[3], embed_msg[4], embed_msg[5])
            items_per_page = calculate_items_per_page(embed_msg[2])
            page_number = 1
            max_pages = (len(embed_msg[2]) + items_per_page - 1) // items_per_page  # Calculate total number of pages

            embed = format_scripture_message(embed_msg[0], embed_msg[1], embed_msg[2], page_number, items_per_page, link)
            print(embed)

        current_time = datetime.now()
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M")
        try:
            print(f'{formatted_time} hey')
            if max_pages > 1:
                await send_paginated_scripture(message.channel, embed_msg, max_pages, link, items_per_page)
            elif max_pages == 1:
                page_number = 1
                embed = format_scripture_message(embed_msg[0], embed_msg[1], embed_msg[2], page_number, items_per_page, link)
                await message.channel.send(embed=embed)
        except Exception as e:
            print(formatted_time, e)
            await message.channel.send(formatted_time)
            await message.channel.send(e)
    await client.process_commands(message)




client.remove_command('help')

@client.command()
async def servers(ctx):
    listofids = []
    for guild in client.guilds:
        listofids.append(guild.id)
    print(len(listofids))

extensions = [
    "commands.scripture",  # All scripture-related commands
    "commands.general",    # General commands (help, quotes, etc.)
    "commands.admin"
]


if __name__ == "__main__":
    # Use the bot's startup to load extensions
    async def start_bot():
        await load_extensions()
        await client.start(TOKEN)

    import asyncio
    asyncio.run(start_bot())
