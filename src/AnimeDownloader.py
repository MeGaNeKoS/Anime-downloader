import threading
import time

from src import config
from src.watcher import download
from src.watcher.rss import start_rss


def start_qbt():
    # start qbt download manager
    download.connect()
    while True:
        try:
            download.check_completion()
            time.sleep(config.SLEEP["download_check"])
        except KeyboardInterrupt:
            break


def initialize_gdrive():
    from src import gdrive
    gdrive.login()
    print("gdrive logged in")


def main():
    # creating the thread
    initialize_gdrive()

    threads = []
    thread = threading.Thread(target=start_qbt, daemon=True)
    thread.start()
    threads.append(thread)
    # start the torrent
    time.sleep(5)
    print("Start 2nd thread")
    thread = threading.Thread(target=start_rss, daemon=True)
    thread.start()
    threads.append(thread)
    thread_status = [thread.is_alive() for thread in threads]
    try:
        while any(thread_status):
            thread_status = [thread.is_alive() for thread in threads]
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
        for thread in threads:
            thread.join(timeout=1)
