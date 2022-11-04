import logging
import os
import threading
import time

import qbittorrentapi
from pymediainfo import MediaInfo

from deps.recognition import recognition
from src import config, gdrive
from src import helper
from src.share_var import queue, downloads, download_lock, queue_lock
from src.torrent import upload

logger = logging.getLogger(__name__)
finished = []
upload_threads = []
upload_remove_time = {}
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
            if "." in name[:-6:-1]:
                # we found the file extensions in the title
                anime = recognition.track(name)
            else:
                # force add an extensions since the title from torrent usually doesn't include extensions
                anime = recognition.track(name + ".mkv")
                anime["file_name"] = name

        anime["hash"] = torrent['hash']
        anime["status"] = "downloading"
        with download_lock:
            downloads[anime_id_eps] = anime


def add_torrent(num_retries=10):
    with queue_lock:
        category = next(iter(queue), None)
        if category is None:
            return

        download = queue.pop(category)  # guaranteed exists by the previous check
    for i in range(num_retries):
        if qbt_client.torrents_add(download["link"], tags=config.CLIENT_TAG, category=category) == "Ok.":
            break
        time.sleep(5)
    else:
        logger.error(f"Failed to add torrent\n{download}")
        with queue_lock:
            queue[category] = download
        return
    datas = qbt_client.torrents_info(category=category)
    if len(datas) != 1:
        logger.error(f"More than one torrent with category {category}")
        with queue_lock:
            queue[category] = download
        return
    data = datas[0]
    download["hash"] = data['hash']
    download["status"] = "downloading"
    threading.Thread(target=check_torrent, args=(data,)).start()

    with download_lock:
        downloads[category] = download


def remove_torrent(anime_or_category):
    # cancel the download, delete the local files,
    # and add the anime to the log file

    if isinstance(anime_or_category, str):
        with download_lock:
            download = downloads.get(anime_or_category)
            if download is None:
                return True
            if download["status"] in ["uploading", "finished"]:
                # the file is in the upload queue, so we won't delete it
                return False
            datas = qbt_client.torrents_info(category=anime_or_category)
            if len(datas) != 1:
                logger.error(f"More than one torrent with category {anime_or_category}, everything will be deleted")
            for data in datas:  # intentional behavior
                qbt_client.torrents_delete(delete_files=True, torrent_hashes=data['hash'])
            qbt_client.torrents_remove_categories(anime_or_category)
            download = downloads.pop(anime_or_category, None)
            finished.remove(anime_or_category) if anime_or_category in finished else None
    else:
        with download_lock:
            qbt_client.torrents_delete(delete_files=True, torrent_hashes=anime_or_category['hash'])
            if anime_or_category.get("anime_type", "torrent").lower() == "torrent" or anime_or_category.get("anilist",
                                                                                                            0) == 0:
                # this anime can't be detected :( put to torrent folder instead.
                key = anime_or_category['file_name']
            else:
                key = str(anime_or_category["anilist"]) + str(anime_or_category.get("episode_number", 0))
            download = downloads.pop(key, None)
            finished.remove(key) if key in finished else None
        qbt_client.torrents_remove_categories(key)
    # record the anime in the log file
    if download is not None and download.get("log_file", None) is not None:
        helper.add_to_log(download["log_file"], download["file_name"])
    return True


def check_completion():
    with download_lock:
        for download in downloads.values():
            if download in finished:
                continue
            torrent = qbt_client.torrents_info(torrent_hashes=download["hash"])
            # remove non-existing torrent
            if not torrent:
                finished.append(download)
                continue
            if len(torrent) != 1:
                logger.error("More than one torrent with hash")
            torrent = torrent[0]

            # check if we finish download the file
            # https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-(qBittorrent-4.1)#torrent-management
            if (torrent['amount_left'] == 0 and torrent['size'] > 0 and
                    torrent['progress'] > 0.99):
                if download["status"] == "downloading":
                    download["status"] = "uploading"
                    # create a new thread to upload the file
                    thread = threading.Thread(target=upload_file, args=(torrent, download), daemon=True)
                    thread.start()
                    # if the all uploaded, then remove the download to start another.

                elif download["status"] == "uploading":
                    # not sure for now
                    pass

        for download in finished:
            remove_torrent(download)

        while len(downloads) < config.MAX_CONCURRENCY and queue:
            logger.error(f"Len download: {len(downloads)}, {config.MAX_CONCURRENCY}")
            add_torrent()

    # check for the manual torrents download
    for download in qbt_client.torrents_info(category=config.MANUAL_DOWNLOAD_CATEGORY):
        if download["hash"] in upload_threads or len(upload_threads) >= config.MAX_MANUAL_UPLOAD_THREADS:
            continue
        torrent = qbt_client.torrents_info(torrent_hashes=download["hash"])
        if len(torrent) != 1:
            logger.error(f"More than one torrent with hash {download['hash']}")
        torrent = torrent[0]

        # check if we finish download the file
        # https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-(qBittorrent-4.1)#torrent-management
        if (torrent['amount_left'] == 0 and torrent['size'] > 0
                and torrent['progress'] > 0.99):
            # create a new thread to upload the file
            thread = threading.Thread(target=upload_manual, args=(torrent,), daemon=True)
            thread.start()
            upload_threads.append(torrent["hash"])

    finished_manual = []
    with download_lock:
        # check if there is a manual torrent that is finished uploading
        for torrent_hash, torrent_detelion_time in upload_remove_time.items():
            if torrent_detelion_time < time.time():
                # remove the torrent from the qbt client
                qbt_client.torrents_delete(delete_files=True, torrent_hashes=torrent_hash)
                upload_threads.remove(torrent_hash)
                finished_manual.append(torrent_hash)

        for torrent_hash in finished_manual:
            upload_remove_time.pop(torrent_hash)


def check_torrent(torrent, track=True):
    while torrent.state == "metaDL" or torrent.state == "checkingResumeData":
        torrents = qbt_client.torrents_info(torrent_hashes=torrent["hash"])
        torrent = torrents[0]
        time.sleep(1)
    for file_torrent in torrent.files:
        file_path = os.path.normpath(file_torrent['name'])
        folder_path, file_name = os.path.split(file_path)  # type: str, str
        torrent_path = folder_path.split(os.sep)  # type: list

        if track:
            try:
                anime = recognition.track(file_name)
                if anime.get("anilist", 0) == 0:
                    anime["anime_type"] = "torrent"
            except Exception:
                anime = {"anime_type": "torrent"}
        else:
            anime, _ = recognition.parsing(file_name, False)
            anime["anime_type"] = "torrent"

        if anime.get("anime_type", "torrent") == "torrent":
            # if the anime undetected, then we can't guarantee the anime title is correct or not
            anime.pop("anime_title", None)
            # replace os invalid characters
            torrent_path = [helper.legalize(name) for name in torrent_path]
        else:
            # replace os invalid characters
            anime["anime_title"] = helper.legalize(anime["anime_title"])
            torrent_path = []

        remote_save_path = helper.get_destination(anime, torrent_path)

        remove_list = []
        no_download = False
        file_list = gdrive.service.get_files(remote_save_path, sub_folder=True)
        # if the anime already exists, then we don't need to upload it
        if any(file_name in file['name'] for file in file_list):
            return True
        uncensored = "uncensored" in str(anime.get("other", "")).lower()
        if anime.get("anime_type", "torrent") != "torrent":
            for file in file_list:
                try:
                    existing, _ = recognition.parsing(file, False)
                except Exception:
                    continue
                if (anime.get("anime_title") == existing.get("anime_title") and
                        anime.get("episode_number") == existing.get("episode_number")):
                    if anime.get("release_version", 1) > existing.get("release_version", 0):
                        remove_list.append(file)
                    elif uncensored and "uncensored" not in str(existing.get("other", "")).lower():
                        remove_list.append(file)
                    elif helper.fansub_priority(anime.get("release_group", ""), existing.get("release_group", "")) == 1:
                        remove_list.append(file)
                    else:
                        no_download = True

        for item in remove_list:
            gdrive.service.delete(item['id'])
        if no_download:
            qbt_client.torrents_file_priority(torrent["hash"], file_torrent.id, 0)


def upload_file(torrent, download):
    status = []
    file8bit = False
    file_format = ""
    for file in torrent.files:
        # https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-(qBittorrent-4.1)#get-torrent-contents
        if file.priority == 0:  # 0 mean do not download
            continue
        status.append(upload.upload(torrent["save_path"], file["name"]))
        try:
            m_info = MediaInfo.parse(os.path.join(torrent["save_path"], file["name"]))

            for track in m_info.tracks:
                if track.track_type.lower() == 'video':
                    if track.bit_depth == 8:
                        file8bit = True
                    elif track.format != "HEVC":
                        file_format = track.format
        except Exception:
            pass
    if all(status):
        logger.info(f"{torrent['name']} uploaded")
        with download_lock:
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


def upload_manual(torrent):
    status = []
    file8bit = False
    file_format = ""
    tags = torrent["tags"].split(",")  # it already guaranties that the tag can't have comma in it
    track = config.MANUAL_DOWNLOAD_TAGS in tags

    for file in torrent.files:
        # https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-(qBittorrent-4.1)#get-torrent-contents
        if file.priority == 0:  # 0 mean do not download
            continue
        m_info = MediaInfo.parse(os.path.join(torrent["save_path"], file["name"]))
        for track in m_info.tracks:
            if track.track_type.lower() == 'video':
                if track.bit_depth == 8:
                    file8bit = True
                elif track.format != "HEVC":
                    file_format = track.format
        status.append(upload.upload(torrent["save_path"], file["name"], track=track))
    if all(status):
        logger.info(f"{torrent['name']} uploaded")
        with download_lock:
            upload_remove_time[torrent["hash"]] = time.time() + config.UPLOAD_REMOVE_TIME
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

    else:
        pass
    # we finish upload the file
    with download_lock:
        global upload_threads
        upload_threads.remove(torrent["hash"])
