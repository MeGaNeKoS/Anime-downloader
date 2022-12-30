import os
import threading

_cache = {}
_max_log = 100
file_lock = threading.RLock()


def add_to_log(file_path: list, msg: str):
    """
    Add message to log file
    """
    for path in file_path:
        with file_lock:
            log = read_file(path)
            log.insert(0, msg)
            log = log[:_max_log]
            write_file(path, '\n'.join(log))


def read_file(file_path: str) -> list:
    """
    Read file and return the content as list
    """
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
    """
    Write data to file
    """
    with file_lock:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w+') as output_file:
            output_file.write(data)

        modified_time = os.stat(file_path).st_mtime
        _cache[file_path]['mTime'] = modified_time


def set_max_log(max_log: int):
    """
    Set the maximum number of log
    """
    global _max_log
    _max_log = max_log
