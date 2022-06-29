from src import config
import threading

queue = {}
downloads = {}
lock = threading.Lock()
logs = {}

for link in config.RSS_LIST:
    query = link.partition("q=")[2]
    log_file = f'{config.DATA_DIR}/log/{query}.txt'
    try:
        with open(log_file, 'r') as f:
            log = f.read().splitlines()
    except FileNotFoundError:
        with open(log_file, 'w+') as f:
            pass
        log = []
    logs[query] = log
