RELEASE_GROUP = ('rom & rem',  # consistent but not much anime they have, and also they provide uncensored version
                 'zza',  # They only give batch
                 'HR',  # Good size, have chapter, Good anime name formate
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

MAX_CONCURRENCY = 20

MAX_LOG = 100

# qbittorrent client
CLIENT_TAG = "auto add anime"
TORRENT_WEB_CLIENT = "localhost"
TORRENT_WEB_CLIENT_PORT = 8080
TORRENT_WEB_CLIENT_USERNAME = "admin"
TORRENT_WEB_CLIENT_PASSWORD = "password"
MAX_MANUAL_UPLOAD_THREADS = 5
MANUAL_DOWNLOAD_CATEGORY = "manual_download"
MANUAL_DOWNLOAD_TAGS = "track"
UPLOAD_REMOVE_TIME = 5 * 60  # 5 minutes

# google drive id stuff
FOLDER_LINK = {
    "Anime": {
        "0season": "1sZwVyck4uxkT4iTNjGXBMR4MTmXFZOnj",
        "movie": "19ghf02sf-AMU2q2hJcx_y2N7mgazq_bB",
        "ona": "1WRvqvZtOCzBpgfZsDQAANxFp-P3vSAJ5",
        "ova": "1vYkcB1YzqgPF3otCZ3QNIXkWhlRkbDQe",
        "special": "1Ux08TLqGDaKY-xQo5_vCMgClYxZJMpUX",
        "tv": "164vTWwEibhpZPpb2rsIu2qcSmbLNMwYz",
        "torrent": "1M7wSjpI5K0AQXHfYqo6L93M1JMQf8IiI",
        "id": "13kayspoKTJ16a-uI_301TxP8X50TeQ0c"
    }
}

# Discord stuff
OWNER = ""  # Owner's discord id
DISCORD_NOTIF = "./data/discord_notif.txt"
