import discord
import asyncio
import os
import random
import re
import csv
import io
import sqlite3
import unicodedata
import time
import better_profanity
from better_profanity import profanity
from cryptography.fernet import Fernet, InvalidToken
from dotenv import load_dotenv

from discord import Embed
from discord.ext import commands
from discord.utils import escape_mentions, escape_markdown

DB_PATH = './data/lightTheWorld.db'

# On the Pi, systemd's EnvironmentFile already sets LTW_ENCRYPTION_KEY
# before this process starts, so load_dotenv() finds nothing to do there.
# On a dev machine with no .env file, this is also a silent no-op. It only
# actually does something when a local .env file is present and the
# variable isn't already set - i.e. local testing.
load_dotenv()

# The encryption key must come from an environment variable, never from a
# file sitting next to the data it protects - if the key and the ciphertext
# live in the same place, encrypting it accomplishes very little.
# Generate one once with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# then set it as the LTW_ENCRYPTION_KEY environment variable wherever the
# bot runs. Store a backup of this key somewhere safe and separate from the
# server (a password manager, etc.) - if it's lost, the encrypted data
# cannot be recovered by anyone, including you.
_encryption_key = #os.environ.get('LTW_ENCRYPTION_KEY')
if not _encryption_key:
    raise RuntimeError(
        'LTW_ENCRYPTION_KEY environment variable is not set. Generate one with:\n'
        '  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"\n'
        'then set it as an environment variable before starting the bot. '
        'Back the key up somewhere safe - losing it makes existing encrypted data unrecoverable.'
    )
_fernet = Fernet(_encryption_key.encode())


def encrypt_value(value):
    """Encrypt a string for storage. Returns a string safe to store in a
    TEXT column or write to a text file."""
    return _fernet.encrypt(value.encode('utf-8')).decode('ascii')


def decrypt_value(token):
    """Decrypt a value previously encrypted with encrypt_value. Returns
    None (rather than raising) if the token is corrupt/unreadable, so one
    bad row or line doesn't take down a whole command."""
    try:
        return _fernet.decrypt(token.encode('ascii')).decode('utf-8')
    except (InvalidToken, ValueError):
        return None


# Letters that don't split into "plain letter + accent", plus the "smart"
# punctuation phone keyboards insert automatically (curly quotes, long dashes).
# Written as \u escapes so the file stays plain ASCII.
_SPECIAL_CHAR_MAP = str.maketrans({
    '\u00df': 'ss', '\u00e6': 'ae', '\u00c6': 'AE', '\u0153': 'oe', '\u0152': 'OE',   # ss ae AE oe OE
    '\u00f8': 'o', '\u00d8': 'O', '\u0142': 'l', '\u0141': 'L',                       # o O l L
    '\u0111': 'd', '\u0110': 'D', '\u00f0': 'd', '\u00d0': 'D',                       # d D d D
    '\u00fe': 'th', '\u00de': 'Th',                                                   # th Th
    '\u2018': "'", '\u2019': "'", '\u201a': "'", '\u201b': "'",                       # curly single quotes
    '\u201c': '"', '\u201d': '"', '\u201e': '"',                                      # curly double quotes
    '\u2013': '-', '\u2014': '-', '\u2212': '-',                                      # en/em dash, minus
    '\u00a0': ' ', '\u2009': ' ', '\u202f': ' ',                                      # non-breaking/thin spaces
})


def to_ascii(text):
    """Converts text to plain ASCII, keeping as much meaning as possible:
    accented letters become their plain letter (e-acute -> e, n-tilde -> n),
    curly quotes become straight quotes, and fullwidth / stylised look-alike
    letters become normal ones. Anything with no ASCII equivalent (emoji,
    other alphabets) is dropped, as are control and zero-width characters.

    This runs FIRST in the sanitising pipeline, so every later check
    (profanity, URLs, mentions, length) sees the final text. Converting
    (rather than deleting) also helps the profanity filter: a look-alike
    spelling is turned back into the real word before it is checked."""
    text = text.translate(_SPECIAL_CHAR_MAP)
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(ch for ch in text if not unicodedata.combining(ch))
    text = text.encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'[\x00-\x08\x0b-\x1f\x7f]', '', text)


def get_connection():
    return sqlite3.connect(DB_PATH)


def load_encrypted_id_list(path):
    """Reads a file of one encrypted Discord ID per line (the format
    trustedUsers.txt and bannedUsers.txt are now stored in) and returns the
    decrypted IDs as a list of strings. Blank lines and lines that fail to
    decrypt are skipped rather than raising, so one bad line doesn't break
    every permission check that depends on this file."""
    ids = []
    with open(path, 'r') as f:
        for line in f.readlines():
            line = line.strip()
            if not line:
                continue
            decrypted = decrypt_value(line)
            if decrypted is not None:
                ids.append(decrypted)
    return ids


def renumber_activities(conn):
    """Keeps activity numbers contiguous (1, 2, 3, ...). Called after a
    removal so everything after the removed item moves down one number, and
    on startup to tidy up any gaps. Rows are renumbered in ascending order
    and only ever move to a lower number, so a target number is always free.
    Also resets SQLite's AUTOINCREMENT counter, otherwise the next new
    activity would skip ahead of the highest remaining number."""
    ids = [r[0] for r in conn.execute('SELECT id FROM activities ORDER BY id').fetchall()]
    for new_id, old_id in enumerate(ids, start=1):
        if new_id != old_id:
            conn.execute('UPDATE activities SET id = ? WHERE id = ?', (new_id, old_id))
    conn.execute("UPDATE sqlite_sequence SET seq = ? WHERE name = 'activities'", (len(ids),))


def init_db():
    conn = get_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity TEXT NOT NULL,
            author_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS removed_activities (
            id INTEGER,
            activity TEXT NOT NULL,
            author_id TEXT NOT NULL,
            removed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    renumber_activities(conn)
    conn.commit()
    conn.close()


def _build_numbered_export():
    """Reads every activity, decrypts it, and builds the CSV for numberedList.
    Returns (number_of_rows, csv_bytes). Runs in a worker thread so decrypting
    a big list doesn't freeze the bot for everyone else."""
    conn = get_connection()
    rows = conn.execute('SELECT id, activity, author_id FROM activities ORDER BY id').fetchall()
    conn.close()
    decrypted_rows = []
    for row_id, enc_activity, enc_author in rows:
        activity_text = decrypt_value(enc_activity)
        author_text = decrypt_value(enc_author)
        if activity_text is None or author_text is None:
            continue  # corrupt/unreadable row - skip rather than crash the export
        decrypted_rows.append((row_id, activity_text, author_text))
    buffer = io.StringIO()
    csv.writer(buffer).writerows(decrypted_rows)
    return len(decrypted_rows), buffer.getvalue().encode('utf-8')


def delete_all_light_the_world_data():
    """Permanently deletes every activity and every archived (removed) entry,
    restarts numbering at 1, then rewrites the database file so the deleted
    data doesn't linger inside it. Returns (activities, archived) counts."""
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute('PRAGMA secure_delete = ON')
    activities = conn.execute('SELECT COUNT(*) FROM activities').fetchone()[0]
    archived = conn.execute('SELECT COUNT(*) FROM removed_activities').fetchone()[0]
    conn.execute('DELETE FROM activities')
    conn.execute('DELETE FROM removed_activities')
    conn.execute("DELETE FROM sqlite_sequence WHERE name = 'activities'")
    conn.commit()
    conn.execute('VACUUM')
    conn.close()
    return activities, archived


class ActivityListView(discord.ui.View):
    """A shared, paginated list of activities. Anyone in the channel can
    press the buttons, and everyone sees the same page. The data is re-read
    from the database on every click, so it stays current if activities are
    added or removed while the list is open. The timeout resets on every
    click, so a list that's being used stays alive.
    """
    def __init__(self, per_page=10, timeout=180):
        super().__init__(timeout=timeout)
        self.per_page = per_page
        self.page = 0
        self.message = None
        self.items = []
        self.total = 0
        self.max_page = 0
        self._refresh_activities()
        self._update_buttons()

    def _refresh_activities(self):
        """Re-reads the current page from the database. Called on creation and
        on every button click, so removals/additions made while this view is
        open show up in the page count, the total, and the page contents.
        Only the entries on screen are fetched and decrypted (plus a count),
        so a click stays fast however long the list gets."""
        conn = get_connection()
        self.total = conn.execute('SELECT COUNT(*) FROM activities').fetchone()[0]
        self.max_page = max(0, (self.total - 1) // self.per_page)
        # If entries were removed and we're now past the last page, clamp back.
        self.page = min(max(self.page, 0), self.max_page)
        rows = conn.execute(
            'SELECT activity FROM activities ORDER BY id DESC LIMIT ? OFFSET ?',
            (self.per_page, self.page * self.per_page)
        ).fetchall()
        conn.close()
        decrypted = [decrypt_value(row[0]) for row in rows]
        self.items = [a for a in decrypted if a is not None]

    def _update_buttons(self):
        self.previous_button.disabled = (self.page <= 0)
        self.next_button.disabled = (self.page >= self.max_page)

    def format_page(self):
        if self.items:
            body = '\n'.join(self.items)
        elif self.total == 0:
            body = 'No activities yet.'
        else:
            body = 'These entries could not be read. Is the encryption key correct?'
        embed = discord.Embed(
            title='Light The World Activities',
            description=body,
            color=0x011738
        )
        embed.set_footer(text=f'Page {self.page + 1} of {self.max_page + 1} • {self.total} total')
        return embed

    @discord.ui.button(label='◀ Previous', style=discord.ButtonStyle.secondary)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page -= 1
        self._refresh_activities()
        self._update_buttons()
        await interaction.response.edit_message(embed=self.format_page(), view=self)

    @discord.ui.button(label='Next ▶', style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        self._refresh_activities()
        self._update_buttons()
        await interaction.response.edit_message(embed=self.format_page(), view=self)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message is not None:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass


class LTW(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        profanity.load_censor_words()
        init_db()
        self.active_lists = {}  # channel id -> open ActivityListView
        self._delete_requests = {}  # owner id -> when -ltwDeleteAll was first run

    @commands.command()
    async def ltw(self, ctx, *, activity = None):
        #check if it is time to run
        with open('././data/lightTheWorld.txt', 'r') as f:
            flag = f.read().strip() == 'True'

        # changeState has to work regardless of the current on/off state -
        # otherwise once it's turned off, nobody could ever turn it back on.
        if activity is not None and activity.strip().lower() == 'changestate':
            ctx.command.reset_cooldown(ctx)
            userId = ctx.message.author.id
            trustedUsers = load_encrypted_id_list('././data/trustedUsers.txt')
            if str(userId) not in trustedUsers:
                await ctx.send('You do not have permissions for that.')
                return

            with open('././data/lightTheWorld.txt', 'r+') as f:
                flag = f.read().strip() == 'True'
                flag = not flag
                f.seek(0)
                f.truncate()
                f.write(str(flag))
                await ctx.send(f'Set Light The World to {flag}')
                return

        #generate ideas
        if activity == None:
            ctx.command.reset_cooldown(ctx)
            who = ['Your mom', 'Your dad', 'Your next-door neighbor', 'Your neighbor down the street', 'A cashier', 'A construction worker', 'The owner of your favorite small business', 'A waiter or waitress', 'Your best friend', 'A coworker', 'Your boss', 'Your employee', 'A friend you’ve lost touch with', 'Your crush', 'A new acquaintance', 'Someone you haven’t talked to in years', 'A sibling', 'An old friend', 'A grandparent', 'Someone you follow online', 'A cousin', 'A former teacher', 'A mentor of yours', 'Someone sitting alone', 'Your mail carrier', 'A health care worker', 'A delivery person', 'Someone wearing blue', 'Someone wearing red', 'Someone wearing green', 'A teenager', 'An elderly person', 'Your significant other', 'Someone you talked to yesterday', 'A high school classmate', 'A childhood friend', 'Someone you’ve seen around but never talked to', 'Someone you don’t understand very well', 'Someone different from you', 'An acquaintance', 'Someone you disagree with', 'A janitor', 'A friend of a friend', 'A customer service worker', 'Someone you’ve forgiven', 'Someone younger than you', 'Someone older than you', 'Someone you feel impatient with', 'Someone walking on the street', 'Anyone of your choice', 'Someone wearing white', 'Someone wearing black', 'Someone wearing a hat', 'Someone who seems lonely', 'A random stranger', 'Someone you love', 'Someone who loves you', 'Someone you struggle with', 'Someone who makes you happy', 'The next person to text you']
            what = ['Research family history with', 'Show compassion for', 'Make dinner plans with', 'Make a phone call to', 'Share a laugh with', 'Do an art project with', 'Take lunch over to', 'Plan a fun activity with', 'Share an encouraging scripture with', 'Deliver hot chocolate to', 'Make a donation in behalf of', 'Draw a funny picture for', 'Ask for advice from', 'Share an inspiring quote with', 'Hold the door open for', 'Fist bump', 'Smile at', 'Say a prayer for', 'Share a funny video with', 'Share a happy memory with', 'Give a compliment to', 'Tell a joke to', 'Genuinely thank', 'Offer a listening ear for', 'Offer a hug to', 'Write a nice comment on social media about', 'Buy a gift for', 'Lend your favorite book to', 'Make a custom playlist for', 'Share your favorite recipe with', 'Bring your favorite treat to', 'Say something nice about', 'Offer forgiveness to', 'Write a kind letter for', 'Buy a meal for', 'Buy groceries for', 'Recommend something you love to', 'Pick up trash for', 'Clean the yard for', 'Give flowers to', 'Show support for', 'Ask for help from', 'Go caroling to', 'Share a Christmas story with', 'Babysit for', 'Have an open conversation with', 'Share a treat with', 'Share a spiritual experience with', 'Provide service for', 'Give the benefit of the doubt to', 'Send a card to', 'Show patience for', 'Give gratitude for', 'Say something encouraging to', 'Send a kind text to', 'Save a seat for']
            when = ['Before you go to bed', 'Before sunrise', 'Before sunset', 'Before noon', 'During lunch', 'During dinner', 'Before you turn on the TV today', 'Right after you wake up next', 'Before you leave work', 'Next time you go to the store', 'Before Christmas', 'The week of Christmas', 'On Christmas Eve', 'In the next 5 minutes', 'In the next 30 minutes', 'In the next hour', 'In the next 2 hours', 'In the next 3 hours', 'In the next 4 hours', 'Before you get on social media', 'Before you use your phone again', 'Before you enter another building', 'Within the next week', 'Sometime today', 'In the next 24 hours', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday', '2:00 today', 'First thing in the morning', 'Before your next meal', 'In the next 2 weeks', 'Tomorrow', 'The end of the day', 'Before noon tomorrow', 'During work', 'At school', 'The next time you’re home', 'Before you get in the car', 'The next time you’re in public', 'In the morning', 'Before you go outside', 'Before your next meal', 'Before you open your mouth again', 'Before you watch another show on TV', 'Before you leave your house']
            
            embed = discord.Embed(title='Light The World Idea Generator', url='https://www.churchofjesuschrist.org/comeuntochrist/light-the-world', color=0x011738)
            embed.add_field(name='What: ', value=random.choice(what), inline=True)
            embed.add_field(name='Who: ', value=random.choice(who), inline=True)
            embed.add_field(name='When: ', value=random.choice(when), inline=True)
         
            await ctx.send(embed=embed)
            await ctx.send(file=discord.File('././data/posters/light_the_world.png'))
            
        #if it is time to go
        elif flag == True:
            activity = activity.replace("\n", " ").replace("\r", "")
            # Convert to plain ASCII FIRST (e-acute -> e, curly quotes -> straight,
            # emoji dropped). Everything after this - profanity, URLs, mentions,
            # length - checks the final text. It must also happen before escaping:
            # escape_mentions works by inserting an invisible non-ASCII character
            # (a zero-width space), which this step would otherwise strip straight
            # back out and re-arm "@everyone".
            activity = to_ascii(activity)
            if profanity.contains_profanity(activity):
                await ctx.send('Sorry, we don\'t allow that sort of language.')
                return

            url_pattern = re.compile(
            r"""
            \b(
            (?:https?://|ftp://|mailto:|www\.|//)
            [^\s<>()"'{}|\\^`]+
            |
            [a-zA-Z0-9.-]+\.[a-zA-Z]{2,}
            (?:/[^\s<>()"']*)?
            )
            """,
            re.IGNORECASE | re.VERBOSE
            )
            activity = url_pattern.sub("", activity).strip()
            if not activity:
                await ctx.send('Please include some text with your activity.')
                return

            badStarters = ('=', '+', '-', '@')
            if activity.startswith(badStarters):
                activity = "'" + activity

            # Escape LAST, so nothing after this point can undo the escapes.
            activity = escape_mentions(escape_markdown(activity))

            activityWords = activity.split()
            if len(activityWords) > 30 or len(activity) > 200:
                await ctx.send('Sorry, that message is too long.')
                return

            # Command words are not case sensitive. "remove" on its own, or
            # "remove" followed only by digits/commas/#, is treated as a
            # (possibly mistyped) remove command instead of being saved as an
            # activity. Real activities that merely start with the word, like
            # "Remove weeds for my neighbor", are still saved normally.
            command = activity.lower()
            remove_match = re.fullmatch(r'remove(?:\s+([\d\s,#]*))?', activity, re.IGNORECASE)

            if remove_match:
                ctx.command.reset_cooldown(ctx)
                userId = ctx.message.author.id
                trustedUsers = load_encrypted_id_list('././data/trustedUsers.txt')
                if str(userId) not in trustedUsers:
                    await ctx.send('You do not have permissions for that.')
                    return

                number_match = re.fullmatch(r'#?(\d{1,9})', (remove_match.group(1) or '').strip())
                if number_match is None:
                    await ctx.send('To remove an entry, use: -ltw remove <number>  (for example: -ltw remove 3)')
                    return
                removedActivity = int(number_match.group(1))

                conn = get_connection()
                row = conn.execute(
                    'SELECT id, activity, author_id FROM activities WHERE id = ?',
                    (removedActivity,)
                ).fetchone()
                if row is not None:
                    conn.execute(
                        'INSERT INTO removed_activities (id, activity, author_id) VALUES (?, ?, ?)',
                        row
                    )
                    conn.execute('DELETE FROM activities WHERE id = ?', (removedActivity,))
                    renumber_activities(conn)
                    conn.commit()
                conn.close()

                if row is not None:
                    await ctx.send(f'Removed #{removedActivity}. Everything after it moved down one number.')
                else:
                    await ctx.send('No activity found with that ID.')

            elif command == 'numberedlist':
                ctx.command.reset_cooldown(ctx)
                userId = ctx.message.author.id
                trustedUsers = load_encrypted_id_list('././data/trustedUsers.txt')
                if str(userId) not in trustedUsers:
                    await ctx.send('You do not have permissions for that.')
                    return

                # Full data, as a file - this scales to any number of rows,
                # unlike chunking into a stream of Discord messages. Decrypting
                # a big list takes a moment, so it runs in a worker thread and
                # the bot keeps answering everyone else meanwhile.
                loop = asyncio.get_running_loop()
                count, csv_bytes = await loop.run_in_executor(None, _build_numbered_export)

                if count == 0:
                    await ctx.send('No activities yet.')
                    return

                await ctx.send(
                    f'{count} activities:',
                    file=discord.File(io.BytesIO(csv_bytes), filename='activities.csv')
                )

            elif command == 'list':
                ctx.command.reset_cooldown(ctx)
                conn = get_connection()
                total = conn.execute('SELECT COUNT(*) FROM activities').fetchone()[0]
                conn.close()
                if total == 0:
                    await ctx.send('No activities yet.')
                    return

                # One shared list per channel. If one is already open here,
                # point to it instead of posting another copy.
                existing = self.active_lists.get(ctx.channel.id)
                if existing is not None and existing.message is not None and not existing.is_finished():
                    await ctx.send(
                        f'The list is already open here: {existing.message.jump_url}',
                        delete_after=15
                    )
                    return

                view = ActivityListView()
                view.message = await ctx.send(embed=view.format_page(), view=view)
                self.active_lists[ctx.channel.id] = view

            else:
                try:
                    bannedUsers = load_encrypted_id_list('././data/bannedUsers.txt')
                except FileNotFoundError:
                    bannedUsers = []
                if str(ctx.message.author.id) in bannedUsers:
                    return

                conn = get_connection()
                cursor = conn.execute(
                    'INSERT INTO activities (activity, author_id) VALUES (?, ?)',
                    (encrypt_value(activity), encrypt_value(str(ctx.message.author.id)))
                )
                conn.commit()
                conn.close()
                await ctx.send(
                    f'Added {activity} (#{cursor.lastrowid})',
                    allowed_mentions=discord.AllowedMentions.none()
                )
        else:
            await ctx.send('Light the World is not open yet.')

    @commands.command()
    async def ltwDeleteAll(self, ctx, confirm: str = None):
        """Owner only. Permanently deletes ALL Light The World data (every
        activity and every archived entry, for every server) and restarts the
        numbering at 1. Two steps so it can't happen by accident: run
        -ltwDeleteAll to see what would go, then -ltwDeleteAll confirm within
        60 seconds."""
        if not await self.bot.is_owner(ctx.author):
            await ctx.send('You do not have permissions for that.')
            return

        now = time.monotonic()
        asked_at = self._delete_requests.get(ctx.author.id)
        confirming = (confirm or '').lower() == 'confirm'

        if confirming and asked_at is not None and now - asked_at <= 60:
            self._delete_requests.pop(ctx.author.id, None)
            loop = asyncio.get_running_loop()
            activities, archived = await loop.run_in_executor(None, delete_all_light_the_world_data)
            await ctx.send(
                f'Deleted {activities} activities and {archived} archived entries. '
                'Numbering will start again at #1.'
            )
            return

        conn = get_connection()
        activities = conn.execute('SELECT COUNT(*) FROM activities').fetchone()[0]
        archived = conn.execute('SELECT COUNT(*) FROM removed_activities').fetchone()[0]
        conn.close()
        self._delete_requests[ctx.author.id] = now
        prefix = 'That confirmation expired or was never requested. ' if confirming else ''
        await ctx.send(
            f'{prefix}This will permanently delete {activities} activities and {archived} archived entries '
            'for every server, and numbering will restart at #1. This cannot be undone. '
            'To go ahead, run `-ltwDeleteAll confirm` within 60 seconds.'
        )

async def setup(bot):
    await bot.add_cog(LTW(bot))

