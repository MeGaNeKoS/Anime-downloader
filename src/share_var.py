from src import config
import threading

queue = {}
downloads = {}
lock = threading.Lock()
logs = {}

for link in config.RSS_LIST:
    query = link.partition("q=")[2]
    logs[query] = []
