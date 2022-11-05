import logging
import os
import random
import time

import devlog

from deps.recognition import recognition
from src import gdrive
from src import helper
from src.ffmpeg import ffmpeg

# This module using basic logging configuration
logger = logging.getLogger(__name__)


@devlog.log_on_error(trace_stack=True)
def upload(save_path, file_path, *, track=True, num_retries=10) -> bool:

    # normalize the path to match this os
    local_save_path = os.path.normpath(save_path)
    file_path = os.path.normpath(file_path)
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
        return True
    # upload the file
    error_count = 0
    archive_save_path = os.path.join(local_save_path, folder_path, file_name + ".mkv")
    local_file_path = os.path.join(local_save_path, folder_path, file_name)
    upload_path = ffmpeg.copy(local_file_path, archive_save_path)

    for retry_num in range(num_retries + 1):
        try:
            logger.info(f"Uploading {file_name},\n{local_file_path},\n{remote_save_path}")
            gdrive.service.upload(file_name, upload_path, remote_save_path)
            try:
                os.remove(archive_save_path)
            except Exception:
                pass
            break
        except (BrokenPipeError, ConnectionResetError):
            # We got a connection error, so we'll retry
            logger.error(f"Failed, and restarting {file_name},\n{local_file_path},\n{remote_save_path}")
            error_count += 1
            sleep_time = random.random() * 2 ** retry_num
            time.sleep(sleep_time)
    else:
        # We tried num_retries number of times, and still haven't succeeded
        logger.error(f"Failed {file_name},\n{local_file_path},\n{remote_save_path}")
        return False
    return True
