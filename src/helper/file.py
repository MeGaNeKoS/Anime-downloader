import os
import threading

from src import config

_cache = {}
file_lock = threading.RLock()

def add_to_log(file_path: list, msg: str):
    """
    Add message to log file
    """
    for path in file_path:
        with file_lock:
            log = read_file(path)
            log.insert(0, msg)
            log = log[:config.MAX_LOG]
            write_file(path, '\n'.join(log))


def read_file(file_path: str) -> list:
    with file_lock:
        try:
            modified_time = os.stat(file_path).st_mtime
            if file_path not in _cache:
                _cache[file_path] = {'mTime': modified_time, 'log': []}
                modified_time = 0
        except FileNotFoundError:
            modified_time = 0
            _cache[file_path] = {'mTime': modified_time, 'log': []}

        if modified_time != _cache[file_path]['mTime']:
            try:
                with open(file_path, 'r+') as input_file:
                    log = input_file.read().splitlines()
            except FileNotFoundError:
                log = []

            _cache[file_path]['mTime'] = modified_time
            _cache[file_path]['log'] = log

        return _cache[file_path]['log']


def write_file(file_path: str, data: str):
    with file_lock:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w+') as output_file:
            output_file.write(data)

        modified_time = os.stat(file_path).st_mtime
        _cache[file_path]['mTime'] = modified_time
