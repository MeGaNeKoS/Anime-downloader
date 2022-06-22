import feedparser

from deps.recognition import recognition

queue = {}
downloads = {}
entries = {}


# parse the RSS feed
def rss(feed_link: str, ignore: list, log: list):
    rss_parser = feedparser.parse(feed_link)

    # only proceed the new entries
    if entries.get(feed_link, None) is None:
        # if this the first time we parse the feed, the new entries are current entries
        new_feeds = rss_parser.entries
    else:
        new_feeds = set(entries[feed_link]).difference(rss_parser.entries)

    for torrent in new_feeds:
        # skip the anime if already downloaded,
        if torrent['title'] in log:
            continue

        anime = recognition.track(torrent["title"], torrent.summary.endswith(" file(s)</a>"))

        # skip if in ignore list,
        if anime["'anime_title'"].lower() in ignore:
            continue

        # get the magnet link
        magnet = "magnet" + str(torrent["summary_detail"].values()).split('href="magnet')[1]
        magnet = magnet.split('">')[0]
        magnet = magnet.replace("&amp;", "&")
        anime['link'] = magnet
        anime['log'] = log  # this mutable,

        # add to the queue list
        queue[anime["anilist"]] = anime

    # update the entries
    entries["feed_link"] = rss_parser.entries
    del log[100:]  # only save last 100 item
