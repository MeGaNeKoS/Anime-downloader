import feedparser

from deps.recognition import recognition
from src.torrent import download
from src import database
from src import helper


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
        if torrent.summary.endswith(" file(s)</a>"):
            anime = recognition.track(torrent["title"], True)
        else:
            # force add an extensions since the title from torrent usually doesn't include extensions
            anime = recognition.track(torrent["title"] + ".mkv")

        # skip if in ignore list,
        if anime["anime_title"].lower() in ignore:
            continue

        # get the magnet link
        magnet = "magnet" + str(torrent["summary_detail"].values()).split('href="magnet')[1]
        magnet = magnet.split('">')[0]
        magnet = magnet.replace("&amp;", "&")
        anime['link'] = magnet
        anime['log'] = log  # this mutable,

        if anime.get("anime_type", "torrent").lower() == "torrent" or anime.get("anilist", 0) == 0:
            # this anime can't be detected :( put to torrent folder instead.
            queue[torrent['title']] = anime
            continue

        # check if the anime already in queue list
        if waiting := queue.get(anime["anilist"]):
            # if already exist, check for the fansub priority
            if helper.fansub_priority(waiting["release_group"], anime["release_group"]):
                # the first fansub has higher priority
                # so this title will not be downloaded
                # add to log if not exist
                if torrent['title'] not in log:
                    log.insert(0, torrent['title'])
                continue
            # replace the queue with the new one
            # I don't want to make a race condition to another process
            # better to remove then re add it again
            queue.pop(anime["anilist"], None)

        # check if the anime already in download list
        if waiting := downloads.get(anime["anilist"]):
            # if already exist, check for the priority
            if helper.fansub_priority(waiting["release_group"], anime["release_group"]):
                # the first fansub has higher priority
                # so this title will not be downloaded
                # add to log if not exist
                if torrent['title'] not in log:
                    log.insert(0, torrent['title'])
                continue
            # remove from download list and download manager
            download.remove(anime["anilist"])

        # check the fansub preference from the database
        if from_db := database.db.select("preference", {"anime_id": anime["anilist"]}):
            if helper.fansub_priority(from_db[0]["release_group"], anime["release_group"]):
                # we already download this anime, but the higher priority fansub is exists,
                # thus we skip this one and wait for that fansub
                if torrent['title'] not in log:
                    log.insert(0, torrent['title'])
                continue
            else:
                # this anime fansub has higher priority,
                # so we update the fansub preference with the new one.
                from_db[0]["release_group"] = anime["release_group"]
                database.db.insert("preference", from_db[0])
        else:
            # if the preference is empty,
            # then create new preference entry
            to_db = {
                "anime_name": anime["anime_title"],
                "anime_id": anime["anilist"],
                "release_group": anime["release_group"]
            }
            database.db.insert("preference", to_db)

        # add to the queue list
        queue[anime["anilist"]] = anime

    # update the entries
    entries[feed_link] = rss_parser.entries
    del log[100:]  # only save last 100 item
