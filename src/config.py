DATA_DIR = {
    "root": "./data",  # required
    "ignored": "./data/ignored.txt",  # required
    "torrent": "./data/torrent",  # required
    "log": "./data/log",  # required
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

LOG_FILE = {
    "rss": "rss.log",
    "download": "download.log",
}

MAX_LOG = 100

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

RULES = {
    "My Rule": {
        "rules": [
            [
                "release_group",
                "in",
                RELEASE_GROUP,
                False,
                True
            ]
        ],
        "match_all": True,
        "active": True
    }
}

SLEEP = {
    "rss_check": 10 * 60,  # 10 minutes, required
    "download_check": 10,  # 1 minute, required
    "global": 3,  # 10 seconds, required
}

