import logging
import os

import devlog

from src import helper
from src.ffmpeg import ffmpeg

# This module using basic logging configuration
logger = logging.getLogger(__name__)


@devlog.log_on_error(trace_stack=True)
def upload(save_path, file_path, *, existing_root=None, track=True, num_retries=10, force=False) -> bool:
    if existing_root is None:
        existing_root = {}
    # normalize the path to match this os
    local_save_path = os.path.normpath(save_path)
    file_path = os.path.normpath(file_path)
    folder_path, file_name = os.path.split(file_path)  # type: str, str
    torrent_path = folder_path.split(os.sep)  # type: list

    anime = helper.parse(file_name, track)

    if anime.get("anime_type", "torrent") == "torrent":
        # if the anime undetected, then we can't guarantee the anime title is correct or not
        anime.pop("anime_title", None)
        # replace os invalid characters
        torrent_path = [helper.legalize(name) for name in torrent_path]
    else:
        # replace os invalid characters
        anime["anime_title"] = helper.legalize(anime["anime_title"])
        torrent_path = []

    save_path = helper.get_destination(anime, torrent_path)

    remove_list = []
    no_download = False
    uncensored = "uncensored" in str(anime.get("other", "")).lower()
    identifier = (f'{anime.get("anime_title")}_'
                  f'{anime.get("episode_number")}')

    file_list = existing_root.get(save_path, {})
    if file_list:
        existing_file = file_list.get(identifier, {})
        if existing_file:
            if existing_file.get("anime_type", "torrent") == "torrent":
                pass
            elif helper.should_download(anime, existing_file, uncensored):
                remove_list.append(existing_file["file_name"])
                file_list[identifier] = anime
            else:
                no_download = True
        else:
            file_list[identifier] = anime

    elif anime.get("anime_type", "torrent") != "torrent":
        file_list = dict.fromkeys(os.listdir(save_path), None)
        for file in file_list:
            existing_file = helper.parse(file, track)

            if existing_file.get("anime_type", "torrent") == "torrent":
                # if the anime undetected, then we can't guarantee the anime title is correct or not
                existing_file.pop("anime_title", None)
            else:
                # replace os invalid characters
                existing_file["anime_title"] = helper.legalize(anime["anime_title"])

            existing_identifier = (f'{anime.get("anime_title")}_'
                                   f'{anime.get("episode_number")}')

            duplicate_file = file_list.get(existing_identifier, {})
            if duplicate_file:
                if helper.should_download(existing_file, duplicate_file, uncensored):
                    remove_list.append(duplicate_file["file_name"])
                    file_list[identifier] = existing_file
                else:
                    remove_list.append(existing_file["file_name"])
                    continue

            if (anime.get("anime_title") == existing_file.get("anime_title")
                    and anime.get("episode_number") == existing_file.get("episode_number")):
                if helper.should_download(anime, existing_file, uncensored):
                    remove_list.append(file)
                    file_list[existing_identifier] = anime
                else:
                    file_list[existing_identifier] = existing_file
                    no_download = True
    if no_download:
        for file in remove_list:
            try:
                os.remove(os.path.join(save_path, file))
            except FileNotFoundError:
                pass
        return True

    # upload the file
    if force:
        name, ext = os.path.splitext(file_name)
        uploaded_name = f'{name}[AnimeTosho Fast Upload]{ext}'
        archive_save_path = os.path.join(save_path, uploaded_name)
    else:
        archive_save_path = os.path.join(save_path, file_name)
    local_file_path = os.path.join(local_save_path, folder_path, file_name)
    for _ in range(num_retries):
        ffmpeg.copy(local_file_path, archive_save_path)
        for file in remove_list:
            try:
                os.remove(os.path.join(save_path, file))
            except FileNotFoundError:
                pass
        break
    else:
        return False
    return True
