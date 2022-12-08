RELEASE_GROUP = ('rom & rem',  # consistent but not much anime they have, and also they provide uncensored version
                 'zza',  # They only give batch
                 'hr',  # Good size, have chapter, Good anime name formate
                 'hakata ramen',  # Good size, have chapter, Good anime name formate
                 'judas',  # recognizable file name, have a lot of release
                 'asw',  # No chapter :(, have a lot of release
                 'anime time',  # No chapter :(
                 'animerg'  # some of their release are 8 bit
                 )  # order is represent the priority, highest to lowest
RSS_LIST = {

    "rom & rem 1080.txt": "https://feed.animetosho.org/rss2?only_tor=1&q=Rom+%26+Rem+1080",
    # "animerg 1080.txt": "https://feed.animetosho.org/rss2?only_tor=1&q=AnimeRG+1080",
    "asw 1080.txt": "https://feed.animetosho.org/rss2?only_tor=1&q=ASW+1080",
    "zza 1080.txt": "https://feed.animetosho.org/rss2?only_tor=1&q=zza+1080",
    "hr 1080.txt": "https://feed.animetosho.org/rss2?only_tor=1&q=HR+1080",
    "judas 1080.txt": "https://feed.animetosho.org/rss2?only_tor=1&q=judas+1080",
    "anime time 1080.txt": "https://feed.animetosho.org/rss2?only_tor=1&q=anime+time+1080"
}

DATA_DIR = {
    "root": "./data",  # required
    "ignored": "./data/ignored.txt",  # required
    "torrent": "./data/torrent",  # required
    "log": "./data/log",  # required
}

SLEEP = {
    "rss_check": 10 * 60,  # 10 minutes, required
    "download_check": 10,  # 1 minute, required
}

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

MAX_CONCURRENCY = 6

MAX_LOG = 100

# qbittorrent client
CLIENT_TAG = "auto add anime"
TORRENT_WEB_CLIENT = "localhost"
TORRENT_WEB_CLIENT_PORT = 8080
TORRENT_WEB_CLIENT_USERNAME = "j89qRzEu7ygqXzC"
TORRENT_WEB_CLIENT_PASSWORD = "2W5B9UKNsthLH7a"
MAX_MANUAL_UPLOAD_THREADS = 5
MANUAL_DOWNLOAD_CATEGORY = "manual_download"
MANUAL_DOWNLOAD_TAGS = "track"
MANUAL_CHECK_REQUEST_TAGS = "check"
MANUAL_CHECK_PROGRESS_TAGS = "checking"
MANUAL_RE_DOWNLOAD_TAGS = "redownload"
UPLOAD_REMOVE_TIME = 5 * 60  # 5 minutes

# google drive id stuff
FOLDER_PATH = {
    "Anime": {
        "0season": r"H:\My Drive\Anime\Unsorted\0 Season",
        "movie": r"H:\My Drive\Anime\Movie",
        "ona": r"H:\My Drive\Anime\ONA",
        "ova": r"H:\My Drive\Anime\OVA",
        "special": r"H:\My Drive\Anime\Special",
        "music": r"H:\My Drive\Anime\MUSIC",
        "tv": r"H:\My Drive\Anime\TV",
        "torrent": r"H:\My Drive\Anime\Unsorted\Torrent",
        "id": r"H:\My Drive\Anime"
    }
}

# Discord stuff
OWNER = ""  # Owner's discord id
DISCORD_NOTIF = "./data/discord_notif.txt"
