import html
import logging

import atoma
import requests
from requests import RequestException

logger = logging.getLogger(__name__)
entries = {}


def parser(feed_link: str, log: list) -> dict:
    try:
        res = requests.get(feed_link)
    except RequestException as e:
        logger.exception(f'Failed to get RSS feed from {feed_link}: {e}')
        return {}

    try:
        if res.headers.get('content-type', '').startswith('application/atom'):
            rss_parser = atoma.parse_atom_bytes(res.content)
        elif res.headers.get('content-type', '').startswith('application/json'):
            json_content = res.json()
            rss_parser = atoma.parse_json_feed(json_content)
        else:
            rss_parser = atoma.parse_rss_bytes(res.content)
    except (atoma.FeedParseError, atoma.FeedDocumentError) as e:
        logger.info(f'Failed to parse feed {feed_link}: content-type: {res.headers.get("content-type", "")}\n\t{e}')
        return {}

    # only proceed the new entries
    new_feeds = []
    for entry in rss_parser.items:
        if entry not in entries.get(feed_link, []):
            new_feeds.append(entry)

    entries[feed_link] = rss_parser.items
    result = {}
    for torrent in rss_parser.items:
        # skip the anime if already downloaded,
        if torrent.title in log:
            continue
        magnet_link = None
        torrent_link = None

        # This is just a workaround solution, as in bittorrent client can grab the torrent/magnet link
        # from the torrent.link regardless of the link are.
        # For example, animetosho.org return a html link for the page, but the torrent client can still download
        # the file. But if you give the html link to the torrent client, it will not work.

        # get the magnet link
        if str(torrent).find('magnet') != -1:
            strings = str(torrent).split('magnet')
            magnet_link = "magnet" + strings[1].split(strings[0][-1])[0]

            magnet_link = magnet_link.split('">')[0]
            magnet_link = html.unescape(magnet_link)

        if str(torrent).find('.torrent') != -1:
            strings = str(torrent).split('.torrent')
            start = strings[0].rfind('http')
            torrent_link = strings[0][start:] + '.torrent'
            torrent_link = html.unescape(torrent_link)

        if not magnet_link and not torrent_link:
            logger.error(f'Failed to get magnet link or torrent link from {torrent}')
        result.update({torrent.title: [magnet_link, torrent_link]})

    return result
