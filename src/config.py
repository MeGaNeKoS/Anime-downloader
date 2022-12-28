DATA_DIR = {
    "root": "./data",  # required
    "ignored": "./data/ignored.txt",  # required
    "torrent": "./data/torrent",  # required
    "log": "./data/log",  # required
}

# Define the changes for invalid characters in the filename
LEGALIZE_CHARACTER = {':': '：',  # colon to full-width colon
                      '/': '／',  # slash to full-width slash
                      '<': '＜',  # less-than to full-width less-than
                      '>': '＞',  # greater-than to full-width greater-than
                      '\"': '＂',  # double-quote to full-width double-quote
                      '\\': '＼',  # backslash to full-width backslash
                      '|': '｜',  # vertical-line to full-width vertical-line
                      '?': '？',  # question-mark to full-width question-mark
                      '*': '＊'  # asterisk to full-width asterisk
                      }

LOG_FILE = {
    "rss": "rss.log",
    "download": "download.log",
    "main": "app.log",
}

MAX_CONCURRENT_DOWNLOADS = 6
MAX_LOG = 100

RELEASE_GROUP = ('rom & rem',  # consistent but not much anime they have, and also they provide uncensored version
                 'zza',  # They only give batch
                 'hr',  # Good size, have chapter, Good anime name formate
                 'hakata ramen',  # Good size, have chapter, Good anime name formate
                 'judas',  # recognizable file name, have a lot of release
                 "amzero", # Good size, AV1, no chapter, but better thatn asw
                 'asw',  # No chapter :(, have a lot of release
                 'anime time',  # No chapter :(
                 'animerg'  # some of their release are 8 bit
                 )  # order is represent the priority, highest to lowest

RSS_LIST = {
    "amzero": "https://feed.animetosho.org/rss2?only_tor=1&q=amzero+1080",
    "rom & rem 1080.txt": "https://feed.animetosho.org/rss2?only_tor=1&q=Rom+%26+Rem+1080",
    # "animerg 1080.txt": "https://feed.animetosho.org/rss2?only_tor=1&q=AnimeRG+1080",
    "asw 1080.txt": "https://feed.animetosho.org/rss2?only_tor=1&q=ASW+1080",
    "zza 1080.txt": "https://feed.animetosho.org/rss2?only_tor=1&q=zza+1080",
    "hr 1080.txt": "https://feed.animetosho.org/rss2?only_tor=1&q=HR+1080",
    "judas 1080.txt": "https://feed.animetosho.org/rss2?only_tor=1&q=judas+1080",
    "anime time 1080.txt": "https://feed.animetosho.org/rss2?only_tor=1&q=anime+time+1080"
}

RULES = {
    "My Collection 1": {
        "rules": [
            (
                "release_group",
                "in",
                RELEASE_GROUP,
                False,
                True
            )
        ],
        "match_all": True,
        "active": True
    }
}

SLEEP = {
    "rss_check": 10 * 60,  # 10 minutes, required
    "download_check": 10,  # 10 seconds, required
    "global": 3,  # 3 seconds, required
}


CLIENT_CONFIG_ARGS = ("localhost", 8080, "admin", "adminadmin")
CLIENT_CONFIG_KWARGS = {}

UPLOAD_REMOVAl_TIME_SECONDS = 0  # 0 means immediate remove


FOLDER_PATH = {
    "Anime": {
        "0season": r"H:\My Drive\Anime\Unsorted\0 Season",
        "movie": r"H:\My Drive\Anime\Movie",
        "ona": r"H:\My Drive\Anime\ONA",
        "ova": r"H:\My Drive\Anime\OVA",
        "special": r"H:\My Drive\Anime\Special",
        "music": r"H:\My Drive\Anime\MUSIC",
        "tv": r"H:\My Drive\Anime\TV",
        "unknown": r"H:\My Drive\Anime\Unsorted\Torrent",
        "id": r"H:\My Drive\Anime"
    }
}

# Discord stuff
OWNER = ""  # Owner's discord id
DISCORD_NOTIF = "./data/discord_notif.txt"
