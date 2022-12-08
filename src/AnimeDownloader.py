import threading
import time
import traceback

import devlog
from src import config
from src.watcher import download
from src.watcher.rss import start_rss


@devlog.log_on_error(trace_stack=True)
def start_qbt():
    # start qbt download manager
    download.connect()
    err = 0
    while True:
        try:
            download.check_completion()
            time.sleep(config.SLEEP["download_check"])
            err = 0
        except KeyboardInterrupt:
            break
        except Exception as e:
            if err > 10:
                with open("torrent.log", "a+") as f:
                    f.write(f"{e}\n{traceback.format_exc()}")
            err += 1
            time.sleep(20)


def main():
    # creating the thread
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
            time.sleep(10)
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
        for thread in threads:
            thread.join(timeout=1)
