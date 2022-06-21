import sys
import time
import traceback

import devlog

from src import config
from src.torrent import rss


@devlog.log_on_error(trace_stack=True)
def main():
    while True:

        for link in config.RSS_LIST:
            log_file = f'{config.DATA_DIR}/log/{link.partition("q=")[2]}.txt'
            try:
                with open(log_file, 'r') as f:
                    log = f.read().splitlines()
            except FileNotFoundError:
                with open(log_file, 'w+') as f:
                    pass
                log = []
            with open(f'{config.DATA_DIR}/ignore.txt', 'r') as f:
                ignore = f.read().splitlines()

            rss.rss(link, ignore, log)
        print("All rss downloaded. wait 10 minute for recheck")
        time.sleep(config.CHECK_INTERVAL)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Exit using ctrl+c")
        sys.exit(0)
    except Exception as e:
        with open("torrent.log", "a+") as f:
            f.write(f"{e}\n{traceback.format_exc()}")
