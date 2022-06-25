import logging
import qbittorrentapi
from src import config
import time

logger = logging.getLogger(__name__)
downloads = {}
queue = {}

qbt_client: qbittorrentapi.Client


# connect to client
def connect():
    global qbt_client
    qbt_client = qbittorrentapi.Client(
        host=config.TORRENT_WEB_CLIENT,
        port=config.TORRENT_WEB_CLIENT_PORT,
        username=config.TORRENT_WEB_CLIENT_USERNAME,
        password=config.TORRENT_WEB_CLIENT_PASSWORD,
    )


def remove(anime_id):
    # cancel the download, delete the local files,
    # and add the anime to the log file

    downloads.pop(anime_id, None)

