import discord
from discord import Embed

# How much text goes on one page when a passage has several verses (unchanged).
MAX_PAGE_LENGTH = 1200
# Discord allows 4,096 characters in an embed's description. A verse too long to
# share a page gets a page to itself and may use up to this much (a little room left).
MAX_DESCRIPTION_LENGTH = 4000

# Kept so any other file importing these names keeps working.
MAX_EMBED_LENGTH = MAX_PAGE_LENGTH
MAX_FIELD_LENGTH = 1024


def _split_text(text, limit):
    """Cuts text into pieces of at most `limit` characters, breaking at the end of
    a sentence where possible, otherwise at a space, so a word is never cut."""
    pieces = []
    while len(text) > limit:
        window = text[:limit]
        end = max(window.rfind('. '), window.rfind('? '), window.rfind('! ')) + 1   # just after the punctuation
        if end < limit // 2:                                   # no sentence end in the second half
            space = window.rfind(' ')
            end = space if space > 0 else limit                # break at a space, or hard-cut a giant word
        pieces.append(text[:end].rstrip())
        text = text[end:].lstrip()
    if text:
        pieces.append(text)
    return pieces


def paginate_verses(verses):
    """Splits a passage into pages. Returns a list of pages; each page is a list
    of text blocks (one per verse).

    - Several short verses share a page, up to MAX_PAGE_LENGTH characters.
    - A verse too long to share a page gets a page to itself, however long it
      is (up to MAX_DESCRIPTION_LENGTH), so it is never cut off or rejected.
    - A verse longer than even that is split across pages at sentence ends,
      each piece labelled "(continued)".
    """
    pages, current, current_length = [], [], 0

    def close_page():
        nonlocal current, current_length
        if current:
            pages.append(current)
        current, current_length = [], 0

    for item in verses:
        number, text = item['verse'], item['text']
        block = f"{number} - {text}"
        if len(block) > MAX_PAGE_LENGTH:
            close_page()
            label = f"{number} (continued) - "
            pieces = _split_text(text, MAX_DESCRIPTION_LENGTH - len(label) - len(f"{number} - "))
            for i, piece in enumerate(pieces):
                pages.append([f"{number} - {piece}" if i == 0 else f"{label}{piece}"])
            continue
        if current and current_length + len(block) + 2 > MAX_PAGE_LENGTH:
            close_page()
        current.append(block)
        current_length += len(block) + 2
    close_page()
    return pages


def count_pages(verses):
    """How many pages a passage needs (0 if there is nothing to show)."""
    return len(paginate_verses(verses))


def format_scripture_message(book, chapterNumber, verses, page_num, items_per_page, url):
    """Builds the embed for one page of a passage. `items_per_page` is no longer
    used (page sizes now depend on how long the verses are) but the argument is
    kept so existing calls keep working."""
    embed = discord.Embed(
        title=f"{book.title()} {chapterNumber}"[:256],
        color=0x011738,
        url=url
    )
    pages = paginate_verses(verses)
    if pages:
        page = pages[min(max(page_num, 1), len(pages)) - 1]
        embed.description = "\n\n".join(page)
    return embed


def calculate_items_per_page(data):
    """Kept so existing calls keep working. Returns how many verses fit on the
    first page (never 0). Paging itself now uses paginate_verses / count_pages."""
    pages = paginate_verses(data)
    return len(pages[0]) if pages else 1
