import logging
import os
import shlex
import subprocess
import sys
import threading

import devlog
import requests

logger = logging.getLogger(__name__)

session = requests


@devlog.log_on_error(trace_stack=True)
def load_local(path):
    logger.info(f"Downloading {path}")
    for _ in range(10):
        try:
            with open(path, 'rb') as f:
                f.read()
            break
        except Exception:
            pass


def copy(local_save_path, archive_save_path) -> bool:
    t = threading.Thread(target=load_local, args=(local_save_path,), daemon=True)
    t.start()

    old_path = sanitize_path(local_save_path)
    new_path = sanitize_path(archive_save_path)

    # create the folder if it doesn't exist
    if not os.path.exists(os.path.dirname(archive_save_path)):
        os.makedirs(os.path.dirname(archive_save_path))

    cmd = f"ffmpeg -v quiet -hide_banner -y -i {old_path} -map 0 -c copy {new_path}"
    try:
        rehashed = subprocess.run(cmd, shell=True, check=True)
        rehashed.check_returncode()
        t.join()
    except Exception:
        try:
            os.remove(new_path.strip('"'))
        except FileNotFoundError:
            pass
        t.join()
        return False
    return True


def sanitize_path(path, max_length=256):
    if sys.platform.startswith("win") or sys.platform.startswith("cygwin"):
        if len(path) > max_length:
            if not path.startswith("\\\\?\\"):
                path = r'\\?\{}'.format(path)
        if not path.startswith('"'):
            path = f'"{path}'
        if not path.endswith('"'):
            path = f'{path}"'
        sanitized_path = path
    else:
        sanitized_path = shlex.quote(os.path.join(path))
    return sanitized_path
