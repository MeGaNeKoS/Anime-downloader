import logging
import qbittorrentapi
from src import config
from deps.recognition import recognition
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
    torrents = qbt_client.torrents_info(tag=config.CLIENT_TAG)
    for torrent in torrents:
        anime_id_eps = torrent['category']
        # it's a folder
        if len(torrent.files) != 1:
            anime = recognition.track(torrent["name"], True)
        else:
            name = torrent['name']
            for char in name[:-6:-1]:
                # we found the file extensions in the title
                if char == ".":
                    anime = recognition.track(name)
                    break
            else:
                # force add an extensions since the title from torrent usually doesn't include extensions
                anime = recognition.track(name + ".mkv")
        anime["hash"] = torrent['hash']
        anime["status"] = "downloading"

        downloads[anime_id_eps] = anime


def add_torrent(num_retries=10):
    anime = next(iter(queue))
    download = queue.pop(anime)
    for i in range(num_retries):
        if qbt_client.torrents_add(download["link"], tags=config.CLIENT_TAG, category=anime) == "Ok.":
            break
    else:
        logger.error(f"Failed to add torrent\n{download}")
        queue[anime] = download
        return
    datas = qbt_client.torrents_info(category=anime)
    if len(datas) != 1:
        logger.error("More than one torrent with category anime_id")
    data = datas[0]
    download["hash"] = data['hash']
    download["status"] = "downloading"

    downloads[anime] = download


def remove(anime_id):
    # cancel the download, delete the local files,
    # and add the anime to the log file

    downloads.pop(anime_id, None)

