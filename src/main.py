import sys
import os
import time
import traceback
import threading

import devlog

from src import config
from src.torrent import rss, download
from src.share_var import logs, lock


@devlog.log_on_error(trace_stack=True)
def start_rss():
    while True:

        for link in config.RSS_LIST:
            print(link)
            query = link.partition("q=")[2]
            log_file = f'{config.DATA_DIR}/log/{query}.txt'
            # using os module, check if the file exists
            if not os.path.isfile(log_file):
                # if not, create with folder
                os.makedirs(os.path.dirname(log_file), exist_ok=True)

            with lock:
                file_log = logs.get(query, [])

            with open(f'{config.DATA_DIR}/ignore.txt', 'r+') as input_file:
                ignore = input_file.read().splitlines()

            rss.rss(link, ignore, file_log)
            with lock:
                with open(log_file, 'w+', encoding="utf-8") as output:
                    for magnet_link in file_log:
                        output.write("%s\n" % magnet_link)
            print(f"All rss downloaded. wait {config.CHECK_INTERVAL // 60} minute for recheck")
        time.sleep(config.CHECK_INTERVAL)


def start_qbt():
    # start qbt download manager
    download.connect()
    while True:
        download.check_completion()
        time.sleep(config.CHECK_INTERVAL)


def initialize_gdrive():
    from src import gdrive
    print("gdrive logged in")


def main():
    # creating the thread
    initialize_gdrive()

    threads = []
    threads[0] = threading.Thread(target=start_qbt, daemon=True)
    threads[0].start()
    # start the torrent
    time.sleep(5)
    threads[1] = threading.Thread(target=start_rss, daemon=True)
    threads[1].start()

    for thread in threads:
        thread.join()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Exit using ctrl+c")
        sys.exit(0)
    except Exception as e:
        with open("torrent.log", "a+") as f:
            f.write(f"{e}\n{traceback.format_exc()}")
