# should be a tuple
RELEASE_GROUP = ('qas',  # Good if it batch, else it too risky since they are not always consistent
                 'rom & rem',  # consistent but not much anime they have, and also they provide uncensored version
                 'zza',  # They only give batch
                 'HR',  # Good size, have chapter, Good anime name formate
                 'judas',  # recognizable file name, have a lot of release
                 'asw',  # No chapter :(, have a lot of release
                 'anime time',  # No chapter :(
                 'animerg'  # some of their release are 8 bit
                 )
DATA_DIR = "./data"
RSS_LIST = ["https://feed.animetosho.org/rss2?only_tor=1&q=qas+1080",
            "https://feed.animetosho.org/rss2?only_tor=1&q=Rom+%26+Rem+1080",
            "https://feed.animetosho.org/rss2?only_tor=1&q=AnimeRG+1080",
            "https://feed.animetosho.org/rss2?only_tor=1&q=ASW+1080",
            "https://feed.animetosho.org/rss2?only_tor=1&q=zza+1080",
            "https://feed.animetosho.org/rss2?only_tor=1&q=HR+1080",
            "https://feed.animetosho.org/rss2?only_tor=1&q=judas+1080",
            "https://feed.animetosho.org/rss2?only_tor=1&q=anime+time+1080"
            ]
CHECK_INTERVAL = 60

LEGALIZE_CHARACTER = {':': '：',
                      '/': '／',
                      '<': '＜',
                      '>': '＞',
                      '\"': '＂',
                      '\\': '＼',
                      '|': '｜',
                      '?': '？',
                      '*': '＊'
                      }

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
