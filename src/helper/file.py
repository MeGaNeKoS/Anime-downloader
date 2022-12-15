import os

from src import config

_cache = {}


def add_to_log(filename: str, msg: str):
    """
    Add message to log file
    """

    log = read_file(filename)
    log.insert(0, msg)
    log = log[config.MAX_LOG:]
    write_file(filename, '\n'.join(log))


def read_file(file_path: str) -> list:

    modified_time = os.stat(file_path).st_mtime

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
    with open(file_path, 'w+') as output_file:
        output_file.write(data)

    modified_time = os.stat(file_path).st_mtime
    _cache[file_path]['mTime'] = modified_time