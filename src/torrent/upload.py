import logging
import os

import devlog

from src import helper
from src.ffmpeg import ffmpeg

# This module using basic logging configuration
logger = logging.getLogger(__name__)


@devlog.log_on_error(trace_stack=True)
def upload(local_save_path, file_path, *, existing_root=None, track=True, num_retries=10, force=False) -> bool:
    if existing_root is None:
        existing_root = {}
    # normalize the path to match this os
    file_path = os.path.normpath(file_path)
    folder_path, file_name = os.path.split(file_path)  # type: str, str
    torrent_path = folder_path.split(os.sep)  # type: list
    local_save_path = os.path.normpath(local_save_path)
    no_download, remove_list, save_path = helper.check_file(file_name, torrent_path, existing_root, track)
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
