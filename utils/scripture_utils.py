import json
from utils.constants import BOMLIST, DCLIST, PGPLIST, OLDTESTLIST, NEWTESTLIST, APOCRYPHALIST, PROCLIST, BOOKNAMEMAP

def is_biblical_references_allowed(id):
    with open("././data/servers.json", "r") as f:  # Adjust to your file path
        serverDict = json.load(f)
    # Default to True if the server is not in the settings file. (The comment below
    # always said this, but nothing set a default, so a server missing from the
    # file crashed with "local variable 'allowed' referenced before assignment".)
    allowed = True
    for item in serverDict:
        if item == str(id):
            if serverDict[item]['bible'] == True:
                allowed = True
            else:
                allowed = False
    # Default to True if the server is not in the settings file
    return allowed


def make_link(book, chapterNumber, script, lowVerse, highVerse):
    abbrevBook = BOOKNAMEMAP.get(book, "Unknown")
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
        link = f"https://www.churchofjesuschrist.org/study/scriptures/dc-testament/od/{chapterNumber}?lang=eng"

    else:
        if highVerse is None:
            link = f"https://www.churchofjesuschrist.org/study/scriptures/{script}/{abbrevBook}/{chapterNumber}?lang=eng&id=p{lowVerse}#p{lowVerse}"
        else:
            link = f"https://www.churchofjesuschrist.org/study/scriptures/{script}/{abbrevBook}/{chapterNumber}?lang=eng&id=p{lowVerse}-p{highVerse}#p{lowVerse}"

    return link

def get_scripture(book, chapterNumber, lowVerse, highVerse, scripture):
    script = ''
    #open json file
    if scripture == "old":
        with open("././data/old-testament.json", "r") as f:
            script = "ot"
            data = json.load(f)
    elif scripture == "new":
        with open("././data/new-testament.json", "r") as f:
            script = "nt"
            data = json.load(f)
    elif scripture == "bom":
        with open("././data/book-of-mormon.json", "r") as f:
            script = "bofm"
            data = json.load(f)
    elif scripture == "pgp":
        script = "pgp"
        with open("././data/pearl-of-great-price.json", "r") as f:
            if book == "jsh" or book == "joseph smith history" or book == "joseph smith-history":
                book = "Joseph Smith—History"
            elif book == "aof" or book == "articles of faith":
                book = "Articles of Faith"
            elif book == "jsm" or book == "joseph smith matthew" or book == "joseph smith-matthew":
                book = "Joseph Smith—Matthew"
            data = json.load(f)
    elif scripture == "proc":
        script = "proc"
        with open("././data/proclamations.json", "r") as f:
            data = json.load(f)
        if book == "family proclamation" or book == "the family":
            book = "the family proclamation"
        elif book == "living christ":
            book = "the living christ"
        elif book == "od":
            book = "official declaration"

    elif scripture == "apoc":
        script = "apoc"
        with open("././data/apocrypha.json", "r") as f:
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

    # Nothing matched (that chapter or verse doesn't exist). Return an empty result
    # instead of None, so callers can quietly skip it instead of crashing.
    return book.title(), int(chapterNumber), [], script, lowVerse, highVerse
