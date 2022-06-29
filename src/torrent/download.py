import logging
import os
import threading

import qbittorrentapi
from pymediainfo import MediaInfo

from deps.recognition import recognition
from src import config
from src import helper
from src.torrent import upload
from src.share_var import queue, downloads, lock

logger = logging.getLogger(__name__)
finished = []
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
        # bug on qbittorrent web api 4.3.9
        if torrent["tags"] == "":
            continue
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
        with lock:
            downloads[anime_id_eps] = anime


def add_torrent(num_retries=10):
    with lock:
        anime = next(iter(queue), None)
        if anime is None:
            return
        download = queue.pop(anime)  # guaranteed exists by the previous check
    for i in range(num_retries):
        if qbt_client.torrents_add(download["link"], tags=config.CLIENT_TAG, category=anime) == "Ok.":
            break
    else:
        logger.error(f"Failed to add torrent\n{download}")
        queue[anime] = download
        return
    datas = qbt_client.torrents_info(category=anime)
    if len(datas) != 1:
        logger.error(f"More than one torrent with category {anime}")
    data = datas[0]
    download["hash"] = data['hash']
    download["status"] = "downloading"

    with lock:
        downloads[anime] = download


def remove(anime):
    # cancel the download, delete the local files,
    # and add the anime to the log file
    if isinstance(anime, str):
        if (download := downloads.get(anime) is not None) and download["status"] in ["uploading", "finished"]:
            # the file is in the upload queue, so we won't delete it
            return False
        datas = qbt_client.torrents_info(category=anime)
        if len(datas) != 1:
            logger.error(f"More than one torrent with category {anime}, everything will be deleted")
        for data in datas:  # intentional behavior
            qbt_client.torrents_delete(delete_files=True, torrent_hashes=data['hash'])
        qbt_client.torrents_remove_categories(anime)
        with lock:
            download = downloads.pop(anime, None)
    else:
        qbt_client.torrents_delete(delete_files=True, torrent_hashes=anime['hash'])
        with lock:
            download = downloads.pop(str(anime["anilist"]) + str(anime.get("episode_number", 0)), None)
    # record the anime in the log file
    if download is not None and download.get("log", None) is not None:
        download["log"].insert(0, download["file_name"])
    return True


def upload_file(torrent, download):
    status = []
    file8bit = False
    file_format = ""
    for file in torrent.files:
        # https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-(qBittorrent-4.1)#get-torrent-contents
        if file.priority == 0:  # 0 mean do not download
            continue
        status.append(upload.upload(torrent["save_path"], file["name"]))
        m_info = MediaInfo.parse(os.path.join(torrent["save_path"], file["name"]))
        for track in m_info.tracks:
            if track.track_type.lower() == 'video':
                if track.bit_depth == 8:
                    file8bit = True
                elif track.format != "HEVC":
                    file_format = track.format
    if all(status):
        logger.info(f"{torrent['name']} uploaded")
        with lock:
            global finished
            finished.append(download)
        mention_owner = False
        notif_text = ""
        if file8bit:
            mention_owner = True
            notif_text += "[8bit] "
        if file_format:
            mention_owner = True
            notif_text += f"[{file_format}] "
        notif_text += f"{torrent['name']} uploaded"
        helper.discord_user_notif(notif_text, mention_owner)
        download["status"] = "finished"
    else:
        download["status"] = "downloading"


def check_completion():
    for download in downloads.values():
        if download in finished:
            continue
        torrent = qbt_client.torrents_info(torrent_hashes=download["hash"])
        if len(torrent) != 1:
            logger.error("More than one torrent with hash")
        torrent = torrent[0]

        # check if we finish download the file
        # need to re work this
        if torrent['amount_left'] == 0 and torrent['size'] > 0 and 'paused' not in torrent['state']:
            if download["status"] == "downloading":
                download["status"] = "uploading"
                # create a new thread to upload the file
                thread = threading.Thread(target=upload_file, args=(torrent, download), daemon=True)
                thread.start()
                # if the all uploaded, then remove the download to start another.

            elif download["status"] == "uploading":
                # not sure for now
                pass

    with lock:
        for download in finished:
            remove(download)

    with lock:
        while len(downloads) < 3 and queue:
            add_torrent()

