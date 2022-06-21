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
