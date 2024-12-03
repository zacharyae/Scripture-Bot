import discord
from discord import Embed


MAX_EMBED_LENGTH = 1200
MAX_FIELD_LENGTH = 1024

def format_scripture_message(book, chapterNumber, verses, page_num, items_per_page, url):
    print(verses)
#    embed = discord.Embed(title=f"{book} Chapter {chapterNumber}", color=0x00ff00)
#    for verse in verses:
#        embed.add_field(name=f"{verse['verse']}", value=verse['text'], inline=False)
    embed = discord.Embed(
        title=f"{book.title()} {chapterNumber}",
        color=0x011738,
        url=url
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
