import os
import logging
import random
import time


from src import helper
from src import gdrive
from deps.recognition import recognition

# This module using basic logging configuration
logger = logging.getLogger(__name__)


def upload(save_path, file_path, *, num_retries=10) -> bool:
    # normalize the path to match this os
    local_save_path = os.path.normpath(save_path)
    file_path = os.path.normpath(file_path)
    folder_path, file_name = os.path.split(file_path)  # type: str, str
    torrent_path = folder_path.split(os.sep)  # type: list

    # replace os invalid characters
    torrent_path = [helper.legalize(name) for name in torrent_path]

    anime = recognition.track(file_name)
    if anime.get("anime_type", "torrent") == "torrent":
        # if the anime undetected, then we can't guarantee the anime title is correct or not
        anime.pop("anime_title", None)
    else:
        # replace os invalid characters
        anime["anime_title"] = helper.legalize(anime["anime_title"])
    remote_save_path = helper.get_destination(anime, torrent_path)

    if anime.get("anime_type", "torrent") != "torrent":
        # remove_list = []
        file_list = gdrive.service.get_files(remote_save_path, sub_folder=True)
        # if the anime already exists, then we don't need to upload it
        if any(file_name in file['name'] for file in file_list):
            return True
        # for item in remove_list:
        #     gdrive.service.delete(item['id'])

    # upload the file
    error_count = 0
    local_file_path = os.path.join(local_save_path, folder_path, file_name)
    for retry_num in range(num_retries + 1):
        try:
            logger.info(f"Uploading {file_name},\n{local_file_path},\n{remote_save_path}")
            gdrive.service.upload(file_name, local_file_path, remote_save_path)
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
